"""Report requirements: ownership, AI validation, replay, payments and audit scope."""

from datetime import date
from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import AuditLog, User
from tests.test_admissions import add_student, admissions, approve, payload, submit  # noqa: F401
from tests.test_auth_api import PASSWORD, seed_user
from tests.test_classrooms import foundation  # noqa: F401
from tests.test_courses import catalog_fixture  # noqa: F401
from tests.test_schedules import schedule  # noqa: F401

BASE = "/api/v1"


def test_locked_account_message_requires_correct_password(admissions):  # noqa: F811
    f = admissions["f"]
    email = "locked-report@example.com"
    uid, _ = seed_user(f[1], f[2], role="staff", email=email)
    with Session(f[1]) as db:
        db.get(User, UUID(uid)).is_active = False
        db.commit()
    wrong = f[0].post(BASE + "/auth/login", json={"email": email, "password": "incorrect-password"})
    assert wrong.status_code == 401 and wrong.json()["error"]["code"] == "INVALID_CREDENTIALS"
    valid = f[0].post(BASE + "/auth/login", json={"email": email, "password": PASSWORD})
    assert valid.status_code == 403 and valid.json()["error"]["code"] == "ACCOUNT_LOCKED"


def test_advisor_fallback_filters_warnings_and_requires_availability(admissions, monkeypatch):  # noqa: F811
    s, f = admissions, admissions["f"]
    rows = [
        {"id": uuid4(), "code": "MATCH", "name": "Matching class", "seats_left": 2, "warnings": []},
        {
            "id": uuid4(),
            "code": "MISMATCH",
            "name": "Wrong time",
            "seats_left": 2,
            "warnings": ["ADMISSION_AVAILABILITY_REVIEW"],
        },
        {
            "id": uuid4(),
            "code": "LEVEL",
            "name": "Unknown level",
            "seats_left": 2,
            "warnings": ["ADMISSION_LEVEL_REVIEW"],
        },
    ]
    monkeypatch.setattr("app.services.admissions.candidates", lambda *_: rows)
    monkeypatch.setattr("app.services.ai.recommendations.invoke", lambda *_: None)
    data = {
        "course_id": f[6]["id"],
        "availability": [{"weekday": 0, "starts_at": "18:00", "ends_at": "21:00"}],
    }
    preview = f[0].post(BASE + "/ai/recommendations/preview", headers=s["learner"], json=data)
    assert preview.status_code == 200, preview.text
    assert preview.json()["mode"] == "rule"
    assert [c["code"] for c in preview.json()["items"]] == ["MATCH"]
    assert (
        f[0]
        .post(
            BASE + "/ai/recommendations/preview",
            headers=s["learner"],
            json={**data, "availability": []},
        )
        .status_code
        == 422
    )
    assert (
        f[0]
        .post(
            BASE + "/ai/recommendations/preview",
            headers=s["learner"],
            json={**data, "student_id": str(uuid4())},
        )
        .status_code
        == 403
    )


def test_passing_rule_is_optional_validated_and_cloned(admissions):  # noqa: F811
    from tests.test_results import components

    f = admissions["f"]
    body = payload(
        course_id=f[6]["id"], name="Passing rule", passing_percent="65.50", components=components()
    )
    result = f[0].post(BASE + "/results/schemes", headers=f[5], json=body)
    assert result.status_code == 201, result.text
    scheme = result.json()
    assert float(scheme["passing_percent"]) == 65.5
    clone = f[0].post(
        BASE + f"/results/schemes/{scheme['id']}/clone",
        headers=f[5],
        json=payload(version=scheme["version"]),
    )
    assert clone.status_code == 201 and float(clone.json()["passing_percent"]) == 65.5
    invalid = f[0].post(
        BASE + "/results/schemes",
        headers=f[5],
        json={**body, "request_key": str(uuid4()), "passing_percent": 101},
    )
    assert invalid.status_code == 422


def test_preferred_class_survives_request_and_placement(admissions):  # noqa: F811
    s = admissions
    row = submit(s, preferred_class_id=s["class_id"])
    assert row["preferred_class_id"] == s["class_id"]
    placed, _ = approve(s, row)
    assert placed["status"] == "placed"
    assert placed["preferred_class_id"] == s["class_id"]


def generator(_db, _tenant, _task, _locale, data, validator):
    return validator(
        {
            "questions": [
                {
                    "stem": f"Select the right English greeting for scenario {i}.",
                    "options": ["Hello", "Goodbye"],
                    "correct_index": 0,
                    "explanation": "Hello is a greeting.",
                }
                for i in range(data["question_count"])
            ]
        }
    ), None


