---
name: Dreamhost import contains attacker-planted artifacts
description: The /home/wn/ rsync import from Dreamhost includes files planted during past compromises — do not treat them as legitimate data to recover
type: project
originSessionId: 600e360a-51ea-43f3-ac8e-c49be01d24ea
---
The `from-dreamhost/` subtree was pulled from a Dreamhost account (`/home/wn/`) that suffered at least one compromise. Several artifact patterns are attacker-planted, not user data.

**Why:** The account contains a `biohack.net_DISABLED_BY_DREAMHOST__COMPROMISED/` tree (Dreamhost locked it due to a confirmed compromise), and `rx.php` in that tree is a classic WSO/b374k-style planted shell filename. User (wbnorris@gmail.com) confirmed on 2026-04-23 that the unreadable `.htpasswd` files under `/home/wn/logs/<domain>/http.<id>/html/` on `admin.*` subdomains are "part of attempts at hacking" — consistent with files created by the web user (`www-data`) during exploitation, which show up as unreadable to the shell user.

**How to apply:** When analyzing or recovering content from this import, treat the following as suspect/do-not-restore rather than as missing data:
- Anything under `*_DISABLED_BY_DREAMHOST*` or `*_COMPROMISED*` paths
- `rx.php` and similarly named stray PHP files outside normal app structure
- Unreadable `.htpasswd` files under `logs/*/html/` (different from legitimate `.htpasswd` in web roots)
- Files owned by non-wn uids that the shell user can't read

If a future rsync/backup shows "permission denied" on these exact categories, that is the expected/desired outcome, not a failure to investigate.
