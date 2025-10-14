import React from 'react';
import { EnrichedNpmPackage, SupabaseStatus } from '../../types';
import { timeAgo, formatBytes } from '../../utils/formatters';
import { ClockIcon } from './icons/ClockIcon';
import { CollectionIcon } from './icons/CollectionIcon';
import { DatabaseIcon } from './icons/DatabaseIcon';
import { DocumentIcon } from './icons/DocumentIcon';
import { PlusIcon } from './icons/PlusIcon';
import { TrashIcon } from './icons/TrashIcon';
import { SyncIcon } from './icons/SyncIcon';
import { CheckIcon } from './icons/CheckIcon';
import { getTimeColor, getSizeColor, getFileCountColor } from '../../utils/colorStyles';
import LoadingSpinner from './LoadingSpinner';

interface PackageCardProps {
  pkg: EnrichedNpmPackage;
  onSelect: (pkg: EnrichedNpmPackage) => void;
  isSaved: boolean;
  onSave: (pkg: EnrichedNpmPackage) => void;
  onRemove: (packageName: string) => void;
  onSync: (pkg: EnrichedNpmPackage) => void;
  isSelected: boolean;
  supabaseStatus: SupabaseStatus;
}

const Stat: React.FC<{icon: React.ReactNode, value: React.ReactNode, title: string, color?: string}> = ({ icon, value, title, color }) => (
    <span className="flex items-center" title={title}>
        {icon}
        <span style={{ color: color || 'inherit' }}>{value}</span>
    </span>
);

const SkeletonStat: React.FC<{icon: React.ReactNode}> = ({icon}) => (
    <span className="flex items-center animate-pulse">
        {icon}
        <span className="h-3 w-10 bg-tertiary rounded-sm"></span>
    </span>
)

const PackageCard: React.FC<PackageCardProps> = ({ pkg, onSelect, isSaved, onSave, onRemove, onSync, isSelected, supabaseStatus }) => {
    
    const { package: p, details, syncStatus } = pkg;
    const depCount = details ? Object.keys(details.dependencies || {}).length : null;

    const timeColor = getTimeColor(p.date);
    const sizeColor = details ? getSizeColor(details.dist?.unpackedSize ?? 0) : undefined;
    const fileCountColor = details ? getFileCountColor(details.dist?.fileCount ?? 0) : undefined;

    const handleActionClick = (e: React.MouseEvent) => {
        e.stopPropagation();
        if (isSaved) onRemove(p.name);
        else onSave(pkg);
    }
    
    const handleSyncClick = (e: React.MouseEvent) => {
        e.stopPropagation();
        if (syncStatus !== 'syncing' && syncStatus !== 'synced') {
            onSync(pkg);
        }
    };

    const isConnected = supabaseStatus === 'connected';

    const renderSyncButton = () => {
        if (!isSaved) return null;
        switch (syncStatus) {
            case 'syncing':
                return (
                    <div className="flex-shrink-0 flex items-center gap-1.5 text-xs font-semibold px-2 py-1.5 rounded-md bg-blue-500/10 text-blue-400">
                        <LoadingSpinner className="w-4 h-4" />
                        Syncing
                    </div>
                );
            case 'synced':
                return (
                    <div className="flex-shrink-0 flex items-center gap-1.5 text-xs font-semibold px-2 py-1.5 rounded-md bg-green-500/10 text-green-400" title="Package contents are synced">
                       <CheckIcon className="w-4 h-4" />
                       Synced
                   </div>
               );
            case 'not_synced':
            default:
                 return (
                    <button
                        onClick={handleSyncClick}
                        disabled={!isConnected}
                        className="flex-shrink-0 flex items-center gap-1.5 text-xs font-semibold px-2 py-1.5 rounded-md transition-colors duration-200 bg-blue-500/10 text-blue-400 hover:bg-blue-500/20 disabled:opacity-50 disabled:cursor-not-allowed disabled:hover:bg-blue-500/10"
                        title={isConnected ? "Sync package contents to Supabase" : "Connect to Supabase to enable sync"}
                    >
                        <SyncIcon className="w-4 h-4" />
                        Sync
                    </button>
                );
        }
    }


    return (
        <div
            onClick={() => onSelect(pkg)}
            className={`bg-secondary border rounded-lg p-3 flex flex-col justify-between hover:border-accent transition-all duration-200 h-full cursor-pointer shadow-lg ${isSelected ? 'border-accent ring-2 ring-accent' : 'border-border-color'}`}
        >
            <div>
                <div className="flex justify-between items-start mb-2">
                    <h3 className="font-semibold text-sm text-accent group-hover:underline truncate pr-2" title={p.name}>
                        {p.name}
                    </h3>
                    <span className="text-xs bg-tertiary text-text-secondary px-2 py-0.5 rounded-full shrink-0">
                        v{p.version}
                    </span>
                </div>
                <p className="text-xs text-text-secondary mb-3 break-words h-10 overflow-hidden">{p.description || 'No description available.'}</p>
            </div>

            <div className="mt-auto pt-2 border-t border-border-color/50">
                <div className="grid grid-cols-2 gap-x-3 gap-y-1.5 text-xs text-text-secondary mb-3">
                    <Stat icon={<ClockIcon className="w-3.5 h-3.5 mr-1.5"/>} value={timeAgo(p.date)} title="Last Publish" color={timeColor}/>
                    {details ? (<Stat icon={<DatabaseIcon className="w-3.5 h-3.5 mr-1.5"/>} value={formatBytes(details.dist?.unpackedSize ?? 0)} title="Unpacked Size" color={sizeColor}/>) : (<SkeletonStat icon={<DatabaseIcon className="w-3.5 h-3.5 mr-1.5"/>}/>) }
                    {details ? (<Stat icon={<DocumentIcon className="w-3.5 h-3.5 mr-1.5"/>} value={`${details.dist?.fileCount ?? 0} files`} title="File Count" color={fileCountColor}/>) : (<SkeletonStat icon={<DocumentIcon className="w-3.5 h-3.5 mr-1.5"/>}/>) }
                    {depCount != null ? (<Stat icon={<CollectionIcon className="w-3.5 h-3.5 mr-1.5"/>} value={`${depCount} deps`} title="Dependencies"/>) : (<SkeletonStat icon={<CollectionIcon className="w-3.5 h-3.5 mr-1.5"/>}/>) }
                </div>

                <div className="flex items-center gap-2">
                    <button
                        onClick={handleActionClick}
                        disabled={!isConnected}
                        title={!isConnected ? "Connect to Supabase to save/remove packages" : (isSaved ? "Remove package" : "Save package")}
                        className={`w-full flex items-center justify-center gap-1.5 text-xs font-semibold px-2 py-1.5 rounded-md transition-colors duration-200 disabled:opacity-50 disabled:cursor-not-allowed ${
                            isSaved 
                            ? 'bg-danger/10 text-danger hover:bg-danger/20 disabled:hover:bg-danger/10'
                            : 'bg-accent/10 text-accent hover:bg-accent/20 disabled:hover:bg-accent/10'
                        }`}
                    >
                        {isSaved ? <TrashIcon className="w-4 h-4" /> : <PlusIcon className="w-4 h-4" />}
                        {isSaved ? 'Remove' : 'Save'}
                    </button>
                    {renderSyncButton()}
                </div>
            </div>
        </div>
    );
};

export default PackageCard;