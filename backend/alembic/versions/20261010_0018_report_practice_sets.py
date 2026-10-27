"""Private AI practice sets and normalized payment references."""

from contextlib import contextmanager

import sqlalchemy as sa

from alembic import op

revision = "20261010_0018"
down_revision = "20261001_0017"
branch_labels = None
depends_on = None


@contextmanager
def preferred_class_table():
    connection = op.get_bind()
    sqlite = connection.dialect.name == "sqlite"
    if sqlite and not connection.connection.driver_connection.in_transaction:
        # sqlite3 legacy transaction control does not BEGIN for DDL. Without
        # an actual transaction, CREATE TABLE resets the deferred-check flag.
        connection.exec_driver_sql("BEGIN")
    deferred = connection.exec_driver_sql("PRAGMA defer_foreign_keys").scalar() if sqlite else None
    if sqlite:
        # Admission requests are referenced by invoices and enrollments. Defer
        # NO ACTION checks until the replacement table is back in place.
        connection.exec_driver_sql("PRAGMA defer_foreign_keys=ON")
    try:
        with op.batch_alter_table("admission_requests") as batch:
            yield batch
        if sqlite and connection.exec_driver_sql("PRAGMA foreign_key_check").first():
            raise RuntimeError("Foreign key violation after rebuilding admission requests")
    finally:
        if sqlite and not deferred:
            connection.exec_driver_sql("PRAGMA defer_foreign_keys=OFF")


def upgrade():
    with preferred_class_table() as batch:
        batch.add_column(sa.Column("preferred_class_id", sa.Uuid(), nullable=True))
        batch.create_foreign_key(
            "fk_admission_preferred_class",
            "learning_classes",
            ["preferred_class_id", "organization_id"],
            ["id", "organization_id"],
        )
    op.add_column("course_grading_schemes", sa.Column("passing_percent", sa.Numeric(5, 2)))
    op.create_table(
        "practice_sets",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("organization_id", sa.Uuid(), sa.ForeignKey("organizations.id"), nullable=False),
        sa.Column("student_id", sa.Uuid(), nullable=False),
        sa.Column("course_id", sa.Uuid(), nullable=False),
        sa.Column("request_key", sa.Uuid(), nullable=False),
        sa.Column("ai_run_id", sa.Uuid(), sa.ForeignKey("ai_runs.id")),
        sa.Column("topic", sa.String(200), nullable=False),
        sa.Column("level", sa.String(100), nullable=False),
        sa.Column("difficulty", sa.String(16), nullable=False),
        sa.Column("locale", sa.String(2), nullable=False),
        sa.Column("questions", sa.JSON(), nullable=False),
        sa.Column("answers", sa.JSON()),
        sa.Column("completed_at", sa.DateTime(timezone=True)),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.ForeignKeyConstraint(
            ["student_id", "organization_id"],
            ["student_profiles.id", "student_profiles.organization_id"],
        ),
        sa.ForeignKeyConstraint(
            ["course_id", "organization_id"], ["courses.id", "courses.organization_id"]
        ),
        sa.UniqueConstraint("organization_id", "student_id", "request_key"),
    )
    op.create_index("ix_practice_sets_organization_id", "practice_sets", ["organization_id"])
    op.create_index("ix_practice_sets_student_id", "practice_sets", ["student_id"])
    # Preserve historical rows; reserve normalized references for all new payments.
    op.add_column("payments", sa.Column("reference_key", sa.String(200), nullable=True))
    op.create_index(
        "uq_payment_reference_key", "payments", ["organization_id", "reference_key"], unique=True
    )


def downgrade():
    with preferred_class_table() as batch:
        batch.drop_constraint("fk_admission_preferred_class", type_="foreignkey")
        batch.drop_column("preferred_class_id")
    op.drop_column("course_grading_schemes", "passing_percent")
    op.drop_index("uq_payment_reference_key", table_name="payments")
    op.drop_column("payments", "reference_key")
    op.drop_table("practice_sets")
