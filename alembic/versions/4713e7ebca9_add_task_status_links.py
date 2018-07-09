"""add task status links

Revision ID: 4713e7ebca9
Revises: 4a5bef3702b
Create Date: 2018-07-05 14:54:18.381988

"""

# revision identifiers, used by Alembic.
revision = '4713e7ebca9'
down_revision = '4a5bef3702b'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa

from drydock_provisioner.statemgmt.db import tables


def upgrade():
    for c in tables.Tasks.__add_result_links__:
        op.add_column(tables.Tasks.__tablename__, c)


def downgrade():
    for c in tables.Tasks.__add_result_links__:
        op.drop_column(tables.Tasks.__tablename__, c.name)
