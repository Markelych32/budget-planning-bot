from alembic import op
import sqlalchemy as sa


revision = "020e8e82f34d"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    categories_table = op.create_table(
        "categories",
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("id", sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_categories")),
    )
    currencies_table = op.create_table(
        "currencies",
        sa.Column("name", sa.String(length=3), nullable=False),
        sa.Column("sign", sa.String(length=1), nullable=False),
        sa.Column("equity", sa.Integer(), nullable=False),
        sa.Column("id", sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_currencies")),
        sa.UniqueConstraint("name", name=op.f("uq_currencies_name")),
        sa.UniqueConstraint("sign", name=op.f("uq_currencies_sign")),
    )
    op.create_table(
        "users",
        sa.Column("account_id", sa.Integer(), nullable=False),
        sa.Column("chat_id", sa.Integer(), nullable=False),
        sa.Column("username", sa.String(length=100), nullable=False),
        sa.Column("full_name", sa.String(length=100), nullable=False),
        sa.Column("id", sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_users")),
        sa.UniqueConstraint("account_id", name=op.f("uq_users_account_id")),
        sa.UniqueConstraint("username", name=op.f("uq_users_username")),
    )
    op.create_table(
        "configurations",
        sa.Column("number_of_dates", sa.Integer(), nullable=False),
        sa.Column("costs_sources", sa.Text(), nullable=True),
        sa.Column("incomes_sources", sa.Text(), nullable=True),
        sa.Column("ignore_categories", sa.Text(), nullable=True),
        sa.Column("user_id", sa.Integer(), nullable=True),
        sa.Column("default_currency_id", sa.Integer(), nullable=True),
        sa.Column("id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(
            ["default_currency_id"],
            ["currencies.id"],
            name=op.f("fk_configurations_default_currency_id_currencies"),
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name=op.f("fk_configurations_user_id_users"),
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_configurations")),
    )
    op.create_table(
        "costs",
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("value", sa.Integer(), nullable=False),
        sa.Column("date", sa.Date(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=True),
        sa.Column("category_id", sa.Integer(), nullable=True),
        sa.Column("currency_id", sa.Integer(), nullable=True),
        sa.Column("id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(
            ["category_id"],
            ["categories.id"],
            name=op.f("fk_costs_category_id_categories"),
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["currency_id"],
            ["currencies.id"],
            name=op.f("fk_costs_currency_id_currencies"),
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name=op.f("fk_costs_user_id_users"),
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_costs")),
    )
    op.create_table(
        "currency_exchange",
        sa.Column("source_value", sa.Integer(), nullable=False),
        sa.Column("destination_value", sa.Integer(), nullable=False),
        sa.Column("date", sa.Date(), nullable=False),
        sa.Column("source_currency_id", sa.Integer(), nullable=True),
        sa.Column("destination_currency_id", sa.Integer(), nullable=True),
        sa.Column("user_id", sa.Integer(), nullable=True),
        sa.Column("id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(
            ["destination_currency_id"],
            ["currencies.id"],
            name=op.f(
                "fk_currency_exchange_destination_currency_id_currencies"
            ),
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["source_currency_id"],
            ["currencies.id"],
            name=op.f("fk_currency_exchange_source_currency_id_currencies"),
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name=op.f("fk_currency_exchange_user_id_users"),
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_currency_exchange")),
    )
    op.create_table(
        "incomes",
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("value", sa.Integer(), nullable=False),
        sa.Column(
            "source",
            sa.Enum("REVENUE", "OTHER", "GIFT", "DEBT", name="incomesource"),
            nullable=False,
        ),
        sa.Column("date", sa.Date(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=True),
        sa.Column("currency_id", sa.Integer(), nullable=True),
        sa.Column("id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(
            ["currency_id"],
            ["currencies.id"],
            name=op.f("fk_incomes_currency_id_currencies"),
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name=op.f("fk_incomes_user_id_users"),
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_incomes")),
    )

    op.bulk_insert(
        categories_table,
        [
            {"name": "🍽 Еда"},
            {"name": "🥗 Рестораны"},
            {"name": "🍔 Доставка еды"},
            {"name": "🚌 Оплата дорог"},
            {"name": "👚 Одежда"},
            {"name": "🚙 Транспорт"},
            {"name": "⛽️ Топливо"},
            {"name": "🪴 Бытовые расходы"},
            {"name": "🤝 Аренда"},
            {"name": "💳 Услуги"},
            {"name": "🏝 Отпуск"},
            {"name": "💻 Техника"},
            {"name": "📚 Образование"},
            {"name": "🎁 Подарки"},
            {"name": "📦 Другое"},
            {"name": "♥️ Здоровье"},
            {"name": "💼 Бизнес"},
            {"name": "💸 Долги"},
            {"name": "🏠️ Дом"},
        ],
    )

    op.bulk_insert(
        currencies_table,
        [
            {"name": "USD", "sign": "$", "equity": 0},
            {"name": "RUB", "sign": "₽", "equity": 0},
        ],
    )


def downgrade() -> None:
    op.drop_table("incomes")
    op.drop_table("currency_exchange")
    op.drop_table("costs")
    op.drop_table("configurations")
    op.drop_table("users")
    op.drop_table("currencies")
    op.drop_table("categories")
