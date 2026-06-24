# User Request And Plan

> Can you add htis new working structure into some documentation that's checked by your personality prompt?

## Plan

Document the agreed working structure in the persistent project docs:

- `project` is the facility.
- `dataset_config` is the dataset/scenario/input version.
- Input rows belong to `dataset_config`.
- Run snapshots belong to `dataset_config`.
- Output file metadata belongs to `file_object` and links back to the dataset/run.

This is documentation-only. No runtime code or schema changes are needed.

## Verification Plan

- Review the updated Markdown for clarity and consistency.

---

# Feature Changes

- Documented the working hierarchy for facility, dataset/scenario, input rows, run snapshots, and output file metadata.
- Clarified that run snapshots belong to `dataset_config`.
- Clarified that run snapshots are not separate datasets.

---

# Files Changed

- `.codex/docs/features/dataset-scenarios.md`
  - Added the `project -> dataset_config -> input rows / run snapshots -> output file metadata` structure.
  - Added a run-history model section explaining how `monthly_snapshot` and `file_object` relate to `dataset_config`.

- `.codex/docs/features/database-backed-streamlit-runtime.md`
  - Added the rule that run snapshots are children of `dataset_config` and not standalone datasets.

---

# Summary And Concerns

The persistent feature docs now capture the design decision that a run snapshot is a record of calculating a specific dataset/scenario at a specific time. This should help future implementation work avoid treating runs as datasets or building dashboard queries at the wrong level.

Concern:

- This is documentation-only. The Streamlit run button still needs to be wired to persist `monthly_snapshot` and `file_object` rows during a successful calculation.
