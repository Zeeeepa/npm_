
import React from 'react';
import { SupabaseStatus } from '../../types';
import { CheckIcon } from './icons/CheckIcon';
import { ExclamationIcon } from './icons/ExclamationIcon';
import { XIcon } from './icons/XIcon';
import LoadingSpinner from './LoadingSpinner';

interface SupabaseStatusIndicatorProps {
  status: SupabaseStatus;
  isConnecting: boolean;
  onClick: () => void;
}

const SupabaseStatusIndicator: React.FC<SupabaseStatusIndicatorProps> = ({ status, isConnecting, onClick }) => {
  // FIX: Added missing 'initializing' and 'connecting' statuses to the statusInfo object.
  const statusInfo: Record<SupabaseStatus, { text: string, color: string, icon: React.ReactNode }> = {
    connected: { text: 'Connected', color: 'text-green-400', icon: <CheckIcon className="w-4 h-4" /> },
    disconnected: { text: 'Disconnected', color: 'text-text-secondary', icon: <XIcon className="w-4 h-4" /> },
    error: { text: 'Connection Failed', color: 'text-red-400', icon: <ExclamationIcon className="w-4 h-4" /> },
    initializing: { text: 'Initializing...', color: 'text-yellow-400', icon: <LoadingSpinner className="h-4 w-4" /> },
    connecting: { text: 'Connecting...', color: 'text-blue-400', icon: <LoadingSpinner className="h-4 w-4" /> },
  };

  const currentStatus = statusInfo[status];

  return (
    <button
      onClick={onClick}
      className="flex items-center gap-2 px-3 py-1.5 rounded-md bg-tertiary hover:bg-border-color transition-colors text-sm"
      title="Open Supabase Configuration"
    >
      <span className="font-semibold text-text-primary">Supabase:</span>
      <div className={`flex items-center gap-1.5 font-medium ${currentStatus.color}`}>
        {isConnecting ? (
          <>
            <LoadingSpinner className="h-4 w-4" />
            <span>Connecting...</span>
          </>
        ) : (
          <>
            {currentStatus.icon}
            <span>{currentStatus.text}</span>
          </>
        )}
      </div>
    </button>
  );
};

export default SupabaseStatusIndicator;
