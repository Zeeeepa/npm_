import React, { useState, useEffect } from 'react';
import { CogIcon } from './icons/CogIcon';
import { SearchIcon } from './icons/SearchIcon';
import { CollectionIcon } from './icons/CollectionIcon';
import { HistoryIcon } from './icons/HistoryIcon';
import { StopIcon } from './icons/StopIcon';
import { PauseIcon } from './icons/PauseIcon';
import { PlayIcon } from './icons/PlayIcon';
import { SupabaseStatus, PastSearch } from '../../types';
import { timeAgo } from '../../utils/formatters';
import { CheckIcon } from './icons/CheckIcon';
import { ExclamationIcon } from './icons/ExclamationIcon';
import { XIcon } from './icons/XIcon';
import LoadingSpinner from './LoadingSpinner';

interface HeaderProps {
    activeView: 'search' | 'projects';
    onViewChange: (view: 'search' | 'projects') => void;
    onOpenSettings: () => void;
    pastSearches: PastSearch[];
    onLoadSearch: (search: PastSearch) => void;
    supabaseStatus: SupabaseStatus;
    
    // Search control props
    isSearching: boolean;
    isSearchPaused: boolean;
    onStopSearch: () => void;
    onSearchPauseToggle: () => void;
    onSearchSubmit: (query: string) => void;
    searchQuery: string;
}

const NavButton: React.FC<{label: string, icon: React.ReactNode, isActive: boolean, onClick: () => void}> = ({ label, icon, isActive, onClick }) => (
     <button
        onClick={onClick}
        className={`flex items-center gap-2 px-4 py-2 rounded-md text-sm font-semibold transition-colors ${
            isActive
                ? 'bg-accent text-white'
                : 'text-text-secondary hover:bg-tertiary hover:text-text-primary'
        }`}
    >
        {icon}
        {label}
    </button>
);

