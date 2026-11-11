"""创建文章表。"""

from alembic import op
import sqlalchemy as sa

revision = "0001_articles"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "articles",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("content", sa.String(), nullable=False),
        sa.Column("summary", sa.String(500), nullable=True),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )

    for column in ("name", "status", "created_at"):
        op.create_index(
            f"ix_articles_{column}",
            "articles",
            [column],
        )


def downgrade():
    op.drop_table("articles")
