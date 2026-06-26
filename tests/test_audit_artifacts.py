import unittest

from app.db.audit import update_audit_event_artifacts


class AuditArtifactTest(unittest.TestCase):
    def test_update_audit_event_artifacts_updates_rows_by_event_id(self):
        engine = _FakeEngine(rowcount=3)

        updated_count = update_audit_event_artifacts(
            engine=engine,
            audit_event_id="audit_event_test",
            artifact_bucket="bess-files",
            artifact_csv_key="scenario_state/salinas/actual/audit_event_test.csv",
            artifact_json_key="scenario_state/salinas/actual/audit_event_test.json",
        )

        self.assertEqual(updated_count, 3)
        self.assertEqual(
            engine.connection.params,
            {
                "audit_event_id": "audit_event_test",
                "artifact_bucket": "bess-files",
                "artifact_csv_key": "scenario_state/salinas/actual/audit_event_test.csv",
                "artifact_json_key": "scenario_state/salinas/actual/audit_event_test.json",
            },
        )

    def test_update_audit_event_artifacts_skips_blank_event_id(self):
        engine = _FakeEngine(rowcount=1)

        updated_count = update_audit_event_artifacts(
            engine=engine,
            audit_event_id=None,
            artifact_bucket="bess-files",
            artifact_csv_key="csv",
            artifact_json_key="json",
        )

        self.assertEqual(updated_count, 0)
        self.assertIsNone(engine.connection.params)


class _FakeEngine:
    def __init__(self, rowcount):
        self.connection = _FakeConnection(rowcount)

    def begin(self):
        return self.connection


class _FakeConnection:
    def __init__(self, rowcount):
        self.params = None
        self.rowcount = rowcount

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        return False

    def execute(self, _statement, params):
        self.params = params
        return _FakeResult(self.rowcount)


class _FakeResult:
    def __init__(self, rowcount):
        self.rowcount = rowcount


if __name__ == "__main__":
    unittest.main()
