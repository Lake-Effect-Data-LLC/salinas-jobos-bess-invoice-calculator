import os
from dataclasses import dataclass


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
    allowed_users: tuple[str, ...]
    smtp_host: str | None
    smtp_port: int
    smtp_username: str | None
    smtp_password: str | None
    smtp_use_tls: bool


@dataclass(frozen=True)
class AppSettings:
    database: DatabaseSettings
    object_storage: ObjectStorageSettings
    auth: AuthSettings


SECRET_SECTIONS = {
    "DATABASE_URL": ("database", "url"),
    "S3_ENDPOINT_URL": ("s3", "endpoint_url"),
    "S3_ACCESS_KEY_ID": ("s3", "access_key_id"),
    "S3_SECRET_ACCESS_KEY": ("s3", "secret_access_key"),
    "S3_BUCKET": ("s3", "bucket"),
    "S3_REGION": ("s3", "region"),
    "S3_FORCE_PATH_STYLE": ("s3", "force_path_style"),
    "AUTH_EMAIL_FROM": ("auth", "email_from"),
    "AUTH_ALLOWED_USERS": ("auth", "allowed_users"),
    "SMTP_HOST": ("smtp", "host"),
    "SMTP_PORT": ("smtp", "port"),
    "SMTP_USERNAME": ("smtp", "username"),
    "SMTP_PASSWORD": ("smtp", "password"),
    "SMTP_USE_TLS": ("smtp", "use_tls"),
}


def load_settings(environ=None, secrets=None):
    env = os.environ if environ is None else environ
    streamlit_secrets = _load_streamlit_secrets() if secrets is None else secrets

    return AppSettings(
        database=DatabaseSettings(
            url=_get_setting("DATABASE_URL", env, streamlit_secrets),
        ),
        object_storage=ObjectStorageSettings(
            endpoint_url=_get_setting("S3_ENDPOINT_URL", env, streamlit_secrets),
            access_key_id=_get_setting("S3_ACCESS_KEY_ID", env, streamlit_secrets),
            secret_access_key=_get_setting("S3_SECRET_ACCESS_KEY", env, streamlit_secrets),
            bucket=_get_setting("S3_BUCKET", env, streamlit_secrets),
            region=_get_setting("S3_REGION", env, streamlit_secrets, default="us-east-1"),
            force_path_style=_get_bool_setting(
                "S3_FORCE_PATH_STYLE",
                env,
                streamlit_secrets,
                default=True,
            ),
        ),
        auth=AuthSettings(
            email_from=_get_setting("AUTH_EMAIL_FROM", env, streamlit_secrets),
            allowed_users=_get_list_setting("AUTH_ALLOWED_USERS", env, streamlit_secrets),
            smtp_host=_get_setting("SMTP_HOST", env, streamlit_secrets),
            smtp_port=_get_int_setting("SMTP_PORT", env, streamlit_secrets, default=587),
            smtp_username=_get_setting("SMTP_USERNAME", env, streamlit_secrets),
            smtp_password=_get_setting("SMTP_PASSWORD", env, streamlit_secrets),
            smtp_use_tls=_get_bool_setting("SMTP_USE_TLS", env, streamlit_secrets, default=True),
        ),
    )


def _get_setting(key, env, secrets, default=None):
    env_value = env.get(key)
    if env_value not in (None, ""):
        return env_value

    secret_value = _get_secret_value(key, secrets)
    if secret_value not in (None, ""):
        return secret_value

    return default


def _get_bool_setting(key, env, secrets, default=False):
    value = _get_setting(key, env, secrets)
    if value in (None, ""):
        return default
    if isinstance(value, bool):
        return value

    normalized = str(value).strip().lower()
    if normalized in {"1", "true", "yes", "y", "on"}:
        return True
    if normalized in {"0", "false", "no", "n", "off"}:
        return False

    raise ValueError(f"{key} must be a boolean value")


def _get_int_setting(key, env, secrets, default):
    value = _get_setting(key, env, secrets)
    if value in (None, ""):
        return default

    try:
        return int(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{key} must be an integer") from exc


def _get_list_setting(key, env, secrets):
    value = _get_setting(key, env, secrets)
    if value in (None, ""):
        return ()
    if isinstance(value, (list, tuple)):
        return tuple(str(item).strip().lower() for item in value if str(item).strip())

    return tuple(
        item.strip().lower()
        for item in str(value).split(",")
        if item.strip()
    )


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
