"""Tenant-scoped operational reports and a redacted audit timeline."""

import csv
import io
from datetime import date, datetime, time, timedelta
from typing import Annotated
from uuid import UUID
from zoneinfo import ZoneInfo

from fastapi import APIRouter, Depends, Query, Request, Response
from sqlalchemy import func, select

from app.api.dependencies import DB, Root, Tenant, auth_guard
from app.api.routes.courses import authorize
from app.core.errors import APIError
from app.core.security import now, utc
from app.models import (
    AttendanceSheet,
    AuditLog,
    ClassSession,
    Enrollment,
    Invoice,
    LearningClass,
    Payment,
    RefundDisbursement,
    StudentProfile,
    TeacherProfile,
    User,
)

router = APIRouter(dependencies=[Depends(auth_guard)])


def bounds(starts_on, ends_on):
    if ends_on < starts_on or (ends_on - starts_on).days > 366:
        raise APIError(422, "REPORT_DATE_INVALID")
    tz = ZoneInfo("Asia/Ho_Chi_Minh")
    return utc(datetime.combine(starts_on, time.min, tz)), utc(
        datetime.combine(ends_on + timedelta(days=1), time.min, tz)
    )


def manager(db, tenant, request, response):
    if authorize(db, tenant, request, response, "business_read") != "organization_manager":
        raise APIError(403, "FORBIDDEN")


def training(db, org_id, starts_on, ends_on, class_id):
    start, end = bounds(starts_on, ends_on)
    classes_query = select(LearningClass).where(LearningClass.organization_id == org_id)
    if class_id:
        classes_query = classes_query.where(LearningClass.id == class_id)
    classes = list(db.scalars(classes_query.order_by(LearningClass.code)))
    if class_id and not classes:
        raise APIError(404, "CLASS_NOT_FOUND")
    ids = [row.id for row in classes]
    enrollments = list(
        db.scalars(
            select(Enrollment).where(
                Enrollment.organization_id == org_id,
                Enrollment.class_id.in_(ids),
            )
        )
    )
    invoice_ids = select(Invoice.id).where(
        Invoice.organization_id == org_id,
        Invoice.request_id.in_([row.request_id for row in enrollments]),
    )
    # Global totals include approved invoices awaiting placement; class totals only its enrollments.
    if not class_id:
        invoice_ids = select(Invoice.id).where(Invoice.organization_id == org_id)
    collected = db.scalar(
        select(func.coalesce(func.sum(Payment.amount), 0)).where(
            Payment.organization_id == org_id,
            Payment.invoice_id.in_(invoice_ids),
            Payment.reversed_at.is_(None),
            Payment.created_at >= start,
            Payment.created_at < end,
        )
    )
    refunded = (
        db.scalar(
            select(func.coalesce(func.sum(RefundDisbursement.amount), 0)).where(
                RefundDisbursement.organization_id == org_id,
                RefundDisbursement.created_at >= start,
                RefundDisbursement.created_at < end,
            )
        )
        if not class_id
        else None
    )
    sheets = db.scalars(
        select(AttendanceSheet)
        .join(ClassSession, ClassSession.id == AttendanceSheet.session_id)
        .where(
            AttendanceSheet.organization_id == org_id,
            AttendanceSheet.class_id.in_(ids),
            AttendanceSheet.finalized.is_(True),
            ClassSession.status == "scheduled",
            ClassSession.starts_at >= start,
            ClassSession.starts_at < end,
        )
    )
    counts = {key: 0 for key in ("present", "late", "absent", "excused")}
    for sheet in sheets:
        for record in sheet.records:
            if record.get("status") in counts:
                counts[record["status"]] += 1
    denominator = counts["present"] + counts["late"] + counts["absent"]
    from app.models import ClassGradebook, ClassGradeItem
    from app.services.results import calculations

    # Completion means a published, locked, fully assessed result, not an assumed pass.
    completed_by_class = {}
    passed_by_class, failed_by_class = {}, {}
    for book in db.scalars(
        select(ClassGradebook).where(
            ClassGradebook.organization_id == org_id,
            ClassGradebook.class_id.in_(ids),
            ClassGradebook.locked_at.is_not(None),
            ClassGradebook.publish_at.is_not(None),
            ClassGradebook.publish_at <= now(),
            ClassGradebook.locked_at >= start,
            ClassGradebook.locked_at < end,
        )
    ):
        roster = [e for e in enrollments if e.class_id == book.class_id]
        items = list(
            db.scalars(select(ClassGradeItem).where(ClassGradeItem.gradebook_id == book.id))
        )
        values = [
            v
            for v in calculations(db, items, roster).values()
            if v["final_score"] is not None and v["coverage_percent"] == 100
        ]
        completed_by_class[book.class_id] = len(values)
        threshold = book.scheme_snapshot.get("passing_percent")
        if threshold is not None:
            from decimal import Decimal

            passed_by_class[book.class_id] = sum(
                v["final_score"] >= Decimal(str(threshold)) for v in values
            )
            failed_by_class[book.class_id] = len(values) - passed_by_class[book.class_id]
    rows = []
    for classroom in classes:
        roster = [e for e in enrollments if e.class_id == classroom.id]
        rows.append(
            {
                "id": classroom.id,
                "code": classroom.code,
                "name": classroom.name,
                "capacity": classroom.capacity,
                "active_students": sum(e.state == "active" for e in roster),
                "total_enrollments": len(roster),
                "completed_results": completed_by_class.get(classroom.id, 0),
                "passed_results": passed_by_class.get(classroom.id),
                "failed_results": failed_by_class.get(classroom.id),
            }
        )
    total, completed = len(enrollments), sum(completed_by_class.values())
    return {
        "starts_on": starts_on,
        "ends_on": ends_on,
        "generated_at": now(),
        "students": db.scalar(
            select(func.count(StudentProfile.id)).where(
                StudentProfile.organization_id == org_id, StudentProfile.archived_at.is_(None)
            )
        ),
        "teachers": db.scalar(
            select(func.count(TeacherProfile.id)).where(
                TeacherProfile.organization_id == org_id, TeacherProfile.archived_at.is_(None)
            )
        ),
        "classes": len(classes),
        "total_enrollments": total,
        "active_enrollments": sum(e.state == "active" for e in enrollments),
        "collected": collected,
        "refunded": refunded,
        "net_cash": collected - refunded if refunded is not None else None,
        "attendance": counts,
        "attendance_percent": round(100 * (counts["present"] + counts["late"]) / denominator, 1)
        if denominator
        else None,
        "completed_results": completed,
        "passed_results": sum(passed_by_class.values()) if passed_by_class else None,
        "failed_results": sum(failed_by_class.values()) if failed_by_class else None,
        "pass_percent": round(100 * sum(passed_by_class.values()) / total, 1)
        if total and passed_by_class
        else None,
        "completion_percent": round(100 * completed / total, 1) if total else None,
        "items": rows,
    }


