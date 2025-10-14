import React, { useState, useEffect, useCallback, useMemo } from 'react';
import Header from './components/shared/Header';
import SearchView from './components/search/SearchView';
import ProjectsView from './components/projects/ProjectsView';
import SettingsModal from './components/SettingsModal';
import PackageDetailModal from './components/modals/PackageDetailModal';
import SupabaseModal from './components/modals/SupabaseModal';
import DatabaseSetupModal from './components/modals/DatabaseSetupModal';
import AdminActionsModal from './components/modals/AdminActionsModal';
import SchemaSetupOverlay from './components/shared/SchemaSetupOverlay';

import { EnrichedNpmPackage, SupabaseCredentials, SupabaseStatus, PastSearch } from './types';
import * as supabase from './services/supabaseService';
import type { Package as SupabasePackage, PastSearch as SupabasePastSearch } from './services/supabaseService';

type View = 'search' | 'projects';


// Adapter function to map the new Supabase `Package` type to the `EnrichedNpmPackage` type used by the UI.
const mapSupabasePackageToEnriched = (p: SupabasePackage): EnrichedNpmPackage => {
    const enriched = p.package_data as EnrichedNpmPackage;
    enriched.syncStatus = p.last_synced_at ? 'synced' : 'not_synced';
    return enriched;
};

// Adapter function to map the new Supabase `PastSearch` type to the `PastSearch` type used by the UI.
const mapSupabaseSearchToPastSearch = (s: SupabasePastSearch): PastSearch => {
    return {
        id: s.id,
        timestamp: new Date(s.created_at || Date.now()).getTime(),
        query: s.query,
        results: s.results_data as EnrichedNpmPackage[],
        totalFound: s.total_found,
        searchMode: s.search_mode,
        // FIX: Added optional chaining to prevent crashes if `filters` is null/undefined.
        weights: s.filters?.weights,
        filtersEnabled: s.filters?.filtersEnabled,
    };
};

const getCredsFromFile = async (): Promise<SupabaseCredentials | null> => {
    try {
        const response = await fetch('/variables.json');
        if (!response.ok) {
            console.error(`Failed to fetch variables.json: ${response.statusText}`);
            return null;
        }
        const config = await response.json();
        if (config && config.SUPABASE_URL && config.SUPABASE_ANON_KEY) {
            return {
                url: config.SUPABASE_URL,
                key: config.SUPABASE_ANON_KEY,
                secretKey: config.SUPABASE_SERVICE_ROLE_KEY || '',
            };
        }
        console.warn("Supabase credentials (SUPABASE_URL, SUPABASE_ANON_KEY) not found in variables.json.");
    } catch (e) {
        console.error("Could not load or parse Supabase credentials from variables.json", e);
    }
    return null;
}

