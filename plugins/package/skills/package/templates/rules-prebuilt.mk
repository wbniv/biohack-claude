#!/usr/bin/make -f
# Pre-built binary upstream — no source compilation.
# Pattern used for upstreams that distribute a pre-built archive (zip, tar.gz)
# rather than source. Replace <NAME> with the Debian package name and
# <INSTALL_DIRS> with the top-level dirs/files to copy from the upstream tree.
# See ~/.claude/skills/package/SKILL.md Step 3 §4 for the full explanation of
# the permission-dance sequence.
export DEB_BUILD_MAINT_OPTIONS = hardening=+all

%:
	dh $@

override_dh_auto_configure:
	# pre-built upstream distribution — no configure step

override_dh_auto_build:
	# pre-built upstream distribution — no build step

override_dh_auto_test:
	# no test suite in the binary distribution

override_dh_auto_install:
	install -d $(CURDIR)/debian/<NAME>/usr/lib/<NAME>
	install -d $(CURDIR)/debian/<NAME>/usr/bin
	# Copy the upstream distribution tree. Enumerate top-level items explicitly
	# to exclude the debian/ overlay directory.
	for item in <INSTALL_DIRS>; do \
	    if [ -e "$(CURDIR)/$$item" ]; then \
	        cp -a "$(CURDIR)/$$item" $(CURDIR)/debian/<NAME>/usr/lib/<NAME>/; \
	    fi; \
	done
	# Strip +x from all files (upstream zips often mark everything executable).
	find $(CURDIR)/debian/<NAME>/usr/lib/<NAME> -type f -exec chmod 644 {} +
	# Restore +x to ELF binaries.
	find $(CURDIR)/debian/<NAME>/usr/lib/<NAME> -type f -print0 \
	    | xargs -0 file \
	    | grep ": ELF " \
	    | cut -d: -f1 \
	    | xargs -r chmod 755
	# Restore +x to shebanged scripts — check ONLY the first 2 bytes to avoid
	# false matches on binary files (.whl, .tar.gz) that contain "#!" internally.
	find $(CURDIR)/debian/<NAME>/usr/lib/<NAME> -type f -print0 \
	    | xargs -0 -I{} sh -c \
	      'head -c 2 "$$1" | grep -qF "#!" && chmod 755 "$$1" || true' -- {}
	# Install launchers in /usr/bin as symlinks into /usr/lib/<NAME>/.
	# Adjust paths to match the upstream's actual launcher scripts/binaries.
	ln -s /usr/lib/<NAME>/<LAUNCHER_SCRIPT> \
	    $(CURDIR)/debian/<NAME>/usr/bin/<NAME>
	# ln -s /usr/lib/<NAME>/<HEADLESS_BINARY> \
	#     $(CURDIR)/debian/<NAME>/usr/bin/<NAME>-headless

override_dh_fixperms:
	dh_fixperms
	# dh_fixperms only actively sets +x in standard binary dirs (/usr/bin, etc.).
	# Files in /usr/lib/<NAME>/ that had +x stripped by dh_fixperms must be
	# restored here — re-run the same ELF and shebang detection passes.
	find $(CURDIR)/debian/<NAME>/usr/lib/<NAME> -type f -print0 \
	    | xargs -0 file \
	    | grep ": ELF " \
	    | cut -d: -f1 \
	    | xargs -r chmod 755
	find $(CURDIR)/debian/<NAME>/usr/lib/<NAME> -type f -print0 \
	    | xargs -0 -I{} sh -c \
	      'head -c 2 "$$1" | grep -qF "#!" && chmod 755 "$$1" || true' -- {}

override_dh_strip:
	dh_strip
	# dh_strip calls objcopy --add-gnu-debuglink which resets permissions on ELF
	# files it touches — this runs AFTER override_dh_fixperms. Restore +x here
	# as the final step that touches binary content, before dh_md5sums.
	# Exclude .so files — shared libraries MUST be 0644 (Debian Policy §8.1).
	find $(CURDIR)/debian/<NAME>/usr/lib/<NAME> -type f \
	    ! -name "*.so" ! -name "*.so.*" \
	    -exec sh -c 'file "$$1" | grep -q ": ELF " && chmod 755 "$$1" || true' \
	    sh {} \;

override_dh_compress:
	# Do not compress JARs or other already-compressed files in the tree.
	dh_compress -X.jar -X.zip -X.gz

override_dh_shlibdeps:
	# Scan native ELF binaries; suppress warnings for sonames resolved from
	# non-system libraries (e.g. JARs) that dpkg-shlibdeps can't find.
	dh_shlibdeps --dpkg-shlibdeps-params=--ignore-missing-info
