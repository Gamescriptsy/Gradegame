"""Add relationship between Transaction and Game

Revision ID: 737c1b1513b1
Revises: 0ec5ae97e614
Create Date: 2024-12-19 15:16:26.472232

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '737c1b1513b1'
down_revision = '0ec5ae97e614'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('games', schema=None) as batch_op:
        batch_op.alter_column('image',
               existing_type=sa.VARCHAR(length=200),
               type_=sa.String(length=255),
               nullable=True)

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('games', schema=None) as batch_op:
        batch_op.alter_column('image',
               existing_type=sa.String(length=255),
               type_=sa.VARCHAR(length=200),
               nullable=False)

    # ### end Alembic commands ###
