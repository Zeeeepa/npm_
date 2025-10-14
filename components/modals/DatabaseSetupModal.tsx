import React, { useState, useEffect } from 'react';
import LoadingSpinner from '../shared/LoadingSpinner';
import { XIcon } from '../shared/icons/XIcon';
import { CheckIcon } from '../shared/icons/CheckIcon';
import { ExclamationIcon } from '../shared/icons/ExclamationIcon';
import { ClipboardIcon } from '../shared/icons/ClipboardIcon';
import { ClipboardCheckIcon } from '../shared/icons/ClipboardCheckIcon';
import * as supabaseService from '../../services/supabaseService';

const SQL_SCHEMA = `
-- Drop existing tables in reverse order of dependency to ensure a clean slate.
-- WARNING: THIS WILL DELETE ALL EXISTING DATA in these tables.
DROP TABLE IF EXISTS public.code_references CASCADE;
DROP TABLE IF EXISTS public.code_symbols CASCADE;
DROP TABLE IF EXISTS public.file_dependencies CASCADE;
DROP TABLE IF EXISTS public.code_files CASCADE;
DROP TABLE IF EXISTS public.directory_tree CASCADE;
DROP TABLE IF EXISTS public.package_versions CASCADE;
DROP TABLE IF EXISTS public.package_analyses CASCADE;
DROP TABLE IF EXISTS public.saved_packages CASCADE;
DROP TABLE IF EXISTS public.search_result_items CASCADE;
DROP TABLE IF EXISTS public.past_searches CASCADE;
DROP TABLE IF EXISTS public.packages CASCADE;

-- 1. Core packages table with enhanced metadata
CREATE TABLE public.packages (
    id BIGSERIAL PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    package_data JSONB NOT NULL,
    description TEXT,
    repository_url TEXT,
    homepage_url TEXT,
    npm_url TEXT,
    author JSONB,
    maintainers JSONB,
    keywords TEXT[],
    license TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ,
    last_synced_at TIMESTAMPTZ,
    download_stats JSONB,
    github_stars INT,
    github_forks INT,
    github_issues INT,
    npm_version_count INT,
    is_deprecated BOOLEAN DEFAULT false,
    deprecation_message TEXT
);
COMMENT ON TABLE public.packages IS 'Core NPM packages table with comprehensive metadata.';

-- 2. Saved/bookmarked packages by users
CREATE TABLE public.saved_packages (
    id BIGSERIAL PRIMARY KEY,
    package_name TEXT NOT NULL REFERENCES public.packages(name) ON DELETE CASCADE,
    saved_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    notes TEXT,
    tags TEXT[],
    favorite BOOLEAN DEFAULT false,
    UNIQUE(package_name)
);
COMMENT ON TABLE public.saved_packages IS 'User-saved/bookmarked packages.';

-- 3. Package analysis results (metrics, quality scores, etc.)
CREATE TABLE public.package_analyses (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    package_name TEXT NOT NULL REFERENCES public.packages(name) ON DELETE CASCADE,
    analyzed_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    analysis_version TEXT DEFAULT '1.0',
    total_files INT,
    total_lines_of_code INT,
    total_size_bytes BIGINT,
    language_breakdown JSONB,
    average_complexity NUMERIC(10,2),
    max_complexity INT,
    total_functions INT,
    total_classes INT,
    total_interfaces INT,
    direct_dependencies INT,
    dev_dependencies INT,
    peer_dependencies INT,
    total_dependencies INT,
    maintainability_score NUMERIC(5,2),
    test_coverage NUMERIC(5,2),
    documentation_coverage NUMERIC(5,2),
    known_vulnerabilities INT DEFAULT 0,
    license_issues JSONB,
    has_tests BOOLEAN,
    has_typescript BOOLEAN,
    has_documentation BOOLEAN,
    build_tools JSONB,
    frameworks JSONB,
    analysis_metadata JSONB,
    UNIQUE(package_name, analyzed_at)
);
COMMENT ON TABLE public.package_analyses IS 'Comprehensive analysis results for packages.';

-- 4. Package versions with detailed metadata
CREATE TABLE public.package_versions (
    id BIGSERIAL PRIMARY KEY,
    package_name TEXT NOT NULL REFERENCES public.packages(name) ON DELETE CASCADE,
    version TEXT NOT NULL,
    version_major INT,
    version_minor INT,
    version_patch INT,
    is_latest BOOLEAN DEFAULT false,
    is_prerelease BOOLEAN DEFAULT false,
    tarball_url TEXT,
    shasum TEXT,
    integrity TEXT,
    unpacked_size BIGINT,
    file_count INT,
    dependencies JSONB,
    dev_dependencies JSONB,
    peer_dependencies JSONB,
    optional_dependencies JSONB,
    bundled_dependencies JSONB,
    published_at TIMESTAMPTZ,
    published_by JSONB,
    git_head TEXT,
    node_version TEXT,
    npm_version TEXT,
    scripts JSONB,
    bin JSONB,
    main_entry_point TEXT,
    module_entry_point TEXT,
    types_entry_point TEXT,
    exports JSONB,
    contents_synced BOOLEAN DEFAULT false,
    synced_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(package_name, version)
);
COMMENT ON TABLE public.package_versions IS 'Detailed version information for each package.';

-- 5. Directory tree structure for package versions
CREATE TABLE public.directory_tree (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    version_id BIGINT NOT NULL REFERENCES public.package_versions(id) ON DELETE CASCADE,
    path TEXT NOT NULL,
    name TEXT NOT NULL,
    type TEXT NOT NULL CHECK (type IN ('file', 'directory', 'symlink')),
    parent_path TEXT,
    depth INT NOT NULL DEFAULT 0,
    size_bytes BIGINT,
    mode TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(version_id, path)
);
COMMENT ON TABLE public.directory_tree IS 'Complete directory structure for each package version.';

-- 6. Code files with complete content and metadata
CREATE TABLE public.code_files (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    version_id BIGINT NOT NULL REFERENCES public.package_versions(id) ON DELETE CASCADE,
    directory_entry_id UUID REFERENCES public.directory_tree(id) ON DELETE CASCADE,
    path TEXT NOT NULL,
    storage_path TEXT,
    content TEXT,
    content_hash TEXT,
    encoding TEXT DEFAULT 'utf-8',
    language TEXT,
    file_type TEXT,
    file_extension TEXT,
    mime_type TEXT,
    is_binary BOOLEAN DEFAULT false,
    is_generated BOOLEAN DEFAULT false,
    is_minified BOOLEAN DEFAULT false,
    is_test_file BOOLEAN DEFAULT false,
    is_entry_point BOOLEAN DEFAULT false,
    line_count INT,
    char_count INT,
    blank_lines INT,
    comment_lines INT,
    code_lines INT,
    size_bytes BIGINT,
    imports JSONB,
    exports JSONB,
    requires JSONB,
    external_dependencies TEXT[],
    parsed BOOLEAN DEFAULT false,
    parse_error TEXT,
    ast_hash TEXT,
    file_metadata JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(version_id, path)
);
COMMENT ON TABLE public.code_files IS 'Complete file contents and metadata for analysis.';

-- 7. File dependencies (imports/requires between files)
CREATE TABLE public.file_dependencies (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    version_id BIGINT NOT NULL REFERENCES public.package_versions(id) ON DELETE CASCADE,
    source_file_id UUID NOT NULL REFERENCES public.code_files(id) ON DELETE CASCADE,
    target_file_id UUID REFERENCES public.code_files(id) ON DELETE CASCADE,
    source_path TEXT NOT NULL,
    import_statement TEXT NOT NULL,
    resolved_path TEXT,
    dependency_type TEXT NOT NULL,
    import_kind TEXT,
    imported_symbols JSONB,
    is_wildcard BOOLEAN DEFAULT false,
    is_default BOOLEAN DEFAULT false,
    is_side_effect BOOLEAN DEFAULT false,
    is_external BOOLEAN DEFAULT false,
    package_name TEXT,
    package_version TEXT,
    is_dev_dependency BOOLEAN DEFAULT false,
    is_peer_dependency BOOLEAN DEFAULT false,
    line_number INT,
    column_number INT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(version_id, source_file_id, import_statement, line_number)
);
COMMENT ON TABLE public.file_dependencies IS 'Tracks all dependencies between files and external packages.';

-- 8. Code symbols (functions, classes, variables, types, etc.)
CREATE TABLE public.code_symbols (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    file_id UUID NOT NULL REFERENCES public.code_files(id) ON DELETE CASCADE,
    version_id BIGINT NOT NULL REFERENCES public.package_versions(id) ON DELETE CASCADE,
    parent_symbol_id UUID REFERENCES public.code_symbols(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    qualified_name TEXT,
    display_name TEXT,
    symbol_type TEXT NOT NULL,
    symbol_kind TEXT,
    scope TEXT,
    visibility TEXT,
    is_exported BOOLEAN DEFAULT false,
    export_type TEXT,
    is_static BOOLEAN DEFAULT false,
    is_abstract BOOLEAN DEFAULT false,
    is_async BOOLEAN DEFAULT false,
    is_generator BOOLEAN DEFAULT false,
    is_readonly BOOLEAN DEFAULT false,
    is_optional BOOLEAN DEFAULT false,
    start_line INT,
    end_line INT,
    start_col INT,
    end_col INT,
    signature TEXT,
    parameters JSONB,
    return_type TEXT,
    type_parameters JSONB,
    extends_types TEXT[],
    implements_types TEXT[],
    value_type TEXT,
    initial_value TEXT,
    docstring TEXT,
    doc_tags JSONB,
    description TEXT,
    decorators JSONB,
    modifiers TEXT[],
    complexity_score INT,
    lines_of_code INT,
    cognitive_complexity INT,
    inferred_type TEXT,
    type_complexity INT,
    is_used BOOLEAN,
    usage_count INT DEFAULT 0,
    symbol_metadata JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
COMMENT ON TABLE public.code_symbols IS 'All code symbols extracted from parsed files (functions, classes, types, variables, etc.)';

-- 9. Code references (where symbols are used/referenced)
CREATE TABLE public.code_references (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    version_id BIGINT NOT NULL REFERENCES public.package_versions(id) ON DELETE CASCADE,
    symbol_id UUID NOT NULL REFERENCES public.code_symbols(id) ON DELETE CASCADE,
    file_id UUID NOT NULL REFERENCES public.code_files(id) ON DELETE CASCADE,
    line_number INT NOT NULL,
    column_number INT NOT NULL,
    end_line INT,
    end_column INT,
    reference_type TEXT NOT NULL,
    context TEXT,
    is_constructor_call BOOLEAN DEFAULT false,
    arguments JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
COMMENT ON TABLE public.code_references IS 'Tracks where and how symbols are used throughout the codebase.';

-- 10. Past searches with complete context
CREATE TABLE public.past_searches (
    id TEXT PRIMARY KEY,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    query TEXT NOT NULL,
    search_mode TEXT NOT NULL,
    total_found INT NOT NULL,
    search_duration_ms INT,
    filters JSONB NOT NULL,
    sort_by TEXT,
    results_data JSONB NOT NULL,
    result_count INT,
    user_clicked BOOLEAN DEFAULT false,
    clicked_package_name TEXT,
    time_to_click_ms INT
);
COMMENT ON TABLE public.past_searches IS 'Search history with complete context and analytics.';

-- 11. Individual search result items (for better querying)
CREATE TABLE public.search_result_items (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    search_id TEXT NOT NULL REFERENCES public.past_searches(id) ON DELETE CASCADE,
    package_name TEXT NOT NULL REFERENCES public.packages(name) ON DELETE CASCADE,
    result_position INT NOT NULL,
    relevance_score NUMERIC(10,4),
    package_snapshot JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(search_id, package_name)
);
COMMENT ON TABLE public.search_result_items IS 'Individual items from search results for granular analysis.';

-- 12. Enable Row Level Security (RLS) for all tables
ALTER TABLE public.packages ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.saved_packages ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.package_analyses ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.package_versions ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.directory_tree ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.code_files ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.file_dependencies ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.code_symbols ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.code_references ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.past_searches ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.search_result_items ENABLE ROW LEVEL SECURITY;

-- 13. Create permissive RLS policies for a single-user (anon key) setup.
-- In a multi-user app, you would replace 'true' with 'auth.uid() = user_id'.
CREATE POLICY "Allow all access to packages" ON public.packages FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "Allow all access to saved_packages" ON public.saved_packages FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "Allow all access to package_analyses" ON public.package_analyses FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "Allow all access to package_versions" ON public.package_versions FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "Allow all access to directory_tree" ON public.directory_tree FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "Allow all access to code_files" ON public.code_files FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "Allow all access to file_dependencies" ON public.file_dependencies FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "Allow all access to code_symbols" ON public.code_symbols FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "Allow all access to code_references" ON public.code_references FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "Allow all access to past_searches" ON public.past_searches FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "Allow all access to search_result_items" ON public.search_result_items FOR ALL USING (true) WITH CHECK (true);
`.trim();

