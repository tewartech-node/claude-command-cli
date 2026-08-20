#!/usr/bin/env bash
# Install the curriculum as a git pre-commit gate.
#
#   ./scripts/install-curriculum-hook.sh          # install
#   ./scripts/install-curriculum-hook.sh --remove # uninstall
#
# The hook runs `warnetech-curriculum preflight` over the files the commit is
# about to take. A critical finding -- an import, symbol or attribute that
# provably does not exist -- stops the commit. Everything else is printed and
# allowed through.
#
# Termux-safe: pure stdlib Python, no network. If the curriculum is not
# installed the hook gets out of the way rather than blocking your commit.
#
# Escape hatch, for when you genuinely need it:  git commit --no-verify

set -eu

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
HOOK="$REPO_ROOT/.git/hooks/pre-commit"

if [ ! -d "$REPO_ROOT/.git" ]; then
  echo "error: $REPO_ROOT is not a git checkout" >&2
  exit 1
fi

if [ "${1:-}" = "--remove" ]; then
  if [ -f "$HOOK" ] && grep -q "warnetech-curriculum" "$HOOK" 2>/dev/null; then
    rm -f "$HOOK"
    echo "removed the curriculum pre-commit hook"
  else
    echo "no curriculum hook installed; nothing to remove"
  fi
  exit 0
fi

if [ -f "$HOOK" ] && ! grep -q "warnetech-curriculum" "$HOOK" 2>/dev/null; then
  echo "error: a different pre-commit hook already exists at $HOOK" >&2
  echo "       move it aside first -- refusing to overwrite someone else's hook" >&2
  exit 1
fi

mkdir -p "$(dirname "$HOOK")"
cat > "$HOOK" <<'HOOKEOF'
#!/usr/bin/env sh
# Installed by scripts/install-curriculum-hook.sh -- see docs/10_CURRICULUM.md
if command -v warnetech-curriculum >/dev/null 2>&1; then
  warnetech-curriculum preflight || exit 1
elif python -c "import warnetech_curriculum" >/dev/null 2>&1; then
  python -m warnetech_curriculum preflight || exit 1
fi
exit 0
HOOKEOF
chmod +x "$HOOK"

echo "installed $HOOK"
echo "  the curriculum now checks every commit before it is written"
echo "  bypass once with: git commit --no-verify"
