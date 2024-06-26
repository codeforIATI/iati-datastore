"""empty message

Revision ID: 4fba6971cbcb
Revises: 70fe5998b4dd
Create Date: 2021-09-29 14:22:18.260148

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '4fba6971cbcb'
down_revision = '70fe5998b4dd'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('activity', sa.Column('raw_json', postgresql.JSONB(astext_type=sa.Text()), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('activity', 'raw_json')
    # ### end Alembic commands ###