const App: React.FC = () => {
    const [activeView, setActiveView] = useState<View>('search');
    const [savedPackages, setSavedPackages] = useState<EnrichedNpmPackage[]>([]);
    const [selectedPackage, setSelectedPackage] = useState<EnrichedNpmPackage | null>(null);
    const [pastSearches, setPastSearches] = useState<PastSearch[]>([]);
    const [historySearchToLoad, setHistorySearchToLoad] = useState<PastSearch | null>(null);
    const [searchQuery, setSearchQuery] = useState('');
    
    const [isSearching, setIsSearching] = useState(false);
    const [isSearchPaused, setIsSearchPaused] = useState(false);
    const searchControllerRef = React.useRef<AbortController | null>(null);

    const [isSettingsModalOpen, setIsSettingsModalOpen] = useState(false);
    const [isSupabaseModalOpen, setIsSupabaseModalOpen] = useState(false);
    const [isDbSetupModalOpen, setIsDbSetupModalOpen] = useState(false);
    const [isAdminActionsModalOpen, setIsAdminActionsModalOpen] = useState(false);
    const [showSchemaOverlay, setShowSchemaOverlay] = useState(false);

    const [supabaseCreds, setSupabaseCreds] = useState<SupabaseCredentials>({ url: '', key: '', secretKey: '' });
    const [supabaseStatus, setSupabaseStatus] = useState<SupabaseStatus>('initializing');
    const [error, setError] = useState<string | null>(null);
    
    useEffect(() => {
        const loadCreds = async () => {
            setSupabaseStatus('initializing');
            const creds = await getCredsFromFile();
            if (creds) {
                setSupabaseCreds(creds);
            } else {
                setError("Could not load Supabase credentials from variables.json. App cannot connect to the database.");
                setSupabaseStatus('disconnected');
            }
        };
        loadCreds();
    }, []);

    const connectToSupabase = useCallback(async (creds: SupabaseCredentials) => {
        if (!creds.url || !creds.key) {
            setSupabaseStatus('disconnected');
            return;
        }
        setSupabaseStatus('connecting');
        setShowSchemaOverlay(false);
        setError(null);
        try {
            supabase.init(creds.url, creds.key, creds.secretKey);
            
            const schemaCheck = await supabase.verifySchema();
            if (!schemaCheck.success) {
                setSupabaseStatus('error');
                if (schemaCheck.error && (schemaCheck.error as any).message.includes("Could not find the table")) {
                     setError("Schema Mismatch Detected: The security policies in your database are for a multi-user application (with sign-in), but this version of the app connects directly. Please use the 'Open Setup Wizard' to copy and run the correct SQL script.");
                } else {
                    setError(`Schema validation failed. Missing tables: ${schemaCheck.missing.join(', ')}.`);
                }
                setShowSchemaOverlay(true);
            } else {
                setSupabaseStatus('connected');
                setIsSupabaseModalOpen(false);
                
                const results = await Promise.allSettled([
                    supabase.packages.getAll({ savedOnly: true }),
                    supabase.searches.getAll()
                ]);

                if (results[0].status === 'fulfilled') {
                    setSavedPackages(results[0].value.map(mapSupabasePackageToEnriched));
                } else {
                    console.error("Failed to fetch saved packages:", results[0].reason);
                }

                if (results[1].status === 'fulfilled') {
                    setPastSearches(results[1].value.map(mapSupabaseSearchToPastSearch));
                } else {
                    console.error("Failed to fetch search history:", results[1].reason);
                }
            }
        } catch (err: any) {
            console.error("Supabase connection/verification error:", err);
            setSupabaseStatus('error');
            let detailedError = err.message || 'Failed to connect to the database.';
            if (err.message?.includes("Could not find the table")) {
                detailedError = "A database schema mismatch was detected. The security policies in your database are for a multi-user application, but this version connects directly. Please use the 'Open Setup Wizard' to run the correct SQL script."
            }
            setError(detailedError);
        }
    }, []);

    useEffect(() => {
        if (supabaseCreds.url && supabaseCreds.key) {
            connectToSupabase(supabaseCreds);
        }
    }, [supabaseCreds, connectToSupabase]);
    
    const handleStopSearch = useCallback(() => {
        searchControllerRef.current?.abort();
    }, []);


    const handleSavePackage = async (pkg: EnrichedNpmPackage) => {
        if (savedPackages.some(p => p.package.name === pkg.package.name)) return;
        if (supabaseStatus !== 'connected') {
            console.warn("Save operation skipped: Not connected to Supabase.");
            return;
        }

        const originalPackages = savedPackages;
        const newPkg = { ...pkg, syncStatus: 'not_synced' as const };
        setSavedPackages(prev => [...prev, newPkg]);
        
        try {
             const supabasePkg: SupabasePackage = {
                name: pkg.package.name,
                package_data: pkg,
                description: pkg.package.description,
                repository_url: pkg.package.links.repository,
                homepage_url: pkg.package.links.homepage,
            };
            await supabase.packages.upsert(supabasePkg);
            await supabase.savedPackages.save(pkg.package.name);
        } catch (e) {
            console.error("Failed to save package to Supabase:", e);
            setSavedPackages(originalPackages); // Revert on error
        }
    };

    const handleRemovePackage = async (packageName: string) => {
        if (supabaseStatus !== 'connected') {
            console.warn("Remove operation skipped: Not connected to Supabase.");
            return;
        }
        
        const originalPackages = savedPackages;
        setSavedPackages(prev => prev.filter(p => p.package.name !== packageName));

        try {
            // FIX: Call the correct method to "unsave" a package.
            await supabase.savedPackages.remove(packageName);
        } catch (e) {
            console.error("Failed to remove package from Supabase:", e);
            setSavedPackages(originalPackages); // Revert on error
        }
    };

    const handleSyncPackage = async (pkg: EnrichedNpmPackage) => {
        if (supabaseStatus !== 'connected') return;
        
        setSavedPackages(prev => prev.map(p => p.package.name === pkg.package.name ? {...p, syncStatus: 'syncing'} : p));
        
        try {
            await supabase.sync.syncPackageContents(pkg.package.name);
            setSavedPackages(prev => prev.map(p => p.package.name === pkg.package.name ? {...p, syncStatus: 'synced'} : p));
        } catch (error) {
            console.error(`Failed to sync package ${pkg.package.name}:`, error);
            setSavedPackages(prev => prev.map(p => p.package.name === pkg.package.name ? {...p, syncStatus: 'not_synced'} : p));
            alert(`Failed to sync contents for ${pkg.package.name}. See console for details.`);
        }
    };

    const handleSaveSearch = async (search: PastSearch) => {
        if (supabaseStatus !== 'connected') {
            console.warn("Save search operation skipped: Not connected to Supabase.");
            return;
        }

        const originalSearches = pastSearches;
        setPastSearches(prev => [search, ...prev.filter(s => s.id !== search.id)].slice(0, 50));

        try {
            const supabaseSearch: SupabasePastSearch = {
                id: search.id,
                query: search.query,
                search_mode: search.searchMode,
                total_found: search.totalFound,
                results_data: search.results,
                filters: {
                    weights: search.weights,
                    filtersEnabled: search.filtersEnabled,
                },
                created_at: new Date(search.timestamp).toISOString(),
            };
            await supabase.searches.save(supabaseSearch);
        } catch (e) {
            console.error("Failed to save search to Supabase:", e);
            setPastSearches(originalSearches);
        }
    };
    
    const handleLoadSearch = (search: PastSearch) => {
        setActiveView('search');
        setSearchQuery(search.query);
        setHistorySearchToLoad(search);
    };

    const savedPackageNames = useMemo(() => new Set(savedPackages.map(p => p.package.name)), [savedPackages]);

    return (
        <div className="flex flex-col h-screen bg-primary text-text-primary font-sans">
            <Header
                activeView={activeView}
                onViewChange={setActiveView}
                onOpenSettings={() => setIsSettingsModalOpen(true)}
                pastSearches={pastSearches}
                onLoadSearch={handleLoadSearch}
                supabaseStatus={supabaseStatus}
                isSearching={isSearching}
                isSearchPaused={isSearchPaused}
                onStopSearch={handleStopSearch}
                onSearchPauseToggle={() => setIsSearchPaused(!isSearchPaused)}
                onSearchSubmit={setSearchQuery}
                searchQuery={searchQuery}
            />
             
            <main className="flex-1 flex flex-col overflow-hidden relative">
                {activeView === 'search' && (
                    <SearchView
                        searchQuery={searchQuery}
                        savedPackageNames={savedPackageNames}
                        onSavePackage={handleSavePackage}
                        onRemovePackage={handleRemovePackage}
                        onPackageClick={setSelectedPackage}
                        onSearchSave={handleSaveSearch}
                        isSearching={isSearching}
                        setIsSearching={setIsSearching}
                        isSearchPaused={isSearchPaused}
                        searchControllerRef={searchControllerRef}
                        historySearchToLoad={historySearchToLoad}
                        onHistorySearchLoaded={() => setHistorySearchToLoad(null)}
                        onSyncPackage={handleSyncPackage}
                        savedPackages={savedPackages}
                        supabaseStatus={supabaseStatus}
                    />
                )}
                {activeView === 'projects' && (
                    <ProjectsView
                        savedPackages={savedPackages}
                        onRemovePackage={handleRemovePackage}
                        onPackageClick={setSelectedPackage}
                        onSyncPackage={handleSyncPackage}
                        supabaseStatus={supabaseStatus}
                    />
                )}
                <SchemaSetupOverlay 
                    isVisible={showSchemaOverlay}
                    error={error}
                    onOpenSetupWizard={() => {
                        setShowSchemaOverlay(false);
                        setIsDbSetupModalOpen(true);
                    }}
                />
            </main>

            {selectedPackage && (
                <PackageDetailModal
                    pkg={selectedPackage}
                    onClose={() => setSelectedPackage(null)}
                />
            )}
            
            <SettingsModal
                isOpen={isSettingsModalOpen}
                onClose={() => setIsSettingsModalOpen(false)}
                onOpenSupabase={() => setIsSupabaseModalOpen(true)}
                onOpenAdminActions={() => setIsAdminActionsModalOpen(true)}
                supabaseStatus={supabaseStatus}
                supabaseError={error}
            />

            <SupabaseModal
                isOpen={isSupabaseModalOpen}
                onClose={() => setIsSupabaseModalOpen(false)}
                credentials={supabaseCreds}
                setCredentials={setSupabaseCreds}
                status={supabaseStatus}
                error={error}
            />

            <DatabaseSetupModal
                isOpen={isDbSetupModalOpen}
                onClose={() => setIsDbSetupModalOpen(false)}
                onVerificationSuccess={() => {
                    setIsDbSetupModalOpen(false);
                    connectToSupabase(supabaseCreds);
                }}
            />

            <AdminActionsModal
                isOpen={isAdminActionsModalOpen}
                onClose={() => setIsAdminActionsModalOpen(false)}
                onOpenDbSetup={() => setIsDbSetupModalOpen(true)}
                onHistoryCleared={() => setPastSearches([])}
            />
        </div>
    );
};

export default App;