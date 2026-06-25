# MinIO Run Artifact Upload

---

## Original Request

> "I need to integrate MinIO (S3-compatible object storage) into the application to store the generated outputs from our calculations.
> 1. Bucket Name: bess-files (single bucket, run_history/ prefix for organization)
> 2. Folder Structure: organized by project / scenario / month
> 3. Upload Logic: upload CSV output to MinIO after each calculation run
> 4. Retrieval Logic: presigned download URL wired to the run dashboard Download button"

---

## Plan

### Overview

MinIO is already provisioned in `docker-compose.yml` and `bess-files` is auto-created by `minio-init`. The `file_object` table, `create_csv_export_file_object`, and the `csv_artifact` parameter on `record_calculation_run` are already scaffolded but never populated. This task wires them up end-to-end.

### Folder structure inside `bess-files`

```
bess-files/
  run_history/
    {project_id}/
      {dataset_name}/
        {YYYY-MM}/
          {snapshot_name}.csv
```

Example:
```
run_history/salinas/actual/2025-06/calculation_run_20250625T143022000000Z.csv
```

### Files changed

| File | Change |
|---|---|
| `requirements.txt` | Add `boto3>=1.35,<2` |
| `app/settings.py` | Add `ObjectStorageSettings`, wire `S3_*` env vars |
| `app/storage.py` | New — cached client, `ensure_bucket_exists`, `upload_bytes`, `build_run_artifact_key`, `get_presigned_download_url` |
| `app/streamlit_app.py` | Upload CSV after calculation, pass `csv_artifact` and shared `snapshot_name` to `record_calculation_run` |
| `app/components/run_dashboard.py` | Use presigned URL `st.link_button` when `csv_artifact` is set; keep `st.download_button` fallback for old runs |
| `.env.docker.example` | Add `S3_*` vars |

---

## Feature Changes

### MinIO CSV artifact upload

After each successful calculation run, the generated CSV is uploaded to MinIO at:

```
run_history/{project_id}/{dataset_name}/{YYYY-MM}/{snapshot_name}.csv
```

A single `snapshot_name` is generated once and shared between the MinIO key and the `monthly_snapshot.snapshot_name` column, so they are always in sync. If MinIO upload fails for any reason (misconfiguration, network), the failure is silently swallowed and the run proceeds without a file artifact — the database snapshot and in-memory downloads continue to work.

### Presigned URL CSV downloads in Run History dashboard

The CSV download button in the Run History dashboard (Latest Run and Previous Runs) now uses a presigned MinIO URL (`st.link_button`) when a `csv_artifact` is linked to the run. Runs without a MinIO artifact (created before this change) fall back to `st.download_button` using the text stored in `snapshot_data`. The report download is unchanged — it still reads from `snapshot_data`.

### Object storage settings

`settings.py` now loads and exposes `ObjectStorageSettings` (`endpoint_url`, `access_key_id`, `secret_access_key`, `bucket`, `region`, `force_path_style`) from `S3_*` environment variables, with the same priority chain as `DATABASE_URL` (env → dotenv → Streamlit secrets).

---

## File Changes

### `requirements.txt`
- Added `boto3>=1.35,<2`

### `app/settings.py`
- Added `ObjectStorageSettings` dataclass
- Added `AppSettings.object_storage` field
- Added `S3_*` keys to `SECRET_SECTIONS`
- Added `_parse_bool` helper for `S3_FORCE_PATH_STYLE`
- Refactored `load_settings` to use an inner `get()` shorthand to reduce repetition

### `app/storage.py` (new)
- `get_storage_client(...)` — `@st.cache_resource` boto3 S3 client factory, one per process
- `get_storage_client_from_settings(settings)` — extracts settings and calls the cached factory
- `ensure_bucket_exists(client, bucket)` — creates the bucket if missing (safety net for non-Docker deployments)
- `build_run_artifact_key(project_id, dataset_name, snapshot_month, snapshot_name, extension)` — constructs the `run_history/...` key
- `upload_bytes(client, bucket, key, data, content_type)` — uploads bytes or string, returns `{storage_bucket, storage_key, checksum_sha256, size_bytes}`
- `get_presigned_download_url(client, bucket, key, expiry_seconds)` — generates a 1-hour presigned GET URL

### `app/streamlit_app.py`
- Added imports: `generate_calculation_snapshot_name`, `build_run_artifact_key`, `get_storage_client_from_settings`, `upload_bytes`
- `render_database_flow`: generates `snapshot_name` once and passes it to both `_upload_run_csv` and `record_calculation_run`; passes `settings` to `render_run_history_dashboard`
- Added `_upload_run_csv(settings, project_id, dataset_name, snapshot_month, snapshot_name, snapshot_data)` — uploads CSV to MinIO, returns `csv_artifact` dict or `None` on failure

### `app/components/run_dashboard.py`
- `render_run_history_dashboard`: accepts optional `settings` param; resolves storage client once and threads it through
- `_render_latest_run`, `_render_previous_runs`: accept and forward `storage_client`
- `_render_downloads`: checks for `csv_artifact`; uses `st.link_button` with presigned URL when available, otherwise falls back to `st.download_button`
- Added `_try_get_storage_client(settings)` — safe wrapper, returns `None` on any error
- Added `_presigned_csv_url(storage_client, csv_artifact)` — safe presigned URL generation, returns `None` on any error

### `.env.docker.example`
- Added `S3_ENDPOINT_URL`, `S3_ACCESS_KEY_ID`, `S3_SECRET_ACCESS_KEY`, `S3_BUCKET`, `S3_REGION`, `S3_FORCE_PATH_STYLE`

---

## Summary

MinIO is now wired into the calculation run flow. Every successful run uploads a CSV to `bess-files/run_history/...`, records a `file_object` row, and links it to the `monthly_snapshot`. The run dashboard uses presigned URLs for CSV downloads on MinIO-backed runs and silently falls back to the existing `snapshot_data` text for older runs. Storage failures are non-fatal — runs succeed even if MinIO is unreachable.

### Concerns / Known Gaps

- **Report text is not uploaded to MinIO** — only the CSV is. The report continues to live in `snapshot_data`. A follow-up could add a second `file_object` row for the report, but the schema only has one `source_file_object_id` per snapshot, so that would require either a new column or a separate lookup.
- **`ensure_bucket_exists` is never called at startup** — it exists in `storage.py` but is not wired into the app boot sequence. For Docker deployments this is fine (`minio-init` handles it). For other deployments it would need to be called explicitly.
- **Presigned URL expiry is 1 hour (hardcoded default)** — suitable for a small internal tool but not configurable via settings yet.
- **Silent MinIO failure on upload** — `_upload_run_csv` catches all exceptions and returns `None`. This is intentional to avoid blocking runs, but means storage failures are invisible unless logs are checked.
