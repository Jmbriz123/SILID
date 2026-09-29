# Python development and configuration

## What Step 1 establishes

The development baseline addresses NFR-001, NFR-002, NFR-012, NFR-013, NFR-014,
and the local Python portion of NFR-016. Least-privilege roles and Compose
reproducibility still require Step 2. The implementation keeps the existing
`config` and `ingestion` packages to avoid a premature directory migration.

### Packaging: imports should not depend on the current folder

`pyproject.toml` declares the project, Python range, runtime dependencies, package
contents, and development tools. Explicit package selection prevents the local
`airflow/` DAG directory from becoming part of our installable package. Installing
SILID allows `import ingestion.extract` from outside the repository. Importing a
module defines functions/classes; it does not read `.env`, configure global
logging, contact services, or require database credentials.

Python 3.12 is the tested baseline (`>=3.12,<3.13`). Existing Airflow 2.10.5 metadata
includes Python 3.12 and excludes 3.13. This establishes a compatible interpreter
choice, not proof that the full image's dependencies are compatible.
[Airflow 2.10.5 package metadata](https://raw.githubusercontent.com/apache/airflow/2.10.5/pyproject.toml).
The existing [Airflow constraints](https://raw.githubusercontent.com/apache/airflow/constraints-2.10.5/constraints-3.12.txt)
are a separate integration input for Step 2; there is no automatic Airflow upgrade.

### Dependencies: a declaration and a resolved recipe

`pyproject.toml` lists what our code directly uses. `uv.lock` records the complete
resolved dependency tree and artifact hashes. Commit both. `uv sync --locked`
installs that recipe and refuses to silently change an outdated lockfile.
[uv locking and syncing](https://docs.astral.sh/uv/concepts/projects/sync/).

Runtime dependencies are Requests, psycopg2, SQLAlchemy and python-dotenv.
Development dependencies are pytest and Ruff. The new package does not install
unused pandas, PyArrow or PyYAML, nor future dashboard/monitoring tools. The legacy
`requirements.txt` remains unchanged for the existing Dockerfile until Step 2;
it is not the source of truth for the standalone development environment.
Do not copy the new lockfile into an Airflow image without resolving and testing
that image's own constraints.

Use uv 0.11.23, matching CI. To make an intentional dependency change:

1. Edit a direct dependency in `pyproject.toml` (or use `uv add` / `uv add --dev`).
2. Run `uv lock`, inspect the lockfile diff, then `uv sync --locked`.
3. Run the complete checks below before committing both files.

Do not use an unrestricted upgrade as part of normal startup. Exact pins improve
repeatability; they still need deliberate maintenance and do not prove security.
The isolated `.venv`, build outputs, and local `.env` are ignored by Git.

### Configuration: collect inputs, validate, then perform work

`load_environment()` reads only a file explicitly supplied by the caller, and
returns a new dictionary. It does not search parent directories or modify
`os.environ`. Precedence is process environment over file. Dotenv interpolation is
disabled, so literal `${...}` in a password is not unexpectedly expanded.
An empty environment value wins over the file and then fails a required-field
check; it does not quietly resurrect a file credential.

`DatabaseSettings.from_env()` and `WeatherSettings.from_env()` convert strings
into validated values. The loader validates its database settings before opening
a connection. Its command-line entrypoint validates database and weather settings
before extraction. The extractor requires only weather settings, so it can be
used independently of a database. Settings can be passed explicitly in tests.

| Setting | Behavior |
|---|---|
| `DB_HOST` | Required hostname/IP; host process normally uses `localhost`, container uses `postgres`. |
| `DB_PORT` | Required integer 1–65535; host uses published port, container uses internal 5432. |
| `DB_NAME` | Required application database name. Old typo `DB_NAEME` raises an actionable error. |
| `DB_USER` | Required application database user. No bootstrap or metadata-user fallback. |
| `DB_PASSWORD` | Required and nonblank. Preserved literally; excluded from settings repr and validation output. |
| `OPEN_METEO_BASE_URL` | Defaults to the public HTTPS forecast endpoint. Overrides must be HTTPS without embedded credentials, query, or fragment. |
| `TIMEZONE` | Defaults to `Asia/Manila`; other values are rejected under the MVP contract. |
| `POSTGRES_*` | Legacy Compose bootstrap inputs only; never application credential fallbacks. |
| `AIRFLOW__DATABASE__SQL_ALCHEMY_CONN` | Airflow metadata setting only; never read by application settings. |

A safe validation command is:

```bash
uv run --locked python -m config.check --env-file .env.example
```

This validates format and presence, not database connectivity or permissions.
A successful result cannot establish that a server exists or a password is correct.
`DatabaseSettings.url` uses SQLAlchemy's structured URL builder so reserved
characters in passwords are encoded correctly. Do not log passwords or unmasked
connection strings; hiding a field from repr is only one protection.

### City configuration: domain inputs are also a contract

`config/cities.py` is the sole city catalog. It retains all five existing cities
and coordinates. Validation requires a nonempty catalog, stable lowercase keys,
nonblank names, finite latitude/longitude in geographic bounds, and the MVP
timezone. A validated copy prevents validation from changing the source catalog.
`ingestion/config.py` re-exports the catalog for compatibility; it does not maintain
a second copy. Batch extraction validates the whole catalog before the first HTTP
call, avoiding a half-completed collection due to a bad city entry.

### Lint, format, test, and CI have different jobs

- Ruff lint catches selected code mistakes and import ordering.
- Ruff format makes layout consistent so reviews can focus on behavior.
- pytest checks behavior: missing settings, precedence, secret-safe errors,
  invalid cities, configured endpoints, propagation of HTTP failures, and portable imports.
- CI runs those checks on pushes and pull requests, then builds and checks the installed package.

The prototype's invalid `except requests.raise_for_status` was changed to catch
and re-raise `requests.RequestException`. This small adjacent fix keeps the
original error visible; the full connector, raw preservation, and retries remain
Steps 3–4. Module-level logging setup moved into command-line entrypoints. The
legacy JSONB loader still lacks Bronze durability/idempotency and must not be
presented as the completed ingestion layer.

## Validation commands

Run from the repository root:

```bash
uv sync --locked
uv pip check
uv run --locked ruff check .
uv run --locked ruff format --check .
uv run --locked pytest
uv build
```

The test suite blocks real Requests session calls and psycopg2 connections. It
also launches fresh Python processes in temporary directories to exercise
installed imports and the configuration CLI without an inherited `.env`.
No source or database service is used during these tests.

CI additionally installs the built wheel without resolving new dependencies and
checks imports from `/tmp`. This verifies packaging rather than relying only on
Python's implicit current-directory import path. CI execution on GitHub must be
observed after a future push; local check results do not claim remote CI passed.

## Step 1 validation evidence

Local verification on Python 3.12.3 completed:

- 66 offline pytest cases passed.
- Ruff lint and formatting checks passed.
- Locked editable installation and a clean non-editable installation succeeded;
  dependency consistency checks passed in both environments.
- Source distribution and wheel built successfully. The built wheel was installed
  in the clean environment and imported from outside the checkout in isolated
  Python mode, without logging setup or service connections.
- Example configuration and all five cities validated without exposing credentials.
- Distribution inspection confirmed the local `.env` is excluded; the source
  archive includes the example, lockfile, and test fixtures.
- Relative documentation links and Git whitespace checks passed.

Remote GitHub CI and Docker integration were not executed. No branch, commit,
service startup, live weather request, or database write was performed.

## Learning checkpoint

Predict the result before trying it:

- A file has `DB_PORT=5432`, while the process sets `DB_PORT=not-a-number`.
- A process has all `POSTGRES_*` settings but no `DB_*` settings.
- You import `ingestion.load` in an empty temporary directory.
- One of five configured cities has latitude 120.

Expected behavior: fail with a DB_PORT error; fail with a missing application
setting; import successfully without I/O; reject the catalog before requesting
any city. Each result follows an explicit boundary and has a regression test.

## Recommended Step 1 Git workflow

Branch: `chore/engineering-baseline`. Branch/commit creation is not automatic.

| Commit | Scope and reason for separation | Validation before commit |
|---|---|---|
| `build(python): define packages and reproducible dependencies` | pyproject.toml, uv.lock, .python-version, MANIFEST.in, config/__init__.py and ingestion/__init__.py. Establishes installation independently of runtime settings. | Locked installation, dependency check, wheel/source build. |
| `fix(config): validate application and city settings` | config/config.py, config/cities.py, config/check.py, ingestion/config.py, ingestion/extract.py, ingestion/load.py, .env.example and tests. One coherent change connects explicit settings to callers and regression coverage. | All offline tests pass, including imports, precedence, invalid inputs and caller integration. |
| `ci: add lint and unit-test checks` | .github/workflows/ci.yml, README.md, docs/DEVELOPMENT.md, docs/REQUIREMENT_TRACEABILITY.md and docs/IMPLEMENTATION_PLAN.md. Makes the validated workflow repeatable and documents its limits. | Full local CI-equivalent checks, wheel import smoke check, documentation links and whitespace. |

The local detailed roadmap's status is updated separately and remains Git-ignored.
Step 2 will reconcile the image dependencies, migrations, roles, MinIO and Compose
injection; no infrastructure is provisioned during Step 1.
