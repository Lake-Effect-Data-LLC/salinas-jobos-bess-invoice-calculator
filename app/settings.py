import os
from dataclasses import dataclass, field
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
LOCAL_ENV_FILE = ROOT_DIR / ".env.docker"


@dataclass(frozen=True)
class DatabaseSettings:
    url: str | None


@dataclass(frozen=True)
class ObjectStorageSettings:
    endpoint_url: str | None
    access_key_id: str | None
    secret_access_key: str | None
    bucket: str | None
    region: str
    force_path_style: bool


@dataclass(frozen=True)
class AuthSettings:
    email_from: str | None


@dataclass(frozen=True)
class AppSettings:
    database: DatabaseSettings
    object_storage: ObjectStorageSettings
    auth: AuthSettings


SECRET_SECTIONS = {
    "DATABASE_URL": ("database", "url"),
    "S3_ENDPOINT_URL": ("object_storage", "endpoint_url"),
    "S3_ACCESS_KEY_ID": ("object_storage", "access_key_id"),
    "S3_SECRET_ACCESS_KEY": ("object_storage", "secret_access_key"),
    "S3_BUCKET": ("object_storage", "bucket"),
    "S3_REGION": ("object_storage", "region"),
    "S3_FORCE_PATH_STYLE": ("object_storage", "force_path_style"),
    "AUTH_EMAIL_FROM": ("auth", "email_from"),
}


def load_settings(environ=None, secrets=None, dotenv_path=LOCAL_ENV_FILE):
    env = os.environ if environ is None else environ
    dotenv_values = _load_dotenv_values(dotenv_path)
    streamlit_secrets = _load_streamlit_secrets() if secrets is None else secrets

    def get(key, default=None):
        return _get_setting(key, env, dotenv_values, streamlit_secrets, default=default)

    return AppSettings(
        database=DatabaseSettings(
            url=get("DATABASE_URL"),
        ),
        object_storage=ObjectStorageSettings(
            endpoint_url=get("S3_ENDPOINT_URL"),
            access_key_id=get("S3_ACCESS_KEY_ID"),
            secret_access_key=get("S3_SECRET_ACCESS_KEY"),
            bucket=get("S3_BUCKET"),
            region=get("S3_REGION", default="us-east-1"),
            force_path_style=_parse_bool(get("S3_FORCE_PATH_STYLE", default="true")),
        ),
        auth=AuthSettings(
            email_from=get("AUTH_EMAIL_FROM"),
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


def _parse_bool(value):
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in {"true", "1", "yes"}
    return bool(value)
