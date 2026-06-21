#!/usr/bin/env sh
set -eu

PATH=/usr/bin:/bin
export PATH
unset MAKEFILES MAKEFILE_LIST MAKEFLAGS MFLAGS MAKEOVERRIDES PYTHON ROOT SHELL

ROOT_DIR=$(CDPATH='' cd -- "$(dirname -- "$0")/.." && /bin/pwd -P)
TEMP_ROOT=$(mktemp -d "${TMPDIR:-/tmp}/transcribe-make-boundary-XXXXXX")
trap 'rm -rf "$TEMP_ROOT"' EXIT HUP INT TERM

require_text() {
  file=$1
  text=$2
  if ! /usr/bin/grep -Fq "$text" "$ROOT_DIR/$file"; then
    /usr/bin/printf '%s\n' "$file must document Make boundary: $text" >&2
    exit 1
  fi
}

require_absent_text() {
  file=$1
  text=$2
  if /usr/bin/grep -Fq "$text" "$ROOT_DIR/$file"; then
    /usr/bin/printf '%s\n' "$file still overclaims Make boundary: $text" >&2
    exit 1
  fi
}

require_text "README.md" "Caller-supplied \`MAKEFILES\`, extra \`-f\` files, target-specific variables, shell overrides, and replaced public-target recipes are outside the local Make trust boundary."
require_text "README.md" "\`python3\` is resolved from the caller's \`PATH\` unless \`PYTHON=/absolute/path\` is supplied."
require_text "docs/plans/2026-06-21-make-authority-isolation.md" "Startup makefiles can execute while GNU Make is parsing, before the repository Makefile can reject them."
require_text "CHANGES.md" "Narrowed Make authority claims to the sole checked-in Makefile path; caller-supplied makefiles, recipe replacements, target-specific shell overrides, and PATH-shadowed Python remain outside that boundary."
require_absent_text "README.md" "isolated Make startup, shell, trusted-Python, and target authority across every gate"
require_absent_text "CHANGES.md" "Isolated Make verification authority from caller-controlled roots, shells, startup files"

CONTROL_DIR="$TEMP_ROOT/control"
CHECKOUT="$TEMP_ROOT/transcribe boundary repo"
ATTACKER_ROOT="$TEMP_ROOT/attacker"
MARKERS="$TEMP_ROOT/markers"
MAKEFILE="$CHECKOUT/Makefile"
/bin/mkdir -p "$CONTROL_DIR" "$CHECKOUT" "$ATTACKER_ROOT/scripts" "$MARKERS"
/bin/cp "$ROOT_DIR/Makefile" "$MAKEFILE"

for script in test-makefile-root.sh test-makefile-boundary.sh; do
cat >"$ATTACKER_ROOT/scripts/$script" <<EOF
#!/bin/sh
/usr/bin/touch "$MARKERS/attacker-root-script"
exit 0
EOF
/bin/chmod +x "$ATTACKER_ROOT/scripts/$script"
done

FAKE_PYTHON="$TEMP_ROOT/fake-python"
cat >"$FAKE_PYTHON" <<EOF
#!/bin/sh
/usr/bin/printf '%s\n' "\$*" >> "$MARKERS/fake-python.log"
/usr/bin/touch "$MARKERS/fake-python"
exit 0
EOF
/bin/chmod +x "$FAKE_PYTHON"

FAKE_SHELL="$TEMP_ROOT/fake-shell"
cat >"$FAKE_SHELL" <<EOF
#!/bin/sh
/usr/bin/printf '%s\n' ok
/usr/bin/printf '%s\n' "\$*" >> "$MARKERS/fake-shell.log"
/usr/bin/touch "$MARKERS/fake-shell"
exit 0
EOF
/bin/chmod +x "$FAKE_SHELL"

LATER_ROOT="$TEMP_ROOT/later-root.mk"
cat >"$LATER_ROOT" <<EOF
audit build check format lint root-test test verify: MAKEFILE_LIST := $MAKEFILE
audit build check format lint root-test test verify: ROOT := $ATTACKER_ROOT
audit build check format lint root-test test verify: PYTHON := $FAKE_PYTHON
EOF

(cd "$CONTROL_DIR" && /usr/bin/make --no-print-directory -f "$MAKEFILE" -f "$LATER_ROOT" check) >/dev/null 2>&1
[ -e "$MARKERS/fake-python" ]
[ -e "$MARKERS/attacker-root-script" ]

/bin/rm -f "$MARKERS/fake-shell" "$MARKERS/fake-shell.log"
LATER_SHELL="$TEMP_ROOT/later-shell.mk"
cat >"$LATER_SHELL" <<EOF
audit build check format lint root-test test verify: MAKEFILE_LIST := $MAKEFILE
audit build check format lint root-test test verify: SHELL := $FAKE_SHELL
audit build check format lint root-test test verify: .SHELLFLAGS := -c
EOF
(cd "$CONTROL_DIR" && /usr/bin/make --no-print-directory -f "$MAKEFILE" -f "$LATER_SHELL" check) >/dev/null 2>&1
[ -e "$MARKERS/fake-shell" ]

/bin/rm -f "$MARKERS/fake-shell" "$MARKERS/fake-shell.log"
LATER_OVERRIDE_SHELL="$TEMP_ROOT/later-override-shell.mk"
cat >"$LATER_OVERRIDE_SHELL" <<EOF
override SHELL := $FAKE_SHELL
override .SHELLFLAGS := -c
audit build check format lint root-test test verify: MAKEFILE_LIST := $MAKEFILE
EOF
(cd "$CONTROL_DIR" && /usr/bin/make --no-print-directory -f "$MAKEFILE" -f "$LATER_OVERRIDE_SHELL" check) >/dev/null 2>&1
[ -e "$MARKERS/fake-shell" ]

LATER_RECIPES="$TEMP_ROOT/later-recipes.mk"
/usr/bin/printf '%s\n' "audit build check format lint root-test test verify: MAKEFILE_LIST := $MAKEFILE" >"$LATER_RECIPES"
for target in audit build check format lint root-test test verify; do
  /usr/bin/printf '%s\n' "$target:" >>"$LATER_RECIPES"
  /usr/bin/printf '\t%s\n' "@/usr/bin/touch '$MARKERS/replaced-$target'" >>"$LATER_RECIPES"
done
for target in audit build check format lint root-test test verify; do
  /bin/rm -f "$MARKERS/replaced-$target"
  (cd "$CONTROL_DIR" && /usr/bin/make --no-print-directory -f "$MAKEFILE" -f "$LATER_RECIPES" "$target") >/dev/null 2>&1
  [ -e "$MARKERS/replaced-$target" ]
done

FAKE_BIN="$TEMP_ROOT/fake-bin"
/bin/mkdir -p "$FAKE_BIN"
/bin/cp "$FAKE_PYTHON" "$FAKE_BIN/python3"
/bin/chmod +x "$FAKE_BIN/python3"
/bin/rm -f "$MARKERS/fake-python"
(cd "$CONTROL_DIR" && PATH="$FAKE_BIN:/usr/bin:/bin" /usr/bin/make --no-print-directory -f "$MAKEFILE" lint) >/dev/null 2>&1
[ -e "$MARKERS/fake-python" ]

/usr/bin/printf '%s\n' "Make boundary documentation checks passed: documented later -f, target-specific variable, shell, recipe-replacement, PATH-shadowed python3, and startup parse boundaries"
