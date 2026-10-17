# Data and empirical reproduction

The public release contains code, aggregate results and research records. It does not contain full provider quote snapshots, the processed minute panels, the USMPD workbook, or individual event-path arrays.

## Public workflow

`python scripts/reproduce_public.py` verifies the analytical freeze, runs 21 numerical/data-parser checks and performs a fresh synthetic example using public files only. No API key or paid service is required.

## Exact empirical replay

The original study retains a separate private research package and raw cache. Exact replay requires those original inputs, including the processed event register and minute panels. Restore the private package into a separate working directory, retain its directory structure, and run its original `scripts/reproduce.py`. The raw-cache reconstruction option additionally checks every input against `raw-manifest.json`.

The original analytical entry points are retained in this repository for inspection. Running them here without the missing input snapshots is expected to fail; the public README does not promise otherwise.

## A new acquisition

The source URLs and acquisition code are available in [the recorded protocol](REPRODUCTION-RECORD.md), `diffusion/data.py`, `diffusion/histdata.py` and `scripts/acquire_histdata.py`. Download sources into a new working copy and construct its event register before processing annual quotes. Source files can change. Compare hashes and treat differing files as a new dataset rather than silently overwriting the recorded study.

Sources:

- USMPD: https://www.frbsf.org/research-and-insights/data-and-indicators/us-monetary-policy-event-study-database/
- HistData: https://www.histdata.com/f-a-q/data-files-detailed-specification/
- Dukascopy: https://www.dukascopy.com/swiss/english/marketwatch/historical/

The public graph gallery replaces the full minute-path view with aggregate lead–lag diagnostics. The private companion and its event paths remain part of the retained research package.
