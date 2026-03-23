ALTER TABLE {schema}.prescriptions
  ADD COLUMN IF NOT EXISTS interaction_warnings_count INTEGER NOT NULL DEFAULT 0;
