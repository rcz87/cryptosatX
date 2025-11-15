"""AI Feedback & Optimization System Tables

Revision ID: ai_feedback_20251115
Revises: da45db127282
Create Date: 2025-11-15 05:20:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'ai_feedback_20251115'
down_revision = 'da45db127282'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### Create ai_prompt_versions table ###
    op.create_table('ai_prompt_versions',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('version_tag', sa.String(length=50), nullable=False),
    sa.Column('prompt_text', sa.Text(), nullable=False),
    sa.Column('change_notes', sa.Text(), nullable=True),
    sa.Column('is_active', sa.Boolean(), server_default=sa.text('false'), nullable=False),
    sa.Column('created_at', sa.TIMESTAMP(), server_default=sa.text('NOW()'), nullable=False),
    sa.Column('created_by', sa.String(length=100), nullable=True),
    sa.Column('ab_test_active', sa.Boolean(), server_default=sa.text('false'), nullable=False),
    sa.Column('ab_test_percentage', sa.Integer(), nullable=True),
    sa.Column('total_signals_processed', sa.Integer(), server_default=sa.text('0'), nullable=False),
    sa.Column('avg_win_rate', sa.Float(), nullable=True),
    sa.Column('avg_calibration_error', sa.Float(), nullable=True),
    sa.Column('deactivated_at', sa.TIMESTAMP(), nullable=True),
    sa.Column('metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('version_tag'),
    comment='Tracks AI prompt versions and their performance metrics'
    )
    
    # Add column comments
    op.execute("""
        COMMENT ON COLUMN ai_prompt_versions.version_tag IS 'Semantic version tag (e.g., v1.0, v1.1-strict, v2.0-beta)';
        COMMENT ON COLUMN ai_prompt_versions.prompt_text IS 'Full system prompt text for OpenAI Signal Judge';
        COMMENT ON COLUMN ai_prompt_versions.change_notes IS 'What changed from previous version and why';
        COMMENT ON COLUMN ai_prompt_versions.is_active IS 'Whether this version is currently in production';
        COMMENT ON COLUMN ai_prompt_versions.created_by IS 'Who created this version (user or automated system)';
        COMMENT ON COLUMN ai_prompt_versions.ab_test_active IS 'Whether this version is in A/B test';
        COMMENT ON COLUMN ai_prompt_versions.ab_test_percentage IS 'Percentage of traffic receiving this version (0-100)';
        COMMENT ON COLUMN ai_prompt_versions.avg_win_rate IS 'Average win rate for signals using this prompt';
        COMMENT ON COLUMN ai_prompt_versions.avg_calibration_error IS 'Average difference between stated confidence and actual win rate';
        COMMENT ON COLUMN ai_prompt_versions.deactivated_at IS 'When this version was deactivated';
        COMMENT ON COLUMN ai_prompt_versions.metadata IS 'Additional version metadata (model params, temperature, etc)';
    """)
    
    op.create_index('idx_prompt_versions_active', 'ai_prompt_versions', ['is_active'])
    op.create_index('idx_prompt_versions_ab_test', 'ai_prompt_versions', ['ab_test_active'])
    op.create_index('idx_prompt_versions_created', 'ai_prompt_versions', ['created_at'])
    
    # ### Create ai_verdict_performance table ###
    op.create_table('ai_verdict_performance',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('verdict', sa.String(length=20), nullable=False),
    sa.Column('signal_type', sa.String(length=20), nullable=False),
    sa.Column('risk_mode', sa.String(length=20), nullable=True),
    sa.Column('prompt_version_id', sa.Integer(), nullable=True),
    sa.Column('period_start', sa.TIMESTAMP(), nullable=False),
    sa.Column('period_end', sa.TIMESTAMP(), nullable=False),
    sa.Column('total_signals', sa.Integer(), server_default=sa.text('0'), nullable=False),
    sa.Column('wins', sa.Integer(), server_default=sa.text('0'), nullable=False),
    sa.Column('losses', sa.Integer(), server_default=sa.text('0'), nullable=False),
    sa.Column('neutral', sa.Integer(), server_default=sa.text('0'), nullable=False),
    sa.Column('win_rate', sa.Float(), server_default=sa.text('0'), nullable=False),
    sa.Column('avg_pnl_pct', sa.Float(), nullable=True),
    sa.Column('avg_ai_confidence', sa.Float(), nullable=True),
    sa.Column('avg_calibrated_confidence', sa.Float(), nullable=True),
    sa.Column('calibration_error', sa.Float(), nullable=True),
    sa.Column('computed_at', sa.TIMESTAMP(), server_default=sa.text('NOW()'), nullable=False),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('verdict', 'signal_type', 'period_start', 'period_end', name='uq_verdict_performance_period'),
    comment='Pre-aggregated AI verdict performance metrics'
    )
    
    # Add column comments
    op.execute("""
        COMMENT ON COLUMN ai_verdict_performance.verdict IS 'CONFIRM/DOWNSIZE/SKIP/WAIT';
        COMMENT ON COLUMN ai_verdict_performance.signal_type IS 'LONG/SHORT/NEUTRAL';
        COMMENT ON COLUMN ai_verdict_performance.risk_mode IS 'NORMAL/REDUCED/AVOID/AGGRESSIVE';
        COMMENT ON COLUMN ai_verdict_performance.prompt_version_id IS 'Which prompt version generated this verdict';
        COMMENT ON COLUMN ai_verdict_performance.calibration_error IS 'Difference between AI confidence and actual win rate';
    """)
    
    op.create_index('idx_verdict_perf_verdict', 'ai_verdict_performance', ['verdict'])
    op.create_index('idx_verdict_perf_signal_type', 'ai_verdict_performance', ['signal_type'])
    op.create_index('idx_verdict_perf_period', 'ai_verdict_performance', ['period_start', 'period_end'])
    op.create_index('idx_verdict_perf_prompt', 'ai_verdict_performance', ['prompt_version_id'])
    
    # ### Enhance signal_outcomes table with AI tracking ###
    op.add_column('signal_outcomes', sa.Column('ai_model_used', sa.String(length=100), nullable=True))
    op.add_column('signal_outcomes', sa.Column('prompt_version_id', sa.Integer(), nullable=True))
    op.add_column('signal_outcomes', sa.Column('ai_confidence_raw', sa.Float(), nullable=True))
    op.add_column('signal_outcomes', sa.Column('ai_confidence_calibrated', sa.Float(), nullable=True))
    op.add_column('signal_outcomes', sa.Column('ai_retry_attempts', sa.Integer(), nullable=True))
    op.add_column('signal_outcomes', sa.Column('ai_cost_optimized', sa.Boolean(), nullable=True))
    
    # Add column comments
    op.execute("""
        COMMENT ON COLUMN signal_outcomes.ai_model_used IS 'Which AI model generated the verdict (gpt-4-turbo, gpt-3.5-turbo, etc)';
        COMMENT ON COLUMN signal_outcomes.prompt_version_id IS 'Foreign key to ai_prompt_versions';
        COMMENT ON COLUMN signal_outcomes.ai_confidence_raw IS 'AI stated confidence (0-100) before calibration';
        COMMENT ON COLUMN signal_outcomes.ai_confidence_calibrated IS 'Calibrated confidence based on historical performance';
        COMMENT ON COLUMN signal_outcomes.ai_retry_attempts IS 'How many retry attempts before successful verdict';
        COMMENT ON COLUMN signal_outcomes.ai_cost_optimized IS 'Whether cheaper model (GPT-3.5) was used instead of GPT-4';
    """)
    
    # Add foreign key constraint
    op.create_foreign_key(
        'fk_signal_outcomes_prompt_version',
        'signal_outcomes', 'ai_prompt_versions',
        ['prompt_version_id'], ['id'],
        ondelete='SET NULL'
    )
    
    # Add indexes for AI tracking columns
    op.create_index('idx_signal_outcomes_ai_model', 'signal_outcomes', ['ai_model_used'])
    op.create_index('idx_signal_outcomes_prompt_version', 'signal_outcomes', ['prompt_version_id'])
    op.create_index('idx_signal_outcomes_confidence', 'signal_outcomes', ['ai_confidence_raw', 'ai_confidence_calibrated'])


def downgrade() -> None:
    # Drop indexes first
    op.drop_index('idx_signal_outcomes_confidence', table_name='signal_outcomes')
    op.drop_index('idx_signal_outcomes_prompt_version', table_name='signal_outcomes')
    op.drop_index('idx_signal_outcomes_ai_model', table_name='signal_outcomes')
    
    # Drop foreign key
    op.drop_constraint('fk_signal_outcomes_prompt_version', 'signal_outcomes', type_='foreignkey')
    
    # Drop columns from signal_outcomes
    op.drop_column('signal_outcomes', 'ai_cost_optimized')
    op.drop_column('signal_outcomes', 'ai_retry_attempts')
    op.drop_column('signal_outcomes', 'ai_confidence_calibrated')
    op.drop_column('signal_outcomes', 'ai_confidence_raw')
    op.drop_column('signal_outcomes', 'prompt_version_id')
    op.drop_column('signal_outcomes', 'ai_model_used')
    
    # Drop ai_verdict_performance table
    op.drop_index('idx_verdict_perf_prompt', table_name='ai_verdict_performance')
    op.drop_index('idx_verdict_perf_period', table_name='ai_verdict_performance')
    op.drop_index('idx_verdict_perf_signal_type', table_name='ai_verdict_performance')
    op.drop_index('idx_verdict_perf_verdict', table_name='ai_verdict_performance')
    op.drop_table('ai_verdict_performance')
    
    # Drop ai_prompt_versions table
    op.drop_index('idx_prompt_versions_created', table_name='ai_prompt_versions')
    op.drop_index('idx_prompt_versions_ab_test', table_name='ai_prompt_versions')
    op.drop_index('idx_prompt_versions_active', table_name='ai_prompt_versions')
    op.drop_table('ai_prompt_versions')
