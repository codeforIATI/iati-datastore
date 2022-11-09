"""Add USD and EUR fields to budgets

Revision ID: 3daa1d4ab046
Revises: fdc7716bb5ea
Create Date: 2022-11-09 11:27:07.289321

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '3daa1d4ab046'
down_revision = 'fdc7716bb5ea'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('budget', sa.Column('value_usd', sa.Numeric(), nullable=True))
    op.add_column('budget', sa.Column('value_eur', sa.Numeric(), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('budget', 'value_eur')
    op.drop_column('budget', 'value_usd')
    # ### end Alembic commands ###
