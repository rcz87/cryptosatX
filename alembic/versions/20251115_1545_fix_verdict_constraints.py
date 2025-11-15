"""Fix AI Verdict Performance Constraints

Revision ID: fix_verdict_constraints
Revises: ai_feedback_20251115
Create Date: 2025-11-15 15:45:00.000000

CRITICAL FIXES:
1. Add missing FK constraint: ai_verdict_performance.prompt_version_id -> ai_prompt_versions.id
2. Fix incomplete unique constraint to include prompt_version_id and risk_mode

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'fix_verdict_constraints'
down_revision = 'ai_feedback_20251115'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    Apply constraint fixes to ai_verdict_performance table
    """
    
    # CRITICAL FIX 1: Add FK constraint for prompt_version_id
    # This ensures data integrity - can't reference non-existent prompt versions
    op.create_foreign_key(
        'fk_ai_verdict_perf_prompt_version',
        'ai_verdict_performance',
        'ai_prompt_versions',
        ['prompt_version_id'],
        ['id'],
        ondelete='SET NULL'
    )
    
    # CRITICAL FIX 2: Drop old incomplete unique constraint
    # Old constraint was missing prompt_version_id and risk_mode
    op.drop_constraint(
        'uq_verdict_performance_period',
        'ai_verdict_performance',
        type_='unique'
    )
    
    # CRITICAL FIX 2 (continued): Create new comprehensive unique constraint
    # Now includes ALL relevant columns to prevent duplicate data
    # This prevents having multiple performance records for:
    # - Same verdict + signal_type + period BUT different prompt versions
    # - Same verdict + signal_type + period BUT different risk modes
    op.create_unique_constraint(
        'uq_verdict_performance_complete',
        'ai_verdict_performance',
        ['verdict', 'signal_type', 'prompt_version_id', 'risk_mode', 'period_start', 'period_end']
    )
    
    # Add comment explaining the constraint
    op.execute("""
        COMMENT ON CONSTRAINT uq_verdict_performance_complete ON ai_verdict_performance IS 
        'Ensures unique performance record per verdict/signal/prompt/risk/period combination. Prevents duplicate aggregations for A/B testing.';
    """)


def downgrade() -> None:
    """
    Reverse constraint changes
    """
    
    # Remove new unique constraint
    op.drop_constraint(
        'uq_verdict_performance_complete',
        'ai_verdict_performance',
        type_='unique'
    )
    
    # Restore old incomplete unique constraint
    # (for backward compatibility, though it's flawed)
    op.create_unique_constraint(
        'uq_verdict_performance_period',
        'ai_verdict_performance',
        ['verdict', 'signal_type', 'period_start', 'period_end']
    )
    
    # Remove FK constraint
    op.drop_constraint(
        'fk_ai_verdict_perf_prompt_version',
        'ai_verdict_performance',
        type_='foreignkey'
    )