const Header: React.FC<HeaderProps> = ({ 
    activeView, onViewChange, onOpenSettings, pastSearches, onLoadSearch, supabaseStatus,
    isSearching, isSearchPaused, onStopSearch, onSearchPauseToggle, onSearchSubmit,
    searchQuery
}) => {
    const [isHistoryOpen, setIsHistoryOpen] = useState(false);
    const [query, setQuery] = useState(searchQuery);

    useEffect(() => {
        setQuery(searchQuery);
    }, [searchQuery]);
    
    const handleSearchSubmit = (e: React.FormEvent) => {
        e.preventDefault();
        if (query.trim() && !isSearching) {
            onSearchSubmit(query);
        }
    };


    const StatusIndicator: React.FC<{ status: SupabaseStatus }> = ({ status }) => {
        const statusInfo = {
            initializing: { text: 'Initializing...', color: 'text-yellow-400' },
            connecting: { text: 'Connecting...', color: 'text-blue-400' },
            connected: { text: 'Connected', color: 'text-green-400' },
            disconnected: { text: 'Disconnected', color: 'text-gray-400' },
            error: { text: 'Error', color: 'text-red-400' },
        };
        const current = statusInfo[status];

        const getIcon = () => {
            switch (status) {
                case 'initializing':
                case 'connecting':
                    return <LoadingSpinner className="w-3 h-3" />;
                case 'connected':
                    return <div className="w-2 h-2 rounded-full bg-green-500" />;
                case 'disconnected':
                    return <div className="w-2 h-2 rounded-full bg-gray-500" />;
                case 'error':
                    return <div className="w-2 h-2 rounded-full bg-red-500" />;
                default:
                    return null;
            }
        };

        return (
            <div className="flex items-center gap-1.5" title={`Supabase: ${current.text}`}>
                {getIcon()}
                <span className={`text-xs ${current.color}`}>{current.text}</span>
            </div>
        );
    };

    return (
        <header className="flex-shrink-0 bg-secondary border-b border-border-color h-16 flex items-center justify-between px-4 gap-4">
            <div className="flex items-center gap-4">
                 <div className="flex items-center gap-2">
                    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor" className="w-7 h-7 text-accent">
                        <path d="M12.378 1.602a.75.75 0 00-.756 0L3 6.632l9 5.25 9-5.25-8.622-5.03zM21.75 7.93l-9 5.25v9l8.628-5.032a.75.75 0 00.372-.648V7.93zM11.25 22.18v-9l-9-5.25v8.57a.75.75 0 00.372.648l8.628 5.032z" />
                    </svg>
                    <h1 className="text-lg font-bold hidden md:block">NPM Explorer</h1>
                </div>
                <div className="h-8 w-px bg-border-color" />
                <NavButton label="Search" icon={<SearchIcon className="w-5 h-5" />} isActive={activeView === 'search'} onClick={() => onViewChange('search')} />
                <NavButton label="Projects" icon={<CollectionIcon className="w-5 h-5" />} isActive={activeView === 'projects'} onClick={() => onViewChange('projects')} />
            </div>
            
            {/* Search Bar & Controls */}
            <div className="flex-1 flex justify-center px-4">
                 <form onSubmit={handleSearchSubmit} className="w-full max-w-lg relative flex items-center">
                    <input
                        type="text"
                        value={query}
                        onChange={(e) => setQuery(e.target.value)}
                        placeholder={
                            activeView === 'search' 
                            ? "Search packages or describe what you need..." 
                            : "Switch to Search view to find packages"
                        }
                        className="w-full bg-primary border border-border-color rounded-md pl-10 pr-20 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-accent"
                        disabled={activeView !== 'search'}
                    />
                    <SearchIcon className="absolute left-3 w-5 h-5 text-text-secondary" />
                    {!isSearching && (
                        <button type="submit" disabled={!query.trim() || activeView !== 'search'} className="absolute right-1 top-1/2 -translate-y-1/2 px-3 py-1 text-xs font-semibold rounded-md bg-accent text-white hover:bg-accent/80 disabled:bg-gray-600 disabled:cursor-not-allowed">
                            Search
                        </button>
                    )}
                </form>
            </div>


            <div className="flex items-center gap-2 relative">
                <button
                    onClick={() => setIsHistoryOpen(prev => !prev)}
                    className="flex items-center gap-2 px-3 py-1.5 rounded-md bg-tertiary hover:bg-border-color transition-colors text-sm"
                >
                    <HistoryIcon className="w-5 h-5 text-text-secondary" />
                    <span className="hidden sm:inline">History</span>
                </button>
                
                {isHistoryOpen && (
                    <div className="absolute top-full right-0 mt-2 w-72 bg-secondary border border-border-color rounded-lg shadow-2xl z-30">
                        <div className="p-3 border-b border-border-color">
                            <h3 className="font-semibold text-sm">Recent Searches</h3>
                        </div>
                        {pastSearches.length > 0 ? (
                            <ul className="py-2 max-h-96 overflow-y-auto">
                                {pastSearches.map(search => (
                                     <li key={search.id}>
                                        <button
                                            onClick={() => {
                                                onLoadSearch(search);
                                                setIsHistoryOpen(false);
                                            }}
                                            className="w-full text-left px-3 py-2 hover:bg-tertiary transition-colors"
                                        >
                                            <p className="text-sm text-text-primary truncate font-medium" title={search.query}>{search.query}</p>
                                            <p className="text-xs text-text-secondary mt-0.5">{timeAgo(new Date(search.timestamp).toISOString())}</p>
                                        </button>
                                    </li>
                                ))}
                            </ul>
                        ): (
                            <p className="p-4 text-xs text-text-secondary text-center">No recent searches.</p>
                        )}
                    </div>
                )}
                 
                {isSearching && (
                    <div className="flex items-center gap-2">
                         <button onClick={onStopSearch} className="px-3 py-1.5 rounded-md bg-danger/20 text-danger hover:bg-danger/30 flex items-center gap-2" title="Stop Search">
                            <StopIcon className="w-5 h-5" /> <span className="hidden md:inline">Stop</span>
                        </button>
                        <button onClick={onSearchPauseToggle} className="px-3 py-1.5 rounded-md bg-yellow-500/20 text-yellow-400 hover:bg-yellow-500/30 flex items-center gap-2" title={isSearchPaused ? "Continue Search" : "Pause Search"}>
                            {isSearchPaused ? <PlayIcon className="w-5 h-5"/> : <PauseIcon className="w-5 h-5" />}
                            <span className="hidden md:inline">{isSearchPaused ? "Continue" : "Pause"}</span>
                        </button>
                    </div>
                )}
            </div>

            <div className="flex items-center gap-4">
                <StatusIndicator status={supabaseStatus} />
                <button
                    onClick={onOpenSettings}
                    className="p-2 rounded-full text-text-secondary hover:bg-tertiary hover:text-text-primary transition-colors"
                    title="Settings"
                >
                    <CogIcon className="w-6 h-6" />
                </button>
            </div>
        </header>
    );
};

export default Header;