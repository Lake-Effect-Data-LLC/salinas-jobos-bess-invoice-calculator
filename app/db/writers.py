from sqlalchemy import text


def _insert_monthly_performance_guarantee(connection, dataset_config_id, record):
    return connection.execute(
        text(
            """
            INSERT INTO monthly_performance_guarantee (
                dataset_config_id,
                timestamp_month,
                agreement_year,
                ce,
                de,
                ae_beg,
                ae_end,
                source_reference,
                notes
            )
            VALUES (
                :dataset_config_id,
                :timestamp_month,
                :agreement_year,
                :ce,
                :de,
                :ae_beg,
                :ae_end,
                :source_reference,
                :notes
            )
            RETURNING id
            """
        ),
        {"dataset_config_id": dataset_config_id, **_without_id(record)},
    ).scalar_one()


def _update_monthly_performance_guarantee(connection, record):
    connection.execute(
        text(
            """
            UPDATE monthly_performance_guarantee
            SET timestamp_month = :timestamp_month,
                agreement_year = :agreement_year,
                ce = :ce,
                de = :de,
                ae_beg = :ae_beg,
                ae_end = :ae_end,
                source_reference = :source_reference,
                notes = :notes,
                updated_at = now()
            WHERE id = :id
            """
        ),
        record,
    )


def _delete_monthly_performance_guarantee(connection, row_id):
    _delete_row(connection, "monthly_performance_guarantee", row_id)


def _insert_performance_test(connection, dataset_config_id, record):
    return connection.execute(
        text(
            """
            INSERT INTO performance_tests (
                dataset_config_id,
                test_id,
                agreement_year,
                test_type,
                test_date,
                requested_by,
                tde,
                measured_ramp_rate,
                certified_by,
                prepa_approved,
                approval_date,
                cure_or_retest_date,
                replaces_test_id,
                ramp_failure_caused_outage,
                outage_start,
                outage_end,
                outage_equivalent_unavhrs,
                source_reference,
                notes
            )
            VALUES (
                :dataset_config_id,
                :test_id,
                :agreement_year,
                :test_type,
                :test_date,
                :requested_by,
                :tde,
                :measured_ramp_rate,
                :certified_by,
                :prepa_approved,
                :approval_date,
                :cure_or_retest_date,
                :replaces_test_id,
                :ramp_failure_caused_outage,
                :outage_start,
                :outage_end,
                :outage_equivalent_unavhrs,
                :source_reference,
                :notes
            )
            RETURNING id
            """
        ),
        {"dataset_config_id": dataset_config_id, **_without_id(record)},
    ).scalar_one()


def _update_performance_test(connection, record):
    connection.execute(
        text(
            """
            UPDATE performance_tests
            SET test_id = :test_id,
                agreement_year = :agreement_year,
                test_type = :test_type,
                test_date = :test_date,
                requested_by = :requested_by,
                tde = :tde,
                measured_ramp_rate = :measured_ramp_rate,
                certified_by = :certified_by,
                prepa_approved = :prepa_approved,
                approval_date = :approval_date,
                cure_or_retest_date = :cure_or_retest_date,
                replaces_test_id = :replaces_test_id,
                ramp_failure_caused_outage = :ramp_failure_caused_outage,
                outage_start = :outage_start,
                outage_end = :outage_end,
                outage_equivalent_unavhrs = :outage_equivalent_unavhrs,
                source_reference = :source_reference,
                notes = :notes,
                updated_at = now()
            WHERE id = :id
            """
        ),
        record,
    )


def _delete_performance_test(connection, row_id):
    _delete_row(connection, "performance_tests", row_id)


def _insert_yearly_input(connection, dataset_config_id, record):
    return connection.execute(
        text(
            """
            INSERT INTO yearly_inputs (
                dataset_config_id,
                agreement_year,
                dde,
                tr,
                gc,
                source_reference,
                notes
            )
            VALUES (
                :dataset_config_id,
                :agreement_year,
                :dde,
                :tr,
                :gc,
                :source_reference,
                :notes
            )
            RETURNING id
            """
        ),
        {"dataset_config_id": dataset_config_id, **_without_id(record)},
    ).scalar_one()


def _update_yearly_input(connection, record):
    connection.execute(
        text(
            """
            UPDATE yearly_inputs
            SET agreement_year = :agreement_year,
                dde = :dde,
                tr = :tr,
                gc = :gc,
                source_reference = :source_reference,
                notes = :notes,
                updated_at = now()
            WHERE id = :id
            """
        ),
        record,
    )


def _delete_yearly_input(connection, row_id):
    _delete_row(connection, "yearly_inputs", row_id)


def _insert_monthly_input(connection, dataset_config_id, record):
    return connection.execute(
        text(
            """
            INSERT INTO monthly_inputs (
                dataset_config_id,
                timestamp_month,
                agreement_year,
                other_adj,
                bphrs,
                pohrs,
                unavhrs,
                unavprodhrs,
                gse,
                pfm,
                ip,
                source_reference,
                notes
            )
            VALUES (
                :dataset_config_id,
                :timestamp_month,
                :agreement_year,
                :other_adj,
                :bphrs,
                :pohrs,
                :unavhrs,
                :unavprodhrs,
                :gse,
                :pfm,
                :ip,
                :source_reference,
                :notes
            )
            RETURNING id
            """
        ),
        {"dataset_config_id": dataset_config_id, **_without_id(record)},
    ).scalar_one()


def _update_monthly_input(connection, record):
    connection.execute(
        text(
            """
            UPDATE monthly_inputs
            SET timestamp_month = :timestamp_month,
                agreement_year = :agreement_year,
                other_adj = :other_adj,
                bphrs = :bphrs,
                pohrs = :pohrs,
                unavhrs = :unavhrs,
                unavprodhrs = :unavprodhrs,
                gse = :gse,
                pfm = :pfm,
                ip = :ip,
                source_reference = :source_reference,
                notes = :notes,
                updated_at = now()
            WHERE id = :id
            """
        ),
        record,
    )


def _delete_monthly_input(connection, row_id):
    _delete_row(connection, "monthly_inputs", row_id)


def _delete_contract_value(connection, row_id):
    _delete_row(connection, "contract_values", row_id)


def _delete_row(connection, table_name, row_id):
    connection.execute(
        text(
            f"""
            DELETE FROM {table_name}
            WHERE id = :id
            """
        ),
        {"id": row_id},
    )


def _without_id(record):
    return {
        key: value
        for key, value in record.items()
        if key != "id"
    }
