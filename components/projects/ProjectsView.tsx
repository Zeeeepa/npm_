import React, { useState, useMemo } from 'react';
import { EnrichedNpmPackage, SupabaseStatus } from '../../types';
import PackageCard from '../shared/PackageCard';
import { CollectionIcon } from '../shared/icons/CollectionIcon';

interface ProjectsViewProps {
  savedPackages: EnrichedNpmPackage[];
  onRemovePackage: (packageName: string) => void;
  onPackageClick: (pkg: EnrichedNpmPackage) => void;
  onSyncPackage: (pkg: EnrichedNpmPackage) => void;
  supabaseStatus: SupabaseStatus;
}

type SortKey = 'name' | 'date' | 'size' | 'files' | 'deps' | 'syncStatus';

const ProjectsView: React.FC<ProjectsViewProps> = ({ savedPackages, onRemovePackage, onPackageClick, onSyncPackage, supabaseStatus }) => {
    const [sortKey, setSortKey] = useState<SortKey>('name');
    const [sortDir, setSortDir] = useState<'asc' | 'desc'>('asc');

    const sortedPackages = useMemo(() => {
        return [...savedPackages].sort((a, b) => {
            let valA: number | string = 0;
            let valB: number | string = 0;

            switch (sortKey) {
                case 'name':
                    valA = a.package.name.toLowerCase();
                    valB = b.package.name.toLowerCase();
                    break;
                case 'date':
                    valA = new Date(a.package.date).getTime();
                    valB = new Date(b.package.date).getTime();
                    break;
                case 'size':
                    valA = a.details?.dist.unpackedSize || 0;
                    valB = b.details?.dist.unpackedSize || 0;
                    break;
                case 'files':
                    valA = a.details?.dist.fileCount || 0;
                    valB = b.details?.dist.fileCount || 0;
                    break;
                case 'deps':
                    valA = Object.keys(a.details?.dependencies || {}).length;
                    valB = Object.keys(b.details?.dependencies || {}).length;
                    break;
                case 'syncStatus':
                    valA = a.syncStatus || 'not_synced';
                    valB = b.syncStatus || 'not_synced';
                    break;
            }

            if (typeof valA === 'string' && typeof valB === 'string') {
                 return sortDir === 'asc' ? valA.localeCompare(valB) : valB.localeCompare(valA);
            }
            if (valA < valB) return sortDir === 'asc' ? -1 : 1;
            if (valA > valB) return sortDir === 'asc' ? 1 : -1;
            return 0;
        });
    }, [savedPackages, sortKey, sortDir]);

    const handleSort = (key: SortKey) => {
      if (key === sortKey) {
          setSortDir(prev => prev === 'asc' ? 'desc' : 'asc');
      } else {
          setSortKey(key);
          setSortDir(key === 'name' ? 'asc' : 'desc');
      }
    }

    const SortButton: React.FC<{ sortField: SortKey, label: string }> = ({ sortField, label }) => (
        <button
          onClick={() => handleSort(sortField)}
          className={`px-3 py-1 text-xs rounded-full transition-colors ${sortKey === sortField ? 'bg-accent text-white font-semibold' : 'bg-tertiary text-text-secondary hover:bg-border-color'}`}
        >
            {label} {sortKey === sortField && (sortDir === 'asc' ? '▲' : '▼')}
        </button>
    );

    if (savedPackages.length === 0) {
        return (
            <div className="flex flex-col items-center justify-center h-full text-center p-8">
                <CollectionIcon className="w-16 h-16 text-text-secondary mb-4" />
                <h2 className="text-2xl font-bold text-text-primary">Your Projects Catalog is Empty</h2>
                <p className="text-text-secondary mt-2 max-w-md">
                    Go to the 'Search' tab to find and add packages to your collection.
                </p>
            </div>
        );
    }
    
    return (
        <div className="h-full flex flex-col">
            <div className="p-4 border-b border-border-color sticky top-0 bg-primary z-10">
                <p className="text-sm text-text-secondary mb-3">You have {savedPackages.length} saved packages.</p>
                 <div className="flex flex-wrap items-center gap-2">
                    <span className="text-xs text-text-secondary">Sort by:</span>
                    <SortButton sortField="name" label="Name" />
                    <SortButton sortField="date" label="Date" />
                    <SortButton sortField="size" label="Size" />
                    <SortButton sortField="files" label="Files" />
                    <SortButton sortField="deps" label="Deps" />
                    <SortButton sortField="syncStatus" label="Sync Status" />
                </div>
            </div>
            <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 2xl:grid-cols-6 gap-4 p-4 overflow-y-auto">
                {sortedPackages.map(pkg => (
                    <PackageCard
                        key={pkg.package.name}
                        pkg={pkg}
                        onSelect={() => onPackageClick(pkg)}
                        isSaved={true}
                        onSave={() => {}}
                        onRemove={onRemovePackage}
                        isSelected={false}
                        onSync={onSyncPackage}
                        supabaseStatus={supabaseStatus}
                    />
                ))}
            </div>
        </div>
    );
};

export default ProjectsView;