import React, { useState, useEffect, useRef, useCallback } from 'react';
import { EnrichedNpmPackage, NpmSearchResult, PastSearch, SupabaseStatus } from '../../types';
import FilterHeader from '../shared/FilterHeader';
import SearchResultsGrid from './SearchResults';
import { searchNpm, getPackageVersionDetails, deepSearchNpm } from '../../services/searchService';
import { discoverPackages } from '../../services/geminiService';
import { useLocalStorage } from '../../hooks/useLocalStorage';
import { processWithConcurrency } from '../../utils/asyncUtils';
import { SearchIcon } from '../shared/icons/SearchIcon';
import { useDebounce } from '../../hooks/useDebounce';

interface SearchViewProps {
    searchQuery: string;
    savedPackageNames: Set<string>;
    savedPackages: EnrichedNpmPackage[];
    onSavePackage: (pkg: EnrichedNpmPackage) => void;
    onRemovePackage: (packageName: string) => void;
    onPackageClick: (pkg: EnrichedNpmPackage) => void;
    onSearchSave: (search: PastSearch) => void;
    onSyncPackage: (pkg: EnrichedNpmPackage) => void;
    isSearching: boolean;
    setIsSearching: (isSearching: boolean) => void;
    isSearchPaused: boolean;
    searchControllerRef: React.MutableRefObject<AbortController | null>;
    historySearchToLoad: PastSearch | null;
    onHistorySearchLoaded: () => void;
    supabaseStatus: SupabaseStatus;
}

