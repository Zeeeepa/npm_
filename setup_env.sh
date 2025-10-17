#!/bin/bash
# Setup script for NPM Discovery

echo "🚀 Setting up NPM Discovery..."

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    echo "📝 Creating .env file..."
    cat > .env << EOF
# Libraries.io API Key (Required)
# Get your free API key at: https://libraries.io/account
LIBRARIES_IO_API_KEY=

# Optional Configuration
NPM_REGISTRY_URL=https://registry.npmjs.org
UNPKG_URL=https://unpkg.com
CACHE_TTL_DAYS=7
MAX_CONCURRENT_REQUESTS=40
REQUEST_TIMEOUT=30
EOF
    echo "✅ Created .env file"
    echo "⚠️  Please edit .env and add your LIBRARIES_IO_API_KEY"
else
    echo "✅ .env file already exists"
fi

# Check Python version
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed"
    exit 1
fi

PYTHON_VERSION=$(python3 --version | cut -d' ' -f2 | cut -d'.' -f1,2)
echo "✅ Python version: $PYTHON_VERSION"

# Install dependencies
echo "📦 Installing dependencies..."
if command -v uv &> /dev/null; then
    echo "Using uv..."
    uv pip install -r requirements.txt
else
    echo "Using pip..."
    python3 -m pip install -r requirements.txt
fi

echo ""
echo "✅ Setup complete!"
echo ""
echo "📚 Quick Start:"
echo "  1. Edit .env and add your LIBRARIES_IO_API_KEY"
echo "  2. Run the GUI: python npm_discovery_gui.py"
echo "  3. Or use CLI: python -m npm_discovery.cli search lodash"
echo ""
echo "🧪 Run tests: pytest tests/ -v"
echo ""

