import unittest

from app.settings import load_settings


class AppSettingsTest(unittest.TestCase):
    def test_loads_from_environment(self):
        settings = load_settings(
            environ={
                "DATABASE_URL": "postgresql://local/db",
                "S3_ENDPOINT_URL": "http://localhost:9001",
                "S3_ACCESS_KEY_ID": "access",
                "S3_SECRET_ACCESS_KEY": "secret",
                "S3_BUCKET": "bess-files",
                "S3_FORCE_PATH_STYLE": "true",
                "AUTH_ALLOWED_USERS": "USER@example.com, second@example.com",
                "SMTP_PORT": "2525",
                "SMTP_USE_TLS": "false",
            },
            secrets={},
        )

        self.assertEqual(settings.database.url, "postgresql://local/db")
        self.assertEqual(settings.object_storage.endpoint_url, "http://localhost:9001")
        self.assertTrue(settings.object_storage.force_path_style)
        self.assertEqual(
            settings.auth.allowed_users,
            ("user@example.com", "second@example.com"),
        )
        self.assertEqual(settings.auth.smtp_port, 2525)
        self.assertFalse(settings.auth.smtp_use_tls)

    def test_environment_overrides_streamlit_secrets(self):
        settings = load_settings(
            environ={"DATABASE_URL": "postgresql://env/db"},
            secrets={"DATABASE_URL": "postgresql://secret/db"},
        )

        self.assertEqual(settings.database.url, "postgresql://env/db")

    def test_loads_from_nested_streamlit_secrets(self):
        settings = load_settings(
            environ={},
            secrets={
                "database": {"url": "postgresql://secret/db"},
                "s3": {
                    "endpoint_url": "https://s3.example.test",
                    "bucket": "hosted-bucket",
                    "force_path_style": False,
                },
                "auth": {
                    "allowed_users": ["one@example.com", "Two@Example.com"],
                },
                "smtp": {
                    "host": "smtp.example.test",
                    "port": 587, 
                    "use_tls": True,
                },
            },
        )

        self.assertEqual(settings.database.url, "postgresql://secret/db")
        self.assertEqual(settings.object_storage.endpoint_url, "https://s3.example.test")
        self.assertEqual(settings.object_storage.bucket, "hosted-bucket")
        self.assertFalse(settings.object_storage.force_path_style)
        self.assertEqual(settings.auth.allowed_users, ("one@example.com", "two@example.com"))
        self.assertEqual(settings.auth.smtp_host, "smtp.example.test")

    def test_rejects_invalid_boolean(self):
        with self.assertRaises(ValueError):
            load_settings(environ={"SMTP_USE_TLS": "maybe"}, secrets={})

    def test_ignores_unavailable_streamlit_secrets_when_env_is_present(self):
        class UnavailableSecrets:
            def __contains__(self, key):
                raise RuntimeError("secrets unavailable")

        settings = load_settings(
            environ={"DATABASE_URL": "postgresql://env/db"},
            secrets=UnavailableSecrets(),
        )

        self.assertEqual(settings.database.url, "postgresql://env/db")


if __name__ == "__main__":
    unittest.main()
