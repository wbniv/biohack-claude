#!/usr/bin/env python3
"""
gen-index.py — emit static index.html files for an apt repository tree.

Walks a source directory (typically `/srv/apt`), and for each subdirectory
writes an index.html in the corresponding location of the output directory.
Pulls per-path metadata (descriptions, suite codenames, signing key info,
sources.list snippets) from a config module passed via --config.

Standard library only. Python ≥ 3.10.

Typical wiring:

    # one-shot
    gen-index.py --root /srv/apt --out /var/www/apt.example.org \\
                 --static $(dirname $0)/static --config $(dirname $0)/config.py

    # incremental — re-run from cron after dak/reprepro publishes
    */5 * * * * /opt/apt-index/gen-index.py --root /srv/apt \\
                 --out /var/www/apt.example.org \\
                 --static /opt/apt-index/static --config /opt/apt-index/config.py \\
                 --quiet

Hashes are off by default (slow on large pools). Pass --sha256 to add a column;
hashes are cached in `.sha256cache` inside the output root keyed by (path, size,
mtime) so subsequent runs are cheap.
"""

from __future__ import annotations

import argparse
import hashlib
import html as html_mod
import importlib.util
import json
import logging
import os
import re
import shutil
import sys
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable, Optional

# ─── filename parsing ──────────────────────────────────────────────────
DEB_RE = re.compile(
    r"^(?P<pkg>[\w.+-]+)_(?P<ver>[\w.+~:-]+)_(?P<arch>amd64|arm64|all|i386|armhf|riscv64|source)\.deb$"
)
DSC_RE = re.compile(r"^(?P<pkg>[\w.+-]+)_(?P<ver>[\w.+~:-]+)\.dsc$")
DBGSYM_RE = re.compile(r"-dbgsym_")
SRC_TAR_RE = re.compile(r"\.(orig|debian)\.tar\.[a-z0-9]+$")

EXT_BY_BASENAME = {
    "Release":      "idx",
    "Release.gpg":  "sig",
    "InRelease":    "sig",
    "Packages":     "idx",
    "Packages.gz":  "gz",
    "Packages.xz":  "gz",
    "Packages.bz2": "gz",
    "Sources":      "idx",
    "Sources.gz":   "gz",
    "Sources.xz":   "gz",
    "Contents":     "idx",
    "README":       "txt",
    "LICENSE":      "txt",
    "LICENSING":    "txt",
    "MIRRORS":      "txt",
    "TRADEMARK":    "txt",
    "key.gpg":      "key",   # the public signing key (per bootstrap-apt.sh)
}

EXT_BY_SUFFIX = [
    (".deb",       "deb"),
    (".udeb",      "deb"),
    (".dsc",       "src"),
    (".tar.xz",    "src"),
    (".tar.gz",    "src"),
    (".tar.bz2",   "src"),
    (".tar.zst",   "src"),
    (".tar",       "src"),
    (".asc",       "key"),
    (".gpg",       "sig"),
    (".sig",       "sig"),
    (".gz",        "gz"),
    (".xz",        "gz"),
    (".bz2",       "gz"),
    (".zst",       "gz"),
    (".jsonl",     "idx"),
    (".json",      "idx"),
    (".list",      "idx"),
    (".md",        "txt"),
    (".txt",       "txt"),
]

def infer_ext(name: str) -> str:
    if name in EXT_BY_BASENAME:
        return EXT_BY_BASENAME[name]
    lower = name.lower()
    for suf, kind in EXT_BY_SUFFIX:
        if lower.endswith(suf):
            return kind
    return "txt"

def infer_arch(name: str) -> Optional[str]:
    m = DEB_RE.match(name)
    if m:
        a = m.group("arch")
        return "src" if a == "source" else a
    if name.endswith(".dsc") or SRC_TAR_RE.search(name):
        return "src"
    return None

# ─── size formatting ───────────────────────────────────────────────────
def fmt_size(b: int) -> str:
    if b < 1024: return f"{b} B"
    for unit, div in (("KB", 1024), ("MB", 1024**2), ("GB", 1024**3), ("TB", 1024**4)):
        if b < div * 1024:
            v = b / div
            return f"{v:.1f} {unit}" if v < 100 else f"{v:.0f} {unit}"
    return f"{b/1024**4:.1f} TB"

MONTHS = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]

def fmt_mtime(ts: float) -> dict:
    d = datetime.fromtimestamp(ts, tz=timezone.utc)
    return {
        "iso": d.isoformat(),
        "y":   f"{d.year}",
        "md":  f"{MONTHS[d.month - 1]} {d.day:02d}",
        "t":   f"{d.hour:02d}:{d.minute:02d}",
    }

# ─── icons (raw SVG strings, monochrome via currentColor) ──────────────
ICONS = {
    "up":  '<svg viewBox="0 0 16 16" width="14" height="14" fill="currentColor" aria-hidden="true"><path d="M3 10 L8 5 L13 10 Z"/></svg>',
    "dir": '<svg viewBox="0 0 16 16" width="14" height="14" fill="currentColor" aria-hidden="true"><path d="M5 4 L11 8 L5 12 Z"/></svg>',
    "deb": '<svg viewBox="0 0 16 16" width="14" height="14" fill="currentColor" aria-hidden="true"><rect x="3" y="3" width="10" height="10"/></svg>',
    "gz":  '<svg viewBox="0 0 16 16" width="14" height="14" fill="none" stroke="currentColor" stroke-width="1.4" aria-hidden="true"><path d="M3 3 L13 3 L13 13 L3 13 Z M3 6 L13 6 M3 9 L13 9 M3 12 L13 12"/></svg>',
    "sig": '<svg viewBox="0 0 16 16" width="14" height="14" fill="currentColor" aria-hidden="true"><path d="M5 1 L5 4 L1 4 L1 6 L5 6 L5 9 L1 9 L1 11 L5 11 L5 15 L7 15 L7 1 Z"/><circle cx="11" cy="8" r="3" fill="none" stroke="currentColor" stroke-width="1.4"/></svg>',
    "key": '<svg viewBox="0 0 16 16" width="14" height="14" fill="none" stroke="currentColor" stroke-width="1.4" aria-hidden="true"><circle cx="5" cy="8" r="3"/><path d="M8 8 L15 8 M12 8 L12 11 M14 8 L14 10"/></svg>',
    "idx": '<svg viewBox="0 0 16 16" width="14" height="14" fill="none" stroke="currentColor" stroke-width="1.4" aria-hidden="true"><path d="M3 4 L13 4 M3 8 L13 8 M3 12 L13 12"/></svg>',
    "txt": '<svg viewBox="0 0 16 16" width="14" height="14" fill="none" stroke="currentColor" stroke-width="1.4" aria-hidden="true"><path d="M3 3 L13 3 L13 13 L3 13 Z M5 6 L11 6 M5 9 L11 9 M5 12 L9 12"/></svg>',
    "src": '<svg viewBox="0 0 16 16" width="14" height="14" fill="none" stroke="currentColor" stroke-width="1.4" aria-hidden="true"><path d="M6 4 L2 8 L6 12 M10 4 L14 8 L10 12"/></svg>',
}

