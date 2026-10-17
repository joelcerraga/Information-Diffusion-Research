# Public data and provenance

The project uses no API key, subscription, paid FTP, paid terminal or trading account.

| Source | Role | Snapshot |
| --- | --- | --- |
| Federal Reserve Bank of San Francisco USMPD workbook | Release times, rate surprises and published stock/futures window returns | Downloaded 16 October 2026; workbook update 17 September 2026 |
| HistData Generic ASCII M1 annual archives | SPXUSD, NSXUSD and EURUSD bid OHLC quotes | 27 annual ZIPs, 2017–2025, downloaded 16 October 2026 |
| Dukascopy public compressed minute files | Initial acquisition experiment and selected clock comparisons | Exact cached files and retrieval records retained |

USMPD: https://www.frbsf.org/wp-content/uploads/USMPD.xlsx

HistData format: https://www.histdata.com/f-a-q/data-files-detailed-specification/

Dukascopy: https://www.dukascopy.com/swiss/english/marketwatch/historical/

Raw prices are provider quotes. SPXUSD and NSXUSD are index-linked series and are not consolidated exchange trades or the SPY/QQQ ETFs. The M1 HistData record is bid-only; its volume field is discarded. No inference about executable spreads or meaningful market volume is made.

## Clock rule

The documented fixed-EST convention fails independent quote probes. A02 applies source timestamp +5 hours in European winter and +4 hours in European summer. The implementation uses `Europe/London` only to obtain the seasonal offset and then adds five hours; it does not assert that the recorded stamps are London local time. Events themselves are localised in `America/New_York` using their USMPD release times.

This deterministic rule is applied to every source quote and control date. There is no per-event offset tuning. The original documented-clock panel and results remain in `archive/documented-clock-run/`. The later sample has already been indirectly exposed through the first run, so corrected transfer is post-audit.

## Acquisition and cache

Each manifest retains URL, path, byte count, SHA-256, retrieval time and observed errors where applicable. `raw-manifest.json` covers every cached raw file. Existing source files are reused; rerunning acquisition is not an instruction to overwrite the recorded snapshot.

With the retained event register and protocol files:

```bash
python scripts/acquire_histdata.py --phase development
python scripts/acquire_histdata.py --phase validation
python scripts/acquire_histdata.py --phase holdout
```

These commands request the ordinary free download page and submit its download form. They do not use the provider's paid download services. `holdout` is an internal historical phase name; its current interpretation is later-period post-audit transfer. The public site may change its form or file content. If a freshly downloaded file differs, preserve both versions and treat the change as a new data snapshot.

`diffusion.data.initialise()` downloads USMPD and builds the initial register. Do not run it over this frozen research record merely to refresh a source; use a separate copy and compare changes first. The bundled processed register is the authoritative snapshot for reproduction.

The raw-cache ZIP extracts to `data/raw/...` when opened inside the project directory. Cached notebook review and full estimation from processed bars work without this ZIP. Exact raw reprocessing additionally requires it and verifies every file hash before parsing.

## Selection rules

Require positive, valid OHLC bars for all offsets −61 through +25. An event–asset pair is excluded if any required minute is missing or invalid. No forward filling, interpolation or substitution from another asset is performed. Audit rows preserve every planned event and control outcome.

Controls use the first available date 7, 14, 21 or 28 days before the release, at the same local time and weekday, excluding USMPD communication dates. Fallback depends on availability, not returns. Controls are observational and may contain other news.

`outputs/tables/missingness-surprise.csv` compares surprise magnitudes across coverage statuses descriptively. It does not establish that missing observations are random. The 2023 gaps remain a material limitation.
