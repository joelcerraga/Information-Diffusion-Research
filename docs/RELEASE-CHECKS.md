# Public release verification

Checks performed on the prepared package:

- 21 analytical tests passed, including HC3 verification, frozen PCA behaviour, timestamp conversion, invalid/missing quote handling and synthetic recovery.
- A fresh 80-event synthetic regression and 1,999-draw wild bootstrap completed.
- All 16 files in the corrected analytical freeze matched their recorded hashes.
- Five website pages passed 99 local-link checks, canonical URL checks and social-image metadata checks.
- Both distinct thumbnail files match their declared image dimensions.
- Eight recorded notebooks contain no error outputs.
- 47 interactive-script checks passed, covering fitted values, sign-correct uncertainty bands, missing-sample recovery, asset/event/sample selection, lag curves, zero-response interpretation, quote delay and CSV controls.
- JavaScript syntax checks passed.
- Full raw and processed market-data snapshots and full event-path arrays are excluded from the release.
- The final paper matches the supplied final PDF byte for byte: `379d4064bc53f3ff0cb2a3b5197c1a8bfaa7555bc48b53fd368afb253d64fd74`.

GitHub publication completed on 17 October 2026. The research-check workflow and GitHub Pages deployment both succeeded for commit `f27db85838e5331168a36d56aeae0d4d0a1c5364`. All 243 uploaded file blobs matched the prepared package. The live landing page, graph gallery, three explorer pages, final PDF and both social thumbnails returned HTTP 200. The live PDF's SHA-256 matches the recorded final paper.

The interactive-script checks exercise chart data and control transitions in a DOM/Plotly harness; they do not certify browser rendering or WebGL support. A final visual browser check was unavailable after the secure GitHub sign-in session became inaccessible. Published files, graph logic and live HTTP delivery were verified separately.
