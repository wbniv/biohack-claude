---
name: feedback-build-in-containers
description: "Always build and test Debian packages in Docker containers, never on the host system. Host deps silently satisfy Build-Depends and mask CI failures."
metadata: 
  node_type: memory
  type: feedback
  originSessionId: d30348d6-f04d-45e5-a17a-ecfd63c41138
---

Always build (dpkg-buildpackage) and verify (lintian, smoke install) Debian packages inside a fresh `ubuntu:26.04` Docker container — never on the host system.

**Why:** Host packages can silently satisfy `Build-Depends:` entries that aren't declared in `debian/control`. The package then builds fine locally but breaks in CI (which starts from a clean container). This happened with vgmstream — several codec dev libs were already installed on the host and masked missing Build-Depends.

**How to apply:** In every `/package` run, when suggesting or running a build, always wrap `dpkg-buildpackage` in `docker run --rm -v "$REPO_ROOT:/repo" ubuntu:26.04 bash -c '... apt-get install <deps> && bash packages/<name>/build.sh'`. Never run the build directly in the host shell.
