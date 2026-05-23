---
name: Codemagic logs are accessible only via artifact zip, not a log endpoint
description: Codemagic's REST API has no /builds/<id>/log endpoint; tee build output to a *.log file declared as an artifact in codemagic.yaml so it's fetchable via /artifacts on red builds.
type: feedback
originSessionId: 3ec77330-7c83-4eb1-b903-1239bafea483
---
Codemagic exposes per-build status (`GET /builds/<id>` with header `x-auth-token: <pat>`) but **no per-step log endpoint**. Verified 2026-05-10: `/builds/<id>/log`, `/builds/<id>/log/<stepId>`, and `/buildActions/<id>/log` all return 404.

**Why:** Without log access you're back to copy-pasting the failure tail from the Codemagic web UI on every red build, which is what made the user frustrated mid-mvp-build-debugging today.

**How to apply:** In every Codemagic workflow's build script that compiles or builds something likely to fail, tee stdout+stderr into a `*.log` file under the workspace, then add that file path to the workflow's `artifacts:` list. On any build (red or green) the artifacts zip is fetchable via the URL embedded in `GET /builds/<id>`'s response (`build.artefacts[].url`). Note the British spelling `artefacts` in the API field name.

Example pattern (from [`gustos-colores`](../../SRC/gustos-colores/codemagic.yaml) and now [`bumper2bumper`](../../SRC/bumper2bumper/codemagic.yaml) `splitledger-android`):

```yaml
scripts:
  - name: Build release APK
    script: |
      cd mobile/splitledger_flutter
      flutter build apk --release \
        --dart-define=... \
        2>&1 | tee ../../flutter-build.log

artifacts:
  - mobile/splitledger_flutter/build/app/outputs/flutter-apk/*.apk
  - flutter-build.log     # ← captures the build output
```

The originating commit on the WorldFoundry-wbniv side was `7021ba58` ("codemagic: pipe gradle output to gradle-build.log artifact for debugging"); same shape, gradle instead of flutter.

[`scripts/codemagic-build.sh`](../../SRC/bumper2bumper/scripts/codemagic-build.sh) implements this fully: on `failed|canceled|timeout` status, it pulls the artifacts zip URL from `build.artefacts[]`, downloads it, and `unzip -p`s every `*.log` inside, printing the last `LOG_TAIL` lines (default 200) of each. So `task codemagic-build BRANCH=mvp` succeeds-or-shows-the-actual-error end-to-end without any browser visit.
