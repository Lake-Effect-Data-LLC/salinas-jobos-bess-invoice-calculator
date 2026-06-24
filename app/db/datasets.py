from sqlalchemy import text


INPUT_TABLES = (
    "contract_values",
    "yearly_inputs",
    "monthly_inputs",
    "monthly_performance_guarantee",
    "performance_tests",
)

DATASET_NAME_PATTERN = "lowercase letters, numbers, and underscores only"


def list_dataset_configs(engine, project_id):
    with engine.connect() as connection:
        rows = connection.execute(
            text(
                """
                SELECT name, description, is_default
                FROM dataset_config
                WHERE project_id = :project_id
                ORDER BY is_default DESC, name
                """
            ),
            {"project_id": project_id},
        ).mappings()

        return [dict(row) for row in rows]


def create_dataset_config(
    engine,
    project_id,
    dataset_name,
    description="",
    copy_from_dataset_name=None,
):
    normalized_name = _normalize_dataset_name(dataset_name)
    with engine.begin() as connection:
        existing = connection.execute(
            text(
                """
                SELECT 1
                FROM dataset_config
                WHERE project_id = :project_id
                  AND name = :dataset_name
                """
            ),
            {"project_id": project_id, "dataset_name": normalized_name},
        ).scalar_one_or_none()
        if existing is not None:
            raise ValueError(
                f"Scenario '{normalized_name}' already exists for this facility."
            )

        new_dataset_id = connection.execute(
            text(
                """
                INSERT INTO dataset_config (
                    project_id,
                    name,
                    description,
                    is_default
                )
                VALUES (
                    :project_id,
                    :dataset_name,
                    :description,
                    false
                )
                RETURNING id
                """
            ),
            {
                "project_id": project_id,
                "dataset_name": normalized_name,
                "description": description,
            },
        ).scalar_one()

        if copy_from_dataset_name:
            source_dataset_id = get_dataset_config_id(
                connection,
                project_id,
                copy_from_dataset_name,
            )
            _copy_input_tables(connection, source_dataset_id, new_dataset_id)
        else:
            contract_seed_dataset_id = _get_contract_seed_dataset_id(
                connection,
                project_id,
                new_dataset_id,
            )
            if contract_seed_dataset_id is not None:
                _copy_contract_values(
                    connection,
                    contract_seed_dataset_id,
                    new_dataset_id,
                )

    return normalized_name


def get_dataset_row_counts(engine, project_id, dataset_name="actual"):
    with engine.connect() as connection:
        dataset_config_id = get_dataset_config_id(connection, project_id, dataset_name)
        counts = {}
        for table_name in INPUT_TABLES:
            counts[table_name] = connection.execute(
                text(
                    f"""
                    SELECT count(*)
                    FROM {table_name}
                    WHERE dataset_config_id = :dataset_config_id
                    """
                ),
                {"dataset_config_id": dataset_config_id},
            ).scalar_one()

    return counts


def _normalize_dataset_name(dataset_name):
    normalized_name = dataset_name.strip().lower()
    if not normalized_name:
        raise ValueError("Scenario name is required.")
    if " " in normalized_name or not normalized_name.replace("_", "").isalnum():
        raise ValueError(f"Scenario name must use {DATASET_NAME_PATTERN}.")
    return normalized_name


def _copy_input_tables(connection, source_dataset_id, new_dataset_id):
    _copy_contract_values(connection, source_dataset_id, new_dataset_id)
    for statement in (
        """
        INSERT INTO yearly_inputs (
            dataset_config_id, agreement_year, dde, tr, gc,
            source_reference, notes, source_file_object_id
        )
        SELECT
            :new_dataset_id, agreement_year, dde, tr, gc,
            source_reference, notes, source_file_object_id
        FROM yearly_inputs
        WHERE dataset_config_id = :source_dataset_id
        """,
        """
        INSERT INTO monthly_inputs (
            dataset_config_id, timestamp_month, agreement_year, other_adj,
            bphrs, pohrs, unavhrs, unavprodhrs, gse, pfm, ip,
            source_reference, notes, source_file_object_id
        )
        SELECT
            :new_dataset_id, timestamp_month, agreement_year, other_adj,
            bphrs, pohrs, unavhrs, unavprodhrs, gse, pfm, ip,
            source_reference, notes, source_file_object_id
        FROM monthly_inputs
        WHERE dataset_config_id = :source_dataset_id
        """,
        """
        INSERT INTO monthly_performance_guarantee (
            dataset_config_id, timestamp_month, agreement_year, ce, de,
            ae_beg, ae_end, source_reference, notes, source_file_object_id
        )
        SELECT
            :new_dataset_id, timestamp_month, agreement_year, ce, de,
            ae_beg, ae_end, source_reference, notes, source_file_object_id
        FROM monthly_performance_guarantee
        WHERE dataset_config_id = :source_dataset_id
        """,
        """
        INSERT INTO performance_tests (
            dataset_config_id, test_id, agreement_year, test_type, test_date,
            requested_by, tde, measured_ramp_rate, certified_by, prepa_approved,
            approval_date, cure_or_retest_date, replaces_test_id,
            ramp_failure_caused_outage, outage_start, outage_end,
            outage_equivalent_unavhrs, source_reference, notes, source_file_object_id
        )
        SELECT
            :new_dataset_id, test_id, agreement_year, test_type, test_date,
            requested_by, tde, measured_ramp_rate, certified_by, prepa_approved,
            approval_date, cure_or_retest_date, replaces_test_id,
            ramp_failure_caused_outage, outage_start, outage_end,
            outage_equivalent_unavhrs, source_reference, notes, source_file_object_id
        FROM performance_tests
        WHERE dataset_config_id = :source_dataset_id
        """,
    ):
        connection.execute(
            text(statement),
            {"source_dataset_id": source_dataset_id, "new_dataset_id": new_dataset_id},
        )


