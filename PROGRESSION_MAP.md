# NPM Discovery Program - Progression Map

**Project**: Consolidation of npm.py, npm2.py, npm_download.py into unified npm_discovery package
**Started**: 2025-10-16
**Status**: 🚀 In Progress

---

## Legend

- ✅ **Completed** - Step finished with validation
- 🔄 **In Progress** - Currently working on this step
- ⏳ **Pending** - Not started yet
- ⚠️ **Blocked** - Waiting on dependencies or decisions
- 🧪 **Testing** - Implementation done, validation in progress
- ❌ **Failed** - Step failed validation (with notes)

---

## Phase 0: Pre-Planning (COMPLETED)

| Step | Status | Description | Validation | Notes |
|------|--------|-------------|------------|-------|
| 0.1 | ✅ | Create feature inventory | Manual review | FEATURE_INVENTORY.md created |
| 0.2 | 🔄 | Create progression map | Manual review | This file |
| 0.3 | ⏳ | Setup git branch | `git branch` check | Branch: feature/npm-discovery-consolidation |

---

## Phase 1: Foundation (Steps 1-8)

### Step 1: Audit Current Scripts and PR #2
| Item | Status | Details |
|------|--------|---------|
| **Status** | ⏳ | Pending |
| **Goal** | Catalog all features from npm.py, npm2.py, npm_download.py |
| **Files Analyzed** | - |
| **Output** | Feature matrix with duplication analysis |
| **Validation** | All 3 files parsed, feature list complete |
| **Dependencies** | None |
| **Blockers** | npm2.py has syntax error (unterminated string) |
| **Notes** | |

**Checklist**:
- [ ] Parse npm.py (done in FEATURE_INVENTORY.md)
- [ ] Fix and parse npm2.py
- [ ] Parse npm_download.py (done)
- [ ] Map feature overlap
- [ ] Identify unique features per file
- [ ] Review PR #2 context
- [ ] Document findings

---

### Step 2: Define Architecture and Create Skeleton
| Item | Status | Details |
|------|--------|---------|
| **Status** | ⏳ | Pending |
| **Goal** | Create clean Python package structure |
| **Directories Created** | - |
| **Validation** | `tree src/` shows correct structure, all `__init__.py` files importable |
| **Dependencies** | Step 1 complete |
| **Blockers** | None |
| **Notes** | |

**Checklist**:
- [ ] Create `src/npm_discovery/` directory
- [ ] Create `src/npm_discovery/__init__.py`
- [ ] Create `api/` subdirectory with `__init__.py`
- [ ] Create `services/` subdirectory with `__init__.py`
- [ ] Create `models/` subdirectory with `__init__.py`
- [ ] Create `ui/` subdirectory with `__init__.py`
- [ ] Create `utils/` subdirectory with `__init__.py`
- [ ] Create `tests/` directory
- [ ] Create `scripts/` directory
- [ ] Test imports: `python -c "import src.npm_discovery"`

---

### Step 3: Add Project Metadata and Dependencies
| Item | Status | Details |
|------|--------|---------|
| **Status** | ⏳ | Pending |
| **Goal** | Create pyproject.toml with all dependencies |
| **File** | `pyproject.toml` |
| **Validation** | `pip install -e .` succeeds, all imports work |
| **Dependencies** | Step 2 complete |
| **Blockers** | None |
| **Notes** | |

**Checklist**:
- [ ] Create `pyproject.toml`
- [ ] Define project metadata (name, version, description)
- [ ] Add runtime dependencies (requests, beautifulsoup4, markdown, etc.)
- [ ] Add dev dependencies (pytest, ruff, mypy)
- [ ] Add console_scripts entry point
- [ ] Test installation: `pip install -e .`
- [ ] Verify imports work

**Dependencies to Include**:
```toml
[project.dependencies]
requests = "^2.31.0"
beautifulsoup4 = "^4.12.0"
markdown = "^3.5.0"
python-dateutil = "^2.8.0"
humanize = "^4.9.0"
diskcache = "^5.6.0"  # or requests-cache
```

---

### Step 4: Centralize Configuration and Secrets
| Item | Status | Details |
|------|--------|---------|
| **Status** | ⏳ | Pending |
| **Goal** | Create config module with environment variable support |
| **Files** | `src/npm_discovery/config.py`, `.env.example` |
| **Validation** | Config loads from env, provides defaults, raises helpful errors |
| **Dependencies** | Step 3 complete |
| **Blockers** | None |
| **Notes** | |

