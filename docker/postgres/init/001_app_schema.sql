CREATE EXTENSION IF NOT EXISTS pgcrypto;

CREATE TABLE IF NOT EXISTS app_user (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    email text NOT NULL UNIQUE,
    display_name text,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS project (
    id text PRIMARY KEY,
    name text NOT NULL,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS dataset_config (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id text NOT NULL REFERENCES project(id) ON DELETE CASCADE,
    name text NOT NULL,
    description text,
    is_default boolean NOT NULL DEFAULT false,
    created_by uuid REFERENCES app_user(id) ON DELETE SET NULL,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),
    UNIQUE (project_id, name)
);

CREATE TABLE IF NOT EXISTS file_object (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id text REFERENCES project(id) ON DELETE SET NULL,
    dataset_config_id uuid REFERENCES dataset_config(id) ON DELETE SET NULL,
    object_type text NOT NULL CHECK (object_type IN ('source_upload', 'csv_export', 'report')),
    original_filename text NOT NULL,
    content_type text,
    storage_bucket text NOT NULL,
    storage_key text NOT NULL UNIQUE,
    checksum_sha256 text,
    size_bytes bigint,
    uploaded_by uuid REFERENCES app_user(id) ON DELETE SET NULL,
    uploaded_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS monthly_snapshot (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    dataset_config_id uuid NOT NULL REFERENCES dataset_config(id) ON DELETE CASCADE,
    snapshot_month date NOT NULL,
    snapshot_name text NOT NULL,
    snapshot_data jsonb NOT NULL,
    source_file_object_id uuid REFERENCES file_object(id) ON DELETE SET NULL,
    created_by uuid REFERENCES app_user(id) ON DELETE SET NULL,
    created_at timestamptz NOT NULL DEFAULT now(),
    UNIQUE (dataset_config_id, snapshot_month, snapshot_name)
);

CREATE TABLE IF NOT EXISTS contract_values (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    dataset_config_id uuid NOT NULL REFERENCES dataset_config(id) ON DELETE CASCADE,
    agreement_year integer NOT NULL,
    cppf numeric(14, 2) NOT NULL,
    cpppif numeric(14, 2) NOT NULL,
    ddd numeric(10, 4) NOT NULL,
    ta numeric(10, 4) NOT NULL,
    rer numeric(14, 4) NOT NULL,
    ge numeric(10, 4) NOT NULL,
    design_dmax numeric(14, 4) NOT NULL,
    design_duration_energy numeric(14, 4) NOT NULL,
    annual_duration_energy_degradation_rate numeric(10, 6) NOT NULL,
    design_charge_energy numeric(14, 4) NOT NULL,
    grid_system_waiting_period_hours numeric(14, 4) NOT NULL,
    force_majeure_waiting_period_hours numeric(14, 4) NOT NULL,
    scheduled_maintenance_allowance_hours numeric(14, 4) NOT NULL,
    source_reference text NOT NULL DEFAULT '',
    notes text NOT NULL DEFAULT '',
    source_file_object_id uuid REFERENCES file_object(id) ON DELETE SET NULL,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),
    UNIQUE (dataset_config_id, agreement_year)
);

CREATE TABLE IF NOT EXISTS yearly_inputs (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    dataset_config_id uuid NOT NULL REFERENCES dataset_config(id) ON DELETE CASCADE,
    agreement_year integer NOT NULL,
    dde numeric(14, 4) NOT NULL,
    tr numeric(14, 4) NOT NULL,
    gc numeric(14, 4),
    source_reference text NOT NULL DEFAULT '',
    notes text NOT NULL DEFAULT '',
    source_file_object_id uuid REFERENCES file_object(id) ON DELETE SET NULL,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),
    UNIQUE (dataset_config_id, agreement_year)
);

CREATE TABLE IF NOT EXISTS monthly_inputs (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    dataset_config_id uuid NOT NULL REFERENCES dataset_config(id) ON DELETE CASCADE,
    timestamp_month date NOT NULL,
    agreement_year integer NOT NULL,
    other_adj numeric(14, 2) NOT NULL DEFAULT 0,
    bphrs numeric(14, 4) NOT NULL,
    pohrs numeric(14, 4) NOT NULL DEFAULT 0,
    unavhrs numeric(14, 4) NOT NULL DEFAULT 0,
    unavprodhrs numeric(14, 4) NOT NULL DEFAULT 0,
    gse numeric(14, 4) NOT NULL DEFAULT 0,
    pfm numeric(14, 4) NOT NULL DEFAULT 0,
    ip numeric(14, 4) NOT NULL DEFAULT 0,
    source_reference text NOT NULL DEFAULT '',
    notes text NOT NULL DEFAULT '',
    source_file_object_id uuid REFERENCES file_object(id) ON DELETE SET NULL,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),
    UNIQUE (dataset_config_id, timestamp_month)
);

