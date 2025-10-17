# NPM Package Discovery 📦

A powerful NPM package discovery tool with a dark-themed native UI. Search, explore, and analyze NPM packages with integrated APIs from Libraries.io, NPM Registry, and Unpkg CDN.

## Features ✨

- 🔍 **Package Search**: Search packages via Libraries.io API
- 📊 **Rich Details**: Complete package metadata from NPM Registry
- 📁 **File Tree Viewer**: Browse package file structures via Unpkg CDN
- 🎨 **Dark Theme UI**: Beautiful dark-themed interface
- ⚡ **Smart Caching**: SQLite-based persistent cache
- 🖥️ **CLI & GUI**: Both command-line and graphical interfaces
- ✅ **100% Test Coverage**: 47/47 tests passing

## Quick Start 🚀

### Prerequisites

- Python 3.8+
- Libraries.io API key ([Get one free](https://libraries.io/account))

### Installation

```bash
# Clone the repository
git clone <repository-url>
cd npm_discovery

# Install dependencies
pip install -r requirements.txt

# Set up environment
cp .env.example .env
# Edit .env and add your LIBRARIES_IO_API_KEY
```

### Usage

#### GUI Application

```bash
python npm_discovery_gui.py
```

or

```bash
python -m npm_discovery.ui
```

#### CLI Interface

Search for packages:
```bash
python -m npm_discovery.cli search "lodash"
```

Get package details:
```bash
python -m npm_discovery.cli details lodash
```

View file tree:
```bash
python -m npm_discovery.cli tree react
```

Cache statistics:
```bash
python -m npm_discovery.cli cache-stats
```

## Architecture 🏗️

```
npm_discovery/
├── api/              # API clients (Libraries.io, NPM, Unpkg)
├── config.py         # Configuration management
├── models/           # Data models
├── services/         # Business logic
├── ui/               # GUI components
├── utils/            # Utilities (HTTP, etc.)
└── cli.py            # CLI interface
```

### Key Components

1. **API Clients**:
   - `LibrariesIOClient`: Package search
   - `NpmRegistryClient`: Package enrichment
   - `UnpkgClient`: File tree retrieval

2. **Services**:
   - `DiscoveryService`: Orchestrates all operations
   - `CacheManager`: Persistent SQLite cache

3. **UI**:
   - Dark-themed tkinter interface
   - Async operations with threading
   - File tree visualization

## Configuration ⚙️

Environment variables:

```bash
# Required
LIBRARIES_IO_API_KEY=your_key_here

# Optional
NPM_REGISTRY_URL=https://registry.npmjs.org
UNPKG_URL=https://unpkg.com
CACHE_TTL_DAYS=7
MAX_CONCURRENT_REQUESTS=40
REQUEST_TIMEOUT=30
```

## Development 🛠️

### Running Tests

```bash
# All tests
pytest tests/ -v

# With coverage
pytest tests/ --cov=npm_discovery --cov-report=html

# Specific test suite
pytest tests/unit/ -v
pytest tests/integration/ -v
```

### Code Quality

```bash
# Linting
ruff check src/

# Type checking
mypy src/

# Format
ruff format src/
```

## API Documentation 📚

### DiscoveryService

Main service for package discovery:

```python
from npm_discovery.services import DiscoveryService

service = DiscoveryService()

# Search packages
results = service.search_packages("lodash", per_page=50)

# Get package details
package = service.get_package_details("lodash")

# Get file tree
tree = service.get_file_tree("react", version="18.0.0")

# Get README
readme = service.get_readme("express")
```

## License 📄

MIT License - see LICENSE file for details.

## Contributing 🤝

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Add tests for new features
4. Ensure all tests pass
5. Submit a pull request

## Acknowledgments 🙏

- [Libraries.io](https://libraries.io) - Package search API
- [NPM Registry](https://registry.npmjs.org) - Package metadata
- [Unpkg](https://unpkg.com) - CDN and file access

