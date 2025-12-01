Product Type Hardcoded Findings
================================

Generated: 2025-12-01
Scope: repo-wide search for hardcoded product-type strings and related phase names

Summary
-------
I scanned the repository for common product-type strings (tablet, capsule, ointment), tablet variants, packing phases (blister_packing, bulk_packing), and coating/bulk indicators. There are many remaining hardcoded occurrences; below are the high-impact files and recommended changes.

High-impact files (recommend addressing first)
--------------------------------------------
- `workflow/services.py` (Large)
  - Contains complex runtime logic that inspects `product_type` strings, checks `tablet_type`, and decides whether to include `coating`, `blister_packing` or `bulk_packing` phases.
  - Examples: `if product_type == 'tablet':`, `if 'tablet' in product_type:`, uses `PHASE_NAMES[...]` and `is_tablet/is_capsule` helpers.
  - Recommendation: Replace direct string checks with helper functions that consult `ProductTypeConfiguration` and `behavior_tags` (e.g., `product_has_tag(bmr.product, 'tablet-like')`, `product_requires('coating')`, `get_packing_phase_for(product)`).
  - Effort: Large (critical, must be carefully tested); start here.

- `workflow/management/commands/setup_phases.py` and `setup_workflow_templates.py` (Medium)
  - These create phase templates and hardcode templates for `ointment`, `tablet_normal`, `tablet_2`, `capsule`.
  - Recommendation: Convert templates to use registered `ProductTypeConfiguration` keys and template lookup by product-type key, or add a thin mapping layer that reads DB config when running the command.
  - Effort: Medium.

- `dashboards/analytics.py` and `dashboards/views.py` (Medium)
  - Some analytics code was updated earlier, but there are still references in views and template rendering that expect fixed buckets.
  - Recommendation: Ensure both server-side aggregation and Chart.js data are driven from `ProductTypeConfiguration` list; add an API endpoint for client JS to fetch metadata if templates can't fully cover dynamic needs.
  - Effort: Medium.

- `workflow/test_rollbacks.py` (Small → Medium)
  - Tests create `Product` fixtures with `product_type='tablet'|'capsule'|'ointment'`. Tests also assert rollbacks to phase names like `blending` or `mixing`.
  - Recommendation: Update tests to either seed `ProductTypeConfiguration` objects (via fixtures or `setUp`) and use helper APIs, or use helper functions to derive expected phases.
  - Effort: Small to Medium (tests must be updated alongside logic changes).

- Templates & JS (templates/*, static/js/*) (Small → Medium)
  - Examples: `templates/dashboards/admin_dashboard.html` was updated earlier, but other templates such as `templates/quarantine/dashboard.html` and client JS may still reference fixed product-type labels.
  - Recommendation: Replace hardcoded arrays/labels with context-driven data (pass `product_distribution` or fetch via API). For smaller templates, use template tags that render product-type options dynamically.
  - Effort: Small to Medium.

- `workflow/management/commands/apply_workflow_templates.py` and `apply_workflow_templates` docstrings (Small)
  - Help texts mention "ointment, tablet, capsule".
  - Recommendation: Update help text to be generic or to enumerate DB-seeded types at runtime.
  - Effort: Small.

Other occurrences and docs (Low)
-------------------------------
- Documentation files: `OPERATOR_ROLES.md`, `README.md`, `KPI_OPERATIONS_SYSTEM_USER_TRAINING_MANUAL.md` contain textual references and may not need code changes—update docs separately.
- Misc. management commands referencing phase names or product types.

Suggested implementation plan
-----------------------------
1. Add runtime helpers
   - Add `workflow/utils.py` (or expand `workflow/constants.py`) with functions:
     - `get_product_type_configs()` -> list of `ProductTypeConfiguration`
     - `product_has_tag(product, tag)`
     - `product_requires_phase(product, phase_name)`
     - `get_packing_phase_for(product)`
   - Small, well-documented module with unit tests.
   - Effort: Small.

2. Update `workflow/services.py` (critical)
   - Replace all direct `product_type`/string logic with helper functions above.
   - Preserve current behavior for backward compatibility if `ProductTypeConfiguration` table is empty.
   - Add comprehensive unit tests mirroring current `test_rollbacks.py` expectations.
   - Effort: Large.

3. Update management commands/templates
   - Make `setup_phases.py` and `apply_workflow_templates.py` call helpers or read DB config when applying templates.
   - Effort: Medium.

4. Update dashboards and analytics
   - Ensure server-side aggregations use `ProductTypeConfiguration` and pass dynamic labels/data to templates/JS or expose via API.
   - Effort: Medium.

5. Update tests and CI
   - Seed `ProductTypeConfiguration` in test `setUp` or use fixtures. Replace hardcoded product_type values with product creation helpers that reference seeded configs.
   - Run `manage.py test` and iterate.
   - Effort: Small–Medium.

6. Migrations & Backfill
   - If `behavior_tags` JSONField not yet present, add migration and backfill seeded entries (`tablet`, `capsule`, `ointment`) with appropriate tags.
   - Effort: Small.

Effort estimate (rough)
-----------------------
- Helpers + unit tests: 1–2 days
- `workflow/services.py` refactor + tests: 2–3 days (high risk; requires careful testing)
- Management commands & templates update: 1 day
- Dashboards/analytics + API endpoint: 1–2 days
- Tests, QA, PR prep: 1 day

Next step options
-----------------
- I can create the feature branch `feature/dynamic-product-types` and start by adding the helper module and unit tests (recommended).
- Or I can produce a detailed per-file patch plan (diffs) for you to review before coding.

What I will do next if you confirm: create the branch and implement the helper utilities, then update `workflow/services.py` in a follow-up change (with tests). If you prefer a different order, tell me.
