import os
from dataclasses import dataclass
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
LOCAL_ENV_FILE = ROOT_DIR / ".env.docker"


@dataclass(frozen=True)
class DatabaseSettings:
    url: str | None


@dataclass(frozen=True)
class AuthSettings:
    email_from: str | None


@dataclass(frozen=True)
class AppSettings:
    database: DatabaseSettings
    auth: AuthSettings


SECRET_SECTIONS = {
    "DATABASE_URL": ("database", "url"),
    "AUTH_EMAIL_FROM": ("auth", "email_from"),
}


def load_settings(environ=None, secrets=None, dotenv_path=LOCAL_ENV_FILE):
    env = os.environ if environ is None else environ
    dotenv_values = _load_dotenv_values(dotenv_path)
    streamlit_secrets = _load_streamlit_secrets() if secrets is None else secrets

    return AppSettings(
        database=DatabaseSettings(
            url=_get_setting("DATABASE_URL", env, dotenv_values, streamlit_secrets),
        ),
        auth=AuthSettings(
            email_from=_get_setting(
                "AUTH_EMAIL_FROM",
                env,
                dotenv_values,
                streamlit_secrets,
            ),
        ),
    )


def _get_setting(key, env, dotenv_values, secrets, default=None):
    env_value = env.get(key)
    if env_value not in (None, ""):
        return env_value

    dotenv_value = dotenv_values.get(key)
    if dotenv_value not in (None, ""):
        return dotenv_value

    secret_value = _get_secret_value(key, secrets)
    if secret_value not in (None, ""):
        return secret_value

    return default


def _load_dotenv_values(dotenv_path):
    if not dotenv_path:
        return {}

    path = Path(dotenv_path)
    if not path.exists():
        return {}

    values = {}
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue

        key, value = line.split("=", 1)
        values[key.strip()] = value.strip().strip("\"'")

    return values


def _get_secret_value(key, secrets):
    if secrets is None:
        return None

    try:
        if key in secrets:
            return secrets[key]
    except Exception:
        return None

    section_name, section_key = SECRET_SECTIONS.get(key, (None, None))
    if not section_name:
        return None

    section = _mapping_get(secrets, section_name)
    if not section:
        return None

    return _mapping_get(section, section_key)


def _mapping_get(mapping, key):
    try:
        return mapping.get(key)
    except AttributeError:
        try:
            return mapping[key]
        except (KeyError, TypeError):
            return None


def _load_streamlit_secrets():
    try:
        import streamlit as st

        return st.secrets
    except Exception:
        return None