@router.get("/reports/training")
def report(
    starts_on: date,
    ends_on: date,
    db: DB,
    tenant: Tenant,
    request: Request,
    response: Response,
    class_id: UUID | None = None,
):
    manager(db, tenant, request, response)
    return training(db, tenant.organization.id, starts_on, ends_on, class_id)


@router.get("/reports/training.csv")
def export_report(
    starts_on: date,
    ends_on: date,
    db: DB,
    tenant: Tenant,
    request: Request,
    response: Response,
    class_id: UUID | None = None,
):
    manager(db, tenant, request, response)
    result = training(db, tenant.organization.id, starts_on, ends_on, class_id)
    stream = io.StringIO()
    writer = csv.writer(stream)

    def safe(value):
        text = str(value)
        return (
            "'" + text if text.lstrip().startswith(("=", "+", "-", "@", "\t", "\r", "\n")) else text
        )

    writer.writerow(["Từ ngày", starts_on, "Đến ngày", ends_on])
    writer.writerow(
        ["Học viên trung tâm", result["students"], "Giáo viên trung tâm", result["teachers"]]
    )
    writer.writerow(["Tiền thu hợp lệ", result["collected"], "Tiền hoàn", result["refunded"]])
    writer.writerow(
        ["Dòng tiền sau hoàn", result["net_cash"], "Chuyên cần (%)", result["attendance_percent"]]
    )
    writer.writerow(
        [
            "Kết quả hoàn tất",
            result["completed_results"],
            "Tỷ lệ hoàn tất (%)",
            result["completion_percent"],
        ]
    )
    writer.writerow(
        ["Kết quả đạt", result["passed_results"], "Tỷ lệ đạt (%)", result["pass_percent"]]
    )
    writer.writerow(
        [
            "Mã lớp",
            "Tên lớp",
            "Sức chứa",
            "Đang học",
            "Tổng đăng ký",
            "Kết quả hoàn tất",
            "Đạt",
            "Chưa đạt",
        ]
    )
    for row in result["items"]:
        writer.writerow(
            [
                safe(row[key])
                for key in (
                    "code",
                    "name",
                    "capacity",
                    "active_students",
                    "total_enrollments",
                    "completed_results",
                    "passed_results",
                    "failed_results",
                )
            ]
        )
    return Response(
        "\ufeff" + stream.getvalue(),
        media_type="text/csv; charset=utf-8",
        headers={
            "Content-Disposition": 'attachment; filename="synapse-training.csv"',
            "Cache-Control": "no-store",
        },
    )


def logs(db, conditions, action, offset, limit):
    if action:
        conditions.append(AuditLog.action == action)
    total = db.scalar(select(func.count(AuditLog.id)).where(*conditions))
    rows = db.execute(
        select(AuditLog, User.display_name)
        .join(User, User.id == AuditLog.actor_id)
        .where(*conditions)
        .order_by(AuditLog.created_at.desc(), AuditLog.id.desc())
        .offset(offset)
        .limit(limit)
    )
    # Do not expose arbitrary details: they may contain personal or future secret fields.
    return {
        "total": total,
        "items": [
            {
                "id": row.id,
                "action": row.action,
                "actor_name": name,
                "target_id": row.target_id,
                "created_at": row.created_at,
                "organization_id": row.organization_id,
            }
            for row, name in rows
        ],
    }


@router.get("/audit-logs")
def tenant_logs(
    db: DB,
    tenant: Tenant,
    request: Request,
    response: Response,
    action: Annotated[str, Query(max_length=80)] = "",
    offset: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=100)] = 25,
):
    manager(db, tenant, request, response)
    return logs(db, [AuditLog.organization_id == tenant.organization.id], action, offset, limit)


@router.get("/admin/audit-logs")
def system_logs(
    db: DB,
    root: Root,
    response: Response,
    action: Annotated[str, Query(max_length=80)] = "",
    offset: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=100)] = 25,
):
    response.headers["Cache-Control"] = "no-store"
    return logs(db, [AuditLog.organization_id.is_(None)], action, offset, limit)
