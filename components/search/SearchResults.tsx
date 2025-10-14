import React, { useState, useMemo } from 'react';
import { EnrichedNpmPackage, SupabaseStatus } from '../../types';
import PackageCard from '../shared/PackageCard';
import LoadingSpinner from '../shared/LoadingSpinner';
import { SortIcon } from '../shared/icons/SortIcon';

interface SearchResultsGridProps {
  results: EnrichedNpmPackage[];
  totalResults: number;
  onSelectPackage: (pkg: EnrichedNpmPackage) => void;
  selectedPackageName: string | null;
  savedPackages: EnrichedNpmPackage[];
  onSavePackage: (pkg: EnrichedNpmPackage) => void;
  onRemovePackage: (packageName: string) => void;
  onSyncPackage: (pkg: EnrichedNpmPackage) => void;
  isLoading: boolean;
  loadingMessage?: string;
  supabaseStatus: SupabaseStatus;
}

type SortKey = 'searchScore' | 'popularity' | 'date' | 'size' | 'files' | 'deps';
const sortOptions: { value: SortKey; label: string }[] = [
    { value: 'searchScore', label: 'Relevance' },
    { value: 'popularity', label: 'Popularity' },
    { value: 'date', label: 'Date' },
    { value: 'size', label: 'Size' },
    { value: 'files', label: 'Files' },
    { value: 'deps', label: 'Dependencies' },
];

