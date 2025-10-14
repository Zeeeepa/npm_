import React, { useState } from 'react';
import * as supabaseService from '../../services/supabaseService';
import ConfirmationModal from '../shared/ConfirmationModal';
import LoadingSpinner from '../shared/LoadingSpinner';
import { TrashIcon } from '../shared/icons/TrashIcon';
import { DatabaseIcon } from '../shared/icons/DatabaseIcon';

interface AdminActionsModalProps {
  isOpen: boolean;
  onClose: () => void;
  onOpenDbSetup: () => void;
  onHistoryCleared: () => void;
}

const AdminActionsModal: React.FC<AdminActionsModalProps> = ({ isOpen, onClose, onOpenDbSetup, onHistoryCleared }) => {
    const [isConfirmOpen, setIsConfirmOpen] = useState(false);
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);

    if (!isOpen) return null;

    const handleClearHistory = async () => {
        setIsConfirmOpen(false);
        setIsLoading(true);
        setError(null);
        try {
            await supabaseService.searches.clearAll();
            alert("All search history has been cleared successfully.");
            onHistoryCleared(); // Notify parent to update state
            onClose();
        } catch (e: any) {
            setError(e.message || "An unknown error occurred.");
        } finally {
            setIsLoading(false);
        }
    };
    
    return (
    <>
        <div className="fixed inset-0 bg-black bg-opacity-70 z-50 flex justify-center items-center p-4" onClick={onClose}>
            <div className="bg-secondary rounded-lg shadow-2xl border border-border-color w-full max-w-lg" onClick={e => e.stopPropagation()}>
                <div className="p-6">
                    <h2 className="text-xl font-bold text-text-primary mb-6 flex items-center gap-2">
                        Admin Actions
                    </h2>
                    
                    <div className="bg-tertiary p-4 rounded-lg border border-border-color space-y-4">
                        {/* Setup Action */}
                        <div className="flex flex-col sm:flex-row items-center justify-between gap-4">
                            <div className="flex-1">
                                <p className="text-sm font-medium">Database Setup Wizard</p>
                                <p className="text-xs text-text-secondary mt-1">
                                   Run the one-time setup to create or verify the required tables in your project.
                                </p>
                            </div>
                            <button
                                onClick={onOpenDbSetup}
                                className="w-full sm:w-auto flex-shrink-0 flex items-center justify-center gap-2 px-4 py-2 text-sm font-semibold rounded-md transition-colors bg-accent/80 text-white hover:bg-accent"
                            >
                                <DatabaseIcon className="w-4 h-4" />
                                Open Wizard
                            </button>
                        </div>
                        
                        {/* Destructive Action */}
                         <div className="flex flex-col sm:flex-row items-center justify-between gap-4 pt-4 border-t border-border-color/50">
                            <div className="flex-1">
                                <p className="text-sm font-medium text-yellow-400">Clear All Search History</p>
                                <p className="text-xs text-text-secondary mt-1">
                                    Permanently delete all search history from the database. This action cannot be undone.
                                </p>
                            </div>
                            <button
                                onClick={() => setIsConfirmOpen(true)}
                                disabled={isLoading}
                                className="w-full sm:w-auto flex-shrink-0 flex items-center justify-center gap-2 px-4 py-2 text-sm font-semibold rounded-md transition-colors bg-danger text-white hover:bg-danger/80 disabled:bg-gray-600"
                            >
                                {isLoading ? <LoadingSpinner className="h-4 w-4" /> : <TrashIcon className="w-4 h-4" />}
                                Clear History
                            </button>
                        </div>
                         {error && <p className="mt-2 text-sm text-danger text-center bg-danger/10 p-2 rounded-md">{error}</p>}
                    </div>
                </div>

                <div className="bg-tertiary px-6 py-4 flex justify-end items-center space-x-4 rounded-b-lg border-t border-border-color">
                    <button onClick={onClose} className="px-4 py-2 rounded-md bg-transparent border border-border-color text-text-primary hover:bg-border-color transition-colors">Close</button>
                </div>
            </div>
        </div>
        <ConfirmationModal
            isOpen={isConfirmOpen}
            onClose={() => setIsConfirmOpen(false)}
            onConfirm={handleClearHistory}
            title="Confirm Deletion"
            message="Are you sure you want to permanently delete all search history? This action cannot be undone."
            confirmText="Yes, Delete Everything"
        />
    </>
    );
};

export default AdminActionsModal;
