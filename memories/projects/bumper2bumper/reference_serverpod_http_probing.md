---
name: Serverpod HTTP probing format (curl)
description: Direct curl probes use GET /<endpoint>/<method>?args; the SDK client uses POST /<endpoint> with a JSON body. Don't try /serverpod/<...>.
type: reference
originSessionId: 44b1801c-d746-43f0-96ea-6ad6f085186f
---
For SplitLedger's Serverpod 3.4.5 backend (and any Serverpod 3.x project), the HTTP server accepts two RPC URL forms:

- **Human / smoke-test probing (used by `infrastructure/aws-lightsail/cloud-init.sh:181`):**
  - `GET /<endpointName>/<methodName>?<arg>=<val>...`
  - Endpoint name = class name minus the `Endpoint` suffix, first letter lowered. `HealthEndpoint` → `health`, `ConfigEndpoint` → `config`, `InvitationEndpoint` → `invitation`.
  - Examples: `curl -i http://localhost:8080/health/check`, `curl -i 'http://localhost:8080/invitation/info?token=<t>'`.

- **SDK client form (`serverpod_client_shared.dart:559` + `serverpod_client_shared_private.dart:8`):**
  - `POST /<endpointName>` with `Content-Type: application/json` and body `{"method":"<methodName>", ...args}`.
  - This is what the generated Dart client emits.

Diagnostic response shapes (verified against `task serve` 2026-04-26):

- `404 Endpoint not found` — first path component didn't match an endpoint name. Most common cause: prepending `/serverpod/` (don't — there's no such prefix).
- `401 Unauthorized` with empty body — properly gated `requireLogin = true` endpoint, no auth header. This is the correct shape. **Caveat:** Serverpod's auth gate at `endpoint_dispatch.dart:190–196` runs *before* method-name resolution, so requesting a non-existent method on an auth-required endpoint also returns 401 (not 404). Method existence is masked behind the auth challenge — good for info-hiding, but it means curl probes alone can't enumerate the method list of an auth-required endpoint. Cross-reference the source.
- `500 Internal Server Error` with body `Internal Server Error` (21 bytes, plain text) on a method with a non-String required param — Serverpod's GET-probe handler does **not** coerce query-string args to the declared parameter type. Every `params[<key>]` arrives as `String`, and the generated connector closure does an implicit cast to the declared type (`int`, `DateTime`, etc.). For non-String types the cast throws `TypeError: type 'String' is not a subtype of type '<T>'` *before any endpoint body runs*. Production runMode strips the error text; the 500 is the diagnostic. Implication for security audits: a class with `requireLogin = false` that hosts methods with int/DateTime params is *more* shielded against unauth GET probes than the auth-gate logic alone suggests — the cast slams the door before `authenticatedUserId(session)` is even called. POSTs from the generated SDK send a JSON body with proper types and bypass this, so the cast is *not* a substitute for proper auth gating. Live example: `InvitationEndpoint` mixed-auth class (Finding 2 in `docs/investigations/2026-04-26-public-without-login-audit.md`).

When probing a non-String param, the 500 is *expected* — to actually exercise the method body via a GET probe, the param must be `String` (or the class must be `requireLogin = true`, in which case you'll see the 401 first anyway). When in doubt, use the GET form for one-off probing — it shows up unmangled in HTTP access logs and works with default `curl -i`.
