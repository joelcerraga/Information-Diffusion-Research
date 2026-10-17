# GitHub publication

Target repository: `joelcerraga/Information-Diffusion-Research`.

1. Create a public repository named `Information-Diffusion-Research` under `joelcerraga`. Initialise it with a README if the connected GitHub tools will upload the prepared package.
2. Upload the contents of this repository directory to its root; `index.html`, `assets/`, `explorers/`, `paper/` and `.github/` must be at that root. Do not upload the surrounding ZIP as the website.
3. In **Settings → Pages → Build and deployment**, choose **GitHub Actions**. The included Pages workflow validates and publishes the static site.
4. The landing page is `https://joelcerraga.github.io/Information-Diffusion-Research/`. The graph gallery is the same address followed by `explorers/`.
5. Check the successful Pages deployment, open the PDF and try each graph. The root page and graph gallery each contain their own Open Graph and Twitter image metadata.
6. In **Settings → General → Social preview**, the optional repository preview can use `assets/thumbnails/information-diffusion-research.png`.

For a manual Git upload from this directory, with GitHub authentication already configured:

```bash
git init -b main
git add .
git commit -m "Publish information diffusion research and interactive website"
git remote add origin https://github.com/joelcerraga/Information-Diffusion-Research.git
git push -u origin main
```

Use that sequence only for an empty remote. If GitHub created an initial README commit, clone the repository first, copy this package into the clone and commit normally. Do not force-push over an existing history.

If a social network cached an earlier preview, refresh it using that network's link-inspection tool after publication. Each page already points to its distinct thumbnail; no separate image upload to LinkedIn is needed for the link metadata.
