"""
config.example.py — repository metadata for gen-index.py.

Copy to gen/config.py and fill in real values.
bootstrap-apt.sh patches KEY_ID and FINGERPRINT automatically after GPG generation.
The skill's Step 0 seeds this file with project-specific values.
"""

# ── identity ──────────────────────────────────────────────────────────
HOST            = "apt.example.org"
PORT            = 443
SCHEME          = "https"
CONTACT_EMAIL   = "apt@example.org"

WORDMARK        = "Your Project"
HOME_URL        = "https://example.org"
HOME_LABEL      = "example.org"

# ── signing key ───────────────────────────────────────────────────────
# bootstrap-apt.sh patches KEY_ID and FINGERPRINT after GPG key generation.
# KEYRING_PATH: where end-users install the dearmored public key.
#   Derived from INSTALL_SLUG — e.g. INSTALL_SLUG="myproject" →
#   KEYRING_PATH="/etc/apt/keyrings/myproject.gpg"
KEY_ID          = "YOUR_KEY_ID_HERE"
FINGERPRINT     = "YOUR_FINGERPRINT_HERE"
INSTALL_SLUG    = "your-project"   # used in keyring filename and sources.list
KEYRING_PATH    = f"/etc/apt/keyrings/{INSTALL_SLUG}.gpg"

# ── repo shape ────────────────────────────────────────────────────────
COMPONENTS      = ["main"]
ARCHITECTURES   = ["amd64", "arm64"]

# Auto-flatten the /pool/<component>/ user-facing listing when total .deb count
# is below this threshold (presentation only; on-disk layout stays Debian Policy
# §2.4 sharded). Set 0 to always shard; large value to always flatten.
FLAT_POOL_THRESHOLD = 30
CODENAMES       = {
    "stable":       "stable",
    "testing":      "testing",
    "experimental": "experimental",
}
DEFAULT_SUITE   = "stable"

# ── render flags ──────────────────────────────────────────────────────
SHOW_ARCH       = True

# ── copy ──────────────────────────────────────────────────────────────
# PAGE_DESCRIPTION: used in <meta name="description">
PAGE_DESCRIPTION = "Signed Debian/Ubuntu package archive for Your Project."

# LEDE_HTML: short blurb rendered below the page headline.
# Leave empty to omit. The skill can fill this in from package content.
LEDE_HTML = ""

# README_HTML: rendered in a panel at the bottom of the root listing only.
README_HTML = """
<p>
  This is the official Debian/Ubuntu package archive for <strong>Your Project</strong>.
  The repository follows the standard Debian layout: per-suite metadata under
  <code>/dists</code>, per-component pools under <code>/pool</code>.
  Suites are signed — do not omit <code>Signed-By</code> from your sources.list entry.
</p>
"""
