"""empty message

Revision ID: 73b98890e8e5
Revises: fdefad17cc6e
Create Date: 2018-11-12 14:06:19.810203

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '73b98890e8e5'
down_revision = 'fdefad17cc6e'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('user_update_signal', 'old_email')
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('user_update_signal', sa.Column('old_email', sa.TEXT(), autoincrement=False, nullable=True))
    # ### end Alembic commands ###
