# Knowledge Ops Next Steps

This is the practical rollout plan for turning the current repo and `X:\LUMA` into a reusable operating model.

## Phase 1

1. Stand up the Notion structure described in [notion-template.md](C:/Code/salinas-and-jobos-invoice-calculator/docs/notion-template.md).
2. Use `Salinas and Jobos` as the first canonical project record.
3. Run the minimal local indexer described in [local-indexer-spec.md](C:/Code/salinas-and-jobos-invoice-calculator/docs/local-indexer-spec.md).
4. Index the four target folders:
   - `X:\LUMA\Salinas and Jobos Invoicing\PPOA`
   - `X:\LUMA\Salinas and Jobos Invoicing\BESS`
   - `X:\LUMA\Contracts\jobos_solar`
   - `X:\LUMA\Contracts\jobos_bess`

## Phase 2

1. Register the key documents in Notion.
2. Add implementation map rows that connect source rules to code in:
   - [main.py](C:/Code/salinas-and-jobos-invoice-calculator/main.py)
   - [calculations.py](C:/Code/salinas-and-jobos-invoice-calculator/calculations.py)
   - [data_reader.py](C:/Code/salinas-and-jobos-invoice-calculator/data_reader.py)
   - [report.py](C:/Code/salinas-and-jobos-invoice-calculator/report.py)
3. Compare repo behavior to the PPOA and BESS calculation docs.

## Phase 3

After the local indexer proves useful, decide whether to:

- keep it as a script plus structured outputs
- wrap it in a local-files MCP server
- sync selected summaries back into Notion automatically

## Team Rule of Thumb

- Drive holds the raw evidence.
- Notion holds the human-readable truth.
- Git holds the executable truth.
