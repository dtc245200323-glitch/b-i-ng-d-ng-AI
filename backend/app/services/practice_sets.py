"""Generation is external; grading and ownership stay on the server."""

from sqlalchemy import select

from app.core.errors import APIError
from app.core.security import now, utc
from app.models import Course, CourseLanguage, PracticeSet, StudentProfile
from app.services.ai.routing import invoke
from app.services.practice import valid_question


def view(row):
    result = {
        "id": row.id,
        "course_id": row.course_id,
        "topic": row.topic,
        "level": row.level,
        "difficulty": row.difficulty,
        "locale": row.locale,
        "created_at": utc(row.created_at),
        "completed_at": utc(row.completed_at) if row.completed_at else None,
        "questions": [{"stem": q["stem"], "options": q["options"]} for q in row.questions],
    }
    if row.completed_at:
        correct = sum(
            a == q["correct_index"] for a, q in zip(row.answers, row.questions, strict=True)
        )
        result.update(
            answers=row.answers,
            correct_count=correct,
            score_percent=round(correct * 100 / len(row.questions), 1),
            feedback=[
                {"correct_index": q["correct_index"], "explanation": q["explanation"]}
                for q in row.questions
            ],
        )
    return result


def generate(db, tenant, profile, body):
    topic, level = body.topic.strip(), body.level.strip()
    if len(topic) < 2 or not level:
        raise APIError(422, "PRACTICE_INPUT_INVALID")
    old = db.scalar(
        select(PracticeSet).where(
            PracticeSet.organization_id == tenant.organization.id,
            PracticeSet.student_id == profile.id,
            PracticeSet.request_key == body.request_key,
        )
    )
    if old:
        if (
            old.course_id,
            old.topic,
            old.level,
            old.difficulty,
            old.locale,
            len(old.questions),
        ) != (
            body.course_id,
            topic,
            level,
            body.difficulty,
            body.locale,
            body.question_count,
        ):
            raise APIError(409, "PRACTICE_REPLAY_CONFLICT")
        return view(old)
    course = db.scalar(
        select(Course).where(
            Course.id == body.course_id,
            Course.organization_id == tenant.organization.id,
            Course.status == "published",
        )
    )
    if not course:
        raise APIError(404, "COURSE_NOT_FOUND")
    language = db.get(CourseLanguage, course.language_id)
    payload = {
        "course": course.name,
        "objectives": course.objectives[:2000],
        "language": language.name,
        "topic": topic,
        "level": level,
        "difficulty": body.difficulty,
        "question_count": body.question_count,
        "locale": body.locale,
        "source_refs": [str(course.id)],
    }

    def check(output):
        questions = output.get("questions")
        if not isinstance(questions, list) or len(questions) != body.question_count:
            raise APIError(422, "PRACTICE_QUESTION_INVALID")
        validated, seen = [], set()
        for q in questions:
            if not isinstance(q, dict):
                raise APIError(422, "PRACTICE_QUESTION_INVALID")
            valid_question(q.get("stem"), q.get("options"), q.get("correct_index"))
            stem = q["stem"].strip()
            explanation = q.get("explanation")
            if (
                not isinstance(explanation, str)
                or not 1 <= len(explanation.strip()) <= 1000
                or stem.casefold() in seen
            ):
                raise APIError(422, "PRACTICE_QUESTION_INVALID")
            seen.add(stem.casefold())
            validated.append(
                {
                    "stem": stem,
                    "options": [x.strip() for x in q["options"]],
                    "correct_index": q["correct_index"],
                    "explanation": explanation.strip(),
                }
            )
        return validated

    generated = invoke(db, tenant, "practice_generation", body.locale, payload, check)
    if generated is None:
        raise APIError(503, "PRACTICE_GENERATION_UNAVAILABLE")
    questions, run_id = generated
    # Recheck account/tenant after the external call released its transaction.
    from app.services.admissions import student_ready

    db.refresh(course)
    if course.status != "published":
        raise APIError(404, "COURSE_NOT_FOUND")
    db.refresh(profile)
    student_ready(db, tenant, profile)
    row = PracticeSet(
        organization_id=tenant.organization.id,
        student_id=profile.id,
        course_id=course.id,
        request_key=body.request_key,
        ai_run_id=run_id,
        topic=topic,
        level=level,
        difficulty=body.difficulty,
        locale=body.locale,
        questions=questions,
    )
    db.add(row)
    db.flush()
    return view(row)


def owned(db, tenant, profile, set_id):
    row = db.scalar(
        select(PracticeSet)
        .where(
            PracticeSet.id == set_id,
            PracticeSet.organization_id == tenant.organization.id,
            PracticeSet.student_id == profile.id,
        )
        .with_for_update()
    )
    if not row:
        raise APIError(404, "PRACTICE_NOT_FOUND")
    return row


def submit(db, tenant, profile, set_id, answers):
    db.scalar(select(StudentProfile.id).where(StudentProfile.id == profile.id).with_for_update())
    row = owned(db, tenant, profile, set_id)
    if row.completed_at:
        return view(row)
    if len(answers) != len(row.questions) or any(
        type(a) is not int or not 0 <= a < len(q["options"])
        for a, q in zip(answers, row.questions, strict=False)
    ):
        raise APIError(422, "PRACTICE_ANSWER_INVALID")
    row.answers = answers
    row.completed_at = now()
    db.flush()
    return view(row)
