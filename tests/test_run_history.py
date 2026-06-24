import unittest
from datetime import datetime, timezone

from sqlalchemy import create_engine, text

from app.db.run_history import (
    generate_calculation_snapshot_name,
    get_file_object,
    get_latest_calculation_run,
    list_latest_calculation_runs_by_month,
    list_recent_calculation_runs,
    record_calculation_run,
)


class RunHistoryTest(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
        with self.engine.begin() as connection:
            _create_minimal_schema(connection)
            _seed_project_and_dataset(connection)

    def test_generate_calculation_snapshot_name_is_utc_and_prefixed(self):
        timestamp = datetime(2026, 6, 23, 18, 30, 5, 123456, tzinfo=timezone.utc)

        snapshot_name = generate_calculation_snapshot_name(timestamp)

        self.assertEqual(snapshot_name, "calculation_run_20260623T183005123456Z")

    def test_record_calculation_run_writes_snapshot_and_csv_artifact_metadata(self):
        result = record_calculation_run(
            self.engine,
            project_id="salinas",
            dataset_name="actual",
            snapshot_month="2026-01-01",
            snapshot_name="calculation_run_test",
            snapshot_data={
                "latest_month": "2026-01-01",
                "MP": 1234.56,
                "FA": 0.99,
            },
            csv_artifact={
                "original_filename": "bess_monthly_results.csv",
                "storage_bucket": "bess-files",
                "storage_key": "salinas/actual/calculation_run_test/results.csv",
                "checksum_sha256": "abc123",
                "size_bytes": 2048,
            },
        )

        self.assertIsNotNone(result["snapshot_id"])
        self.assertIsNotNone(result["file_object_id"])

        latest_run = get_latest_calculation_run(
            self.engine,
            project_id="salinas",
            dataset_name="actual",
        )

        self.assertEqual(latest_run["snapshot_name"], "calculation_run_test")
        self.assertEqual(latest_run["snapshot_month"], "2026-01-01")
        self.assertEqual(latest_run["snapshot_data"]["MP"], 1234.56)
        self.assertEqual(
            latest_run["csv_artifact"]["storage_key"],
            "salinas/actual/calculation_run_test/results.csv",
        )

        file_object = get_file_object(self.engine, result["file_object_id"])
        self.assertEqual(file_object["object_type"], "csv_export")
        self.assertEqual(file_object["content_type"], "text/csv")
        self.assertEqual(file_object["checksum_sha256"], "abc123")

    def test_record_calculation_run_normalizes_year_month_snapshot_month(self):
        record_calculation_run(
            self.engine,
            project_id="salinas",
            dataset_name="actual",
            snapshot_month="2027-12",
            snapshot_name="calculation_run_year_month",
            snapshot_data={"MP": 100},
        )

        latest_run = get_latest_calculation_run(
            self.engine,
            project_id="salinas",
            dataset_name="actual",
        )

        self.assertEqual(latest_run["snapshot_month"], "2027-12-01")

    def test_recent_calculation_runs_are_limited_and_sorted_newest_first(self):
        older = record_calculation_run(
            self.engine,
            project_id="salinas",
            dataset_name="actual",
            snapshot_month="2026-01-01",
            snapshot_name="calculation_run_older",
            snapshot_data={"MP": 100},
        )
        newer = record_calculation_run(
            self.engine,
            project_id="salinas",
            dataset_name="actual",
            snapshot_month="2026-02-01",
            snapshot_name="calculation_run_newer",
            snapshot_data={"MP": 200},
        )
        with self.engine.begin() as connection:
            connection.execute(
                text(
                    """
                    UPDATE monthly_snapshot
                    SET created_at = :created_at
                    WHERE id = :snapshot_id
                    """
                ),
                {
                    "created_at": "2026-06-23 10:00:00",
                    "snapshot_id": older["snapshot_id"],
                },
            )
            connection.execute(
                text(
                    """
                    UPDATE monthly_snapshot
                    SET created_at = :created_at
                    WHERE id = :snapshot_id
                    """
                ),
                {
                    "created_at": "2026-06-23 11:00:00",
                    "snapshot_id": newer["snapshot_id"],
                },
            )

        runs = list_recent_calculation_runs(
            self.engine,
            project_id="salinas",
            dataset_name="actual",
            limit=1,
        )

        self.assertEqual(len(runs), 1)
        self.assertEqual(runs[0]["snapshot_name"], "calculation_run_newer")
        self.assertIsNone(runs[0]["csv_artifact"])

    def test_latest_calculation_runs_by_month_keeps_latest_run_for_each_month(self):
        january_first = record_calculation_run(
            self.engine,
            project_id="salinas",
            dataset_name="actual",
            snapshot_month="2026-01-01",
            snapshot_name="calculation_run_january_first",
            snapshot_data={"MP": 100},
        )
        january_latest = record_calculation_run(
            self.engine,
            project_id="salinas",
            dataset_name="actual",
            snapshot_month="2026-01-01",
            snapshot_name="calculation_run_january_latest",
            snapshot_data={"MP": 150},
        )
        february = record_calculation_run(
            self.engine,
            project_id="salinas",
            dataset_name="actual",
            snapshot_month="2026-02-01",
            snapshot_name="calculation_run_february",
            snapshot_data={"MP": 200},
        )
        with self.engine.begin() as connection:
            _set_snapshot_created_at(connection, january_first, "2026-06-23 10:00:00")
            _set_snapshot_created_at(connection, january_latest, "2026-06-23 11:00:00")
            _set_snapshot_created_at(connection, february, "2026-06-23 09:00:00")

        runs = list_latest_calculation_runs_by_month(
            self.engine,
            project_id="salinas",
            dataset_name="actual",
            limit=12,
        )

        self.assertEqual(
            [run["snapshot_name"] for run in runs],
            [
                "calculation_run_february",
                "calculation_run_january_latest",
            ],
        )
        self.assertEqual(runs[1]["snapshot_data"]["MP"], 150)

    def test_get_latest_calculation_run_returns_none_when_no_runs_exist(self):
        self.assertIsNone(
            get_latest_calculation_run(
                self.engine,
                project_id="salinas",
                dataset_name="actual",
            )
        )


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
            CREATE TABLE file_object (
                id text PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),
                project_id text,
                dataset_config_id text,
                object_type text NOT NULL,
                original_filename text NOT NULL,
                content_type text,
                storage_bucket text NOT NULL,
                storage_key text NOT NULL UNIQUE,
                checksum_sha256 text,
                size_bytes integer,
                uploaded_by text,
                uploaded_at text NOT NULL DEFAULT (datetime('now'))
            )
            """
        )
    )
    connection.execute(
        text(
            """
            CREATE TABLE monthly_snapshot (
                id text PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),
                dataset_config_id text NOT NULL,
                snapshot_month text NOT NULL,
                snapshot_name text NOT NULL,
                snapshot_data text NOT NULL,
                source_file_object_id text,
                created_by text,
                created_at text NOT NULL DEFAULT (datetime('now')),
                UNIQUE (dataset_config_id, snapshot_month, snapshot_name)
            )
            """
        )
    )


def _seed_project_and_dataset(connection):
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


def _set_snapshot_created_at(connection, result, created_at):
    connection.execute(
        text(
            """
            UPDATE monthly_snapshot
            SET created_at = :created_at
            WHERE id = :snapshot_id
            """
        ),
        {
            "created_at": created_at,
            "snapshot_id": result["snapshot_id"],
        },
    )


if __name__ == "__main__":
    unittest.main()
