"""add forecast model

Revision ID: 003
Revises: 002
Create Date: 2024-01-01 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '003'
down_revision = '002'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add trend column to risk_snapshot
    op.add_column('risksnapshot', sa.Column('trend', sa.String(), nullable=True))
    
    # Add risk_tolerance to ticker
    op.add_column('ticker', sa.Column('risk_tolerance', sa.String(), nullable=True))
    
    # Create risk_forecast table
    op.create_table(
        'riskforecast',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('symbol', sa.String(), nullable=False),
        sa.Column('forecast_date', sa.DateTime(), nullable=False),
        sa.Column('days_ahead', sa.Integer(), nullable=False),
        sa.Column('predicted_score', sa.Float(), nullable=False),
        sa.Column('confidence', sa.Float(), nullable=False),
        sa.Column('trend_direction', sa.String(), nullable=False),
        sa.Column('forecast_reasons', sa.Text(), nullable=False),
        sa.Column('pattern_match', sa.String(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.Index('ix_riskforecast_symbol', 'symbol'),
        sa.Index('ix_riskforecast_forecast_date', 'forecast_date')
    )


def downgrade() -> None:
    op.drop_table('riskforecast')
    op.drop_column('ticker', 'risk_tolerance')
    op.drop_column('risksnapshot', 'trend')

