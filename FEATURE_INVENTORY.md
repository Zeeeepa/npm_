# NPM Discovery Program - Feature Inventory

## Source Files Analysis

### npm.py (Primary - 4,217 lines)
**Status**: ✅ Fully Functional, Most Complete

#### Classes & Key Features:

##### 1. Theme (Dark UI Theme System)
- **Line**: 84
- **Purpose**: Centralized dark color scheme
- **Methods**: `get_code_theme()`
- **Colors**: BG, TEXT, ACCENT, SUCCESS, WARNING, ERROR, CODE syntax colors
- **Features**:
  - GitHub-inspired dark theme
  - Gradient colors for sizes (KB/MB/GB) and time (recent/day/week/month)
  - Code syntax highlighting theme

##### 2. MarkdownRenderer
- **Line**: 136
- **Purpose**: Rich README display with syntax highlighting
- **Methods**: 6 methods including `render()`, `_parse_html()`, `_format_inline_text()`
- **Features**:
  - Full markdown parsing (headers, code blocks, tables, lists)
  - Syntax highlighting for code
  - Links, quotes, formatting
  - Handles HTML entities

##### 3. PackageInfo (Data Model)
- **Line**: 392
- **Purpose**: Structured package metadata with utilities
- **Methods**: 10 methods including serialization, humanization, caching
- **Features**:
  - Complete package metadata fields (name, version, description, stats, dependencies, etc.)
  - Cache key generation
  - Stale data detection
  - Human-friendly size/date formatting
  - Color interpolation for visual indicators

##### 4. SettingsManager
- **Line**: 642
- **Purpose**: Persistent configuration management
- **Methods**: 9 methods (load, save, get/set typed values)
- **Features**:
  - INI-based config file
  - Type-safe getters (int, bool, string)
  - Download directory management
  - Settings persistence

##### 5. CacheManager
- **Line**: 742
- **Purpose**: SQLite-based package data caching with TTL
- **Methods**: 13 methods including compression, dependency caching
- **Features**:
  - SQLite database with packages, dependencies, dependents tables
  - Data compression (zlib)
  - TTL-based expiration
  - Dependency/dependent details caching
  - Stats tracking
  - Bulk clear operations

##### 6. SearchHistoryManager
- **Line**: 1125
- **Purpose**: Track and suggest search queries
- **Methods**: 7 methods (add, get recent, stats, popular queries)
- **Features**:
  - SQLite-based history storage
  - Timestamp tracking
  - Popular query analysis
  - Configurable history limit

##### 7. NPMClient (Core API Integration)
- **Line**: 1289
- **Purpose**: Comprehensive npm registry API client
- **Methods**: 24 methods covering all npm operations
- **Features**:
  - Session with retry logic (HTTPAdapter + Retry)
  - Registry API integration (registry.npmjs.org)
  - Download stats API (api.npmjs.org/downloads)
  - README fetching (GitHub, npmjs.com fallbacks)
  - Repository URL extraction
  - File tree extraction from tarballs
  - Dependency/dependent details fetching
  - Concurrent package downloads
  - Search with pagination
  - Progress callbacks
  
**API Endpoints Used**:
- `https://registry.npmjs.org/{package}` - Package metadata
- `https://api.npmjs.org/downloads/point/last-week/{package}` - Download stats
- GitHub README fallback via repository links
- npmjs.com web scraping for file info

##### 8. FileTreeViewer
- **Line**: 2331
- **Purpose**: Interactive file browser with syntax highlighting
- **Methods**: 11 methods (tree population, file loading, highlighting)
- **Features**:
  - Treeview widget with directory/file icons
  - On-demand file loading
  - Syntax highlighting for code files
  - Double-click to open files
  - Text display with code formatting

##### 9. NPMAnalyzerApp (Main Application)
- **Line**: 2710
- **Purpose**: Complete Tkinter UI application
- **Methods**: 44 methods (UI creation, event handlers, downloads)
- **Features**:
  - Multi-tab interface (Overview, File Tree, Dependencies, JSON)
  - Search with multiple modes (text, keyword, author, maintainer)
  - Date filtering
  - Max results limiting
  - Search history with autocomplete
  - Package selection (single/multiple)
  - Concurrent downloads with progress
  - Cache management UI
  - Settings dialog
  - Results list with stats (downloads, size, date)
  - Package details display (metadata, README, dependencies)
  - URL opening (npm page, repository, homepage)
  - Worker count control
  - Stop/cancel operations
  
