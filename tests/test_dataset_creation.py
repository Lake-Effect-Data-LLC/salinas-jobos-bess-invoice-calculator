import unittest

from sqlalchemy import create_engine, text

from app.db.datasets import create_dataset_config, get_dataset_row_counts


class DatasetCreationTest(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
        with self.engine.begin() as connection:
            _create_minimal_schema(connection)
            _seed_project_and_actual_dataset(connection)
            _seed_contract_value(connection, "actual-id", agreement_year=1)

    def test_new_dataset_starts_with_contract_values_from_actual(self):
        created_name = create_dataset_config(
            self.engine,
            project_id="salinas",
            dataset_name="testing",
        )

        self.assertEqual(created_name, "testing")
        row_counts = get_dataset_row_counts(self.engine, "salinas", "testing")
        self.assertEqual(row_counts["contract_values"], 1)
        self.assertEqual(row_counts["yearly_inputs"], 0)
        self.assertEqual(row_counts["monthly_inputs"], 0)

    def test_new_dataset_can_seed_from_non_actual_dataset_with_contract_values(self):
        with self.engine.begin() as connection:
            connection.execute(
                text("DELETE FROM contract_values WHERE dataset_config_id = 'actual-id'")
            )
            connection.execute(
                text(
                    """
                    INSERT INTO dataset_config (id, project_id, name, description, is_default)
                    VALUES ('template-id', 'salinas', 'template', '', false)
                    """
                )
            )
            _seed_contract_value(connection, "template-id", agreement_year=2)

        create_dataset_config(
            self.engine,
            project_id="salinas",
            dataset_name="scenario_1",
        )

        row_counts = get_dataset_row_counts(self.engine, "salinas", "scenario_1")
        self.assertEqual(row_counts["contract_values"], 1)


def _create_minimal_schema(connection):
    connection.execute(
        text(
            """
            CREATE TABLE project (
                id text PRIMARY KEY,
                name text NOT NULL
            )
            """
        )
    )
    connection.execute(
        text(
            """
            CREATE TABLE dataset_config (
                id text PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),
                project_id text NOT NULL,
                name text NOT NULL,
                description text,
                is_default boolean NOT NULL DEFAULT false,
                UNIQUE (project_id, name)
            )
            """
        )
    )
    connection.execute(
        text(
            """
            CREATE TABLE contract_values (
                id text PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),
                dataset_config_id text NOT NULL,
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
                source_file_object_id text,
                UNIQUE (dataset_config_id, agreement_year)
            )
            """
        )
    )
    for table_name in (
        "yearly_inputs",
        "monthly_inputs",
        "monthly_performance_guarantee",
        "performance_tests",
    ):
        connection.execute(
            text(
                f"""
                CREATE TABLE {table_name} (
                    id text PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),
                    dataset_config_id text NOT NULL
                )
                """
            )
        )


def _seed_project_and_actual_dataset(connection):
    connection.execute(
        text("INSERT INTO project (id, name) VALUES ('salinas', 'Salinas BESS')")
    )
    connection.execute(
        text(
            """
            INSERT INTO dataset_config (id, project_id, name, description, is_default)
            VALUES ('actual-id', 'salinas', 'actual', 'Current production input dataset', true)
            """
        )
    )


def _seed_contract_value(connection, dataset_config_id, agreement_year):
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
            VALUES (
                :dataset_config_id, :agreement_year, 1, 2, 4, 5, 6, 7,
                8, 400, 0.01, 500, 24, 48, 12, 'test source', 'test notes', NULL
            )
            """
        ),
        {
            "dataset_config_id": dataset_config_id,
            "agreement_year": agreement_year,
        },
    )


if __name__ == "__main__":
    unittest.main()
