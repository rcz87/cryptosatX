"""HIGH PRIORITY FIXES: Validation, Sync Logic, and Performance Indexes

Revision ID: high_priority_fixes
Revises: fix_verdict_constraints
Create Date: 2025-11-15 16:00:00.000000

CRITICAL FIXES:
1. Add CHECK constraint for ab_test_percentage (0-100)
2. Create automated sync logic for avg_win_rate from ai_verdict_performance
3. Add missing composite indexes for common query patterns

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'high_priority_fixes'
down_revision = 'fix_verdict_constraints'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    Apply HIGH PRIORITY fixes for data validation, sync, and performance
    """

    # ========================================================================
    # FIX 1: Add CHECK constraint for ab_test_percentage (0-100)
    # ========================================================================
    # IMPACT: Prevents invalid values like -100 or 999
    # BEFORE: Could insert any integer value
    # AFTER: Only allows 0-100 or NULL

    op.create_check_constraint(
        'chk_ab_test_percentage_range',
        'ai_prompt_versions',
        'ab_test_percentage IS NULL OR (ab_test_percentage >= 0 AND ab_test_percentage <= 100)'
    )

    op.execute("""
        COMMENT ON CONSTRAINT chk_ab_test_percentage_range ON ai_prompt_versions IS
        'Ensures ab_test_percentage is NULL or between 0-100 (percentage values only)';
    """)

    # ========================================================================
    # FIX 2: Create automated sync function for avg_win_rate
    # ========================================================================
    # IMPACT: Automatically updates ai_prompt_versions.avg_win_rate from
    #         ai_verdict_performance when performance data is inserted/updated
    # APPROACH: PostgreSQL function + trigger for real-time sync

    # Create function to calculate and update avg_win_rate
    op.execute("""
        CREATE OR REPLACE FUNCTION sync_prompt_version_metrics()
        RETURNS TRIGGER AS $$
        BEGIN
            -- Update avg_win_rate for the affected prompt_version_id
            -- Calculate weighted average based on total_signals
            UPDATE ai_prompt_versions
            SET
                avg_win_rate = (
                    SELECT
                        CASE
                            WHEN SUM(avp.total_signals) > 0 THEN
                                SUM(avp.win_rate * avp.total_signals) / SUM(avp.total_signals)
                            ELSE NULL
                        END
                    FROM ai_verdict_performance avp
                    WHERE avp.prompt_version_id = COALESCE(NEW.prompt_version_id, OLD.prompt_version_id)
                ),
                avg_calibration_error = (
                    SELECT
                        CASE
                            WHEN COUNT(*) > 0 THEN
                                AVG(avp.calibration_error)
                            ELSE NULL
                        END
                    FROM ai_verdict_performance avp
                    WHERE avp.prompt_version_id = COALESCE(NEW.prompt_version_id, OLD.prompt_version_id)
                    AND avp.calibration_error IS NOT NULL
                ),
                total_signals_processed = (
                    SELECT COALESCE(SUM(avp.total_signals), 0)
                    FROM ai_verdict_performance avp
                    WHERE avp.prompt_version_id = COALESCE(NEW.prompt_version_id, OLD.prompt_version_id)
                )
            WHERE id = COALESCE(NEW.prompt_version_id, OLD.prompt_version_id);

            RETURN COALESCE(NEW, OLD);
        END;
        $$ LANGUAGE plpgsql;
    """)

    op.execute("""
        COMMENT ON FUNCTION sync_prompt_version_metrics() IS
        'Auto-syncs avg_win_rate, avg_calibration_error, and total_signals_processed from ai_verdict_performance to ai_prompt_versions';
    """)

    # Create trigger on ai_verdict_performance for INSERT/UPDATE/DELETE
    op.execute("""
        CREATE TRIGGER trg_sync_prompt_metrics_after_insert_update
        AFTER INSERT OR UPDATE ON ai_verdict_performance
        FOR EACH ROW
        WHEN (NEW.prompt_version_id IS NOT NULL)
        EXECUTE FUNCTION sync_prompt_version_metrics();
    """)

    op.execute("""
        CREATE TRIGGER trg_sync_prompt_metrics_after_delete
        AFTER DELETE ON ai_verdict_performance
        FOR EACH ROW
        WHEN (OLD.prompt_version_id IS NOT NULL)
        EXECUTE FUNCTION sync_prompt_version_metrics();
    """)

    # Initial sync for existing data
    op.execute("""
        -- Sync all existing prompt versions with their current performance data
        UPDATE ai_prompt_versions apv
        SET
            avg_win_rate = subq.avg_win_rate,
            avg_calibration_error = subq.avg_calibration_error,
            total_signals_processed = subq.total_signals
        FROM (
            SELECT
                avp.prompt_version_id,
                CASE
                    WHEN SUM(avp.total_signals) > 0 THEN
                        SUM(avp.win_rate * avp.total_signals) / SUM(avp.total_signals)
                    ELSE NULL
                END as avg_win_rate,
                AVG(avp.calibration_error) as avg_calibration_error,
                COALESCE(SUM(avp.total_signals), 0) as total_signals
            FROM ai_verdict_performance avp
            WHERE avp.prompt_version_id IS NOT NULL
            GROUP BY avp.prompt_version_id
        ) subq
        WHERE apv.id = subq.prompt_version_id;
    """)

    # ========================================================================
    # FIX 3: Add missing composite and performance indexes
    # ========================================================================
    # IMPACT: Dramatically improves query performance for common patterns

    # 3A. Composite index for active prompts with A/B testing
    # USE CASE: SELECT * FROM ai_prompt_versions WHERE is_active=true AND ab_test_active=true
    # BEFORE: Requires scanning both indexes separately
    # AFTER: Single index scan - 10x+ faster for this query pattern
    op.create_index(
        'idx_prompt_versions_active_ab_test_composite',
        'ai_prompt_versions',
        ['is_active', 'ab_test_active'],
        postgresql_where=sa.text('is_active = true OR ab_test_active = true')
    )

    # 3B. Index for latest performance records (period_end DESC)
    # USE CASE: SELECT * FROM ai_verdict_performance ORDER BY period_end DESC LIMIT 10
    # BEFORE: Full table scan + sort
    # AFTER: Index scan only - crucial for dashboard "latest metrics" queries
    op.create_index(
        'idx_verdict_perf_period_end_desc',
        'ai_verdict_performance',
        [sa.text('period_end DESC')]
    )

    # 3C. Composite index for prompt version + period queries
    # USE CASE: Getting latest performance for a specific prompt version
    # BEFORE: Two separate index scans
    # AFTER: Single composite index scan
    op.create_index(
        'idx_verdict_perf_prompt_period_composite',
        'ai_verdict_performance',
        ['prompt_version_id', sa.text('period_end DESC')]
    )

    # Add comments explaining the performance benefits
    op.execute("""
        COMMENT ON INDEX idx_prompt_versions_active_ab_test_composite IS
        'Optimizes queries filtering by is_active and ab_test_active (common in production routing logic)'
    """)

    op.execute("""
        COMMENT ON INDEX idx_verdict_perf_period_end_desc IS
        'Optimizes ORDER BY period_end DESC queries for fetching latest performance metrics'
    """)

    op.execute("""
        COMMENT ON INDEX idx_verdict_perf_prompt_period_composite IS
        'Optimizes queries getting latest performance for specific prompt versions'
    """)


def downgrade() -> None:
    """
    Reverse all HIGH PRIORITY fixes
    """

    # Remove performance indexes
    op.drop_index('idx_verdict_perf_prompt_period_composite', table_name='ai_verdict_performance')
    op.drop_index('idx_verdict_perf_period_end_desc', table_name='ai_verdict_performance')
    op.drop_index('idx_prompt_versions_active_ab_test_composite', table_name='ai_prompt_versions')

    # Remove triggers
    op.execute('DROP TRIGGER IF EXISTS trg_sync_prompt_metrics_after_delete ON ai_verdict_performance;')
    op.execute('DROP TRIGGER IF EXISTS trg_sync_prompt_metrics_after_insert_update ON ai_verdict_performance;')

    # Remove sync function
    op.execute('DROP FUNCTION IF EXISTS sync_prompt_version_metrics();')

    # Remove CHECK constraint
    op.drop_constraint('chk_ab_test_percentage_range', 'ai_prompt_versions', type_='check')
