// index.js — progressive enhancement for the static index pages.
//
// The page is fully functional without JS (links work, the table is sorted
// server-side, the setup snippet is visible). This script layers on:
//   - sticky header shrink-on-scroll
//   - filter box (hides non-matching rows; updates count)
//   - sortable columns (Name / Last modified / Size)
//   - setup-banner tab switching + copy button
//
// No dependencies. Safe to inline if you want one fewer round-trip.

(function () {
  "use strict";

  // ── header shrink-on-scroll ─────────────────────────────────────────
  function bindHeader() {
    var html = document.documentElement;
    function update() {
      html.setAttribute("data-shrink", (window.scrollY || 0) > 32 ? "1" : "0");
    }
    window.addEventListener("scroll", update, { passive: true });
    update();
  }

  // ── setup banner tabs + copy ────────────────────────────────────────
  function bindSetupBanner() {
    var banner = document.querySelector(".setup");
    if (!banner) return;

    var tabs  = banner.querySelectorAll(".setup-tab");
    var panes = banner.querySelectorAll(".setup-pane");
    var target = banner.querySelector("[data-file-target]");

    tabs.forEach(function (btn) {
      btn.addEventListener("click", function () {
        var id = btn.getAttribute("data-tab");
        tabs.forEach(function (b) {
          b.setAttribute("aria-selected", b === btn ? "true" : "false");
        });
        panes.forEach(function (p) {
          var match = p.getAttribute("data-tab") === id;
          p.hidden = !match;
          if (match && target) {
            var t = p.getAttribute("data-target");
            if (t) target.textContent = t;
          }
        });
      });
    });

    banner.querySelectorAll("[data-copy]").forEach(function (btn) {
      btn.addEventListener("click", function () {
        var pane = btn.closest(".setup-pane");
        var code = pane && pane.querySelector("pre code");
        if (!code) return;
        var text = code.textContent || "";
        var done = function () {
          btn.setAttribute("data-copied", "1");
          var prev = btn.textContent;
          btn.textContent = "Copied";
          setTimeout(function () {
            btn.removeAttribute("data-copied");
            btn.textContent = prev;
          }, 1400);
        };
        if (navigator.clipboard && navigator.clipboard.writeText) {
          navigator.clipboard.writeText(text).then(done).catch(function () {
            fallbackCopy(text); done();
          });
        } else {
          fallbackCopy(text); done();
        }
      });
    });

    function fallbackCopy(text) {
      var ta = document.createElement("textarea");
      ta.value = text;
      ta.setAttribute("readonly", "");
      ta.style.position = "fixed";
      ta.style.opacity = "0";
      document.body.appendChild(ta);
      ta.select();
      try { document.execCommand("copy"); } catch (e) {}
      document.body.removeChild(ta);
    }
  }

  // ── filter ──────────────────────────────────────────────────────────
  function bindFilter() {
    var input  = document.getElementById("filter-q");
    var clear  = document.querySelector(".filter-clear");
    var table  = document.querySelector(".listing-table");
    var count  = document.querySelector("[data-count]");
    if (!input || !table || !count) return;

    var tbody = table.querySelector("tbody");
    var rows  = Array.prototype.slice.call(tbody.querySelectorAll("tr"));
    var dataRows = rows.filter(function (r) { return !r.hasAttribute("data-parent"); });
    var origCountHTML = count.innerHTML;

    function apply() {
      var q = (input.value || "").trim().toLowerCase();
      var dirs = 0, files = 0;
      dataRows.forEach(function (r) {
        var name = r.getAttribute("data-name") || "";
        var desc = r.getAttribute("data-desc") || "";
        var match = !q || name.indexOf(q) !== -1 || desc.indexOf(q) !== -1;
        r.hidden = !match;
        if (match) {
          if (r.getAttribute("data-is-dir") === "1") dirs++;
          else files++;
        }
      });
      if (clear) clear.hidden = !q;
      if (q) {
        count.innerHTML =
          "<b>" + dirs + "</b> " + (dirs === 1 ? "directory" : "directories") +
          '<span style="color:var(--color-border)"> · </span>' +
          "<b>" + files + "</b> " + (files === 1 ? "file" : "files") +
          ' · <span style="color:var(--color-accent)">filtered "' + escapeHtml(q) + '"</span>';
      } else {
        count.innerHTML = origCountHTML;
      }
    }

    input.addEventListener("input", apply);
    if (clear) {
      clear.addEventListener("click", function () {
        input.value = "";
        input.focus();
        apply();
      });
    }
  }

  function escapeHtml(s) {
    return String(s).replace(/[&<>"']/g, function (c) {
      return ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"})[c];
    });
  }

  // ── column sort ─────────────────────────────────────────────────────
  function bindSort() {
    var table = document.querySelector(".listing-table");
    if (!table) return;
    var tbody = table.querySelector("tbody");
    var ths   = table.querySelectorAll("thead th[data-sort]");

    var state = { key: "name", dir: "asc" };

    function setIndicators() {
      ths.forEach(function (th) {
        var ind = th.querySelector(".sort-ind");
        if (!ind) return;
        if (th.getAttribute("data-sort") === state.key) {
          ind.textContent = state.dir === "asc" ? "▲" : "▼";
          ind.style.color = "var(--color-accent)";
        } else {
          ind.textContent = "↕";
          ind.style.color = "var(--color-on-surface-dim)";
        }
      });
    }

    function sortRows() {
      var parentRow = tbody.querySelector("tr[data-parent]");
      var rows = Array.prototype.slice.call(tbody.querySelectorAll("tr"))
        .filter(function (r) { return !r.hasAttribute("data-parent"); });
      var key = state.key, dir = state.dir === "asc" ? 1 : -1;

      rows.sort(function (a, b) {
        // directories always before files
        var ad = a.getAttribute("data-is-dir") === "1";
        var bd = b.getAttribute("data-is-dir") === "1";
        if (ad !== bd) return ad ? -1 : 1;

        var av, bv;
        if (key === "size") {
          av = parseInt(a.getAttribute("data-size")  || "0", 10);
          bv = parseInt(b.getAttribute("data-size")  || "0", 10);
        } else if (key === "mtime") {
          av = parseInt(a.getAttribute("data-mtime") || "0", 10);
          bv = parseInt(b.getAttribute("data-mtime") || "0", 10);
        } else {
          av = a.getAttribute("data-name") || "";
          bv = b.getAttribute("data-name") || "";
        }
        if (av < bv) return -1 * dir;
        if (av > bv) return  1 * dir;
        return 0;
      });

      var frag = document.createDocumentFragment();
      if (parentRow) frag.appendChild(parentRow);
      rows.forEach(function (r) { frag.appendChild(r); });
      tbody.appendChild(frag); // moves the rows (no duplication, no re-render)
    }

    ths.forEach(function (th) {
      th.style.cursor = "pointer";
      th.addEventListener("click", function () {
        var key = th.getAttribute("data-sort");
        if (state.key === key) {
          state.dir = state.dir === "asc" ? "desc" : "asc";
        } else {
          state.key = key;
          state.dir = key === "name" ? "asc" : "desc";
        }
        setIndicators();
        sortRows();
      });
    });

    setIndicators();
  }

  // ── go ──────────────────────────────────────────────────────────────
  function ready(fn) {
    if (document.readyState !== "loading") fn();
    else document.addEventListener("DOMContentLoaded", fn);
  }
  // ── metapackage expand/collapse ─────────────────────────────────────
  // Click a tr.meta-row to toggle the immediately-following tr.meta-details
  // row's `hidden` attribute. Pure data lookup via data-meta-pkg attribute on
  // the row + data-for attribute on the details row.
  function bindMetaExpand() {
    var metaRows = document.querySelectorAll("tr.meta-row");
    metaRows.forEach(function (row) {
      // a11y: make the row keyboard-focusable and announce its toggle role.
      row.setAttribute("role", "button");
      row.setAttribute("tabindex", "0");
      row.setAttribute("aria-expanded", "false");

      function toggle() {
        var pkg = row.getAttribute("data-meta-pkg");
        if (!pkg) return;
        var details = document.querySelector('tr.meta-details[data-for="' + pkg + '"]');
        if (!details) return;
        var willOpen = details.hasAttribute("hidden");
        if (willOpen) {
          details.removeAttribute("hidden");
          row.classList.add("is-expanded");
          row.setAttribute("aria-expanded", "true");
        } else {
          details.setAttribute("hidden", "");
          row.classList.remove("is-expanded");
          row.setAttribute("aria-expanded", "false");
        }
      }

      row.addEventListener("click", function (e) {
        // Don't intercept clicks on the actual <a> in the name cell —
        // let those navigate to the .deb file as normal.
        if (e.target.closest("a")) return;
        toggle();
      });
      row.addEventListener("keydown", function (e) {
        if (e.key === "Enter" || e.key === " ") {
          if (e.target.closest("a")) return;
          e.preventDefault();
          toggle();
        }
      });
    });
  }

  ready(function () {
    bindHeader();
    bindSetupBanner();
    bindFilter();
    bindSort();
    bindMetaExpand();
  });
})();