def test_private_practice_validation_ownership_and_replay(admissions, monkeypatch):  # noqa: F811
    s, f = admissions, admissions["f"]
    monkeypatch.setattr("app.services.practice_sets.invoke", generator)
    body = payload(
        course_id=f[6]["id"], topic="Greetings", level="A2", difficulty="easy", question_count=2
    )
    response = f[0].post(BASE + "/practice/sets/generate", headers=s["learner"], json=body)
    assert response.status_code == 200, response.text
    row = response.json()
    assert len(row["questions"]) == 2
    assert "correct_index" not in response.text and "explanation" not in response.text
    replay = f[0].post(BASE + "/practice/sets/generate", headers=s["learner"], json=body)
    assert replay.json()["id"] == row["id"]
    _, other = add_student(s, "other-practice@example.com")
    path = BASE + "/practice/sets/" + row["id"]
    assert f[0].get(path, headers=other).status_code == 404
    assert f[0].post(path + "/submit", headers=other, json={"answers": [0, 0]}).status_code == 404
    assert (
        f[0].post(path + "/submit", headers=s["learner"], json={"answers": [0]}).status_code == 422
    )
    done = f[0].post(path + "/submit", headers=s["learner"], json={"answers": [0, 1]})
    assert done.status_code == 200, done.text
    assert done.json()["score_percent"] == 50
    again = f[0].post(path + "/submit", headers=s["learner"], json={"answers": [1, 1]})
    assert again.json() == done.json()
    assert (
        f[0]
        .get(BASE + "/practice/sets/mine", headers=s["learner"])
        .json()["items"][0]["score_percent"]
        == 50
    )
    for count in (0, 21):
        assert (
            f[0]
            .post(
                BASE + "/practice/sets/generate",
                headers=s["learner"],
                json={**body, "question_count": count},
            )
            .status_code
            == 422
        )
    for count in (1, 20):
        r = f[0].post(
            BASE + "/practice/sets/generate",
            headers=s["learner"],
            json={**body, "request_key": str(uuid4()), "question_count": count},
        )
        assert r.status_code == 200, r.text
        assert len(r.json()["questions"]) == count


def test_invalid_ai_set_is_not_saved(admissions, monkeypatch):  # noqa: F811
    s, f = admissions, admissions["f"]

    def bad(_db, _tenant, _task, _locale, data, validator):
        return validator({"questions": []}), None

    monkeypatch.setattr("app.services.practice_sets.invoke", bad)
    r = f[0].post(
        BASE + "/practice/sets/generate",
        headers=s["learner"],
        json=payload(course_id=f[6]["id"], topic="Greetings", level="A2", question_count=2),
    )
    assert r.status_code == 422
    assert not f[0].get(BASE + "/practice/sets/mine", headers=s["learner"]).json()["items"]
    monkeypatch.setattr("app.services.practice_sets.invoke", lambda *_: None)
    assert (
        f[0]
        .post(
            BASE + "/practice/sets/generate",
            headers=s["learner"],
            json=payload(course_id=f[6]["id"], topic="Greetings", level="A2", question_count=2),
        )
        .status_code
        == 503
    )


def test_reports_payment_reference_and_audit_scope(admissions):  # noqa: F811
    s, f = admissions, admissions["f"]
    approve(s, submit(s))
    first = f[0].get(BASE + "/admissions/invoices", headers=s["learner"]).json()["items"][0]
    payment = payload(amount=100, method="transfer", reference=" BANK-001 ")
    path = BASE + f"/admissions/invoices/{first['id']}/payments"
    assert f[0].post(path, headers=f[5], json=payment).status_code == 200
    assert f[0].post(path, headers=f[5], json=payment).status_code == 200
    second_id, _ = add_student(s, "second-invoice@example.com")
    s["student"] = second_id
    approve(s, submit(s))
    invoices = f[0].get(BASE + "/admissions/invoices", headers=f[5]).json()["items"]
    second = next(i for i in invoices if i["id"] != first["id"])
    duplicate = f[0].post(
        BASE + f"/admissions/invoices/{second['id']}/payments",
        headers=f[5],
        json=payload(amount=100, method="transfer", reference="bank-001"),
    )
    assert (
        duplicate.status_code == 409
        and duplicate.json()["error"]["code"] == "PAYMENT_REFERENCE_USED"
    )
    today = date.today().isoformat()
    query = f"?starts_on={today}&ends_on={today}"
    report = f[0].get(BASE + "/reports/training" + query, headers=f[5])
    assert report.status_code == 200, report.text
    assert report.json()["collected"] == 100
    assert report.json()["active_enrollments"] == 2
    assert report.json()["attendance_percent"] is None
    assert f[0].get(BASE + "/reports/training" + query, headers=s["learner"]).status_code == 403
    assert (
        f[0]
        .get(BASE + "/reports/training?starts_on=2026-02-01&ends_on=2026-01-01", headers=f[5])
        .status_code
        == 422
    )
    assert (
        f[0]
        .get(BASE + "/reports/training" + query + "&class_id=" + str(uuid4()), headers=f[5])
        .status_code
        == 404
    )
    export = f[0].get(BASE + "/reports/training.csv" + query, headers=f[5])
    assert export.status_code == 200 and "text/csv" in export.headers["content-type"]
    with Session(f[1]) as db:
        actor = db.scalar(select(User))
        db.add(
            AuditLog(
                actor_id=actor.id,
                organization_id=UUID(f[3]),
                action="secret.other",
                details={"secret": "DO_NOT_EXPOSE"},
            )
        )
        db.commit()
    logs = f[0].get(BASE + "/audit-logs", headers=f[5])
    assert logs.status_code == 200, logs.text
    assert "secret.other" not in logs.text and "details" not in logs.text
    assert f[0].get(BASE + "/audit-logs", headers=s["learner"]).status_code == 403
