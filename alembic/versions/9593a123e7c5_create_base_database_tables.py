"""create base database tables

Revision ID: 9593a123e7c5
Revises: 
Create Date: 2017-09-21 14:56:13.866443

"""

# revision identifiers, used by Alembic.
revision = '9593a123e7c5'
down_revision = None
branch_labels = None
depends_on = None

from alembic import op

from drydock_provisioner.statemgmt.db import tables


def upgrade():
    op.create_table(tables.Tasks.__tablename__, *tables.Tasks.__schema__)
    op.create_table(tables.ResultMessage.__tablename__,
                    *tables.ResultMessage.__schema__)
    op.create_table(tables.ActiveInstance.__tablename__,
                    *tables.ActiveInstance.__schema__)
    op.create_table(tables.BuildData.__tablename__,
                    *tables.BuildData.__schema__)


def downgrade():
    op.drop_table(tables.Tasks.__tablename__)
    op.drop_table(tables.ResultMessage.__tablename__)
    op.drop_table(tables.ActiveInstance.__tablename__)
    op.drop_table(tables.BuildData.__tablename__)
