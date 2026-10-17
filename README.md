# Information Diffusion in Financial Markets

**Joel Cerraga · Quantitative research · Free public data**

How quickly do quoted prices respond to scheduled Federal Reserve communication? This project combines event-time regressions, a source-clock audit, synthetic validation and interactive 3D graphs to investigate that question.

[![Information Diffusion in Financial Markets](assets/thumbnails/information-diffusion-research.png)](https://joelcerraga.github.io/Information-Diffusion-Research/)

[Landing page](https://joelcerraga.github.io/Information-Diffusion-Research/) · [Interactive graphs](https://joelcerraga.github.io/Information-Diffusion-Research/explorers/) · [Final paper](paper/final/Information-Diffusion-Final-Paper.pdf) · [Eight notebooks](notebooks/)

## Research at a glance

| Component | Scope |
| --- | --- |
| Events | 63 scheduled FOMC statements and 65 meeting-minutes releases |
| Period | 2018–2025; development 2018–2022, validation 2023, later period 2024–2025 |
| Quotes | SPXUSD, NSXUSD and EURUSD provider bid quotes, at one-minute resolution |
| Accepted sample | 336 of 384 planned event–asset pairs |
| Methods | Frozen principal-component rate factor, horizon regressions, HC3 intervals, wild-bootstrap bands, lead–lag diagnostics and conditional adjustment fits |
| Validation | Six synthetic mechanisms, 4,800 scenario fits, 21 analytical checks |
| Deliverables | 46-page A4 paper, eight recorded notebooks, three public interactive explorers |

SPX and NSX denote provider index-linked quotes, not consolidated exchange trades. Earnings announcements are a proposed extension, not part of the empirical sample.

## Main findings

- In 49 accepted pooled SPX statement windows, the 20-minute slope is **−29.46 bp per development surprise standard deviation**, with a pointwise 95% HC3 interval of **−40.31 to −18.61 bp**.
- Much of that estimated association appears early. The additional minute-5-to-minute-20 slope is **+0.44 bp**, with interval **−6.66 to +7.54 bp**. This does not establish complete information absorption by minute five.
- Meeting minutes show a more delayed exploratory association.
- A seasonal source-clock mismatch was identified and corrected. Corrected SPX statement-window returns correlate **0.9949** with published USMPD stock-index returns; this supports alignment without certifying every quote.
- **No primary empirical speed estimate passes every reporting condition.** Coverage failures, model shape, plateau and bootstrap diagnostics limit interpretation.
- Later-period prediction comparisons show **no convincing improvement over a development-mean baseline**. No profitable executable strategy is established.

The rate factor uses information through +20 minutes. Within-window estimates are retrospective associations, not announcement-time forecasts or structurally identified policy effects. The original later-period results were inspected before the clock correction: corrected 2024–2025 results are **post-audit chronological transfer**, not untouched validation. Primary SPX development and pooled statement coverage remain below the declared 80% threshold.

## Interactive graphs

| Explorer | What it shows |
| --- | --- |
| [Response surface](https://joelcerraga.github.io/Information-Diffusion-Research/explorers/response-surface/) | Fitted responses across horizon and rate surprise, with a simultaneous uncertainty band for the selected slice |
| [Lead–lag relationships](https://joelcerraga.github.io/Information-Diffusion-Research/explorers/lead-lag/) | Discrete correlation curves for directed asset pairs, with a two-dimensional companion |
| [Diffusion laboratory](https://joelcerraga.github.io/Information-Diffusion-Research/explorers/diffusion-laboratory/) | A controlled adjustment model with separate latent response and quote delay |

The public empirical explorers contain aggregate estimates. The private research companion retains individual event paths; full minute observations are not bundled in this public release. All public graphs work locally after downloading the repository. Plotly is bundled with its licence, and no analytics, API keys or external chart service is required.

## Run the public checks and synthetic example

Use Python 3.12. From the repository root:

```bash
python -m venv .venv
# Activate the virtual environment using your operating system's command.
python -m pip install -r requirements.txt
python scripts/reproduce_public.py
```

This verifies the recorded analytical freeze, runs the 21 analytical checks, validates the public website package and performs a fresh synthetic regression with a 1,999-draw simultaneous band. It needs no network or raw-market-data cache after dependencies are installed. Output goes to `outputs/public-reproduction/`.

To rebuild the website from the published aggregate tables:

```bash
python scripts/build_site.py
python scripts/verify_public_release.py
```

Open `index.html` locally, or serve the repository with `python -m http.server 8000` and visit `http://localhost:8000`. The supplied GitHub Pages workflow publishes the same static files without a frontend package install.

## Empirical reproduction and recorded notebooks

The eight notebooks retain their actual executed outputs from the completed research run. Their empirical cells require separately retained inputs. They are not represented as fully rerunnable from public files alone. See [the data instructions](data/README.md), [recorded acquisition protocol](data/REPRODUCTION-RECORD.md) and [release boundaries](DATA_AND_SOFTWARE_RIGHTS.md).

| Notebook | Milestone |
| --- | --- |
| [00](notebooks/00_research_question_and_design.ipynb) | Research question, design, information sets and scholarly foundations |
| [01](notebooks/01_public_data_and_clock_audit.ipynb) | Public-data acquisition, missingness and source-clock audit |
| [02](notebooks/02_synthetic_validation.ipynb) | Known mechanisms, uncertainty and simulation validation |
| [03](notebooks/03_event_response_estimation.ipynb) | Rate-surprise construction, event responses and activity |
| [04](notebooks/04_learning_lead_lag_analysis.ipynb) | Known-delay example and empirical lead–lag diagnostics |
| [05](notebooks/05_chronological_transfer_and_information_sets.ipynb) | Chronological prediction checks and information availability |
| [06](notebooks/06_robustness_and_research_reflections.ipynb) | Reporting gates, robustness, failures and mitigation |
| [07](notebooks/07_synthesis_and_publication_registers.ipynb) | Synthesis, notation and publication registers |

## Repository map

- `diffusion/`: frozen analytical Python modules.
- `scripts/`: acquisition, analysis, public reproduction and site building.
- `notebooks/`: eight recorded research notebooks.
- `outputs/tables/`: selected aggregate estimates, diagnostics and synthetic results.
- `protocol/`: original design, amendments and hashes.
- `paper/final/`: final PDF, editable XeLaTeX source, vector figures and compilation script.
- `references/`: Harvard bibliography and separate verification records.
- `assets/` and `explorers/`: website, thumbnails, static previews and interactive graphs.
- `docs/`: research reflections and publication instructions.

## Sources and interpretation

As MacKinlay (1997) explains in *Event studies in economics and finance*, event-time analysis provides a framework for examining price changes around information releases. As Hasbrouck (2007) explains in *Empirical market microstructure*, the observation process matters for interpreting those changes. This project makes timestamp alignment and quote provenance explicit before fitting an adjustment model.

The [Harvard reference list](references/harvard-references.txt) contains the full bibliography. Source-verification notes are stored separately. Data acquisition uses the Federal Reserve Bank of San Francisco USMPD workbook, HistData's free annual archives and selected Dukascopy comparisons.

## Publication record

The public package was prepared in October 2026 from the completed analysis and the supplied final PDF. The PDF's cover displays September 2025; that cover date does not describe the data-retrieval or repository-release date. Exact research chronology is recorded in `protocol/` and the source manifests. The PDF bytes in this release match the final supplied version.

Original code, research and design are credited to Joel Cerraga. No blanket open-source licence is assigned. Third-party licences remain in `vendor/`. See [data and software rights](DATA_AND_SOFTWARE_RIGHTS.md).