CREATE TABLE IF NOT EXISTS monthly_performance_guarantee (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    dataset_config_id uuid NOT NULL REFERENCES dataset_config(id) ON DELETE CASCADE,
    timestamp_month date NOT NULL,
    agreement_year integer NOT NULL,
    ce numeric(14, 4) NOT NULL,
    de numeric(14, 4) NOT NULL,
    ae_beg numeric(14, 4) NOT NULL,
    ae_end numeric(14, 4) NOT NULL,
    source_reference text NOT NULL DEFAULT '',
    notes text NOT NULL DEFAULT '',
    source_file_object_id uuid REFERENCES file_object(id) ON DELETE SET NULL,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),
    UNIQUE (dataset_config_id, timestamp_month)
);

CREATE TABLE IF NOT EXISTS performance_tests (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    dataset_config_id uuid NOT NULL REFERENCES dataset_config(id) ON DELETE CASCADE,
    test_id text NOT NULL,
    agreement_year integer NOT NULL,
    test_type text NOT NULL,
    test_date date NOT NULL,
    requested_by text,
    tde numeric(14, 4) NOT NULL,
    measured_ramp_rate numeric(14, 4),
    certified_by text,
    prepa_approved boolean NOT NULL DEFAULT false,
    approval_date date,
    cure_or_retest_date date,
    replaces_test_id text,
    ramp_failure_caused_outage boolean NOT NULL DEFAULT false,
    outage_start timestamptz,
    outage_end timestamptz,
    outage_equivalent_unavhrs numeric(14, 4) NOT NULL DEFAULT 0,
    source_reference text,
    notes text,
    source_file_object_id uuid REFERENCES file_object(id) ON DELETE SET NULL,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),
    UNIQUE (dataset_config_id, test_id)
);

CREATE TABLE IF NOT EXISTS row_edit_history (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    dataset_config_id uuid NOT NULL REFERENCES dataset_config(id) ON DELETE CASCADE,
    table_name text NOT NULL CHECK (
        table_name IN (
            'contract_values',
            'yearly_inputs',
            'monthly_inputs',
            'monthly_performance_guarantee',
            'performance_tests'
        )
    ),
    row_id uuid NOT NULL,
    action text NOT NULL CHECK (action IN ('insert', 'update', 'delete')),
    audit_event_id text,
    previous_data jsonb,
    new_data jsonb,
    edited_by uuid REFERENCES app_user(id) ON DELETE SET NULL,
    edit_reason text,
    source text,
    artifact_bucket text,
    artifact_csv_key text,
    artifact_json_key text,
    created_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS validation_result (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    dataset_config_id uuid NOT NULL REFERENCES dataset_config(id) ON DELETE CASCADE,
    table_name text,
    row_id uuid,
    severity text NOT NULL CHECK (severity IN ('warning', 'blocking')),
    code text NOT NULL,
    message text NOT NULL,
    created_at timestamptz NOT NULL DEFAULT now()
);

INSERT INTO project (id, name)
VALUES
    ('salinas', 'Salinas BESS'),
    ('jobos', 'Jobos BESS')
ON CONFLICT (id) DO NOTHING;

INSERT INTO dataset_config (project_id, name, description, is_default)
VALUES
    ('salinas', 'actual', 'Current production input dataset', true),
    ('jobos', 'actual', 'Current production input dataset', true)
ON CONFLICT (project_id, name) DO NOTHING;

CREATE INDEX IF NOT EXISTS idx_dataset_config_project_id ON dataset_config(project_id);
CREATE INDEX IF NOT EXISTS idx_file_object_dataset_config_id ON file_object(dataset_config_id);
CREATE INDEX IF NOT EXISTS idx_monthly_snapshot_dataset_month ON monthly_snapshot(dataset_config_id, snapshot_month);
CREATE INDEX IF NOT EXISTS idx_contract_values_dataset ON contract_values(dataset_config_id);
CREATE INDEX IF NOT EXISTS idx_yearly_inputs_dataset ON yearly_inputs(dataset_config_id);
CREATE INDEX IF NOT EXISTS idx_monthly_inputs_dataset_month ON monthly_inputs(dataset_config_id, timestamp_month);
CREATE INDEX IF NOT EXISTS idx_monthly_performance_dataset_month ON monthly_performance_guarantee(dataset_config_id, timestamp_month);
CREATE INDEX IF NOT EXISTS idx_performance_tests_dataset ON performance_tests(dataset_config_id);
CREATE INDEX IF NOT EXISTS idx_row_edit_history_dataset_table ON row_edit_history(dataset_config_id, table_name);
CREATE INDEX IF NOT EXISTS idx_row_edit_history_audit_event_id ON row_edit_history(audit_event_id);
CREATE INDEX IF NOT EXISTS idx_validation_result_dataset_severity ON validation_result(dataset_config_id, severity);
