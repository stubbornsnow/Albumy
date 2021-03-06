"""user add notification

Revision ID: 4eb71a1fcf3b
Revises: 051edf0d0ac2
Create Date: 2019-05-02 15:40:20.029884

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = '4eb71a1fcf3b'
down_revision = '051edf0d0ac2'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('user') as batch_op:
        batch_op.add_column(sa.Column('receive_collect_notification', sa.Boolean(), nullable=True))
        batch_op.add_column(sa.Column('receive_comment_notification', sa.Boolean(), nullable=True))
        batch_op.add_column(sa.Column('receive_follow_notification', sa.Boolean(), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('user') as batch_op:
        batch_op.drop_column('receive_follow_notification')
        batch_op.drop_column('receive_comment_notification')
        batch_op.drop_column('receive_collect_notification')
    # ### end Alembic commands ###
