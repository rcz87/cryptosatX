"""phase4_performance_outcomes

Revision ID: phase4_perf_001
Revises: 20251115_1600_high_priority_fixes
Create Date: 2025-11-15 16:00:00.000000

Creates the performance_outcomes table for Phase 4: Automated Performance Tracking.
This table tracks signal outcomes at multiple intervals (1h, 4h, 24h, 7d, 30d) to
calculate win rates and validate system performance.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = 'phase4_perf_001'
down_revision: Union[str, Sequence[str], None] = '20251115_1600_high_priority_fixes'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    Upgrade database for Phase 4 Performance Tracking.
    Creates performance_outcomes table with composite unique constraint.
    """
    # Create performance_outcomes table
    op.create_table(
        'performance_outcomes',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('signal_id', sa.String(length=100), nullable=False),
        sa.Column('symbol', sa.String(length=20), nullable=False),
        sa.Column('signal_type', sa.String(length=10), nullable=False),
        sa.Column('interval', sa.String(length=10), nullable=False),
        sa.Column('entry_price', sa.Numeric(precision=20, scale=8), nullable=False),
        sa.Column('exit_price', sa.Numeric(precision=20, scale=8), nullable=True),
        sa.Column('pnl_pct', sa.Numeric(precision=10, scale=4), nullable=True),
        sa.Column('outcome', sa.String(length=10), nullable=True),
        sa.Column('unified_score', sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column('tier', sa.String(length=30), nullable=True),
        sa.Column('scanner_type', sa.String(length=30), nullable=True),
        sa.Column('checked_at', sa.DateTime(), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('NOW()'), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('signal_id', 'interval', name='uq_performance_signal_interval')
    )

    # Create indexes for performance_outcomes table
    op.create_index('idx_performance_symbol', 'performance_outcomes', ['symbol'])
    op.create_index('idx_performance_outcome', 'performance_outcomes', ['outcome'])
    op.create_index('idx_performance_checked_at', 'performance_outcomes', [sa.text('checked_at DESC')])
    op.create_index('idx_performance_scanner', 'performance_outcomes', ['scanner_type'])
    op.create_index('idx_performance_tier', 'performance_outcomes', ['tier'])
    op.create_index('idx_performance_interval', 'performance_outcomes', ['interval'])

    # Composite indexes for analytics queries
    op.create_index(
        'idx_performance_scanner_outcome',
        'performance_outcomes',
        ['scanner_type', 'outcome']
    )
    op.create_index(
        'idx_performance_tier_outcome',
        'performance_outcomes',
        ['tier', 'outcome']
    )
    op.create_index(
        'idx_performance_interval_outcome',
        'performance_outcomes',
        ['interval', 'outcome']
    )

    # Index for win rate queries
    op.create_index(
        'idx_performance_wins',
        'performance_outcomes',
        ['outcome', sa.text('checked_at DESC')],
        postgresql_where=sa.text("outcome = 'WIN'")
    )
    op.create_index(
        'idx_performance_losses',
        'performance_outcomes',
        ['outcome', sa.text('checked_at DESC')],
        postgresql_where=sa.text("outcome = 'LOSS'")
    )


def downgrade() -> None:
    """
    Downgrade database by removing performance_outcomes table.
    """
    # Drop all indexes first
    op.drop_index('idx_performance_losses', table_name='performance_outcomes')
    op.drop_index('idx_performance_wins', table_name='performance_outcomes')
    op.drop_index('idx_performance_interval_outcome', table_name='performance_outcomes')
    op.drop_index('idx_performance_tier_outcome', table_name='performance_outcomes')
    op.drop_index('idx_performance_scanner_outcome', table_name='performance_outcomes')
    op.drop_index('idx_performance_interval', table_name='performance_outcomes')
    op.drop_index('idx_performance_tier', table_name='performance_outcomes')
    op.drop_index('idx_performance_scanner', table_name='performance_outcomes')
    op.drop_index('idx_performance_checked_at', table_name='performance_outcomes')
    op.drop_index('idx_performance_outcome', table_name='performance_outcomes')
    op.drop_index('idx_performance_symbol', table_name='performance_outcomes')

    # Drop table
    op.drop_table('performance_outcomes')
