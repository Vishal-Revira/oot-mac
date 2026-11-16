#!/bin/bash
# Gets nxnative at the commit these patches were made on and applies them.
# Usage: ./setup.sh [folder]      (default: ./nxnative next to this script)
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
DEST="${1:-$HERE/nxnative}"
COMMIT=a0cad7e06a0821c52477ff20dbc53d6126748c54   # nxnative main, 16 Nov 2026

if [ ! -d "$DEST/.git" ]; then
  git clone https://github.com/seedds/nxnative.git "$DEST"
fi
cd "$DEST"
git fetch -q origin "$COMMIT" 2>/dev/null || git fetch -q origin
git -c advice.detachedHead=false checkout -q "$COMMIT"

for p in "$HERE"/patches/*.patch; do
  if git apply --reverse --check "$p" 2>/dev/null; then
    echo "already applied: $(basename "$p")"
  else
    git apply "$p"
    echo "applied: $(basename "$p")"
  fi
done

echo
echo "nxnative is ready in $DEST (commit ${COMMIT:0:8} with the patches)."
echo "Next: build the app, as in the README's step 4."