interface DatabaseSetupModalProps {
    isOpen: boolean;
    onClose: () => void;
    onVerificationSuccess: () => void;
}

type Step = 'welcome' | 'checking' | 'results' | 'manual';

const DatabaseSetupModal: React.FC<DatabaseSetupModalProps> = ({ isOpen, onClose, onVerificationSuccess }) => {
    const [step, setStep] = useState<Step>('welcome');
    const [missingTables, setMissingTables] = useState<string[]>([]);
    const [error, setError] = useState<string | null>(null);
    const [copied, setCopied] = useState(false);

    useEffect(() => {
        if (isOpen) {
            setStep('welcome');
            setMissingTables([]);
            setError(null);
        }
    }, [isOpen]);

    const handleCheckSchema = async () => {
        setStep('checking');
        setError(null);
        try {
            const result = await supabaseService.verifySchema();
            setMissingTables(result.missing);
            setStep('results');
            if (result.success) {
                // Give user feedback before closing automatically
                setTimeout(() => onVerificationSuccess(), 1500);
            }
        } catch (e: any) {
            setError(e.message || 'An unknown error occurred during schema verification.');
            setStep('results');
        }
    };

    const handleCopyToClipboard = () => {
        navigator.clipboard.writeText(SQL_SCHEMA);
        setCopied(true);
        setTimeout(() => setCopied(false), 2000);
    };

    const renderContent = () => {
        switch (step) {
            case 'welcome':
                return (
                    <>
                        <p className="text-sm text-text-secondary mb-6">This wizard will check your Supabase project for the necessary tables and guide you through setup if needed.</p>
                        <div className="flex justify-end">
                            <button onClick={handleCheckSchema} className="px-4 py-2 rounded-md transition-colors font-semibold bg-accent text-white hover:bg-accent/80">
                                Verify Database Schema
                            </button>
                        </div>
                    </>
                );
            case 'checking':
                 return (
                    <div className="flex flex-col items-center justify-center p-8">
                        <LoadingSpinner />
                        <p className="mt-4 text-text-secondary">Verifying database schema...</p>
                    </div>
                 );
            case 'results':
                const isSuccess = missingTables.length === 0 && !error;
                return (
                    <div>
                        <h3 className="font-semibold text-lg mb-4">Verification Results</h3>
                        {error && (
                            <div className="bg-danger/10 border border-danger text-danger p-3 rounded-md text-sm mb-4">
                                <p className="font-semibold">An Error Occurred</p>
                                <p>{error}</p>
                            </div>
                        )}
                        {isSuccess ? (
                            <div className="bg-green-500/10 border border-green-500 text-green-400 p-4 rounded-md flex items-center gap-4">
                                <CheckIcon className="w-8 h-8 shrink-0" />
                                <div>
                                    <p className="font-semibold">Schema is correct!</p>
                                    <p className="text-sm">All required tables were found. This modal will close automatically.</p>
                                </div>
                            </div>
                        ) : (
                            <div className="bg-yellow-500/10 border border-yellow-500 text-yellow-400 p-4 rounded-md flex items-center gap-4">
                                 <ExclamationIcon className="w-8 h-8 shrink-0" />
                                 <div>
                                    <p className="font-semibold">Tables Missing</p>
                                    <p className="text-sm">The following tables seem to be missing: {missingTables.join(', ')}.</p>
                                </div>
                            </div>
                        )}
                        <div className="mt-6 flex justify-end gap-4">
                             <button onClick={onClose} className="px-4 py-2 rounded-md bg-transparent border border-border-color text-text-primary hover:bg-border-color transition-colors">
                                {isSuccess ? "Finish" : "Close"}
                            </button>
                            {!isSuccess && (
                                <button onClick={() => setStep('manual')} className="px-4 py-2 rounded-md transition-colors font-semibold bg-accent text-white hover:bg-accent/80">
                                    Show Setup Instructions
                                </button>
                            )}
                        </div>
                    </div>
                );
            case 'manual':
                 const projectRef = supabaseService.getProjectRef();
                 return (
                    <div>
                         <h3 className="font-semibold text-lg mb-2">Manual Setup</h3>
                         <p className="text-sm text-text-secondary mb-4">Run the following SQL script in your Supabase project's SQL Editor to create the necessary tables.</p>
                         <div className="relative bg-primary p-4 rounded-md border border-border-color max-h-64 overflow-y-auto">
                            <pre className="text-xs text-text-primary whitespace-pre-wrap">
                                <code>{SQL_SCHEMA}</code>
                            </pre>
                            <button onClick={handleCopyToClipboard} className="absolute top-2 right-2 p-2 rounded-md bg-secondary hover:bg-border-color transition-colors">
                                {copied ? <ClipboardCheckIcon className="w-5 h-5 text-green-400" /> : <ClipboardIcon className="w-5 h-5" />}
                            </button>
                         </div>
                         <div className="mt-6 flex justify-end gap-4">
                            {/* FIX: Call getProjectRef and handle potential null value to prevent broken links. */}
                            <a href={projectRef ? `https://supabase.com/dashboard/project/${projectRef}/sql/new` : '#'} target="_blank" rel="noopener noreferrer" className={`px-4 py-2 rounded-md bg-transparent border border-border-color text-text-primary hover:bg-border-color transition-colors no-underline ${!projectRef ? 'opacity-50 cursor-not-allowed' : ''}`} onClick={(e) => !projectRef && e.preventDefault()} title={!projectRef ? "Could not determine project reference from URL" : "Open Supabase SQL Editor"}>
                                Open Supabase SQL Editor
                            </a>
                             <button onClick={handleCheckSchema} className="px-4 py-2 rounded-md transition-colors font-semibold bg-accent text-white hover:bg-accent/80">
                                Verify Again
                            </button>
                         </div>
                    </div>
                 );
        }
    };

    if (!isOpen) return null;
    return (
        <div className="fixed inset-0 bg-black bg-opacity-70 z-50 flex justify-center items-center p-4" onClick={onClose}>
            <div className="bg-secondary rounded-lg shadow-2xl border border-border-color w-full max-w-2xl" onClick={e => e.stopPropagation()}>
                <header className="flex justify-between items-center p-4 border-b border-border-color">
                    <h2 className="text-lg font-bold">Supabase Database Setup</h2>
                    <button onClick={onClose} className="p-1 rounded-full hover:bg-tertiary">
                        <XIcon className="w-6 h-6" />
                    </button>
                </header>
                <div className="p-6">
                    {renderContent()}
                </div>
            </div>
        </div>
    );
};

export default DatabaseSetupModal;