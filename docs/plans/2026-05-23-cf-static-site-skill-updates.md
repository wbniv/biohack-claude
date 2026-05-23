# Plan — cf-static-site skill: 2.4.x fixes from biohack.net migration

## Context

Live run of `cf-static-site` Pages path against `biohack.net` exposed gaps in the
skill templates. Fixes applied incrementally during implementation.

## Changes (all complete)

- 2.4.0: add deploy-dir + branch inputs, www-redirect removal step, existing-repo
  variant, fix credential error message
- Interactive token prompt (foundrylinux.org pattern) instead of error-and-exit
- Store creds in `.creds/bootstrap.env` (repo-local, gitignored) not `/tmp/`
- Fix `BASH_SOURCE` path: use `REPO_ROOT=$(cd "$(dirname ...)" && pwd)` pattern

## Verification

`bash scripts/bootstrap-site.sh --dry-run` in a project using the template should
print all dry-run steps without errors.
