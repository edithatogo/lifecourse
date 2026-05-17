# Starlight Migration Plan

## Phase 1: Scaffold [checkpoint: 084c58]

- [x] Create `docs/astro-site/package.json` with Starlight, polyglot, versions,
      links-validator, llms-txt, and sitemap dependencies.
- [x] Create `docs/astro-site/astro.config.mjs` with Starlight integration,
      sidebar configuration, and polyglot API reference generation.
- [x] Create `docs/astro-site/tsconfig.json` for Astro TypeScript configuration.
- [x] Create `docs/astro-site/public/.nojekyll` for GitHub Pages compatibility.
- [x] Create landing page at `docs/astro-site/src/content/docs/index.mdx`.
- [x] Create getting-started page at
      `docs/astro-site/src/content/docs/getting-started.mdx`.
- [x] Create `.github/workflows/docs.yml` for GitHub Pages deployment on main
      branch pushes.
- [x] Update `conductor/tech-stack.md` with Starlight documentation section.
- [x] Update `conductor/tracks/documentation_stack_readiness_20260428/plan.md`
      with completion marker.
- [x] Create this migration track with metadata.json, spec.md (fulfills
      REQ-MIG-004), and plan.md.

## Phase 2: Content Migration [checkpoint: TBD]

- [ ] Migrate `docs/design.md` → `src/content/docs/design.mdx`.
- [ ] Migrate `docs/requirements.md` → `src/content/docs/requirements.mdx`.
- [ ] Migrate `docs/architecture_status.md` → `src/content/docs/architecture.mdx`.
- [ ] Migrate `docs/simulation_engine_status.md` → `src/content/docs/simulation-engine.mdx`.
- [ ] Migrate `docs/stack_strategy.md` → `src/content/docs/stack-strategy.mdx`.
- [ ] Add remaining documentation pages for scientific-model, bindings, etc.
- [ ] Ensure all internal cross-references use Starlight slug paths.
- [ ] Run `pnpm build` and fix any link validation errors.

## Phase 3: CI/CD Verification [checkpoint: TBD]

- [ ] Verify `docs.yml` workflow runs successfully on push to a test branch.
- [ ] Verify GitHub Pages deployment renders correctly.
- [ ] Verify API reference pages are generated from `src/lifecourse`.
- [ ] Verify link validation catches broken links during build.
- [ ] Add documentation status badge to README.

## Phase 4: Content Freeze And Switchover [checkpoint: TBD]

- [ ] Add redirect or notice in `docs/` root markdown files pointing to the
      generated site.
- [ ] Update `README.md` to link to the Starlight site as primary documentation.
- [ ] Update `CONTRIBUTING.md` with instructions for editing docs via Starlight.
- [ ] Deprecate flat markdown docs as authoring source of truth.
