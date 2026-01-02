-- Normalize objections submitter column and indexes
-- Handles legacy objector_email column by renaming/backfilling safely

DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.tables
        WHERE table_schema = 'public' AND table_name = 'objections'
    ) THEN
        -- Rename legacy column when submitted_by is missing
        IF NOT EXISTS (
            SELECT 1 FROM information_schema.columns
            WHERE table_schema = 'public' AND table_name = 'objections' AND column_name = 'submitted_by'
        ) AND EXISTS (
            SELECT 1 FROM information_schema.columns
            WHERE table_schema = 'public' AND table_name = 'objections' AND column_name = 'objector_email'
        ) THEN
            EXECUTE 'ALTER TABLE public.objections RENAME COLUMN objector_email TO submitted_by';
        END IF;

        -- Backfill and drop legacy column when both exist
        IF EXISTS (
            SELECT 1 FROM information_schema.columns
            WHERE table_schema = 'public' AND table_name = 'objections' AND column_name = 'submitted_by'
        ) AND EXISTS (
            SELECT 1 FROM information_schema.columns
            WHERE table_schema = 'public' AND table_name = 'objections' AND column_name = 'objector_email'
        ) THEN
            EXECUTE 'UPDATE public.objections SET submitted_by = objector_email WHERE submitted_by IS NULL';
            BEGIN
                EXECUTE 'ALTER TABLE public.objections DROP COLUMN objector_email';
            EXCEPTION
                WHEN dependent_objects_still_exist THEN
                    RAISE NOTICE 'objector_email has dependent objects; skipping drop';
                WHEN undefined_column THEN
                    NULL;
            END;
        END IF;

        -- Ensure foreign key exists for submitted_by
        IF EXISTS (
            SELECT 1 FROM information_schema.columns
            WHERE table_schema = 'public' AND table_name = 'objections' AND column_name = 'submitted_by'
        ) THEN
            IF NOT EXISTS (
                SELECT 1
                FROM pg_constraint c
                JOIN pg_class t ON t.oid = c.conrelid
                JOIN pg_attribute a ON a.attrelid = t.oid AND a.attnum = ANY (c.conkey)
                WHERE t.relname = 'objections'
                  AND c.contype = 'f'
                  AND a.attname = 'submitted_by'
            ) THEN
                EXECUTE 'ALTER TABLE public.objections ADD CONSTRAINT objections_submitted_by_fkey FOREIGN KEY (submitted_by) REFERENCES public.people(email) ON DELETE CASCADE';
            END IF;
        END IF;
    END IF;
END $$;

DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.tables
        WHERE table_schema = 'public' AND table_name = 'objections'
    ) THEN
        DROP INDEX IF EXISTS idx_objections_objector;
        DROP INDEX IF EXISTS idx_objection_objector;
        DROP INDEX IF EXISTS idx_objections_status;

        IF EXISTS (
            SELECT 1 FROM information_schema.columns
            WHERE table_schema = 'public' AND table_name = 'objections' AND column_name = 'submitted_by'
        ) THEN
            CREATE INDEX IF NOT EXISTS idx_objection_submitter ON objections(submitted_by);
        END IF;
    END IF;
END $$;
