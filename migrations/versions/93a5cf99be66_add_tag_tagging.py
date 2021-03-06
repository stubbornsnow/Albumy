"""add tag tagging

Revision ID: 93a5cf99be66
Revises: 2247c41acec7
Create Date: 2019-04-16 19:08:33.540880

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = '93a5cf99be66'
down_revision = '2247c41acec7'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('tag',
                    sa.Column('id', sa.Integer(), nullable=False),
                    sa.Column('name', sa.String(length=20), nullable=True),
                    sa.PrimaryKeyConstraint('id')
                    )
    op.create_index(op.f('ix_tag_name'), 'tag', ['name'], unique=False)
    op.create_table('tagging',
                    sa.Column('photo_id', sa.Integer(), nullable=True),
                    sa.Column('tag_id', sa.Integer(), nullable=True),
                    sa.ForeignKeyConstraint(['photo_id'], ['photo.id'], name=op.f('fk_tagging_photo_id_photo')),
                    sa.ForeignKeyConstraint(['tag_id'], ['tag.id'], name=op.f('fk_tagging_tag_id_tag'))
                    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('tagging')
    op.drop_index(op.f('ix_tag_name'), table_name='tag')
    op.drop_table('tag')
    # ### end Alembic commands ###
