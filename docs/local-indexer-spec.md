# Local Indexer Spec for `X:\LUMA`

This is a minimal spec for a local file indexing/search tool that supports LUMA invoicing projects.

The first version should be intentionally small:

- scan a fixed root such as `X:\LUMA`
- classify files by project and document type
- extract lightweight searchable text where possible
- output structured records that can later feed a search UI, MCP server, or Notion sync

## Purpose

The indexer exists to answer questions like:

- Which documents define the billing rules for a project?
- Which files are the primary calculation docs?
- Which sample inputs go with a given project?
- Where do we have related solar and BESS materials for the same facility?

## Scope for Version 1

### Supported File Types

- `.pdf`
- `.docx`
- `.pptx`
- `.csv`
- `.txt`
- `.md`

### Root

- fixed root: `X:\LUMA`

### Required Behaviors

1. Walk the directory tree from the root.
2. Capture file metadata.
3. Infer project and document type from the path and filename.
4. Extract searchable text when feasible.
5. Emit one structured record per file.

## Output Record

Each indexed file should produce a record with these fields:

| Field | Required | Notes |
| --- | --- | --- |
| `file_path` | Yes | Full local path |
| `project` | Yes | Example: `Salinas and Jobos` |
| `facility` | No | Example: `Salinas`, `Jobos` |
| `service_type` | No | Example: `PPOA`, `BESS` |
| `doc_type` | Yes | Classified type |
| `source_level` | Yes | `Legal`, `Operational`, `Implementation`, `Reference` |
| `modified_date` | Yes | ISO timestamp preferred |
| `extension` | Yes | File extension |
| `title` | Yes | Friendly display title |
| `searchable_text` | No | Extracted text or chunk text |
| `snippet` | No | Short preview text |
| `tags` | No | List of inferred tags |

### Example JSON

```json
{
  "file_path": "X:\\LUMA\\Salinas and Jobos Invoicing\\PPOA\\Salinas_Monthly_Payment_Calculation.pdf",
  "project": "Salinas and Jobos",
  "facility": "Salinas",
  "service_type": "PPOA",
  "doc_type": "calculation_doc",
  "source_level": "Operational",
  "modified_date": "2026-05-19T13:30:00",
  "extension": ".pdf",
  "title": "Salinas Monthly Payment Calculation",
  "searchable_text": "Monthly payment is calculated from NEO, ENEO, DNEO, contract rate...",
  "snippet": "Monthly payment is calculated from NEO, ENEO, DNEO...",
  "tags": ["salinas", "ppoa", "monthly payment"]
}
```

## Classification Rules

Keep the first pass simple and deterministic.

### Source Level

- path under `Contracts\` -> `Legal`
- path under `* Invoicing\` -> `Operational`
- path under repo or code workspace -> `Implementation`
- known cross-project data files -> `Reference`

### Service Type

- path contains `\PPOA\` -> `PPOA`
- path contains `\BESS\` -> `BESS`

### Document Type

Use filename and path heuristics:

- filename contains `required_data` -> `required_data`
- filename contains `performance_guarantee` -> `performance_guarantee`
- filename contains `monthly_payment_calculation` -> `calculation_doc`
- filename contains `compensation_calculation` -> `calculation_doc`
- filename contains `sample input` or path contains `Sample Input` -> `sample_input`
- path under `Contracts\` and filename contains `Amend` -> `amendment`
- path under `Contracts\` otherwise -> `contract`
- filename ends with `.csv` and sits at root or shared utility location -> `reference_data`
- filename ends with `.pptx` -> `presentation`

## Project Inference

Project should be inferred from the nearest project folder pattern where possible.

Examples:

- `X:\LUMA\Salinas and Jobos Invoicing\...` -> `Salinas and Jobos`
- `X:\LUMA\Ciro One Invoicing\...` -> `Ciro One`
- `X:\LUMA\Contracts\jobos_solar\...` -> `Salinas and Jobos`
- `X:\LUMA\Contracts\jobos_bess\...` -> `Salinas and Jobos`

Use an override mapping file so special cases can be maintained without code changes.

## Recommended Output Files

Version 1 can write:

- `index.jsonl`
- `index.csv`

Optional:

- `projects_summary.json`

## Search Behavior

Version 1 does not need semantic search.

It only needs:

- filename search
- path search
- keyword search over `searchable_text`
- filters for `project`, `service_type`, `doc_type`, `source_level`

## Suggested Implementation Approach

An engineer can build this in Python with:

- `pathlib` or `os.walk` for traversal
- `pandas` only if needed for CSV normalization
- `python-docx` for `.docx`
- `python-pptx` for `.pptx`
- `pypdf` for `.pdf`

If those libraries are not available yet, version 1 can still ship with metadata-only indexing and add text extraction later.

## Prototype Script

This repo includes a first-pass implementation at [luma_indexer.py](C:/Code/salinas-and-jobos-invoice-calculator/tools/luma_indexer.py).

PowerShell:

```powershell
python tools\luma_indexer.py --root "X:\LUMA"
```

Git Bash:

```bash
python tools/luma_indexer.py --root /x/LUMA
```

Target just the first Salinas and Jobos corpus:

```bash
python tools/luma_indexer.py \
  --root "/x/LUMA/Salinas and Jobos Invoicing/PPOA" \
  --root "/x/LUMA/Salinas and Jobos Invoicing/BESS" \
  --root "/x/LUMA/Contracts/jobos_solar" \
  --root "/x/LUMA/Contracts/jobos_bess"
```

By default, outputs are written to:

- `local/luma-index/index.jsonl`
- `local/luma-index/index.csv`
- `local/luma-index/projects_summary.json`

The `local/` folder is ignored by Git.

## Initial Target Corpus

The first project to index should be:

- `X:\LUMA\Salinas and Jobos Invoicing\PPOA`
- `X:\LUMA\Salinas and Jobos Invoicing\BESS`
- `X:\LUMA\Contracts\jobos_solar`
- `X:\LUMA\Contracts\jobos_bess`

That gives a full template project:

- operational calculation docs
- required data docs
- performance guarantee docs
- sample inputs
- legal amendments

## Exit Criteria for Version 1

Version 1 is good enough when we can:

1. list all key source documents for `Salinas and Jobos`
2. filter documents by `PPOA` vs `BESS`
3. identify legal vs operational docs
4. search for terms like `NEO`, `ENEO`, `shortfall`, `performance guarantee`
5. hand the resulting index to a human or later wrap it behind an MCP server