const SearchView: React.FC<SearchViewProps> = ({
    searchQuery,
    savedPackageNames,
    savedPackages,
    onSavePackage,
    onRemovePackage,
    onPackageClick,
    onSearchSave,
    onSyncPackage,
    isSearching,
    setIsSearching,
    isSearchPaused,
    searchControllerRef,
    historySearchToLoad,
    onHistorySearchLoaded,
    supabaseStatus
}) => {
    const [results, setResults] = useState<EnrichedNpmPackage[]>([]);
    const [totalResults, setTotalResults] = useState(0);
    const [error, setError] = useState<string | null>(null);
    const [loadingMessage, setLoadingMessage] = useState('');

    const [searchMode, setSearchMode] = useLocalStorage('searchMode', 'general');
    const [weights, setWeights] = useLocalStorage('searchWeights', { quality: 1.0, popularity: 1.0, maintenance: 1.0 });
    const [filtersEnabled, setFiltersEnabled] = useLocalStorage('searchFiltersEnabled', { weighting: true });

    const debouncedSearchQuery = useDebounce(searchQuery, 300);

    useEffect(() => {
        if (historySearchToLoad) {
            if (searchControllerRef.current) {
                searchControllerRef.current.abort();
            }
            setIsSearching(false);
            setResults(historySearchToLoad.results || []);
            setTotalResults(historySearchToLoad.totalFound);
            setSearchMode(historySearchToLoad.searchMode);
            setWeights(historySearchToLoad.weights);
            setFiltersEnabled(historySearchToLoad.filtersEnabled);
            setError(null);
            onHistorySearchLoaded();
        }
    }, [historySearchToLoad, searchControllerRef, setIsSearching, onHistorySearchLoaded]);


    const enrichResults = useCallback(async (packages: NpmSearchResult[], signal: AbortSignal) => {
        const enriched: EnrichedNpmPackage[] = [];
        await processWithConcurrency({
            items: packages,
            processor: (pkg, sig) => getPackageVersionDetails(pkg.package.name, sig),
            concurrency: 8,
            onResult: (item, details) => {
                if(details) {
                    enriched.push({ ...item, details });
                }
            },
            signal,
        });
        
        if (signal.aborted) return;

        setResults(prev => {
            const newResults = [...prev];
            enriched.forEach(enrichedPkg => {
                const index = newResults.findIndex(r => r.package.name === enrichedPkg.package.name);
                if (index !== -1) {
                    newResults[index] = enrichedPkg;
                }
            });
            return newResults;
        });

    }, []);

    const executeSearch = useCallback(async (query: string, currentController: AbortController) => {
        if (!query.trim()) return;

        setResults([]);
        setTotalResults(0);
        setError(null);
        setIsSearching(true);

        const startTime = Date.now();
        const searchId = `${query}-${startTime}`;
        let finalResults: EnrichedNpmPackage[] = [];
        let finalTotal = 0;

        try {
            if (searchMode === 'discovery') {
                setLoadingMessage(`Asking Gemini about "${query}"...`);
                const recommendations = await discoverPackages(query);
                if (currentController.signal.aborted) return;
                
                setLoadingMessage(`Found ${recommendations.length} packages. Searching on NPM...`);
                const discoveryQuery = recommendations.map(r => r.packageName).join(' ');
                
                const { objects, total } = await searchNpm(discoveryQuery, weights, filtersEnabled.weighting, 0, 250, currentController.signal);
                finalTotal = total;
                setTotalResults(total);
                finalResults = objects.map(o => ({...o, details: undefined}));
                setResults(finalResults);
                await enrichResults(objects, currentController.signal);

            } else {
                 const finalQuery = searchMode === 'general' ? query : `${searchMode}:${query}`;
                 setLoadingMessage('Searching NPM...');
                
                if (searchMode === 'general' && query.length > 2) {
                     setLoadingMessage('Performing deep search...');
                    for await (const chunk of deepSearchNpm(finalQuery, weights, filtersEnabled.weighting, currentController.signal)) {
                        if (currentController.signal.aborted) break;
                        
                        while(isSearchPaused) {
                            if (currentController.signal.aborted) break;
                            await new Promise(resolve => setTimeout(resolve, 200));
                        }

                        finalTotal = chunk.totalFound;
                        setTotalResults(chunk.totalFound);
                        const newPackages = chunk.packages.map(p => ({...p, details: undefined}));
                        finalResults.push(...newPackages);
                        setResults(prev => [...prev, ...newPackages]);
                        enrichResults(chunk.packages, currentController.signal);
                        setLoadingMessage(`Deep search... (${chunk.totalFound} found, ${chunk.progress.toFixed(0)}%)`);
                    }
                } else {
                    const { objects, total } = await searchNpm(finalQuery, weights, filtersEnabled.weighting, 0, 250, currentController.signal);
                    finalTotal = total;
                    setTotalResults(total);
                    finalResults = objects.map(o => ({...o, details: undefined}));
                    setResults(finalResults);
                    await enrichResults(objects, currentController.signal);
                }
            }
             if (!currentController.signal.aborted) {
                onSearchSave({
                    id: searchId,
                    query: query,
                    timestamp: startTime,
                    results: finalResults.slice(0, 100).map(r => ({...r, details: undefined})),
                    totalFound: finalTotal,
                    searchMode,
                    weights,
                    filtersEnabled,
                });
            }

        } catch (err: any) {
            if (err.name !== 'AbortError') {
                setError(err.message || 'An unexpected error occurred.');
            }
        } finally {
            // FIX: This check ensures that only the LATEST search controller can reset the state.
            // This prevents a race condition where an old, aborted search's finally block
            // could incorrectly set isSearching to false.
            if (!currentController.signal.aborted || searchControllerRef.current === currentController) {
                setIsSearching(false);
                setLoadingMessage('');
            }
        }
    // FIX: Removed isSearchPaused from dependency array to prevent re-running the entire search effect on pause.
    // The generator inside already handles the pause logic correctly.
    }, [searchMode, weights, filtersEnabled, enrichResults, onSearchSave, setIsSearching, searchControllerRef]);


    useEffect(() => {
        if (historySearchToLoad || !debouncedSearchQuery) {
            if (!debouncedSearchQuery && !historySearchToLoad) {
                setResults([]);
                setTotalResults(0);
                setError(null);
            }
            return;
        }

        if (searchControllerRef.current) {
            searchControllerRef.current.abort();
        }
        
        const newController = new AbortController();
        searchControllerRef.current = newController;

        executeSearch(debouncedSearchQuery, newController);

        // FIX: The cleanup function now robustly resets the state if the component
        // unmounts or the query changes mid-search.
        return () => {
            newController.abort();
            if (searchControllerRef.current === newController) {
                 setIsSearching(false);
                 setLoadingMessage('');
            }
        }
    }, [debouncedSearchQuery, executeSearch, historySearchToLoad, searchControllerRef, setIsSearching]);


    return (
        <div className="h-full flex flex-col">
            <FilterHeader
                searchMode={searchMode}
                setSearchMode={setSearchMode}
                weights={weights}
                onWeightsChange={setWeights}
                filtersEnabled={filtersEnabled}
                setFiltersEnabled={setFiltersEnabled}
                isSearching={isSearching}
            />
            
            <div className="flex-1 overflow-y-auto">
                 {error && (
                    <div className="p-4 m-4 bg-danger/10 border border-danger text-danger text-sm rounded-md">
                        <p className="font-semibold">Search Failed</p>
                        <p>{error}</p>
                    </div>
                )}
                {results.length > 0 || isSearching ? (
                    <SearchResultsGrid
                        results={results}
                        totalResults={totalResults}
                        onSelectPackage={onPackageClick}
                        selectedPackageName={null}
                        savedPackages={savedPackages}
                        onSavePackage={onSavePackage}
                        onRemovePackage={onRemovePackage}
                        onSyncPackage={onSyncPackage}
                        isLoading={isSearching}
                        loadingMessage={loadingMessage}
                        supabaseStatus={supabaseStatus}
                    />
                ) : !isSearching && !error && (
                     <div className="flex flex-col items-center justify-center h-full text-center p-8">
                        <SearchIcon className="w-16 h-16 text-text-secondary mb-4" />
                        <h2 className="text-2xl font-bold text-text-primary">Find Your Next Package</h2>
                        <p className="text-text-secondary mt-2 max-w-md">
                           Start typing to search the NPM registry, or use Discovery mode for AI-powered recommendations.
                        </p>
                    </div>
                )}
            </div>
        </div>
    );
};

export default SearchView;