# ─── entry record ──────────────────────────────────────────────────────
@dataclass
class Entry:
    name: str
    is_dir: bool
    size: int
    mtime: float
    desc: str = ""
    arch: Optional[str] = None
    ext: str = "txt"
    sha256: Optional[str] = None
    # Optional explicit href override. When set (e.g. in flat-pool mode),
    # used verbatim instead of deriving from `name`. Lets the flat view link
    # `cdpack_*.deb` at the real on-disk path `c/cdpack/cdpack_*.deb`.
    href: Optional[str] = None
    # True if the .deb declares Section: metapackages. Drives the META chip
    # and the sectioned-table presentation in flat-pool mode.
    is_metapackage: bool = False
    # Multi-line body of the .deb's Description field (the part below the
    # one-line summary that lands in `desc`). Empty when no long body exists.
    description_long: str = ""
    # Parsed Depends and Recommends lists (base pkg names, version constraints
    # stripped). Populated alongside is_metapackage when section_map is loaded.
    depends: list = field(default_factory=list)
    recommends: list = field(default_factory=list)

# ─── config loading ────────────────────────────────────────────────────
def load_config(path: Path):
    spec = importlib.util.spec_from_file_location("apt_index_config", path)
    if spec is None or spec.loader is None:
        raise SystemExit(f"Cannot load config: {path}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod

# ─── HTML helpers ──────────────────────────────────────────────────────
def esc(s: str) -> str:
    return html_mod.escape(s, quote=True)

def parent_of(rel: str) -> Optional[str]:
    """rel is the URL-style directory path with trailing '/'; '/' is root."""
    if rel == "/" or rel == "":
        return None
    trimmed = rel.rstrip("/")
    idx = trimmed.rfind("/")
    return "/" if idx <= 0 else trimmed[: idx + 1]

def segments_of(rel: str) -> list[str]:
    if rel == "/" or rel == "":
        return []
    return [s for s in rel.split("/") if s]

# ─── sha-256 cache ─────────────────────────────────────────────────────
class HashCache:
    def __init__(self, path: Path):
        self.path = path
        self.data: dict[str, dict] = {}
        if path.exists():
            try:
                self.data = json.loads(path.read_text())
            except Exception:
                self.data = {}

    def get(self, abs_path: Path, size: int, mtime: float) -> Optional[str]:
        key = str(abs_path)
        rec = self.data.get(key)
        if rec and rec.get("size") == size and abs(rec.get("mtime", 0) - mtime) < 1.5:
            return rec.get("sha256")
        return None

    def put(self, abs_path: Path, size: int, mtime: float, sha: str):
        self.data[str(abs_path)] = {"size": size, "mtime": mtime, "sha256": sha}

    def save(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(self.data))

def hash_file(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()

# ─── scanning ──────────────────────────────────────────────────────────
SKIP_NAMES = {".sha256cache", "index.html", ".DS_Store", ".git", ".gitignore"}

def scan(root: Path, rel: str, descriptions: dict[str, dict[str, str]],
         do_sha256: bool, cache: Optional[HashCache], logger: logging.Logger) -> list[Entry]:
    abs_dir = root / rel.lstrip("/")
    entries: list[Entry] = []
    desc_for_dir = descriptions.get(rel, {})
    try:
        with os.scandir(abs_dir) as it:
            for de in it:
                if de.name in SKIP_NAMES:
                    continue
                try:
                    st = de.stat(follow_symlinks=False)
                except FileNotFoundError:
                    continue
                e = Entry(
                    name=de.name,
                    is_dir=de.is_dir(follow_symlinks=False),
                    size=st.st_size,
                    mtime=st.st_mtime,
                    desc=desc_for_dir.get(de.name, ""),
                    ext="dir" if de.is_dir(follow_symlinks=False) else infer_ext(de.name),
                    arch=None if de.is_dir(follow_symlinks=False) else infer_arch(de.name),
                )
                if do_sha256 and not e.is_dir:
                    abs_p = Path(de.path)
                    cached = cache.get(abs_p, e.size, e.mtime) if cache else None
                    if cached:
                        e.sha256 = cached
                    else:
                        logger.info("hashing %s", abs_p)
                        e.sha256 = hash_file(abs_p)
                        if cache:
                            cache.put(abs_p, e.size, e.mtime, e.sha256)
                entries.append(e)
    except FileNotFoundError:
        return []
    # dirs first, then alphabetic
    entries.sort(key=lambda e: (not e.is_dir, e.name.lower()))
    return entries

def _parse_packages_stanzas(text: str):
    """Yield one dict per Debian-format stanza in *text*.

    A stanza ends at the first blank line (or end of input). Multi-line
    field values (Description, etc.) are joined with embedded newlines
    so callers can re-split if they care; leading-space continuation
    indentation per RFC 822 is honored.
    """
    stanza: dict[str, str] = {}
    last_field: Optional[str] = None
    for raw in text.splitlines() + [""]:
        if not raw.strip():
            if stanza:
                yield stanza
            stanza = {}
            last_field = None
            continue
        if raw.startswith((" ", "\t")) and last_field is not None:
            stanza[last_field] = stanza[last_field] + "\n" + raw[1:]
            continue
        if ":" in raw:
            k, _, v = raw.partition(":")
            stanza[k.strip()] = v.strip()
            last_field = k.strip()

def _parse_dep_list(raw: str) -> list[str]:
    """Turn a Depends/Recommends value into a list of base package names.

    Strips version constraints `(>= 1.2)`, splits alternatives `a | b`
    (keeps the first), and drops the auto-generated `${shlibs:Depends}`
    style substitution markers if any survive into the published file.
    """
    out: list[str] = []
    for chunk in raw.split(","):
        chunk = chunk.strip()
        if not chunk or chunk.startswith("${"):
            continue
        # alternatives: 'foo | bar' — keep the first.
        chunk = chunk.split("|", 1)[0].strip()
        # version constraint: strip '(...)' tail.
        chunk = chunk.split("(", 1)[0].strip()
        # arch qualifier: strip ':any', ':amd64' etc.
        chunk = chunk.split(":", 1)[0].strip()
        if chunk:
            out.append(chunk)
    return out

def load_package_metadata(root: Path) -> dict[str, dict]:
    """Build {package_name: {section, description_short, description_long,
                              depends, recommends, filename}} from
    published Packages files.

    Reads every `dists/<suite>/<component>/binary-<arch>/Packages` file
    under `root`. Falls back to scanning each `.deb` via dpkg-deb on a
    fully un-published tree. Returns an empty dict if neither is present.
    """
    meta: dict[str, dict] = {}
    def _store(stanza: dict[str, str]):
        pkg = stanza.get("Package", "")
        if not pkg or pkg in meta:
            return
        desc_full = stanza.get("Description", "")
        # First line = short summary; rest = long. Long has leading-space
        # paragraph indentation from the Packages format ("\n " continuation,
        # "\n .\n" for blank-line paragraph breaks).
        if "\n" in desc_full:
            desc_short, _, desc_long_raw = desc_full.partition("\n")
        else:
            desc_short, desc_long_raw = desc_full, ""
        # Cleanup the long: each line lost its leading space already in
        # _parse_packages_stanzas; convert " ." (which became ".") on a
        # line by itself into a paragraph break.
        long_lines = []
        for ln in desc_long_raw.splitlines():
            long_lines.append("" if ln.strip() == "." else ln)
        meta[pkg] = {
            "section": stanza.get("Section", ""),
            "description_short": desc_short.strip(),
            "description_long": "\n".join(long_lines).strip(),
            "depends": _parse_dep_list(stanza.get("Depends", "")),
            "recommends": _parse_dep_list(stanza.get("Recommends", "")),
            "filename": stanza.get("Filename", ""),
        }
    dists_root = root / "dists"
    if dists_root.is_dir():
        for packages_file in dists_root.rglob("Packages"):
            try:
                text = packages_file.read_text(encoding="utf-8", errors="replace")
            except OSError:
                continue
            for stanza in _parse_packages_stanzas(text):
                _store(stanza)
    if meta:
        return meta
    # Fallback: dpkg-deb on each .deb under pool/. Slower path.
    pool_root = root / "pool"
    if not pool_root.is_dir():
        return meta
    for deb in pool_root.rglob("*.deb"):
        try:
            import subprocess
            out = subprocess.run(
                ["dpkg-deb", "--field", str(deb),
                 "Package", "Section", "Description", "Depends", "Recommends"],
                check=True, capture_output=True, text=True,
            ).stdout
        except (OSError, subprocess.CalledProcessError):
            continue
        for stanza in _parse_packages_stanzas(out):
            stanza.setdefault("Filename",
                              str(deb.relative_to(root)).replace(os.sep, "/"))
            _store(stanza)
    return meta

def load_section_map(root: Path) -> dict[str, str]:
    """Backwards-compat shim: returns just {pkg: section}. New callers
    should use load_package_metadata() directly to also get descriptions,
    depends, recommends."""
    return {k: v["section"] for k, v in load_package_metadata(root).items()}

def flat_pool_scan(root: Path, rel: str, descriptions: dict[str, dict[str, str]],
                   do_sha256: bool, cache: Optional[HashCache], logger: logging.Logger,
                   section_map: Optional[dict[str, str]] = None,
                   pkg_meta: Optional[dict[str, dict]] = None) -> list[Entry]:
    """Recursive variant of scan() for /pool/<component>/ in flat-pool mode.

    Walks every file under <root>/<rel> regardless of shard / source-package
    nesting and returns one Entry per leaf file. Each Entry's `href` is set
    to the path relative to <rel> (preserving the real on-disk sub-path so
    the browser link still resolves), while `name` shows only the file's
    basename so the table reads as a simple package list. Subdirectory
    Entries are NOT emitted — the whole point of flat mode is to skip them.

    Descriptions are looked up by the file's *real* containing directory
    (e.g. /pool/main/c/cdpack/), matching the same DESCRIPTIONS scheme used
    by scan(), so per-package descriptions still surface in the flat view.
    """
    abs_dir = root / rel.lstrip("/")
    entries: list[Entry] = []
    try:
        for dirpath, dirnames, filenames in os.walk(abs_dir):
            # stable order and skip SKIP_NAMES (e.g. index.html)
            dirnames.sort()
            real_dir_rel = "/" + str(Path(dirpath).relative_to(root)).replace(os.sep, "/") + "/"
            desc_for_dir = descriptions.get(real_dir_rel, {})
            for fname in sorted(filenames):
                if fname in SKIP_NAMES:
                    continue
                fpath = Path(dirpath) / fname
                try:
                    st = fpath.stat()
                except FileNotFoundError:
                    continue
                # href = path relative to the page we're rendering (<rel>)
                href = str(fpath.relative_to(abs_dir)).replace(os.sep, "/")
                # Filename shape: <pkg>_<version>_<arch>.deb. Take first '_'-segment as pkg name.
                pkg_name = fname.split("_", 1)[0] if "_" in fname else fname
                is_meta = bool(section_map) and section_map.get(pkg_name) == "metapackages"
                meta_for_pkg = (pkg_meta or {}).get(pkg_name, {})
                # Prefer the Packages-file Description over the static
                # DESCRIPTIONS config (which is empty in practice).
                short_desc = meta_for_pkg.get("description_short", "") or desc_for_dir.get(fname, "")
                e = Entry(
                    name=fname,
                    is_dir=False,
                    size=st.st_size,
                    mtime=st.st_mtime,
                    desc=short_desc,
                    ext=infer_ext(fname),
                    arch=infer_arch(fname),
                    href=href,
                    is_metapackage=is_meta,
                    description_long=meta_for_pkg.get("description_long", ""),
                    depends=list(meta_for_pkg.get("depends", [])),
                    recommends=list(meta_for_pkg.get("recommends", [])),
                )
                if do_sha256:
                    cached = cache.get(fpath, e.size, e.mtime) if cache else None
                    if cached:
                        e.sha256 = cached
                    else:
                        logger.info("hashing %s", fpath)
                        e.sha256 = hash_file(fpath)
                        if cache:
                            cache.put(fpath, e.size, e.mtime, e.sha256)
                entries.append(e)
    except FileNotFoundError:
        return []
    # alphabetic by filename (no dirs in the result)
    entries.sort(key=lambda e: e.name.lower())
    return entries

# ─── render ────────────────────────────────────────────────────────────
def render_setup_banner(cfg) -> str:
    suite = getattr(cfg, "DEFAULT_SUITE", "stable")
    codename = cfg.CODENAMES.get(suite, "")
    deb822 = (
        f"Types: deb deb-src\n"
        f"URIs: {cfg.SCHEME}://{cfg.HOST}\n"
        f"Suites: {suite}\n"
        f"Components: {' '.join(cfg.COMPONENTS)}\n"
        f"Signed-By: {cfg.KEYRING_PATH}\n"
        f"Architectures: {' '.join(cfg.ARCHITECTURES)}"
    )
    classic = (
        f"deb [signed-by={cfg.KEYRING_PATH} arch={','.join(cfg.ARCHITECTURES)}] \\\n"
        f"    {cfg.SCHEME}://{cfg.HOST} {suite} {' '.join(cfg.COMPONENTS)}\n"
        f"deb-src [signed-by={cfg.KEYRING_PATH}] \\\n"
        f"    {cfg.SCHEME}://{cfg.HOST} {suite} {' '.join(cfg.COMPONENTS)}"
    )
    one_liner = (
        f"# 1. trust the signing key\n"
        f"curl -fsSL {cfg.SCHEME}://{cfg.HOST}/key.gpg \\\n"
        f"  | sudo gpg --dearmor -o {cfg.KEYRING_PATH}\n\n"
        f"# 2. add the source (deb + deb-src so `apt-get source <pkg>` works)\n"
        f'echo "deb [signed-by={cfg.KEYRING_PATH}] {cfg.SCHEME}://{cfg.HOST} {suite} main\n'
        f'deb-src [signed-by={cfg.KEYRING_PATH}] {cfg.SCHEME}://{cfg.HOST} {suite} main" \\\n'
        f"  | sudo tee /etc/apt/sources.list.d/{cfg.HOST.split('.')[0]}.list\n\n"
        f"# 3. install\n"
        f"sudo apt update && sudo apt install {cfg.HOST.split('.')[0]}"
    )
    tabs = [
        ("modern",    "deb822 (apt ≥ 1.1)",       f"/etc/apt/sources.list.d/{cfg.HOST.split('.')[0]}.sources", deb822),
        ("classic",   "Classic sources.list",     f"/etc/apt/sources.list.d/{cfg.HOST.split('.')[0]}.list",    classic),
        ("oneliner",  "One-liner install",        "Shell",                                                     one_liner),
    ]
    panes = []
    btns = []
    for i, (tid, label, target, body) in enumerate(tabs):
        sel = "true" if i == 0 else "false"
        btns.append(
            f'<button class="setup-tab" role="tab" data-tab="{tid}" aria-selected="{sel}">{esc(label)}</button>'
        )
        hidden = "" if i == 0 else ' hidden'
        panes.append(
            f'<div class="setup-pane" data-tab="{tid}" data-target="{esc(target)}"{hidden}>'
            f'<button class="copy" type="button" data-copy>Copy</button>'
            f'<pre><code>{esc(body)}</code></pre>'
            f'</div>'
        )
    return (
        f'<section class="setup" aria-label="Repository setup">'
        f'<div class="setup-head">'
        f'<span class="label"><span class="square"></span>How to use this repository</span>'
        f'<span class="file-target" data-file-target style="font-family:var(--font-mono);font-size:0.78rem;color:var(--color-on-surface-muted)">{esc(tabs[0][2])}</span>'
        f'</div>'
        f'<div class="setup-tabs" role="tablist">{"".join(btns)}</div>'
        f'<div class="setup-body">{"".join(panes)}</div>'
        f'<div class="fp-row">'
        f'<span><span class="k">Signing key</span> <span class="v">{esc(cfg.KEY_ID)}</span></span>'
        f'<span><span class="k">Fingerprint</span> <span class="v">{esc(cfg.FINGERPRINT)}</span></span>'
        f'<span><span class="k">Suite</span> <span class="v">{esc(suite)}</span> <span style="color:var(--color-on-surface-dim)">· codename "{esc(codename)}"</span></span>'
        f'</div>'
        f'</section>'
    )

def render_crumbs(rel: str, cfg) -> str:
    segs = segments_of(rel)
    bits = [f'<a href="/">{esc(cfg.HOST)}</a>']
    acc = "/"
    for i, s in enumerate(segs):
        acc += s + "/"
        bits.append('<span class="crumb-sep">/</span>')
        if i == len(segs) - 1:
            bits.append(f'<span class="here">{esc(s)}</span>')
        else:
            bits.append(f'<a href="{esc(acc)}">{esc(s)}</a>')
    return f'<nav class="crumbs" aria-label="Breadcrumb">{"".join(bits)}</nav>'

def render_headline(rel: str) -> str:
    segs = segments_of(rel)
    if not segs:
        path_html = '<span class="path"><span class="slash">/</span></span>'
    else:
        parts = ['<span class="slash">/</span>']
        for i, s in enumerate(segs):
            parts.append(f'<span>{esc(s)}</span>')
            if i < len(segs) - 1:
                parts.append('<span class="slash">/</span>')
        path_html = '<span class="path">' + "".join(parts) + '</span>'
    return f'<h1 class="headline"><span>Index of</span>{path_html}</h1>'

def name_with_wbr(name: str) -> str:
    """Escape the name, then insert <wbr> word-break opportunities after
    every -, _, ., + so narrow viewports break at logical token boundaries
    (e.g., your-project-blender-addons_1.1.1_amd64.deb wraps as
    `your-project-/blender-/addons_/1.1.1_/amd64.deb` rather than
    character-by-character). Lets the CSS drop overflow-wrap: anywhere."""
    escaped = esc(name)
    return re.sub(r'([-_.+])', r'\1<wbr>', escaped)


def render_row(e: Entry, rel: str, show_arch: bool, show_hash: bool,
               repology_map: Optional[dict] = None,
               changelog_map: Optional[dict] = None) -> str:
    href = esc(e.href if e.href is not None else (e.name + ("/" if e.is_dir else "")))
    icon = ICONS["dir"] if e.is_dir else ICONS.get(e.ext, ICONS["txt"])
    cls = "entry " + ("dir" if e.is_dir else "file")
    name_html = (
        f'<a class="{cls}" href="{href}">'
        f'<span class="icon">{icon}</span>'
        f'<span class="name">{name_with_wbr(e.name)}{"/" if e.is_dir else ""}</span>'
        f'</a>'
    )
    if e.is_dir:
        size_cell = '<span style="color:var(--color-on-surface-dim)">—</span>'
    else:
        size_cell = esc(fmt_size(e.size))
    t = fmt_mtime(e.mtime)
    time_cell = (
        f'<time class="tstamp" datetime="{esc(t["iso"])}" title="{esc(t["iso"])}">'
        f'<span class="y">{t["y"]}</span>'
        f'<span class="md">{t["md"]}</span>'
        f'<span class="t">{t["t"]}</span>'
        f'</time>'
    )
    arch_cell = ""
    if show_arch:
        chips = []
        if e.is_metapackage:
            chips.append('<span class="arch meta">META</span>')
        if e.arch:
            chips.append(f'<span class="arch {e.arch}">{esc(e.arch)}</span>')
        arch_cell = f'<td class="col-arch">{"".join(chips)}</td>'
    hash_cell = ""
    if show_hash:
        hv = (e.sha256[:12] + "…") if e.sha256 else ("" if e.is_dir else "—")
        hash_cell = f'<td class="col-hash" title="{esc(e.sha256 or "")}">{esc(hv)}</td>'
    # data-* attrs let the JS sort numerically without re-parsing
    sort_size = "" if e.is_dir else str(e.size)
    # Metapackage rows get clickable styling + a data-meta-pkg= tag that the
    # JS toggle handler uses to find the matching meta-details row to expand.
    meta_attrs = ""
    meta_cls = ""
    desc_cell_content = esc(e.desc)
    pkg_name = e.name.split("_", 1)[0] if "_" in e.name else e.name
    if e.is_metapackage:
        meta_attrs = f' data-meta-pkg="{esc(pkg_name)}"'
        meta_cls = " meta-row"
        # Inline preview of Depends + Recommends in the Description cell so
        # users see what each metapackage pulls in without clicking. Plain
        # comma-separated names (no links here — the expanded panel has the
        # linked version). Recommends get an italicized suffix.
        bits = []
        if e.depends:
            bits.append(f'<span class="desc-deps"><span class="desc-deps-label">Pulls in:</span> {esc(", ".join(e.depends))}</span>')
        if e.recommends:
            bits.append(f'<span class="desc-recommends"><span class="desc-deps-label">Recommends:</span> {esc(", ".join(e.recommends))}</span>')
        if bits:
            desc_cell_content = f'{esc(e.desc)}<br>{" ".join(bits)}'
    # Changelog hover tooltip
    if not e.is_dir and changelog_map:
        cl = (changelog_map or {}).get(pkg_name, "")
        if cl:
            desc_cell_content = (
                f'<span class="ver-wrap">{desc_cell_content}'
                f'<span class="ver-tip">{esc(cl)}</span></span>'
            )
    # Repology badge for vendored/source-built packages
    if not e.is_dir and e.ext == "deb" and repology_map:
        rp = (repology_map or {}).get(pkg_name, "")
        if rp:
            badge_url  = f"https://repology.org/badge/latest-versions/{esc(rp)}.svg"
            badge_href = f"https://repology.org/project/{esc(rp)}/versions"
            desc_cell_content += (
                f'<a class="repology-badge" href="{badge_href}" target="_blank"'
                f' rel="noopener" aria-label="Repology versions">'
                f'<img src="{badge_url}" alt="latest versions" height="14"></a>'
            )
    return (
        f'<tr class="entry-row{meta_cls}" data-name="{esc(e.name.lower())}" data-size="{sort_size}" data-mtime="{e.mtime:.0f}" data-is-dir="{int(e.is_dir)}" data-desc="{esc(e.desc.lower())}"{meta_attrs}>'
        f'<td class="col-name">{name_html}</td>'
        f'{arch_cell}'
        f'<td class="col-mod">{time_cell}</td>'
        f'<td class="col-size">{size_cell}</td>'
        f'{hash_cell}'
        f'<td class="col-desc">{desc_cell_content}</td>'
        f'</tr>'
    )

def render_section_header_row(label: str, n_cols: int) -> str:
    """In-table header row used to split metapackages from constituent packages
    in flat-pool listings. Renders as a full-width <tr> spanning every column."""
    return (
        f'<tr class="section-header" data-section-header="1">'
        f'<td class="section-header-cell" colspan="{n_cols}">{esc(label)}</td>'
        f'</tr>'
    )

def _package_link(pkg_name: str, section_map: dict[str, str],
                  pkg_meta: dict[str, dict], rel: str, ubuntu_suite: str) -> str:
    """Render a single package name as an <a> link.

    Same-repo packages (present in `pkg_meta` with a Filename:) link to the
    .deb under our pool, made relative to *rel*. External packages link to
    `packages.ubuntu.com/<ubuntu_suite>/<pkg>` which redirects appropriately
    even for packages we don't own.
    """
    meta = pkg_meta.get(pkg_name)
    if meta and meta.get("filename"):
        # Filename in Packages is repo-rooted (e.g. "pool/main/c/cdpack/...").
        # *rel* like "/pool/main/" — strip its leading slash and the matching
        # prefix from filename to get an href relative to the page we're on.
        filename = meta["filename"]
        rel_clean = rel.strip("/")
        if filename.startswith(rel_clean + "/"):
            href = filename[len(rel_clean) + 1:]
        else:
            # Fallback: walk up to repo root, then descend
            depth = len([s for s in rel_clean.split("/") if s])
            href = ("../" * depth) + filename
        return f'<a class="dep-link same-repo" href="{esc(href)}">{esc(pkg_name)}</a>'
    # External — point at Ubuntu's package tracker for the configured suite.
    upstream = f"https://packages.ubuntu.com/{ubuntu_suite}/{pkg_name}"
    return f'<a class="dep-link external" href="{esc(upstream)}" rel="external">{esc(pkg_name)}</a>'

def render_meta_details_row(e: Entry, n_cols: int, section_map: dict[str, str],
                            pkg_meta: dict[str, dict], rel: str, ubuntu_suite: str) -> str:
    """Hidden-by-default row emitted directly after a metapackage row.

    JS toggles its visibility on click of the parent row. Contains the
    long Description body + clickable Depends and Recommends lists.
    """
    pkg_name = e.name.split("_", 1)[0] if "_" in e.name else e.name
    parts = []
    if e.description_long:
        # Preserve paragraph breaks; collapse newlines within a paragraph
        # into spaces so the long desc reads as flowing prose.
        paragraphs = [p.replace("\n", " ").strip()
                      for p in e.description_long.split("\n\n")]
        for p in paragraphs:
            if p:
                parts.append(f'<p class="meta-long">{esc(p)}</p>')
    if e.depends:
        links = [_package_link(d, section_map, pkg_meta, rel, ubuntu_suite) for d in e.depends]
        parts.append(
            f'<p class="meta-deps"><span class="meta-deps-label">Depends:</span> '
            + ' <span class="meta-deps-sep">·</span> '.join(links) + '</p>'
        )
    if e.recommends:
        links = [_package_link(d, section_map, pkg_meta, rel, ubuntu_suite) for d in e.recommends]
        parts.append(
            f'<p class="meta-recommends"><span class="meta-deps-label">Recommends:</span> '
            + ' <span class="meta-deps-sep">·</span> '.join(links) + '</p>'
        )
    body = "\n".join(parts) or '<p class="meta-long meta-empty">No additional metadata.</p>'
    return (
        f'<tr class="meta-details" data-for="{esc(pkg_name)}" hidden>'
        f'<td class="meta-details-cell" colspan="{n_cols}">{body}</td>'
        f'</tr>'
    )

def render_table(rel: str, entries: list[Entry], show_arch: bool, show_hash: bool,
                 section_map: Optional[dict[str, str]] = None,
                 pkg_meta: Optional[dict[str, dict]] = None,
                 ubuntu_suite: str = "resolute",
                 repology_map: Optional[dict] = None,
                 changelog_map: Optional[dict] = None) -> str:
    parent = parent_of(rel)
    ndirs = sum(1 for e in entries if e.is_dir)
    nfiles = sum(1 for e in entries if not e.is_dir)
    arch_th = '<th scope="col" class="col-arch">Arch</th>' if show_arch else ""
    hash_th = '<th scope="col" class="col-hash">SHA-256</th>' if show_hash else ""
    parent_row = ""
    if parent is not None:
        parent_arch = '<td class="col-arch"></td>' if show_arch else ""
        parent_hash = '<td class="col-hash"></td>' if show_hash else ""
        parent_row = (
            f'<tr data-parent="1">'
            f'<td class="col-name"><a class="entry up" href="../">'
            f'<span class="icon">{ICONS["up"]}</span>'
            f'<span class="name">Parent directory</span></a></td>'
            f'{parent_arch}'
            f'<td class="col-mod"><span style="color:var(--color-on-surface-dim)">—</span></td>'
            f'<td class="col-size"><span style="color:var(--color-on-surface-dim)">—</span></td>'
            f'{parent_hash}'
            f'<td class="col-desc">Up to <code style="font-family:var(--font-mono)">{esc(parent)}</code></td>'
            f'</tr>'
        )
    # If at least one entry is a metapackage and at least one is not, split the
    # body into two sections with header rows. Otherwise render as one block.
    metas = [e for e in entries if e.is_metapackage]
    leaves = [e for e in entries if not e.is_metapackage]
    n_cols = 4 + (1 if show_arch else 0) + (1 if show_hash else 0)  # name + mod + size + desc + optional arch/hash
    sm = section_map or {}
    pm = pkg_meta or {}
    rm = repology_map or {}
    cm = changelog_map or {}

    def meta_row(e: Entry) -> str:
        return (
            render_row(e, rel, show_arch, show_hash, rm, cm)
            + render_meta_details_row(e, n_cols, sm, pm, rel, ubuntu_suite)
        )
    if metas and leaves:
        rows = (
            parent_row
            + render_section_header_row("Install this — umbrella metapackages", n_cols)
            + "".join(meta_row(e) for e in metas)
            + render_section_header_row("Constituent packages", n_cols)
            + "".join(render_row(e, rel, show_arch, show_hash, rm, cm) for e in leaves)
        )
    elif metas:
        rows = parent_row + "".join(meta_row(e) for e in metas)
    else:
        rows = parent_row + "".join(render_row(e, rel, show_arch, show_hash, rm, cm) for e in entries)
    return (
        f'<div class="listing-wrap">'
        f'<div class="listing-bar">'
        f'<span class="label">Index of {esc(rel)}</span>'
        f'<span class="count" data-count>'
        f'<b>{ndirs}</b> {"directory" if ndirs == 1 else "directories"}'
        f'<span style="color:var(--color-border)"> · </span>'
        f'<b>{nfiles}</b> {"file" if nfiles == 1 else "files"}'
        f'</span>'
        f'</div>'
        f'<table class="listing-table">'
        f'<thead><tr>'
        f'<th scope="col" class="col-name" data-sort="name">Name <span class="sort-ind"></span></th>'
        f'{arch_th}'
        f'<th scope="col" class="col-mod"  data-sort="mtime">Last modified <span class="sort-ind"></span></th>'
        f'<th scope="col" class="col-size" data-sort="size">Size <span class="sort-ind"></span></th>'
        f'{hash_th}'
        f'<th scope="col" class="col-desc">Description</th>'
        f'</tr></thead>'
        f'<tbody>{rows}</tbody>'
        f'</table>'
        f'</div>'
    )

def render_filter() -> str:
    return (
        '<div class="filter-bar">'
        '<label class="filter-label" for="filter-q"><span class="dim">[</span>filter<span class="dim">]</span></label>'
        '<input id="filter-q" class="filter-input" type="text" placeholder="type to filter — name or description" autocomplete="off" spellcheck="false">'
        '<button class="filter-clear" type="button" aria-label="Clear filter" hidden>×</button>'
        '</div>'
    )

def render_readme(cfg) -> str:
    return (
        '<section class="readme">'
        f'<div class="readme-head"><span class="square"></span>README · {esc(cfg.HOST)}</div>'
        '<div class="readme-body">'
        f'{cfg.README_HTML.strip()}'
        '</div>'
        '</section>'
    )

def render_footer(cfg, total_bytes_label: str) -> str:
    return (
        '<footer class="footer">'
        '<span class="left">'
        '<span class="square"></span>'
        f'<a href="https://{esc(cfg.HOST)}/">{esc(cfg.HOST)}</a>'
        '</span>'
        '<span class="right">'
        f'<span>{esc(total_bytes_label)} across {len(cfg.CODENAMES)} suites</span>'
        '<span class="pipe">|</span>'
        f'<a href="mailto:{esc(cfg.CONTACT_EMAIL)}">{esc(cfg.CONTACT_EMAIL)}</a>'
        '<span class="pipe">|</span>'
        '<a href="/key.gpg">key.gpg</a>'
        '<span class="pipe">|</span>'
        '<a href="/project/MIRRORS">mirrors</a>'
        '</span>'
        '</footer>'
    )

def render_page(rel: str, entries: list[Entry], cfg, do_sha256: bool, total_label: str,
                section_map: Optional[dict[str, str]] = None,
                pkg_meta: Optional[dict[str, dict]] = None,
                repology_map: Optional[dict] = None,
                changelog_map: Optional[dict] = None) -> str:
    is_root = rel == "/"
    depth = len(segments_of(rel))
    rel_prefix = "../" * depth  # "" at root, "../" at /dists/, "../../" at /dists/stable/, ...
    title = f"Index of {rel} — {cfg.HOST}"
    setup = render_setup_banner(cfg) if is_root else ""
    readme = render_readme(cfg) if is_root else ""
    lede_text = getattr(cfg, "LEDE_HTML", "").strip()
    lede = f'<p class="lede">{lede_text}</p>' if lede_text else ""
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(title)}</title>
<meta name="description" content="{esc(cfg.PAGE_DESCRIPTION)}">
<meta property="og:type"        content="website">
<meta property="og:url"         content="{esc(cfg.SCHEME)}://{esc(cfg.HOST)}{esc(rel)}">
<meta property="og:title"       content="{esc(title)}">
<meta property="og:description" content="{esc(cfg.PAGE_DESCRIPTION)}">
<meta name="twitter:card"       content="summary">
<meta name="color-scheme" content="dark">
<link rel="icon" type="image/svg+xml" href="{rel_prefix}favicon.svg">
<link rel="apple-touch-icon" href="{rel_prefix}apple-touch-icon.png">
<link rel="manifest" href="{rel_prefix}site.webmanifest">
<link rel="alternate" type="application/rss+xml" title="{esc(getattr(cfg, 'WORDMARK', cfg.HOST))} APT" href="/feed.xml">
<meta name="theme-color" content="#888888">
<!-- Theme tokens live in styles.css (:root). Edit there to recolour. -->
<style>html,body{{background:#111;color:#e8e8e8;margin:0}}</style>
<link rel="stylesheet" href="{rel_prefix}styles.css">
</head>
<body>
<header class="site-header">
  <div class="header-inner">
    <a href="/" class="wordmark">
      <span class="square"></span>
      <span>{esc(cfg.WORDMARK)}</span>
      <span class="subdomain">/ APT</span>
    </a>
    <a href="{esc(cfg.HOME_URL)}" class="nav-link">
      <img class="logo" src="{rel_prefix}logo.png" alt="" width="108" height="133">
      <span>{esc(cfg.HOME_LABEL)}</span>
    </a>
  </div>
</header>
<main class="page">
  <p class="section-label">Package Archive</p>
  {render_headline(rel)}
  {lede}
  {setup}
  {render_crumbs(rel, cfg)}
  {render_filter()}
  {render_table(rel, entries, show_arch=cfg.SHOW_ARCH, show_hash=do_sha256, section_map=section_map, pkg_meta=pkg_meta, ubuntu_suite=getattr(cfg, "UPSTREAM_UBUNTU_SUITE", "resolute"), repology_map=repology_map, changelog_map=changelog_map)}
  {readme}
  {render_footer(cfg, total_label)}
</main>
<script src="{rel_prefix}index.js" defer></script>
</body>
</html>
"""

# ─── walking ───────────────────────────────────────────────────────────
def walk_rel(root: Path) -> Iterable[str]:
    """Yield every directory path under root as a URL-style rel ('/', '/dists/', ...)"""
    yield "/"
    for dirpath, dirnames, _ in os.walk(root):
        # stable order
        dirnames.sort()
        rel_root = Path(dirpath).relative_to(root)
        for d in list(dirnames):
            full = rel_root / d
            yield "/" + str(full).replace(os.sep, "/") + "/"

# ─── main ──────────────────────────────────────────────────────────────
def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description="Generate static index.html files for an apt repository tree.")
    ap.add_argument("--root", required=True, type=Path, help="Source tree (e.g. /srv/apt)")
    ap.add_argument("--out",  required=True, type=Path, help="Output dir (e.g. /var/www/apt.example.org)")
    ap.add_argument("--static", required=True, type=Path, help="Static assets dir (styles.css, index.js)")
    ap.add_argument("--config", required=True, type=Path, help="Python config module path")
    ap.add_argument("--sha256", action="store_true", help="Compute & show SHA-256 column (slow; cached)")
    ap.add_argument("--quiet",  action="store_true")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args(argv)

    logging.basicConfig(
        level=logging.WARNING if args.quiet else logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
    )
    logger = logging.getLogger("gen-index")

    cfg = load_config(args.config)
    args.out.mkdir(parents=True, exist_ok=True)

    # copy static assets
    if not args.dry_run:
        for p in args.static.glob("*"):
            shutil.copy2(p, args.out / p.name)
            logger.info("static: %s -> %s", p, args.out / p.name)

    cache_path = args.out / ".sha256cache"
    cache = HashCache(cache_path) if args.sha256 else None

    # total size for footer
    total = 0
    for dp, _, fs in os.walk(args.root):
        for f in fs:
            try:
                total += (Path(dp) / f).stat().st_size
            except OSError:
                pass
    total_label = fmt_size(total)

    descriptions = getattr(cfg, "DESCRIPTIONS", {})

    # Decide whether to flatten /pool/<component>/ listings. Counted once,
    # applied uniformly to every component on this run. Threshold is
    # configurable per-repo via cfg.FLAT_POOL_THRESHOLD; default = 30 .debs.
    # Set 0 to always shard (Debian Policy §2.4 default); set huge to always
    # flatten. The on-disk layout is unchanged either way — only the HTML.
    flat_pool_threshold = getattr(cfg, "FLAT_POOL_THRESHOLD", 30)
    pool_root = args.root / "pool"
    total_debs = 0
    if pool_root.is_dir():
        for dirpath, _, filenames in os.walk(pool_root):
            total_debs += sum(1 for f in filenames if f.endswith(".deb"))
    flat_pool_mode = 0 < flat_pool_threshold and total_debs < flat_pool_threshold
    logger.info("pool .deb count: %d; flat-pool threshold: %d; flat mode: %s",
                total_debs, flat_pool_threshold, flat_pool_mode)
    # Regex for paths like "/pool/main/" — exactly one segment past /pool/.
    pool_component_re = re.compile(r"^/pool/[^/]+/$")
    # Section: <foo> per package name, used to surface metapackages
    # ("Section: metapackages") with a META chip + sectioned table layout.
    # Always loaded — also powers packages.json / feed.xml generation.
    pkg_meta = load_package_metadata(args.root)
    section_map = {k: v["section"] for k, v in pkg_meta.items()}
    if flat_pool_mode:
        n_meta = sum(1 for s in section_map.values() if s == "metapackages")
        logger.info("section map: %d total packages; %d metapackages",
                    len(section_map), n_meta)

    repology_map  = getattr(cfg, "REPOLOGY_PROJECTS",  {}) or {}
    changelog_map = getattr(cfg, "CHANGELOG_ENTRIES",  {}) or {}

    n = 0
    for rel in walk_rel(args.root):
        if flat_pool_mode and pool_component_re.match(rel):
            entries = flat_pool_scan(args.root, rel, descriptions, args.sha256, cache, logger,
                                     section_map=section_map, pkg_meta=pkg_meta)
        else:
            entries = scan(args.root, rel, descriptions, args.sha256, cache, logger)
        html = render_page(rel, entries, cfg, args.sha256, total_label,
                           section_map=section_map, pkg_meta=pkg_meta,
                           repology_map=repology_map, changelog_map=changelog_map)
        out_path = args.out / rel.strip("/") / "index.html" if rel != "/" else args.out / "index.html"
        if args.dry_run:
            logger.info("would write %s (%d entries)", out_path, len(entries))
        else:
            out_path.parent.mkdir(parents=True, exist_ok=True)
            out_path.write_text(html, encoding="utf-8")
            logger.info("wrote %s (%d entries)", out_path, len(entries))
        n += 1

    if cache:
        cache.save()
    logger.info("done — %d index.html files", n)

    # packages.json — machine-readable package index
    # feed.xml — RSS 2.0 feed (one item per package, pubDate from .deb mtime)
    if not args.dry_run and pkg_meta:
        from email.utils import formatdate as _rfc2822
        generated_iso = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        site_url = f"{cfg.SCHEME}://{cfg.HOST}"
        suite = getattr(cfg, "DEFAULT_SUITE", "stable")
        wordmark = getattr(cfg, "WORDMARK", cfg.HOST)

        pkg_list = []
        for pkg_name in sorted(pkg_meta.keys()):
            m_data = pkg_meta[pkg_name]
            fname = m_data.get("filename", "")
            basename = fname.rsplit("/", 1)[-1] if "/" in fname else fname
            deb_m = DEB_RE.match(basename)
            pkg_list.append({
                "name":             pkg_name,
                "version":          deb_m.group("ver")  if deb_m else "",
                "architecture":     deb_m.group("arch") if deb_m else "",
                "section":          m_data.get("section", ""),
                "description_short": m_data.get("description_short", ""),
                "description_long": m_data.get("description_long", ""),
                "depends":          m_data.get("depends", []),
                "deb_url":          "/" + fname if fname else "",
            })

        (args.out / "packages.json").write_text(
            json.dumps({"generated": generated_iso, "suite": suite,
                        "count": len(pkg_list), "packages": pkg_list}, indent=2)
        )
        logger.info("wrote packages.json (%d packages)", len(pkg_list))

        items: list[str] = []
        for p in pkg_list:
            link = site_url + (p["deb_url"] or "/")
            cl = (changelog_map or {}).get(p["name"], "")
            desc_parts = [esc(p.get("description_short", ""))]
            if cl:
                desc_parts.append(esc(cl))
            pub_date = _rfc2822(usegmt=True)
            if p["deb_url"]:
                try:
                    pub_date = _rfc2822((args.root / p["deb_url"].lstrip("/")).stat().st_mtime, usegmt=True)
                except OSError:
                    pass
            items.append(
                f"    <item>\n"
                f"      <title>{esc(p['name'] + ' ' + p['version'])}</title>\n"
                f"      <link>{esc(link)}</link>\n"
                f"      <guid isPermaLink=\"false\">{esc(p['name'] + '@' + p['version'])}</guid>\n"
                f"      <pubDate>{pub_date}</pubDate>\n"
                f"      <description>{' — '.join(desc_parts)}</description>\n"
                f"    </item>"
            )

        feed = (
            '<?xml version="1.0" encoding="UTF-8"?>\n'
            '<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom">\n'
            '  <channel>\n'
            f'    <title>{esc(wordmark + " APT Repository")}</title>\n'
            f'    <link>{esc(site_url)}</link>\n'
            f'    <description>{esc(cfg.PAGE_DESCRIPTION)}</description>\n'
            '    <language>en-us</language>\n'
            f'    <atom:link href="{esc(site_url + "/feed.xml")}" rel="self" type="application/rss+xml"/>\n'
            + "\n".join(items) + "\n"
            '  </channel>\n'
            '</rss>\n'
        )
        (args.out / "feed.xml").write_text(feed)
        logger.info("wrote feed.xml (%d items)", len(items))

    return 0

if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
