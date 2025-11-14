"""initial_schema

Revision ID: da45db127282
Revises: 
Create Date: 2025-11-14 13:35:58.508236

Creates the initial database schema with three tables:
1. signals - Main signal history storage
2. signal_outcomes - AI verdict accuracy tracking
3. hype_history - Social sentiment and hype tracking
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = 'da45db127282'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    Upgrade database to initial schema.
    Creates signals, signal_outcomes, and hype_history tables with indexes.
    """
    # Create signals table
    op.create_table(
        'signals',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('symbol', sa.String(length=20), nullable=False),
        sa.Column('signal', sa.String(length=10), nullable=False),
        sa.Column('score', sa.Numeric(precision=5, scale=2), nullable=False),
        sa.Column('confidence', sa.String(length=10), nullable=False),
        sa.Column('price', sa.Numeric(precision=20, scale=8), nullable=False),
        sa.Column('timestamp', sa.DateTime(), nullable=False),
        sa.Column('reasons', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('metrics', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('comprehensive_metrics', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('lunarcrush_metrics', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('coinapi_metrics', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('smc_analysis', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('ai_validation', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('NOW()'), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes for signals table
    op.create_index('idx_signals_symbol', 'signals', ['symbol'])
    op.create_index('idx_signals_timestamp', 'signals', [sa.text('timestamp DESC')])
    op.create_index('idx_signals_signal', 'signals', ['signal'])
    op.create_index('idx_signals_created_at', 'signals', [sa.text('created_at DESC')])
    op.create_index('idx_signals_symbol_timestamp', 'signals', ['symbol', sa.text('timestamp DESC')])
    
    # MSS-specific indexes with WHERE clause
    op.create_index(
        'idx_signals_mss_timestamp', 
        'signals', 
        ['signal', sa.text('timestamp DESC')],
        postgresql_where=sa.text("signal LIKE 'MSS_%'")
    )
    op.create_index(
        'idx_signals_mss_score',
        'signals',
        [sa.text('score DESC')],
        postgresql_where=sa.text("signal LIKE 'MSS_%'")
    )
    
    # Create signal_outcomes table
    op.create_table(
        'signal_outcomes',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('signal_id', sa.Integer(), nullable=True),
        sa.Column('symbol', sa.String(length=20), nullable=False),
        sa.Column('signal_type', sa.String(length=10), nullable=False),
        sa.Column('verdict', sa.String(length=10), nullable=False),
        sa.Column('risk_mode', sa.String(length=20), nullable=True),
        sa.Column('entry_price', sa.Numeric(precision=20, scale=8), nullable=False),
        sa.Column('entry_timestamp', sa.DateTime(), nullable=False),
        sa.Column('price_1h', sa.Numeric(precision=20, scale=8), nullable=True),
        sa.Column('price_4h', sa.Numeric(precision=20, scale=8), nullable=True),
        sa.Column('price_24h', sa.Numeric(precision=20, scale=8), nullable=True),
        sa.Column('outcome_1h', sa.String(length=10), nullable=True),
        sa.Column('outcome_4h', sa.String(length=10), nullable=True),
        sa.Column('outcome_24h', sa.String(length=10), nullable=True),
        sa.Column('pnl_1h', sa.Numeric(precision=10, scale=4), nullable=True),
        sa.Column('pnl_4h', sa.Numeric(precision=10, scale=4), nullable=True),
        sa.Column('pnl_24h', sa.Numeric(precision=10, scale=4), nullable=True),
        sa.Column('tracked_at_1h', sa.DateTime(), nullable=True),
        sa.Column('tracked_at_4h', sa.DateTime(), nullable=True),
        sa.Column('tracked_at_24h', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('NOW()'), nullable=True),
        sa.ForeignKeyConstraint(['signal_id'], ['signals.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes for signal_outcomes table
    op.create_index('idx_outcomes_verdict', 'signal_outcomes', ['verdict'])
    op.create_index('idx_outcomes_symbol_verdict', 'signal_outcomes', ['symbol', 'verdict'])
    op.create_index('idx_outcomes_timestamp', 'signal_outcomes', [sa.text('entry_timestamp DESC')])
    op.create_index('idx_outcomes_signal_id', 'signal_outcomes', ['signal_id'])
    op.create_index(
        'idx_outcomes_24h',
        'signal_outcomes',
        ['outcome_24h'],
        postgresql_where=sa.text('outcome_24h IS NOT NULL')
    )
    
    # Create hype_history table
    op.create_table(
        'hype_history',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('symbol', sa.String(length=20), nullable=False),
        sa.Column('social_hype_score', sa.Numeric(precision=5, scale=2), nullable=False),
        sa.Column('social_volume', sa.Integer(), nullable=False),
        sa.Column('social_engagement', sa.BigInteger(), nullable=False),
        sa.Column('social_contributors', sa.Integer(), nullable=False),
        sa.Column('social_dominance', sa.Numeric(precision=5, scale=2), nullable=False),
        sa.Column('sentiment', sa.Numeric(precision=5, scale=2), nullable=False),
        sa.Column('twitter_hype', sa.Numeric(precision=5, scale=2), nullable=False),
        sa.Column('tiktok_hype', sa.Numeric(precision=5, scale=2), nullable=False),
        sa.Column('reddit_hype', sa.Numeric(precision=5, scale=2), nullable=False),
        sa.Column('youtube_hype', sa.Numeric(precision=5, scale=2), nullable=False),
        sa.Column('news_hype', sa.Numeric(precision=5, scale=2), nullable=False),
        sa.Column('pump_risk', sa.String(length=20), nullable=True),
        sa.Column('pump_risk_score', sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column('price', sa.Numeric(precision=20, scale=8), nullable=False),
        sa.Column('price_change_24h', sa.Numeric(precision=10, scale=4), nullable=True),
        sa.Column('market_cap', sa.Numeric(precision=30, scale=2), nullable=True),
        sa.Column('volume_24h', sa.Numeric(precision=30, scale=2), nullable=True),
        sa.Column('timestamp', sa.DateTime(), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('NOW()'), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes for hype_history table
    op.create_index('idx_hype_history_symbol', 'hype_history', ['symbol'])
    op.create_index('idx_hype_history_timestamp', 'hype_history', [sa.text('timestamp DESC')])
    op.create_index('idx_hype_history_symbol_timestamp', 'hype_history', ['symbol', sa.text('timestamp DESC')])
    op.create_index('idx_hype_history_score', 'hype_history', [sa.text('social_hype_score DESC')])
    op.create_index(
        'idx_hype_history_pump_risk',
        'hype_history',
        ['pump_risk'],
        postgresql_where=sa.text("pump_risk = 'EXTREME'")
    )


def downgrade() -> None:
    """
    Downgrade to previous schema.
    Drops all tables and indexes created in upgrade.
    """
    # Drop tables in reverse order to respect foreign key constraints
    op.drop_table('hype_history')
    op.drop_table('signal_outcomes')
    op.drop_table('signals')
