import unittest

from app.settings import load_settings


class AppSettingsTest(unittest.TestCase):
    def test_loads_from_environment(self):
        settings = load_settings(
            environ={
                "DATABASE_URL": "postgresql://local/db",
                "AUTH_EMAIL_FROM": "no-reply@example.com",
            },
            secrets={},
        )

        self.assertEqual(settings.database.url, "postgresql://local/db")
        self.assertEqual(settings.auth.email_from, "no-reply@example.com")

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
                "auth": {
                    "email_from": "no-reply@example.com",
                },
            },
        )

        self.assertEqual(settings.database.url, "postgresql://secret/db")
        self.assertEqual(settings.auth.email_from, "no-reply@example.com")

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
