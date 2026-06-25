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

### Files to change

| File | Change |
|---|---|
| `requirements.txt` | Add `boto3` |
| `app/settings.py` | Add `ObjectStorageSettings`, wire `S3_*` env vars |
| `app/storage.py` | New — cached client, ensure_bucket_exists, upload_bytes, build key, presigned URL |
| `app/streamlit_app.py` | Upload CSV after calculation, pass `csv_artifact` to `record_calculation_run` |
| `app/components/run_dashboard.py` | Use presigned URL link button when `csv_artifact` is set; keep download_button fallback |
| `.env.docker.example` | Add `S3_*` vars (already in `.env.docker`, missing from example) |

---

## Changes

*(populated after implementation)*

---

## Feature Summary

*(populated after implementation)*

---

## File Summary

*(populated after implementation)*

---

## Final Summary & Concerns

*(populated after implementation)*
