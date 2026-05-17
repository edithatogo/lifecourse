# Starlight Documentation Site — Migration Plan

## Phase 1: Create Full Documentation Content

- [ ] Task: Enhance `index.mdx` with project description, badges, quick links,
      card grid, and feature highlights.
- [ ] Task: Enhance `getting-started.mdx` with installation instructions, system
      requirements, quick start example, and next steps.
- [ ] Task: Create `usage.mdx` with detailed usage guide covering CLI, Python
      API, scenario configuration, sensitivity analysis, and plotting.
- [ ] Task: Create `api-reference.mdx` with an overview of the public API
      surface, including engine registry, data loading, analysis, and CLI.
- [ ] Task: Create `contributing.mdx` with contribution guidelines, development
      setup, testing, and documentation conventions.

## Phase 2: Configure Plugins

- [ ] Task: Update `astro.config.mjs` with all plugins:
      - `starlight-polyglot` with Python entry point `src/lifecourse`
      - `starlight-versions` for versioned docs
      - `starlight-links-validator` for link checking
      - `starlight-llms-txt` for LLM export
      - `sitemap` for SEO
- [ ] Task: Configure Starlight with proper title, social links, edit link, and
      complete sidebar.

## Phase 3: Conductor Track

- [ ] Task: Create `conductor/tracks/migrate_starlight/` with:
      - `metadata.json` — track metadata with status "in_progress"
      - `spec.md` — specification matching this plan
      - `plan.md` — this plan file

## Phase 4: Verification and Deployment

- [ ] Task: Update `.gitignore` with any new patterns.
- [ ] Task: Run `pnpm build` from `docs/astro-site/` and verify success.
- [ ] Task: Stage all files, commit with descriptive message, and push to
      remote.
- [ ] Task: Verify GitHub Actions workflow runs on push.
