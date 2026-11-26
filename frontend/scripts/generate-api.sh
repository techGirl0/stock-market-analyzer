#!/usr/bin/env bash
# Exports the FastAPI OpenAPI spec and regenerates the TypeScript types.
# Run from the frontend/ directory: bash scripts/generate-api.sh
#
# Requirements:
#   - Python 3.13 with the backend dependencies installed (pip install -r ../backend/requirements.txt)
#   - npm packages installed (npm install)

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
FRONTEND_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
BACKEND_DIR="$(cd "$FRONTEND_DIR/../backend" && pwd)"
SPEC_FILE="$FRONTEND_DIR/openapi.json"

echo "→ Exporting OpenAPI spec from FastAPI..."
PYTHONPATH="$BACKEND_DIR" python3 -c "
from app.main import app
import json
with open('$SPEC_FILE', 'w') as f:
    json.dump(app.openapi(), f, indent=2)
print('  Saved to $SPEC_FILE')
"

echo "→ Generating TypeScript types..."
cd "$FRONTEND_DIR"
npx openapi-typescript "$SPEC_FILE" -o src/lib/api/generated/schema.d.ts

echo "✓ Done. Commit openapi.json and src/lib/api/generated/schema.d.ts."
