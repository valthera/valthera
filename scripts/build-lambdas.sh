#!/bin/bash
set -e

echo "🔧 Setting up Valthera Core Layer..."

# Ensure layer directory structure exists
mkdir -p lambdas/shared/valthera-core-layer/python

# Prefer in-repo source for the layer. If missing, fall back to wheel.
if [ -d lambdas/shared/valthera-core-layer/python/valthera_core ]; then
  echo "📁 Using in-repo valthera_core source for the layer"
  # Remove any previous dist-info from wheel extractions
  rm -rf lambdas/shared/valthera-core-layer/python/valthera_core-*.dist-info
else
  echo "📦 In-repo source not found; falling back to wheel extraction"
  WHEEL=$(ls lambdas/wheels/valthera_core-*.whl | head -n 1)
  if [ -z "$WHEEL" ]; then
    echo "❌ No valthera_core wheel found at lambdas/wheels. Aborting."
    exit 1
  fi
  echo "📦 Extracting $WHEEL into layer..."
  (cd lambdas/shared/valthera-core-layer/python && unzip -q ../../../wheels/valthera_core-*.whl)
  rm -rf lambdas/shared/valthera-core-layer/python/valthera_core-*.dist-info
fi

echo "✅ Layer setup complete!"

# Install dependencies for each lambda function
echo "📦 Installing dependencies for Lambda functions..."

for req_file in $(find lambdas/functions -name "requirements.txt"); do
    func_dir=$(dirname "$req_file")
    echo "Installing dependencies for $func_dir"
    venv_dir="$func_dir/.venv"
    mkdir -p "$venv_dir"
    pip install -r "$req_file" -t "$venv_dir"
done

echo "🚀 Building SAM application..."
sam build --template template.yaml

echo "✅ Build complete! You can now deploy with: sam deploy --guided"
