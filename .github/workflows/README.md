# Workflows

`checks.yml` runs on every push and pull request.

It installs pinned dependencies from the lockfiles, applies migrations to a
PostgreSQL service, runs the backend tests, Ruff, the content validator, the
deterministic contract export and its drift check, then the frontend lint,
typecheck, unit tests, build and format check, and finally the browser suite
against the real API and database.

Two things it deliberately does not do:

- It never calls a paid or quota-consuming model endpoint. The browser suite
  runs with `TUTOR_PROVIDER=authored`, and the live provider smoke test
  (`python -m app.tools.tutor_smoke`) is opt-in and never run here.
- It never requires an NVIDIA credential. `NVIDIA_API_KEY` is set to the empty
  string so a missing secret cannot make a check pass or fail by accident.

Before the release baseline, resolve the official releases for each action and
pin full commit SHAs with version comments, as GitHub's secure-use guidance
recommends. The current file keeps the supplied major-version tags rather than
inventing hashes.
