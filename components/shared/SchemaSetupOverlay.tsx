import React from 'react';
import { DatabaseIcon } from './icons/DatabaseIcon';
import { ExclamationIcon } from './icons/ExclamationIcon';

interface SchemaSetupOverlayProps {
  isVisible: boolean;
  onOpenSetupWizard: () => void;
  error: string | null;
}

const SchemaSetupOverlay: React.FC<SchemaSetupOverlayProps> = ({ isVisible, onOpenSetupWizard, error }) => {
  if (!isVisible) {
    return null;
  }

  return (
    <div className="absolute inset-0 bg-primary/90 backdrop-blur-sm z-20 flex flex-col items-center justify-center p-4 text-center">
      <div className="max-w-md p-6 bg-secondary border border-border-color rounded-lg shadow-xl">
        <div className="flex justify-center mb-4">
            <div className="relative">
                <DatabaseIcon className="w-16 h-16 text-text-secondary" />
                <div className="absolute -bottom-1 -right-1 bg-secondary rounded-full p-1">
                    <ExclamationIcon className="w-8 h-8 text-yellow-400" />
                </div>
            </div>
        </div>
        <h2 className="text-xl font-bold text-text-primary">Database Setup Required</h2>
        <p className="mt-2 text-sm text-text-secondary">
          Your Supabase project is connected, but the required database tables are missing or incomplete.
        </p>
        {error && (
            <p className="text-xs text-red-400 mt-3 bg-red-500/10 p-2 rounded-md border border-red-500/20">
                <strong>Error:</strong> {error}
            </p>
        )}
        <button
          onClick={onOpenSetupWizard}
          className="mt-6 w-full flex items-center justify-center gap-2 px-4 py-2 text-sm font-semibold rounded-md transition-colors bg-accent text-white hover:bg-accent/80"
        >
          <DatabaseIcon className="w-4 h-4" />
          Open Setup Wizard
        </button>
      </div>
    </div>
  );
};

export default SchemaSetupOverlay;
