"""role add level

Revision ID: a5888e9566a8
Revises: 9daa3e9d32c2
Create Date: 2019-05-04 22:32:59.943766

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'a5888e9566a8'
down_revision = '9daa3e9d32c2'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('role') as batch_op:
        batch_op.add_column(sa.Column('level', sa.Integer(), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('role') as batch_op:
        batch_op.drop_column('level')
    # ### end Alembic commands ###
