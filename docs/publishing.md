# GitHub and GitHub Pages

Target repository: `ADEPT-ORG/FastRoverVLA`. Static site source: `docs/site/`.
The page has no build dependencies, analytics, external fonts or API keys.

After authenticating GitHub CLI as `chang2tz`, run from the repository root:

```bash
gh auth status
gh repo create ADEPT-ORG/FastRoverVLA --public --source . --remote origin --push
gh api --method POST repos/ADEPT-ORG/FastRoverVLA/pages -f build_type=workflow
gh workflow run pages.yml --repo ADEPT-ORG/FastRoverVLA
gh run list --repo ADEPT-ORG/FastRoverVLA --limit 5
```

If the repository already exists, inspect it before adding a remote or pushing. Never
force-push over existing work. If Pages already exists, use the repository's Pages
settings to select **GitHub Actions** rather than repeating the creation request.

The configured workflow publishes `docs/site` to
`https://adept-org.github.io/FastRoverVLA/`. It includes the permissions and deployment
environment described in the [official GitHub Pages documentation](https://docs.github.com/en/pages/getting-started-with-github-pages/using-custom-workflows-with-github-pages).

Preview locally:

```bash
python -m http.server 8765 --directory docs/site
```

Open `http://localhost:8765/` in a browser. The interactive numerical explorer uses
local JSON fetches, so opening `index.html` directly with `file://` is insufficient.

No arXiv identifier or venue acceptance is asserted. Add a paper link once its public
URL is available; update `CITATION.cff` and the citation block at the same time.