**Checklist**:
- [ ] Create `config.py` with Config class
- [ ] Load LIBRARIES_IO_API_KEY from environment
- [ ] Define default timeouts, concurrency, cache TTL
- [ ] Create `.env.example` file
- [ ] Add validation for required keys
- [ ] Add get_config() singleton function
- [ ] Test: Config loads correctly, missing key raises error

**Config Fields**:
- LIBRARIES_IO_API_KEY (required)
- NPM_REGISTRY_URL (default: https://registry.npmjs.org)
- UNPKG_URL (default: https://unpkg.com)
- CACHE_TTL_DAYS (default: 7)
- MAX_CONCURRENT_REQUESTS (default: 40)
- REQUEST_TIMEOUT (default: 30)

---

### Step 5: HTTP Client Utilities
| Item | Status | Details |
|------|--------|---------|
| **Status** | ⏳ | Pending |
| **Goal** | Shared HTTP layer with retry/backoff |
| **File** | `src/npm_discovery/utils/http.py` |
| **Validation** | get_json() works, retries on failure, respects timeout |
| **Dependencies** | Step 4 complete |
| **Blockers** | None |
| **Notes** | |

**Checklist**:
- [ ] Create `http.py` module
- [ ] Implement `create_session()` with HTTPAdapter + Retry
- [ ] Implement `get_json(url, **kwargs)` helper
- [ ] Implement `get_text(url, **kwargs)` helper
- [ ] Add User-Agent header by default
- [ ] Add timeout parameter with config default
- [ ] Define custom exceptions (HttpError, TimeoutError)
- [ ] Test: Request succeeds, retries work, timeout enforced

---

### Step 6: Structured Logging Foundation
| Item | Status | Details |
|------|--------|---------|
| **Status** | ⏳ | Pending |
| **Goal** | Rotating file logs with console output |
| **File** | `src/npm_discovery/utils/logging.py` |
| **Validation** | Logs written to file, console output works, rotation works |
| **Dependencies** | None |
| **Blockers** | None |
| **Notes** | |

**Checklist**:
- [ ] Create `logging.py` module
- [ ] Setup RotatingFileHandler (5MB, 2 backups)
- [ ] Add console StreamHandler
- [ ] Define log format with timestamp
- [ ] Export logger instance
- [ ] Add convenience functions (debug, info, warn, error)
- [ ] Test: Log messages appear in file and console

---

### Step 7: Cache Layer with TTL
| Item | Status | Details |
|------|--------|---------|
| **Status** | ⏳ | Pending |
| **Goal** | Transparent caching for API responses |
| **File** | `src/npm_discovery/utils/cache.py` |
| **Validation** | Cache stores/retrieves data, TTL works, compression works |
| **Dependencies** | Step 6 complete |
| **Blockers** | None |
| **Notes** | |

**Checklist**:
- [ ] Create `cache.py` module
- [ ] Choose backend (SQLite or diskcache)
- [ ] Implement `get_or_set(key, fetch_fn, ttl)` function
- [ ] Add compression helpers (zlib)
- [ ] Add expiration checking
- [ ] Add clear() and stats() functions
- [ ] Test: Data cached, retrieved, expires correctly

---

### Step 8: Core Data Models
| Item | Status | Details |
|------|--------|---------|
| **Status** | ⏳ | Pending |
| **Goal** | Define Package, Version, FileNode dataclasses |
| **Files** | `src/npm_discovery/models/package.py`, `models/file_tree.py` |
| **Validation** | Models instantiate, serialize/deserialize, type hints work |
| **Dependencies** | None |
| **Blockers** | None |
| **Notes** | |

**Checklist**:
- [ ] Create `models/package.py`
- [ ] Define Package dataclass with all fields
- [ ] Add `from_json()` class method
- [ ] Add `to_dict()` method
- [ ] Create `models/file_tree.py`
- [ ] Define FileNode dataclass (name, path, type, size, children)
- [ ] Test: Models create, serialize, deserialize

---

## Phase 2: Business Logic (Steps 9-16)

### Step 9: Libraries.io API Client
| Item | Status | Details |
|------|--------|---------|
| **Status** | ⏳ | Pending |
| **Goal** | Fetch package lists/search from Libraries.io |
| **File** | `src/npm_discovery/api/libraries_io_client.py` |
| **Validation** | API calls work, pagination works, rate limits respected |
| **Dependencies** | Steps 4, 5, 6 complete |
| **Blockers** | Need LIBRARIES_IO_API_KEY |
| **Notes** | |

**Checklist**:
- [ ] Create `libraries_io_client.py`
- [ ] Implement `search_projects(query, page, per_page)`
- [ ] Add rate limit handling (60 req/min free tier)
- [ ] Add pagination support
- [ ] Add filter parameters (platform=npm, sort, etc.)
- [ ] Test with mock API responses
- [ ] Test rate limit behavior
- [ ] Document API key requirement

---

### Step 10: npm Registry Client
| Item | Status | Details |
|------|--------|---------|
| **Status** | ⏳ | Pending |
| **Goal** | Refactor npm.py registry logic into client |
| **File** | `src/npm_discovery/api/npm_registry_client.py` |
| **Validation** | get_package() works, downloads stats work |
| **Dependencies** | Steps 5, 6, 8 complete |
| **Blockers** | None |
| **Notes** | |

**Checklist**:
- [ ] Create `npm_registry_client.py`
- [ ] Extract `get_package(name)` from NPMClient
- [ ] Extract `get_downloads_stats(name)` from NPMClient
- [ ] Add `get_readme(name, version)` method
- [ ] Add version resolution (latest, specific)
- [ ] Return Package dataclass instances
- [ ] Test with real npm packages (e.g., "react")

---

### Step 11: unpkg Client
| Item | Status | Details |
|------|--------|---------|
| **Status** | ⏳ | Pending |
| **Goal** | Integrate unpkg '?meta' API for file trees |
| **File** | `src/npm_discovery/api/unpkg_client.py` |
| **Validation** | list_tree() returns FileNode tree, get_file() retrieves content |
| **Dependencies** | Steps 5, 6, 8 complete |
| **Blockers** | None |
| **Notes** | |

**Checklist**:
- [ ] Create `unpkg_client.py`
- [ ] Implement `list_tree(package, version, path='/')`
- [ ] Parse `?meta` JSON response into FileNode tree
- [ ] Implement `get_file(package, version, path)`
- [ ] Add depth limiting for large trees
- [ ] Test with "react@18.2.0"
- [ ] Handle errors (404, rate limits)

---

### Step 12: PackageService Orchestrator
| Item | Status | Details |
|------|--------|---------|
| **Status** | ⏳ | Pending |
| **Goal** | High-level service coordinating discovery→enrichment→files |
| **File** | `src/npm_discovery/services/package_service.py` |
| **Validation** | search_packages() works end-to-end, caching integrated |
| **Dependencies** | Steps 7, 9, 10, 11 complete |
| **Blockers** | None |
| **Notes** | |

**Checklist**:
- [ ] Create `package_service.py`
- [ ] Implement `search_packages(query, filters)` (uses Libraries.io)
- [ ] Implement `enrich_package(pkg)` (adds npm details)
- [ ] Implement `get_file_tree(pkg, version)` (uses unpkg)
- [ ] Integrate caching at service level
- [ ] Add error aggregation (partial results on failure)
- [ ] Test complete workflow

---

### Step 13: Download/Extract Service
| Item | Status | Details |
|------|--------|---------|
| **Status** | ⏳ | Pending |
| **Goal** | Refactor download logic from npm.py and npm_download.py |
| **File** | `src/npm_discovery/services/download_service.py` |
| **Validation** | download_package() works, progress callbacks work |
| **Dependencies** | Step 10 complete |
| **Blockers** | None |
| **Notes** | |

**Checklist**:
- [ ] Create `download_service.py`
- [ ] Implement `download_package(pkg, version, dest, progress_callback)`
- [ ] Extract tarball logic from NPMClient
- [ ] Add progress reporting
- [ ] Add integrity checking
- [ ] Test download and extraction

---

### Step 14: Background Task Runner
| Item | Status | Details |
|------|--------|---------|
| **Status** | ⏳ | Pending |
| **Goal** | ThreadPoolExecutor wrapper for Tkinter |
| **File** | `src/npm_discovery/services/task_runner.py` |
| **Validation** | Tasks run in background, results posted to main thread |
| **Dependencies** | None |
| **Blockers** | None |
| **Notes** | |

**Checklist**:
- [ ] Create `task_runner.py`
- [ ] Implement TaskRunner class with ThreadPoolExecutor
- [ ] Add `submit(fn, *args, callback)` method
- [ ] Use queue.Queue for thread-safe result passing
- [ ] Add `.after()` polling to check queue
- [ ] Add cancel/shutdown methods
- [ ] Test with dummy long-running task

---

### Steps 15-16: (Similar detailed checklists for remaining Phase 2 steps)

---

## Phase 3: UI Layer (Steps 17-24)

### Step 17: Extract Dark Theme
| Item | Status | Details |
|------|--------|---------|
| **Status** | ⏳ | Pending |
| **Goal** | Move Theme class to reusable module |
| **File** | `src/npm_discovery/ui/theme.py` |
| **Validation** | Theme imports work, colors accessible |
| **Dependencies** | None |
| **Blockers** | None |
| **Notes** | |

**Checklist**:
- [ ] Copy Theme class from npm.py
- [ ] Add widget styling helpers
- [ ] Create `apply_theme(widget)` function
- [ ] Test in simple Tkinter window

---

### Steps 18-24: (UI components - detailed checklists pending)

---

## Phase 4: Integration & Quality (Steps 25-30)

### Steps 25-30: (Wiring, testing, docs - detailed checklists pending)

---

## Validation Criteria by Phase

### Phase 1 (Foundation)
- ✅ All imports resolve without errors
- ✅ Config loads from environment
- ✅ HTTP client makes successful requests
- ✅ Cache stores and retrieves data
- ✅ Logs appear in file and console

### Phase 2 (Business Logic)
- ✅ Libraries.io search returns results
- ✅ npm registry returns package details
- ✅ unpkg returns file tree
- ✅ PackageService orchestrates end-to-end
- ✅ Downloads complete successfully

### Phase 3 (UI)
- ✅ Dark theme applies to all widgets
- ✅ Search returns and displays results
- ✅ Package details render correctly
- ✅ File tree loads lazily from unpkg
- ✅ Downloads show progress

### Phase 4 (Integration)
- ✅ All features from legacy scripts work
- ✅ Tests pass (unit + integration)
- ✅ App installs via pip
- ✅ Documentation complete
- ✅ Legacy scripts deprecated

---

## Known Issues & Blockers

1. **npm2.py Parse Error** (Line 263)
   - Status: ⚠️ Unresolved
   - Impact: Cannot analyze npm2.py features
   - Action: Fix syntax error before Step 1

2. **Libraries.io API Key**
   - Status: ⏳ Pending
   - Impact: Cannot test Libraries.io client (Step 9)
   - Action: Obtain API key or use mock responses

3. **unpkg Rate Limits**
   - Status: ⚠️ Unknown
   - Impact: May need throttling in Step 11
   - Action: Test rate limits, add backoff if needed

---

## Progress Tracking

| Phase | Steps | Completed | In Progress | Pending | Blocked |
|-------|-------|-----------|-------------|---------|---------|
| 0 (Pre) | 3 | 1 | 1 | 1 | 0 |
| 1 (Foundation) | 8 | 0 | 0 | 8 | 0 |
| 2 (Logic) | 8 | 0 | 0 | 8 | 0 |
| 3 (UI) | 8 | 0 | 0 | 8 | 0 |
| 4 (Integration) | 6 | 0 | 0 | 6 | 0 |
| **Total** | **33** | **1** | **1** | **31** | **0** |

**Overall Progress**: 3% (1/33 steps complete)

---

## Test Results Summary

| Component | Tests | Passed | Failed | Coverage |
|-----------|-------|--------|--------|----------|
| Config | - | - | - | - |
| HTTP Utils | - | - | - | - |
| Cache | - | - | - | - |
| Libraries.io Client | - | - | - | - |
| npm Registry Client | - | - | - | - |
| unpkg Client | - | - | - | - |
| PackageService | - | - | - | - |
| DownloadService | - | - | - | - |
| UI Components | - | - | - | - |
| **Total** | **0** | **0** | **0** | **0%** |

---

## Next Actions

1. 🔄 **Complete Step 0.2** - Finish this progression map
2. ⏳ **Step 0.3** - Create git branch `feature/npm-discovery-consolidation`
3. ⏳ **Step 1** - Fix npm2.py, complete feature audit
4. ⏳ **Step 2** - Create package skeleton

---

**Last Updated**: 2025-10-16 (Initial creation)
**Next Update**: After Step 1 completion

