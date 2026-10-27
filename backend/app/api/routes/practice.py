"""Practice review, personal submissions and theme rewards."""

from uuid import UUID

from fastapi import APIRouter, Depends, Request, Response
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.api.dependencies import DB, Tenant, audit, auth_guard
from app.api.practice_schemas import (
    GenerateInput,
    PracticeSetInput,
    PracticeSetSubmit,
    QuestionInput,
    SubmitInput,
    ThemeInput,
)
from app.api.routes.courses import authorize
from app.core.errors import APIError
from app.core.security import now
from app.models import (
    ClassTeacher,
    Course,
    LearningClass,
    PracticeAttempt,
    PracticeQuestion,
    PracticeSet,
    TeacherProfile,
    ThemeSelection,
)
from app.services import admissions, practice_sets
from app.services import practice as svc

router = APIRouter(prefix="/practice", dependencies=[Depends(auth_guard)])


def student_access(db, tenant, request, response):
    if authorize(db, tenant, request, response, "business_read") != "student":
        raise APIError(403, "FORBIDDEN")
    return admissions.own_student(db, tenant)


@router.post("/sets/generate")
def generate_set(
    body: PracticeSetInput, db: DB, tenant: Tenant, request: Request, response: Response
):
    profile = student_access(db, tenant, request, response)
    try:
        result = practice_sets.generate(db, tenant, profile, body)
        student_access(db, tenant, request, response)
        audit(db, tenant.actor, "practice.set.generate", tenant.organization.id, result["id"])
        db.commit()
        return result
    except IntegrityError as error:
        db.rollback()
        raise APIError(409, "PRACTICE_CONFLICT") from error


@router.get("/sets/mine")
def my_sets(db: DB, tenant: Tenant, request: Request, response: Response):
    profile = student_access(db, tenant, request, response)
    rows = db.scalars(
        select(PracticeSet)
        .where(
            PracticeSet.organization_id == tenant.organization.id,
            PracticeSet.student_id == profile.id,
        )
        .order_by(PracticeSet.created_at.desc(), PracticeSet.id)
        .limit(100)
    )
    return {
        "items": [
            {
                "id": row.id,
                "topic": row.topic,
                "level": row.level,
                "difficulty": row.difficulty,
                "question_count": len(row.questions),
                "created_at": row.created_at,
                "completed_at": row.completed_at,
                "score_percent": practice_sets.view(row).get("score_percent"),
            }
            for row in rows
        ]
    }


@router.get("/sets/{set_id}")
def get_set(set_id: UUID, db: DB, tenant: Tenant, request: Request, response: Response):
    profile = student_access(db, tenant, request, response)
    return practice_sets.view(practice_sets.owned(db, tenant, profile, set_id))


@router.post("/sets/{set_id}/submit")
def submit_set(
    set_id: UUID,
    body: PracticeSetSubmit,
    db: DB,
    tenant: Tenant,
    request: Request,
    response: Response,
):
    profile = student_access(db, tenant, request, response)
    result = practice_sets.submit(db, tenant, profile, set_id, body.answers)
    audit(db, tenant.actor, "practice.set.submit", tenant.organization.id, set_id)
    db.commit()
    return result


def reviewer(db, tenant, request, response, course_id):
    role = authorize(db, tenant, request, response, "business_read")
    if role == "organization_manager":
        return
    if role != "teacher":
        raise APIError(403, "FORBIDDEN")
    assigned = db.scalar(
        select(ClassTeacher.id)
        .join(LearningClass, LearningClass.id == ClassTeacher.class_id)
        .join(TeacherProfile, TeacherProfile.id == ClassTeacher.teacher_profile_id)
        .where(
            LearningClass.organization_id == tenant.organization.id,
            LearningClass.course_id == course_id,
            TeacherProfile.user_id == tenant.actor.user.id,
            TeacherProfile.archived_at.is_(None),
        )
    )
    if not assigned:
        raise APIError(403, "FORBIDDEN")


def question(db, tenant, question_id):
    row = db.scalar(
        select(PracticeQuestion).where(
            PracticeQuestion.id == question_id,
            PracticeQuestion.organization_id == tenant.organization.id,
        )
    )
    if not row:
        raise APIError(404, "PRACTICE_NOT_FOUND")
    return row


@router.post("/questions")
def create_question(
    body: QuestionInput, db: DB, tenant: Tenant, request: Request, response: Response
):
    if authorize(db, tenant, request, response, "business_read") != "organization_manager":
        raise APIError(403, "FORBIDDEN")
    course = db.scalar(
        select(Course).where(
            Course.id == body.course_id,
            Course.organization_id == tenant.organization.id,
            Course.status == "published",
        )
    )
    if not course:
        raise APIError(404, "COURSE_NOT_FOUND")
    svc.valid_question(body.stem, body.options, body.correct_index)
    row = PracticeQuestion(
        organization_id=tenant.organization.id,
        course_id=course.id,
        creator_id=tenant.actor.user.id,
        locale=body.locale,
        stem=body.stem.strip(),
        options=[x.strip() for x in body.options],
        correct_index=body.correct_index,
        explanation=body.explanation,
        source_refs=[str(course.id)],
        status="draft",
    )
    db.add(row)
    db.flush()
    audit(db, tenant.actor, "practice.question.create", tenant.organization.id, row.id)
    db.commit()
    return svc.question_view(row, reveal=True)


