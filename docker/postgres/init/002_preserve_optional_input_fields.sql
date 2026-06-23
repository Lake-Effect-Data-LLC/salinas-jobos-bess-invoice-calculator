ALTER TABLE contract_values
    ADD COLUMN IF NOT EXISTS source_reference text NOT NULL DEFAULT '',
    ADD COLUMN IF NOT EXISTS notes text NOT NULL DEFAULT '';

ALTER TABLE yearly_inputs
    ADD COLUMN IF NOT EXISTS gc numeric(14, 4),
    ADD COLUMN IF NOT EXISTS source_reference text NOT NULL DEFAULT '',
    ALTER COLUMN notes SET DEFAULT '';

UPDATE yearly_inputs
SET notes = ''
WHERE notes IS NULL;

ALTER TABLE yearly_inputs
    ALTER COLUMN notes SET NOT NULL;

ALTER TABLE monthly_inputs
    ADD COLUMN IF NOT EXISTS source_reference text NOT NULL DEFAULT '',
    ADD COLUMN IF NOT EXISTS notes text NOT NULL DEFAULT '';

ALTER TABLE monthly_performance_guarantee
    ADD COLUMN IF NOT EXISTS source_reference text NOT NULL DEFAULT '',
    ALTER COLUMN notes SET DEFAULT '';

UPDATE monthly_performance_guarantee
SET notes = ''
WHERE notes IS NULL;

ALTER TABLE monthly_performance_guarantee
    ALTER COLUMN notes SET NOT NULL;