def _get_contract_seed_dataset_id(connection, project_id, new_dataset_id):
    return connection.execute(
        text(
            """
            SELECT dataset.id
            FROM dataset_config dataset
            WHERE dataset.project_id = :project_id
              AND dataset.id <> :new_dataset_id
              AND EXISTS (
                  SELECT 1
                  FROM contract_values contract
                  WHERE contract.dataset_config_id = dataset.id
              )
            ORDER BY
                CASE
                    WHEN dataset.name = 'actual' THEN 0
                    WHEN dataset.is_default THEN 1
                    ELSE 2
                END,
                dataset.name
            LIMIT 1
            """
        ),
        {"project_id": project_id, "new_dataset_id": new_dataset_id},
    ).scalar_one_or_none()


def _copy_contract_values(connection, source_dataset_id, new_dataset_id):
    connection.execute(
        text(
            """
            INSERT INTO contract_values (
                dataset_config_id, agreement_year, cppf, cpppif, ddd, ta, rer, ge,
                design_dmax, design_duration_energy, annual_duration_energy_degradation_rate,
                design_charge_energy, grid_system_waiting_period_hours,
                force_majeure_waiting_period_hours, scheduled_maintenance_allowance_hours,
                source_reference, notes, source_file_object_id
            )
            SELECT
                :new_dataset_id, agreement_year, cppf, cpppif, ddd, ta, rer, ge,
                design_dmax, design_duration_energy, annual_duration_energy_degradation_rate,
                design_charge_energy, grid_system_waiting_period_hours,
                force_majeure_waiting_period_hours, scheduled_maintenance_allowance_hours,
                source_reference, notes, source_file_object_id
            FROM contract_values
            WHERE dataset_config_id = :source_dataset_id
            """
        ),
        {"source_dataset_id": source_dataset_id, "new_dataset_id": new_dataset_id},
    )


def ensure_project_and_dataset(
    connection,
    project_id,
    project_name,
    dataset_name="actual",
    dataset_description="Current production input dataset",
    is_default=True,
):
    connection.execute(
        text(
            """
            INSERT INTO project (id, name)
            VALUES (:project_id, :project_name)
            ON CONFLICT (id) DO UPDATE
            SET name = EXCLUDED.name,
                updated_at = now()
            """
        ),
        {"project_id": project_id, "project_name": project_name},
    )
    connection.execute(
        text(
            """
            INSERT INTO dataset_config (
                project_id,
                name,
                description,
                is_default
            )
            VALUES (
                :project_id,
                :dataset_name,
                :dataset_description,
                :is_default
            )
            ON CONFLICT (project_id, name) DO UPDATE
            SET description = EXCLUDED.description,
                is_default = EXCLUDED.is_default,
                updated_at = now()
            """
        ),
        {
            "project_id": project_id,
            "dataset_name": dataset_name,
            "dataset_description": dataset_description,
            "is_default": is_default,
        },
    )
    return get_dataset_config_id(connection, project_id, dataset_name)


def get_dataset_config_id(connection, project_id, dataset_name="actual"):
    result = connection.execute(
        text(
            """
            SELECT id
            FROM dataset_config
            WHERE project_id = :project_id
              AND name = :dataset_name
            """
        ),
        {"project_id": project_id, "dataset_name": dataset_name},
    ).scalar_one_or_none()

    if result is None:
        raise ValueError(
            f"Dataset '{dataset_name}' does not exist for project '{project_id}'."
        )

    return result
