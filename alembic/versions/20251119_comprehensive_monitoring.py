"""comprehensive_monitoring

Revision ID: comprehensive_monitor_001
Revises: phase4_perf_001
Create Date: 2025-11-19 00:00:00.000000

Creates tables for comprehensive multi-coin, multi-timeframe monitoring system.
Supports custom alert rules, multi-metric tracking, and intelligent entry/exit alerts.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = 'comprehensive_monitor_001'
down_revision: Union[str, Sequence[str], None] = 'phase4_perf_001'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    Upgrade database for Comprehensive Monitoring System.
    Creates coin_watchlist, monitoring_rules, and monitoring_alerts tables.
    """

    # 1. Create coin_watchlist table
    op.create_table(
        'coin_watchlist',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('symbol', sa.String(length=20), nullable=False),
        sa.Column('exchange', sa.String(length=20), nullable=True, server_default='binance'),
        sa.Column('status', sa.String(length=20), nullable=False, server_default='active'),
        sa.Column('priority', sa.Integer(), nullable=True, server_default='1'),
        sa.Column('check_interval_seconds', sa.Integer(), nullable=False, server_default='300'),
        sa.Column('timeframes', postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column('metrics_enabled', postgresql.JSONB(), nullable=True),
        sa.Column('metadata', postgresql.JSONB(), nullable=True),
        sa.Column('last_check_at', sa.DateTime(), nullable=True),
        sa.Column('last_alert_at', sa.DateTime(), nullable=True),
        sa.Column('alert_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('NOW()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('NOW()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('symbol', 'exchange', name='uq_watchlist_symbol_exchange')
    )

    # Indexes for coin_watchlist
    op.create_index('idx_watchlist_symbol', 'coin_watchlist', ['symbol'])
    op.create_index('idx_watchlist_status', 'coin_watchlist', ['status'])
    op.create_index('idx_watchlist_priority', 'coin_watchlist', ['priority', sa.text('created_at DESC')])
    op.create_index('idx_watchlist_last_check', 'coin_watchlist', ['last_check_at'])

    # 2. Create monitoring_rules table
    op.create_table(
        'monitoring_rules',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('watchlist_id', sa.Integer(), nullable=False),
        sa.Column('rule_type', sa.String(length=50), nullable=False),
        sa.Column('rule_name', sa.String(length=100), nullable=False),
        sa.Column('condition', postgresql.JSONB(), nullable=False),
        sa.Column('timeframe', sa.String(length=10), nullable=True),
        sa.Column('priority', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('enabled', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('cooldown_minutes', sa.Integer(), nullable=True, server_default='60'),
        sa.Column('last_triggered_at', sa.DateTime(), nullable=True),
        sa.Column('trigger_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('metadata', postgresql.JSONB(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('NOW()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('NOW()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['watchlist_id'], ['coin_watchlist.id'], ondelete='CASCADE')
    )

    # Indexes for monitoring_rules
    op.create_index('idx_rules_watchlist', 'monitoring_rules', ['watchlist_id'])
    op.create_index('idx_rules_type', 'monitoring_rules', ['rule_type'])
    op.create_index('idx_rules_enabled', 'monitoring_rules', ['enabled'])
    op.create_index('idx_rules_priority', 'monitoring_rules', ['priority', 'enabled'])

    # 3. Create monitoring_alerts table
    op.create_table(
        'monitoring_alerts',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('watchlist_id', sa.Integer(), nullable=False),
        sa.Column('rule_id', sa.Integer(), nullable=True),
        sa.Column('symbol', sa.String(length=20), nullable=False),
        sa.Column('alert_type', sa.String(length=50), nullable=False),
        sa.Column('severity', sa.String(length=20), nullable=False, server_default='medium'),
        sa.Column('title', sa.String(length=200), nullable=False),
        sa.Column('message', sa.Text(), nullable=True),
        sa.Column('price', sa.Numeric(precision=20, scale=8), nullable=True),
        sa.Column('timeframe', sa.String(length=10), nullable=True),
        sa.Column('metrics', postgresql.JSONB(), nullable=True),
        sa.Column('analysis', postgresql.JSONB(), nullable=True),
        sa.Column('recommendations', postgresql.JSONB(), nullable=True),
        sa.Column('telegram_sent', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('telegram_sent_at', sa.DateTime(), nullable=True),
        sa.Column('telegram_message_id', sa.String(length=100), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('NOW()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['watchlist_id'], ['coin_watchlist.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['rule_id'], ['monitoring_rules.id'], ondelete='SET NULL')
    )

    # Indexes for monitoring_alerts
    op.create_index('idx_alerts_watchlist', 'monitoring_alerts', ['watchlist_id'])
    op.create_index('idx_alerts_rule', 'monitoring_alerts', ['rule_id'])
    op.create_index('idx_alerts_symbol', 'monitoring_alerts', ['symbol'])
    op.create_index('idx_alerts_type', 'monitoring_alerts', ['alert_type'])
    op.create_index('idx_alerts_severity', 'monitoring_alerts', ['severity'])
    op.create_index('idx_alerts_created', 'monitoring_alerts', [sa.text('created_at DESC')])
    op.create_index('idx_alerts_telegram', 'monitoring_alerts', ['telegram_sent', sa.text('created_at DESC')])

    # Composite indexes for common queries
    op.create_index(
        'idx_alerts_symbol_created',
        'monitoring_alerts',
        ['symbol', sa.text('created_at DESC')]
    )
    op.create_index(
        'idx_alerts_type_severity',
        'monitoring_alerts',
        ['alert_type', 'severity', sa.text('created_at DESC')]
    )

    # 4. Create monitoring_metrics table for historical tracking
    op.create_table(
        'monitoring_metrics',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('watchlist_id', sa.Integer(), nullable=False),
        sa.Column('symbol', sa.String(length=20), nullable=False),
        sa.Column('timeframe', sa.String(length=10), nullable=False),
        sa.Column('price', sa.Numeric(precision=20, scale=8), nullable=False),
        sa.Column('volume', sa.Numeric(precision=20, scale=2), nullable=True),
        sa.Column('funding_rate', sa.Numeric(precision=10, scale=6), nullable=True),
        sa.Column('open_interest', sa.Numeric(precision=20, scale=2), nullable=True),
        sa.Column('liquidations_long', sa.Numeric(precision=20, scale=2), nullable=True),
        sa.Column('liquidations_short', sa.Numeric(precision=20, scale=2), nullable=True),
        sa.Column('social_volume', sa.BigInteger(), nullable=True),
        sa.Column('metrics', postgresql.JSONB(), nullable=True),
        sa.Column('timestamp', sa.DateTime(), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('NOW()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['watchlist_id'], ['coin_watchlist.id'], ondelete='CASCADE'),
        sa.UniqueConstraint('symbol', 'timeframe', 'timestamp', name='uq_metrics_symbol_timeframe_timestamp')
    )

    # Indexes for monitoring_metrics
    op.create_index('idx_metrics_watchlist', 'monitoring_metrics', ['watchlist_id'])
    op.create_index('idx_metrics_symbol', 'monitoring_metrics', ['symbol'])
    op.create_index('idx_metrics_timeframe', 'monitoring_metrics', ['timeframe'])
    op.create_index('idx_metrics_timestamp', 'monitoring_metrics', [sa.text('timestamp DESC')])
    op.create_index(
        'idx_metrics_symbol_timeframe',
        'monitoring_metrics',
        ['symbol', 'timeframe', sa.text('timestamp DESC')]
    )


def downgrade() -> None:
    """Drop comprehensive monitoring tables."""
    op.drop_index('idx_metrics_symbol_timeframe', table_name='monitoring_metrics')
    op.drop_index('idx_metrics_timestamp', table_name='monitoring_metrics')
    op.drop_index('idx_metrics_timeframe', table_name='monitoring_metrics')
    op.drop_index('idx_metrics_symbol', table_name='monitoring_metrics')
    op.drop_index('idx_metrics_watchlist', table_name='monitoring_metrics')
    op.drop_table('monitoring_metrics')

    op.drop_index('idx_alerts_type_severity', table_name='monitoring_alerts')
    op.drop_index('idx_alerts_symbol_created', table_name='monitoring_alerts')
    op.drop_index('idx_alerts_telegram', table_name='monitoring_alerts')
    op.drop_index('idx_alerts_created', table_name='monitoring_alerts')
    op.drop_index('idx_alerts_severity', table_name='monitoring_alerts')
    op.drop_index('idx_alerts_type', table_name='monitoring_alerts')
    op.drop_index('idx_alerts_symbol', table_name='monitoring_alerts')
    op.drop_index('idx_alerts_rule', table_name='monitoring_alerts')
    op.drop_index('idx_alerts_watchlist', table_name='monitoring_alerts')
    op.drop_table('monitoring_alerts')

    op.drop_index('idx_rules_priority', table_name='monitoring_rules')
    op.drop_index('idx_rules_enabled', table_name='monitoring_rules')
    op.drop_index('idx_rules_type', table_name='monitoring_rules')
    op.drop_index('idx_rules_watchlist', table_name='monitoring_rules')
    op.drop_table('monitoring_rules')

    op.drop_index('idx_watchlist_last_check', table_name='coin_watchlist')
    op.drop_index('idx_watchlist_priority', table_name='coin_watchlist')
    op.drop_index('idx_watchlist_status', table_name='coin_watchlist')
    op.drop_index('idx_watchlist_symbol', table_name='coin_watchlist')
    op.drop_table('coin_watchlist')