**UI Tabs**:
1. Overview: Package metadata, stats, README
2. File Tree: Interactive file browser
3. Dependencies: Deps and devDeps lists
4. JSON: Raw package.json view

#### Global Functions:
- `find_npm_executable()` - Locate npm binary on system

---

### npm2.py (Variant)
**Status**: ⚠️ Parse Error (unterminated string literal at line 263)
**Note**: Likely a duplicate/variant of npm.py with some experimental changes. Needs syntax fix before analysis.

---

### npm_download.py (Download-focused - 1,099 lines)
**Status**: ✅ Functional, Specialized for Downloads

#### Classes:

##### 1. NpmAPI
- **Line**: 15
- **Purpose**: Simplified API client focused on search and download
- **Methods**: 12 methods
- **Features**:
  - Basic search via registry
  - Package details fetching
  - Dependency/dependent lookup
  - Time-based filtering
  - Concurrent downloads with ThreadPoolExecutor
  - Progress tracking
  - Configurable download directory
  - Configurable concurrency

**API Endpoints**:
- `https://registry.npmjs.org/{package}` - Package info
- `https://registry.npmjs.org/{package}/{version}` - Version-specific info

##### 2. NpmDownloaderUI
- **Line**: 461
- **Purpose**: Tkinter UI for search and download
- **Methods**: 10 methods
- **Features**:
  - Two search types (package name, general search)
  - Results listbox
  - Package details display
  - Download with options (latest, all versions, specific version)
  - Progress bar
  - Download directory selection

#### Global Functions:
- `main()` - Application entry point

---

## Feature Matrix

| Feature | npm.py | npm2.py | npm_download.py | Target |
|---------|--------|---------|------------------|--------|
| **Data Sources** |
| npm registry API | ✅ | ❓ | ✅ | ✅ |
| npm downloads API | ✅ | ❓ | ❌ | ✅ |
| Libraries.io API | ❌ | ❓ | ❌ | ✅ **NEW** |
| unpkg file tree API | ❌ | ❓ | ❌ | ✅ **NEW** |
| GitHub README | ✅ | ❓ | ❌ | ✅ |
| **Core Features** |
| Package search | ✅ (advanced) | ❓ | ✅ (basic) | ✅ |
| Package details | ✅ (rich) | ❓ | ✅ (basic) | ✅ |
| README rendering | ✅ (markdown) | ❓ | ❌ | ✅ |
| File tree view | ✅ (tarball) | ❓ | ❌ | ✅ (unpkg) |
| Download packages | ✅ | ❓ | ✅ | ✅ |
| Concurrent downloads | ✅ | ❓ | ✅ | ✅ |
| Progress tracking | ✅ | ❓ | ✅ | ✅ |
| **Caching & Performance** |
| SQLite caching | ✅ | ❓ | ❌ | ✅ |
| Compression | ✅ | ❓ | ❌ | ✅ |
| TTL expiration | ✅ | ❓ | ❌ | ✅ |
| Retry logic | ✅ | ❓ | ❌ | ✅ |
| **UI Features** |
| Dark theme | ✅ | ❓ | ⚠️ (basic) | ✅ |
| Search history | ✅ | ❓ | ❌ | ✅ |
| Multiple tabs | ✅ | ❓ | ❌ | ✅ |
| Syntax highlighting | ✅ | ❓ | ❌ | ✅ |
| Settings dialog | ✅ | ❓ | ❌ | ✅ |
| Stats display | ✅ | ❓ | ❌ | ✅ |
| URL opening | ✅ | ❓ | ❌ | ✅ |
| **Data Management** |
| Persistent settings | ✅ | ❓ | ❌ | ✅ |
| Search history DB | ✅ | ❓ | ❌ | ✅ |
| Cache management | ✅ | ❓ | ❌ | ✅ |

---

## Dependencies Used

### npm.py Dependencies:
- tkinter (UI framework)
- requests (HTTP client)
- sqlite3 (caching, history)
- markdown + extensions (README rendering)
- BeautifulSoup4 (HTML parsing)
- humanize (date/size formatting)
- dateutil (date parsing)
- tarfile/zipfile (package extraction)

### npm_download.py Dependencies:
- tkinter (UI framework)
- requests (HTTP client)
- concurrent.futures (ThreadPoolExecutor)
- tarfile (package extraction)

---

## Integration Gaps (To Be Filled)

