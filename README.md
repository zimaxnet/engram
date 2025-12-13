# Engram Wiki

This branch is documentation-only. All application code, infra, and tests have been removed to keep the repository focused on the published wiki.

- Live wiki: https://wiki.engram.work  
- Source: `docs/` (Jekyll-compatible structure with Markdown and images in `docs/assets/images/`)

## Editing
- Update Markdown pages under `docs/`.
- Place new images in `docs/assets/images/` and reference them with site-relative paths (e.g., `/assets/images/example.png`).

## Local preview (optional)
If you want to preview locally with Jekyll:
```bash
gem install bundler jekyll   # if not already installed
jekyll serve --source docs --livereload
```
Then open http://localhost:4000.

## Key pages
- `docs/index.md` — overview
- `docs/architecture.md` — Brain + Spine and context schema
- `docs/system-navigator.md` — Navigator UI (Chat, Memory, Workflows, Admin)
- `docs/connectors-plan.md` — ingestion/connectors
- `docs/app-insights-guide.md` — telemetry
- `docs/TESTING-GUIDE.md` — Golden Thread validation and test checklist

## License
MIT
