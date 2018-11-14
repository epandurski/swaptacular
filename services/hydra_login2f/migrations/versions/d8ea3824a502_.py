"""empty message

Revision ID: d8ea3824a502
Revises: 610f027cd7b0
Create Date: 2018-10-01 12:56:05.555157

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'd8ea3824a502'
down_revision = '610f027cd7b0'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column('user', 'recovery_code_hash',
               existing_type=sa.TEXT(),
               nullable=True)
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column('user', 'recovery_code_hash',
               existing_type=sa.TEXT(),
               nullable=False)
    # ### end Alembic commands ###