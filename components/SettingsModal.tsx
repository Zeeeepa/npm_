import React from 'react';
import { XIcon } from './shared/icons/XIcon';
import { DatabaseIcon } from './shared/icons/DatabaseIcon';
import { LockIcon } from './shared/icons/LockIcon';
import { SupabaseStatus } from '../types';

interface SettingsModalProps {
    isOpen: boolean;
    onClose: () => void;
    onOpenSupabase: () => void;
    onOpenAdminActions: () => void;
    supabaseStatus: SupabaseStatus;
    supabaseError: string | null;
}

const SettingsModal: React.FC<SettingsModalProps> = ({
    isOpen,
    onClose,
    onOpenSupabase,
    onOpenAdminActions,
    supabaseStatus,
    supabaseError
}) => {
    if (!isOpen) return null;
    
    const statusInfo = {
        connected: { text: 'Connected', color: 'text-green-400' },
        disconnected: { text: 'Disconnected', color: 'text-text-secondary' },
        error: { text: 'Error', color: 'text-red-400' },
        initializing: { text: 'Initializing...', color: 'text-yellow-400' },
        connecting: { text: 'Connecting...', color: 'text-blue-400' },
    };
    const currentStatus = statusInfo[supabaseStatus];

    return (
        <div className="fixed inset-0 bg-black bg-opacity-70 z-50 flex justify-center items-center p-4" onClick={onClose}>
            <div className="bg-secondary rounded-lg shadow-2xl border border-border-color w-full max-w-lg" onClick={e => e.stopPropagation()}>
                <header className="flex justify-between items-center p-4 border-b border-border-color">
                    <h2 className="text-lg font-bold">Settings</h2>
                    <button onClick={onClose} className="p-1 rounded-full hover:bg-tertiary">
                        <XIcon className="w-6 h-6" />
                    </button>
                </header>

                <div className="p-6 space-y-6">
                    {/* Sync Settings */}
                    <div className="bg-tertiary p-4 rounded-lg border border-border-color">
                        <h3 className="font-semibold mb-3">Sync &amp; Storage</h3>
                        <div className="flex flex-col sm:flex-row items-start justify-between gap-4">
                            <div className="flex-1">
                               <p className="text-sm font-medium flex items-center gap-2">
                                    Supabase Sync
                                    <span className={`text-xs font-bold ${currentStatus.color}`}>({currentStatus.text})</span>
                                </p>
                                <p className="text-xs text-text-secondary mt-1">
                                    Connect to a Supabase project to persist your saved packages and search history across sessions.
                                </p>
                                {supabaseStatus === 'error' && supabaseError && (
                                    <p className="text-xs text-red-400 mt-2 bg-red-500/10 p-2 rounded-md border border-red-500/20">{supabaseError}</p>
                                )}
                            </div>
                            <button
                                onClick={() => {
                                    onClose();
                                    onOpenSupabase();
                                }}
                                className="w-full sm:w-auto flex-shrink-0 flex items-center justify-center gap-2 px-4 py-2 text-sm font-semibold rounded-md transition-colors bg-accent/80 text-white hover:bg-accent"
                            >
                                <DatabaseIcon className="w-4 h-4" />
                                Configure
                            </button>
                        </div>
                    </div>
                     
                     {/* Admin Actions */}
                    {supabaseStatus === 'connected' && (
                         <div className="bg-tertiary p-4 rounded-lg border border-border-color">
                            <h3 className="font-semibold mb-3">Advanced</h3>
                            <div className="flex flex-col sm:flex-row items-center justify-between gap-4">
                                <div className="flex-1">
                                   <p className="text-sm font-medium">Admin Actions</p>
                                    <p className="text-xs text-text-secondary mt-1">
                                       Manage database schema and perform administrative tasks.
                                    </p>
                                </div>
                                <button
                                    onClick={() => {
                                        onClose();
                                        onOpenAdminActions();
                                    }}
                                    className="w-full sm:w-auto flex-shrink-0 flex items-center justify-center gap-2 px-4 py-2 text-sm font-semibold rounded-md transition-colors bg-yellow-600 text-white hover:bg-yellow-500"
                                >
                                    <LockIcon className="w-4 h-4" />
                                    Open Admin Panel
                                </button>
                            </div>
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
};

export default SettingsModal;