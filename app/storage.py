import hashlib
import io

import boto3
import streamlit as st
from botocore.config import Config


RUN_HISTORY_PREFIX = "run_history"


@st.cache_resource
def get_storage_client(
    endpoint_url,
    access_key_id,
    secret_access_key,
    region,
    force_path_style,
):
    return boto3.client(
        "s3",
        endpoint_url=endpoint_url,
        aws_access_key_id=access_key_id,
        aws_secret_access_key=secret_access_key,
        region_name=region,
        config=Config(s3={"addressing_style": "path" if force_path_style else "auto"}),
    )


def get_storage_client_from_settings(settings):
    s = settings.object_storage
    if not s.endpoint_url or not s.access_key_id or not s.secret_access_key:
        raise ValueError(
            "Object storage is not configured. "
            "Set S3_ENDPOINT_URL, S3_ACCESS_KEY_ID, and S3_SECRET_ACCESS_KEY."
        )
    return get_storage_client(
        endpoint_url=s.endpoint_url,
        access_key_id=s.access_key_id,
        secret_access_key=s.secret_access_key,
        region=s.region,
        force_path_style=s.force_path_style,
    )


def ensure_bucket_exists(client, bucket):
    try:
        client.head_bucket(Bucket=bucket)
    except client.exceptions.ClientError:
        client.create_bucket(Bucket=bucket)


def build_run_artifact_key(project_id, dataset_name, snapshot_month, snapshot_name, extension):
    month_prefix = snapshot_month[:7] if snapshot_month else "unknown"
    return f"{RUN_HISTORY_PREFIX}/{project_id}/{dataset_name}/{month_prefix}/{snapshot_name}.{extension}"


def upload_bytes(client, bucket, key, data, content_type="application/octet-stream"):
    if isinstance(data, str):
        data = data.encode("utf-8")

    checksum = hashlib.sha256(data).hexdigest()
    size_bytes = len(data)

    client.put_object(
        Bucket=bucket,
        Key=key,
        Body=io.BytesIO(data),
        ContentType=content_type,
    )

    return {
        "storage_bucket": bucket,
        "storage_key": key,
        "checksum_sha256": checksum,
        "size_bytes": size_bytes,
    }


def get_presigned_download_url(client, bucket, key, expiry_seconds=3600):
    return client.generate_presigned_url(
        "get_object",
        Params={"Bucket": bucket, "Key": key},
        ExpiresIn=expiry_seconds,
    )
