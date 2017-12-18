"""create build_data table

Revision ID: 4a5bef3702b
Revises: 9593a123e7c5
Create Date: 2017-12-15 21:15:17.884404

"""

# revision identifiers, used by Alembic.
revision = '4a5bef3702b'
down_revision = '9593a123e7c5'
branch_labels = None
depends_on = None

from alembic import op

from drydock_provisioner.statemgmt.db import tables


def upgrade():
    op.create_table(tables.BuildData.__tablename__,
                    *tables.BuildData.__schema__)


def downgrade():
    op.drop_table(tables.BuildData.__tablename__)