const SearchResultsGrid: React.FC<SearchResultsGridProps> = ({ 
    results, totalResults, onSelectPackage, selectedPackageName,
    savedPackages, onSavePackage, onRemovePackage, onSyncPackage,
    isLoading, loadingMessage, supabaseStatus
}) => {
    const [sortKey, setSortKey] = useState<SortKey>('searchScore');
    const [sortDir, setSortDir] = useState<'asc' | 'desc'>('desc');
    
    const [dateFilter, setDateFilter] = useState({ enabled: false, value: '' });
    const [sizeFilter, setSizeFilter] = useState({ enabled: false, value: '' });
    const [fileCountFilter, setFileCountFilter] = useState({ enabled: false, value: '' });

    const filteredAndSortedResults = useMemo(() => {
        const filtered = results.filter(pkg => {
            if (dateFilter.enabled && dateFilter.value) {
                try {
                    if (new Date(pkg.package.date).getTime() < new Date(dateFilter.value).getTime()) return false;
                } catch(e) { /* ignore invalid date */ }
            }
            const minSizeKb = parseInt(sizeFilter.value, 10);
            if (sizeFilter.enabled && !isNaN(minSizeKb) && minSizeKb > 0) {
                 if (!pkg.details || (pkg.details.dist?.unpackedSize ?? 0) < (minSizeKb * 1024)) return false;
            }
            const minFileCount = parseInt(fileCountFilter.value, 10);
             if (fileCountFilter.enabled && !isNaN(minFileCount) && minFileCount > 0) {
                 if (!pkg.details || (pkg.details.dist?.fileCount ?? 0) < minFileCount) return false;
            }
            return true;
        });

        return [...filtered].sort((a, b) => {
            if (['size', 'files', 'deps'].includes(sortKey)) {
                if (!!a.details && !b.details) return -1;
                if (!a.details && !!b.details) return 1;
            }
            let valA: number | string = 0;
            let valB: number | string = 0;
            switch (sortKey) {
                case 'searchScore': valA = a.searchScore; valB = b.searchScore; break;
                case 'popularity': valA = a.score.detail.popularity; valB = b.score.detail.popularity; break;
                case 'date': valA = new Date(a.package.date).getTime(); valB = new Date(b.package.date).getTime(); break;
                case 'size': valA = a.details?.dist?.unpackedSize || 0; valB = b.details?.dist?.unpackedSize || 0; break;
                case 'files': valA = a.details?.dist?.fileCount || 0; valB = b.details?.dist?.fileCount || 0; break;
                case 'deps': valA = Object.keys(a.details?.dependencies || {}).length; valB = Object.keys(b.details?.dependencies || {}).length; break;
            }
            if (valA < valB) return sortDir === 'asc' ? -1 : 1;
            if (valA > valB) return sortDir === 'asc' ? 1 : -1;
            return b.searchScore - a.searchScore;
        });
    }, [results, sortKey, sortDir, dateFilter, sizeFilter, fileCountFilter]);
  
    const getStatusText = () => {
      const isFiltered = dateFilter.enabled || sizeFilter.enabled || fileCountFilter.enabled;
      const loadedCount = results.length.toLocaleString();
      const displayCount = filteredAndSortedResults.length.toLocaleString();
      if (isLoading && loadingMessage) return `${loadingMessage} (${loadedCount} loaded)`;
      if (isLoading && results.length > 0) return `Loading... (${loadedCount} loaded)`;
      if (isFiltered) return `Displaying ${displayCount} of ${loadedCount} loaded packages.`;
      return `Displaying ${displayCount} of ${totalResults.toLocaleString()} packages.`;
    }
  
    const savedPackagesMap = useMemo(() => new Map(savedPackages.map(p => [p.package.name, p])), [savedPackages]);

    return (
    <div>
        <div className="p-4 sticky top-0 bg-primary z-10 border-b border-border-color space-y-3">
            <p className="text-sm text-text-secondary flex items-center gap-2">
                {getStatusText()}
                {isLoading && <LoadingSpinner className="h-4 w-4 text-accent" />}
            </p>
            <div className="flex flex-wrap items-center gap-x-4 gap-y-2">
                <div className="flex items-center gap-2">
                    <label htmlFor="sort-key" className="text-xs font-medium text-text-secondary">Sort by</label>
                    <select id="sort-key" value={sortKey} onChange={e => setSortKey(e.target.value as SortKey)} className="bg-tertiary border border-border-color rounded-md px-2 py-1 text-xs focus:outline-none focus:ring-1 focus:ring-accent">
                        {sortOptions.map(opt => <option key={opt.value} value={opt.value}>{opt.label}</option>)}
                    </select>
                    <button onClick={() => setSortDir(p => p === 'asc' ? 'desc' : 'asc')} className="p-1 rounded-md bg-tertiary hover:bg-border-color" title={`Sort ${sortDir === 'asc' ? 'Descending' : 'Ascending'}`}>
                        <SortIcon direction={sortDir} className="w-4 h-4 text-text-secondary" />
                    </button>
                </div>
                <div className="flex flex-wrap items-center gap-x-4 gap-y-2">
                    <span className="text-xs font-medium text-text-secondary">Filter</span>
                    <div className="flex items-center gap-2">
                        <input type="checkbox" id="date-filter-cb" checked={dateFilter.enabled} onChange={e => setDateFilter(p => ({...p, enabled: e.target.checked}))} className="h-4 w-4 rounded bg-tertiary border-border-color text-accent focus:ring-accent" />
                        <label htmlFor="date-filter-cb" className="text-xs text-text-primary select-none">Published Since</label>
                        <input type="date" value={dateFilter.value} onChange={e => setDateFilter(p => ({...p, value: e.target.value}))} disabled={!dateFilter.enabled} className="bg-tertiary border border-border-color rounded-md px-2 py-1 text-xs disabled:opacity-50" />
                    </div>
                    <div className="flex items-center gap-2">
                        <input type="checkbox" id="size-filter-cb" checked={sizeFilter.enabled} onChange={e => setSizeFilter(p => ({...p, enabled: e.target.checked}))} className="h-4 w-4 rounded bg-tertiary border-border-color text-accent focus:ring-accent" />
                        <label htmlFor="size-filter-cb" className="text-xs text-text-primary select-none">Min Size (KB)</label>
                        <input type="number" min="0" value={sizeFilter.value} onChange={e => setSizeFilter(p => ({...p, value: e.target.value}))} disabled={!sizeFilter.enabled} className="bg-tertiary border border-border-color rounded-md px-2 py-1 text-xs w-20 disabled:opacity-50" />
                    </div>
                    <div className="flex items-center gap-2">
                        <input type="checkbox" id="files-filter-cb" checked={fileCountFilter.enabled} onChange={e => setFileCountFilter(p => ({...p, enabled: e.target.checked}))} className="h-4 w-4 rounded bg-tertiary border-border-color text-accent focus:ring-accent" />
                        <label htmlFor="files-filter-cb" className="text-xs text-text-primary select-none">Min Files</label>
                        <input type="number" min="0" value={fileCountFilter.value} onChange={e => setFileCountFilter(p => ({...p, value: e.target.value}))} disabled={!fileCountFilter.enabled} className="bg-tertiary border border-border-color rounded-md px-2 py-1 text-xs w-20 disabled:opacity-50" />
                    </div>
                </div>
            </div>
        </div>

        {filteredAndSortedResults.length > 0 ? (
            <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-5 xl:grid-cols-6 2xl:grid-cols-7 gap-4 p-4">
                {filteredAndSortedResults.map((pkg) => {
                    const savedVersion = savedPackagesMap.get(pkg.package.name);
                    const isSaved = !!savedVersion;
                    const finalPkg = isSaved ? { ...pkg, syncStatus: savedVersion.syncStatus } : pkg;
                    return (
                        <PackageCard
                            key={pkg.package.name}
                            pkg={finalPkg}
                            onSelect={onSelectPackage}
                            isSaved={isSaved}
                            onSave={onSavePackage}
                            onRemove={onRemovePackage}
                            onSync={onSyncPackage}
                            isSelected={selectedPackageName === pkg.package.name}
                            supabaseStatus={supabaseStatus}
                        />
                    );
                })}
            </div>
        ) : (
            !isLoading && <div className="p-8 text-center text-text-secondary">No packages match your filter criteria.</div>
        )}
    </div>
  );
};

export default SearchResultsGrid;