@router.post("/questions/generate")
def generate_question(
    body: GenerateInput, db: DB, tenant: Tenant, request: Request, response: Response
):
    if authorize(db, tenant, request, response, "business_read") != "organization_manager":
        raise APIError(403, "FORBIDDEN")
    result = svc.generate(db, tenant, body.course_id, body.locale)
    audit(db, tenant.actor, "practice.question.generate", tenant.organization.id, result["id"])
    db.commit()
    return result


@router.get("/questions")
def questions(course_id: UUID, db: DB, tenant: Tenant, request: Request, response: Response):
    reviewer(db, tenant, request, response, course_id)
    return {
        "items": [
            svc.question_view(q, reveal=True)
            for q in db.scalars(
                select(PracticeQuestion)
                .where(
                    PracticeQuestion.organization_id == tenant.organization.id,
                    PracticeQuestion.course_id == course_id,
                )
                .order_by(PracticeQuestion.created_at.desc())
                .limit(100)
            )
        ]
    }


@router.post("/questions/{question_id}/publish")
def publish_question(
    question_id: UUID, db: DB, tenant: Tenant, request: Request, response: Response
):
    row = question(db, tenant, question_id)
    reviewer(db, tenant, request, response, row.course_id)
    svc.valid_question(row.stem, row.options, row.correct_index)
    row.status = "published"
    row.published_at = now()
    audit(db, tenant.actor, "practice.question.publish", tenant.organization.id, row.id)
    db.commit()
    return svc.question_view(row, reveal=True)


@router.post("/questions/{question_id}/hide")
def hide_question(question_id: UUID, db: DB, tenant: Tenant, request: Request, response: Response):
    row = question(db, tenant, question_id)
    reviewer(db, tenant, request, response, row.course_id)
    row.status = "hidden"
    audit(db, tenant.actor, "practice.question.hide", tenant.organization.id, row.id)
    db.commit()
    return svc.question_view(row, reveal=True)


@router.get("/mine")
def mine(db: DB, tenant: Tenant, request: Request, response: Response):
    if authorize(db, tenant, request, response, "business_read") != "student":
        raise APIError(403, "FORBIDDEN")
    profile = admissions.own_student(db, tenant)
    courses = svc.accessible_courses(db, tenant, profile.id)
    if not courses:
        return {"items": []}
    completed = select(PracticeAttempt.question_id).where(
        PracticeAttempt.organization_id == tenant.organization.id,
        PracticeAttempt.student_id == profile.id,
    )
    rows = db.scalars(
        select(PracticeQuestion)
        .where(
            PracticeQuestion.organization_id == tenant.organization.id,
            PracticeQuestion.course_id.in_(courses),
            PracticeQuestion.status == "published",
            PracticeQuestion.id.not_in(completed),
        )
        .order_by(PracticeQuestion.published_at, PracticeQuestion.id)
        .limit(20)
    )
    return {"items": [svc.question_view(q) for q in rows]}


@router.post("/questions/{question_id}/submit")
def submit(
    question_id: UUID,
    body: SubmitInput,
    db: DB,
    tenant: Tenant,
    request: Request,
    response: Response,
):
    if authorize(db, tenant, request, response, "business_read") != "student":
        raise APIError(403, "FORBIDDEN")
    profile = admissions.own_student(db, tenant)
    row = question(db, tenant, question_id)
    try:
        return svc.submit(db, tenant, profile, row, body.request_key, body.answer_index)
    except IntegrityError as error:
        db.rollback()
        raise APIError(409, "PRACTICE_CONFLICT") from error


@router.get("/rewards/mine")
def my_rewards(db: DB, tenant: Tenant, request: Request, response: Response):
    if authorize(db, tenant, request, response, "business_read") != "student":
        raise APIError(403, "FORBIDDEN")
    return svc.rewards(db, tenant, admissions.own_student(db, tenant))


@router.put("/rewards/theme")
def select_theme(body: ThemeInput, db: DB, tenant: Tenant, request: Request, response: Response):
    if authorize(db, tenant, request, response, "business_read") != "student":
        raise APIError(403, "FORBIDDEN")
    profile = admissions.own_student(db, tenant)
    if body.theme not in svc.rewards(db, tenant, profile)["unlocked"]:
        raise APIError(403, "THEME_LOCKED")
    row = db.scalar(
        select(ThemeSelection).where(
            ThemeSelection.organization_id == tenant.organization.id,
            ThemeSelection.student_id == profile.id,
        )
    )
    if not row:
        row = ThemeSelection(organization_id=tenant.organization.id, student_id=profile.id)
        db.add(row)
    row.theme = body.theme
    audit(
        db,
        tenant.actor,
        "practice.theme.select",
        tenant.organization.id,
        profile.id,
        theme=body.theme,
    )
    db.commit()
    return {"selected": row.theme}
