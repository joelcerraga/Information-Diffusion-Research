# Final paper

`Information-Diffusion-Final-Paper.pdf` is the supplied final 46-page A4 PDF. Its title-page date is September 2025. Data retrieval and final repository packaging took place in October 2026, as recorded elsewhere in the study.

The editable source is `main.tex`, with included TeX sections, generated tables, vector figures and code excerpts. To compile it without refitting the research models:

```bash
python paper/final/compile_paper.py
```

This requires a working XeLaTeX installation, the TeX packages imported in `main.tex`, Nimbus Sans (TeX Gyre/Nimbus font files), DejaVu Sans Mono and Latin Modern Math. The script performs four compilation passes and checks for typesetting warnings. It writes the PDF inside this directory. Rendering under a different TeX or font environment may change pagination; inspect the output before replacing the supplied PDF.

The repository verifier checks the supplied PDF's exact SHA-256. If a new paper version is deliberately approved, update that recorded hash as part of its release rather than bypassing the check.
