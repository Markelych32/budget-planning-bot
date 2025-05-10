from alembic import op


revision = "04dc3fae2386"
down_revision = "020e8e82f34d"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("INSERT INTO categories (name) VALUES ('💸 Налоги')")


def downgrade() -> None:
    op.execute("DELETE FROM categories WHERE name = '💸 Налоги'")
