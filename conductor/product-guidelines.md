# Product Guidelines

## Purpose
These guidelines define how `lifecourse` should communicate in documentation, generated outputs, contributor-facing material, and analytical summaries. The goal is to keep the project understandable to policy and research audiences while preserving methodological precision and practical clarity for contributors.

## Core Communication Principles
- Write in plain English first, then add technical detail where needed.
- Prefer evidence-led statements over promotional or speculative language.
- Make assumptions, limitations, and uncertainty visible instead of implied.
- Optimize for reproducibility and operational clarity, not rhetorical flourish.
- When a choice exists between sounding impressive and being precise, choose precision.

## Voice and Tone
- Use direct, neutral, professional language.
- Explain analytical purpose before implementation detail.
- Keep prose concise and readable, especially in README content, results summaries, and contributor documentation.
- Avoid exaggerated claims such as "proves", "guarantees", or "best-in-class" unless they are strictly defensible.
- Treat the project as research software and analytical infrastructure, not a consumer product.

## Writing Style
- Prefer short sentences and concrete nouns over abstract phrasing.
- Define acronyms on first use in a document unless the audience is clearly technical and domain-specific.
- Use consistent terminology for core concepts such as scenario, parameter, intervention, QALY, ICER, PSA, and budget impact.
- Distinguish clearly between observed behavior, configured assumptions, inferred interpretation, and future intent.
- When documenting workflows, make actions explicit: what to run, what inputs are used, and what outputs are expected.

## Evidence and Claims
- Tie important claims to one of the following whenever possible:
  - maintained code behavior
  - configuration values
  - tests
  - documented references or source notes
- If a statement depends on an assumption, label it as an assumption.
- If a result depends on jurisdiction-specific parameters, say so explicitly.
- If a behavior is historical, experimental, or archival, do not present it as current maintained behavior.
- Do not blur the boundary between model outputs and policy recommendations.

## Assumptions, Caveats, and Limitations
- State the scope of the model when presenting results.
- Call out major assumptions that materially influence interpretation.
- Acknowledge uncertainty, especially in scenario design, parameterization, and sensitivity outputs.
- Note when outputs are suitable for research comparison but not for clinical or operational deployment.
- If a metric can be misread without context, add the context.

## Contributor-Facing Clarity
- Documentation should tell contributors where behavior lives:
  - `src/lifecourse/` for implementation
  - `config/` for scenarios and configuration
  - `tests/` for executable expectations
  - `results/` for generated artifacts
- Prefer instructions that are actionable and sequence-aware.
- When describing a change, say what changed, why it changed, and how it should be validated.
- Keep ownership boundaries clear between maintained code, support scripts, documentation, and archived notebooks.
- Avoid contributor guidance that requires readers to infer hidden workflow rules.

## Documentation Conventions
- README and top-level docs should explain purpose, setup, execution paths, and expected outputs before deeper design details.
- Design and requirements docs should separate current behavior from aspirational or planned capabilities.
- Historical material should be clearly labeled as archival, draft, or exploratory.
- Document file and module names exactly as they exist in the maintained codebase.
- When naming commands, configs, or paths, use the literal identifiers used in the repository.

## Results and Output Presentation
- Summaries should report what was run, under which configuration, and what the key outputs mean.
- Present costs, QALYs, ICERs, and uncertainty outputs with units and enough context to interpret them correctly.
- Generated figures and tables should favor readability over decorative styling.
- Plot titles, labels, and legends should be explicit about the metric, scenario, and threshold where relevant.
- When comparing scenarios, clearly distinguish baseline, intervention, and incremental outputs.

## Naming and Terminology
- The maintained package name is `lifecourse`.
- Legacy references to `LifeCourseID` or similar names should be treated as historical unless intentionally preserved for context.
- Use consistent naming for modules, scenarios, and artifacts to reduce ambiguity between current code and archived material.
- Avoid introducing new synonyms for existing concepts unless there is a compelling reason.

## Review Standard
Before publishing documentation or analytical summaries, check:
- Is the wording plain enough for a research or policy reader to follow?
- Are important claims tied to evidence, implementation, or documented assumptions?
- Are caveats and limitations visible where they matter?
- Would a contributor know what file, config, or test to inspect next?
- Does the document describe current maintained behavior rather than accidental legacy behavior?

## Anti-Patterns
Avoid:
- marketing language
- vague claims without evidence
- unclear ownership between maintained code and archived experiments
- undocumented jumps from model outputs to policy conclusions
- instructions that omit validation steps
- imprecise reuse of terms like "result", "impact", or "validation" without context
