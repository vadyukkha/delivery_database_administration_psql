"""initial

Revision ID: 5b30d6842205
Revises: 
Create Date: 2024-12-17 00:23:14.182903

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "5b30d6842205"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Создаем схему
    op.create_schema("delivery_tables_schema")

    # Создаем таблицу Users
    op.create_table(
        "Users",
        sa.Column("user_id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("name", sa.String(50), nullable=False),
        sa.Column("email", sa.String(50), unique=True, nullable=True),
        sa.Column("phone", sa.String(15), nullable=False),
        sa.Column("address", sa.String(100), nullable=False),
        schema="delivery_tables_schema",
    )

    # Создаем таблицу Products
    op.create_table(
        "Products",
        sa.Column("product_id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("price", sa.Integer, nullable=False),
        sa.Column("stock", sa.Integer, nullable=False),
        sa.CheckConstraint("price > 0", name="positive_price"),
        sa.CheckConstraint("stock > 0", name="positive_stock"),
        schema="delivery_tables_schema",
    )

    # Создаем таблицу Orders
    op.create_table(
        "Orders",
        sa.Column("order_id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column(
            "user_id",
            sa.Integer,
            sa.ForeignKey("delivery_tables_schema.Users.user_id", ondelete="CASCADE"),
        ),
        sa.Column(
            "order_date", sa.TIMESTAMP, server_default=sa.text("CURRENT_TIMESTAMP")
        ),
        sa.Column("total_cost", sa.Integer, server_default=sa.text("0")),
        sa.Column("status", sa.String(20), nullable=False),
        schema="delivery_tables_schema",
    )

    # Создаем таблицу OrderItems
    op.create_table(
        "OrderItems",
        sa.Column("order_item_id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column(
            "order_id",
            sa.Integer,
            sa.ForeignKey("delivery_tables_schema.Orders.order_id", ondelete="CASCADE"),
        ),
        sa.Column(
            "product_id",
            sa.Integer,
            sa.ForeignKey(
                "delivery_tables_schema.Products.product_id", ondelete="CASCADE"
            ),
        ),
        sa.Column("quantity", sa.Integer, nullable=False),
        sa.CheckConstraint("quantity > 0", name="positive_quantity"),
        schema="delivery_tables_schema",
    )

    # Создаем индексы
    op.create_index(
        "lower_idx_product_name",
        "Products",
        [sa.text("lower(name)")],
        schema="delivery_tables_schema",
    )
    op.create_index(
        "lower_idx_username",
        "Users",
        [sa.text("lower(name)")],
        schema="delivery_tables_schema",
    )


def downgrade() -> None:
    # Удаляем схему
    op.execute("DROP SCHEMA delivery_tables_schema CASCADE")
