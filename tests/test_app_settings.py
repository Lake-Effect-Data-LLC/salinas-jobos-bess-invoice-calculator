import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

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

    def test_loads_from_local_dotenv_file(self):
        with TemporaryDirectory() as temp_dir:
            dotenv_path = Path(temp_dir) / ".env.docker"
            dotenv_path.write_text(
                "DATABASE_URL=postgresql+psycopg://local/db\n"
                "AUTH_EMAIL_FROM=no-reply@example.com\n",
                encoding="utf-8",
            )

            settings = load_settings(
                environ={},
                secrets={},
                dotenv_path=dotenv_path,
            )

        self.assertEqual(settings.database.url, "postgresql+psycopg://local/db")
        self.assertEqual(settings.auth.email_from, "no-reply@example.com")

    def test_environment_overrides_local_dotenv_file(self):
        with TemporaryDirectory() as temp_dir:
            dotenv_path = Path(temp_dir) / ".env.docker"
            dotenv_path.write_text(
                "DATABASE_URL=postgresql://dotenv/db\n",
                encoding="utf-8",
            )

            settings = load_settings(
                environ={"DATABASE_URL": "postgresql://env/db"},
                secrets={},
                dotenv_path=dotenv_path,
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
            dotenv_path=None,
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
