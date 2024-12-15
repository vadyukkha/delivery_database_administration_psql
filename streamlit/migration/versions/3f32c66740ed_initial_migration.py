"""initial migration

Revision ID: 3f32c66740ed
Revises: 
Create Date: 2024-12-16 00:33:58.154401

"""

from pathlib import Path
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "3f32c66740ed"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    dump_path = Path(__file__).parent.parent.absolute() / "schema.dump"

    with open(dump_path, "r") as sql_reader:
        op.execute(sa.text(sql_reader.read()))

    op.execute(sa.text("SET search_path = public"))


def downgrade() -> None:
    pass
