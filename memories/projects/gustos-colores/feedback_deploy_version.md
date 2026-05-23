---
name: Bump and report version on every deploy
description: Always increment the build number in settings_screen.dart before deploying, and tell the user the new version after the deploy completes.
type: feedback
originSessionId: a932a4d6-9527-4de0-b1ed-8d0bad9c6f67
---
Before every `task app-deploy-web`, bump the version string in `app/lib/features/settings/settings_screen.dart` (format: `build YYYYMMDD-N`). After the deploy completes, report the new version number to the user.

**Why:** User needs to know what version is live so they can verify they're testing the right build.

**How to apply:** Treat version bump + deploy as one atomic step. Never deploy without bumping first.