### 1. Libraries.io Integration
- **Purpose**: Discover packages at scale with filtering
- **API**: `https://libraries.io/api`
- **Features Needed**:
  - Search/list projects with pagination
  - Filter by platform (npm), keywords, dates
  - Sort by popularity, stars, updated date
  - Rate limit handling (60 req/min free tier)

### 2. unpkg Integration
- **Purpose**: Browse package files without downloading
- **API**: `https://unpkg.com/{package}@{version}/?meta`
- **Features Needed**:
  - Fetch directory tree metadata
  - Lazy-load subdirectories
  - Retrieve individual file contents
  - Display file sizes, types

### 3. Architecture Improvements
- **Current**: Monolithic scripts
- **Target**: Modular package structure
  - `api/` - Separate client modules
  - `services/` - Orchestration logic
  - `models/` - Data classes
  - `ui/` - UI components
  - `utils/` - Shared utilities

---

## Reusable Components from npm.py

### High Priority (Extract First):
1. ✅ **Theme class** - Complete dark theme system
2. ✅ **MarkdownRenderer** - Working markdown display
3. ✅ **CacheManager** - SQLite caching with compression
4. ✅ **SettingsManager** - Config management
5. ✅ **NPMClient search/details logic** - Registry API integration

### Medium Priority:
6. ✅ **SearchHistoryManager** - Query tracking
7. ✅ **FileTreeViewer** - File browser widget (adapt for unpkg)
8. ✅ **PackageInfo** - Data model (enhance with more fields)

### Low Priority (Nice to Have):
9. ✅ **NPMClient download logic** - Concurrent downloads
10. ✅ **Syntax highlighting** - Code display

---

## File Structure (Current vs Target)

### Current:
```
.
├── npm.py (4,217 lines)
├── npm2.py (broken)
├── npm_download.py (1,099 lines)
├── npm_cache.db
├── search_history.db
├── npm_analyzer_settings.ini
└── npm_analyzer.log
```

### Target:
```
.
├── src/npm_discovery/
│   ├── __init__.py
│   ├── api/
│   │   ├── __init__.py
│   │   ├── libraries_io_client.py ← NEW
│   │   ├── npm_registry_client.py ← FROM npm.py
│   │   └── unpkg_client.py ← NEW
│   ├── services/
│   │   ├── __init__.py
│   │   ├── package_service.py ← NEW (orchestrator)
│   │   ├── download_service.py ← FROM npm.py + npm_download.py
│   │   └── task_runner.py ← NEW (threading)
│   ├── models/
│   │   ├── __init__.py
│   │   ├── package.py ← FROM PackageInfo
│   │   └── file_tree.py ← NEW
│   ├── ui/
│   │   ├── __init__.py
│   │   ├── app.py ← FROM NPMAnalyzerApp
│   │   ├── theme.py ← FROM Theme
│   │   ├── views/
│   │   │   ├── search_view.py
│   │   │   ├── package_list_view.py
│   │   │   ├── package_detail_view.py
│   │   │   ├── file_tree_view.py ← FROM FileTreeViewer
│   │   │   └── settings_view.py
│   │   └── widgets/
│   │       ├── markdown_view.py ← FROM MarkdownRenderer
│   │       └── progress.py
│   ├── utils/
│   │   ├── __init__.py
│   │   ├── http.py ← NEW (shared HTTP logic)
│   │   ├── cache.py ← FROM CacheManager
│   │   ├── logging.py ← NEW
│   │   └── config.py ← FROM SettingsManager
│   └── config.py ← NEW (environment, API keys)
├── tests/
│   ├── test_libraries_io_client.py
│   ├── test_npm_registry_client.py
│   ├── test_unpkg_client.py
│   └── test_package_service.py
├── scripts/
│   └── run_app.py
├── pyproject.toml
├── .env.example
└── README.md
```

---

## Code Metrics

| File | Lines | Classes | Methods | Functions |
|------|-------|---------|---------|-----------|
| npm.py | 4,217 | 9 | 143 | 1 |
| npm2.py | ? | ? | ? | ? (broken) |
| npm_download.py | 1,099 | 2 | 22 | 1 |
| **Total** | ~5,316+ | 11+ | 165+ | 2+ |

---

## Next Steps

1. ✅ Fix npm2.py syntax error and analyze
2. ✅ Create comprehensive progression map
3. ⏳ Begin Step 1: Audit and extract reusable components
4. ⏳ Execute 30-step plan with validation after each step

---

**Generated**: 2025-10-16
**Last Updated**: 2025-10-16

