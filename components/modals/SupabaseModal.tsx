
import React, { useState, useEffect } from 'react';
import { SupabaseCredentials, SupabaseStatus } from '../../types';
import LoadingSpinner from '../shared/LoadingSpinner';
import { EyeIcon } from '../shared/icons/EyeIcon';
import { EyeSlashIcon } from '../shared/icons/EyeSlashIcon';
import { CheckIcon } from '../shared/icons/CheckIcon';
import { ExclamationIcon } from '../shared/icons/ExclamationIcon';
import { XIcon } from '../icons/XIcon';

interface SupabaseModalProps {
  isOpen: boolean;
  onClose: () => void;
  credentials: SupabaseCredentials;
  setCredentials: React.Dispatch<React.SetStateAction<SupabaseCredentials>>;
  status: SupabaseStatus;
  error: string | null;
}

const SupabaseModal: React.FC<SupabaseModalProps> = ({
  isOpen,
  onClose,
  credentials,
  setCredentials,
  status,
  error,
}) => {
  const [localCreds, setLocalCreds] = useState<SupabaseCredentials>(credentials);
  const [showAnonKey, setShowAnonKey] = useState(false);
  const [showSecretKey, setShowSecretKey] = useState(false);

  useEffect(() => {
    setLocalCreds(credentials);
  }, [credentials, isOpen]);

  const handleSaveAndConnect = () => {
    setCredentials(localCreds);
    // The connection will be triggered by the useEffect in App.tsx
    if (localCreds.url && localCreds.key) {
      onClose();
    }
  };

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setLocalCreds(prev => ({ ...prev, [name]: value }));
  };
  
  const isConnecting = status === 'connecting' || status === 'initializing';

  const statusIndicator = {
    connected: { text: 'Connected', color: 'text-green-400', icon: <CheckIcon className="w-5 h-5" /> },
    disconnected: { text: 'Disconnected', color: 'text-text-secondary', icon: <XIcon className="w-5 h-5" /> },
    error: { text: 'Connection Failed', color: 'text-red-400', icon: <ExclamationIcon className="w-5 h-5" /> },
    initializing: { text: 'Initializing...', color: 'text-yellow-400', icon: <LoadingSpinner className="h-5 w-5" />},
    connecting: { text: 'Connecting...', color: 'text-blue-400', icon: <LoadingSpinner className="h-5 w-5" />},
  };
  const currentStatus = statusIndicator[status];

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-70 z-50 flex justify-center items-center p-4" onClick={onClose}>
      <div className="bg-secondary rounded-lg shadow-2xl border border-border-color w-full max-w-lg" onClick={e => e.stopPropagation()}>
        <div className="p-6">
          <h2 className="text-xl font-bold text-text-primary mb-2">Supabase Configuration</h2>
          <p className="text-sm text-text-secondary mb-6">Connect to your Supabase project to sync saved packages and search history.</p>

          <div className="space-y-4">
            <div>
              <label htmlFor="url" className="block text-sm font-medium text-text-secondary mb-1">Project URL</label>
              <input type="text" id="url" name="url" value={localCreds.url} onChange={handleInputChange} className="w-full bg-primary border border-border-color rounded-md px-3 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-accent" placeholder="https://your-project-ref.supabase.co" />
            </div>

            <div>
              <label htmlFor="key" className="block text-sm font-medium text-text-secondary mb-1">Anon (Public) Key</label>
              <div className="relative">
                <input type={showAnonKey ? 'text' : 'password'} id="key" name="key" value={localCreds.key} onChange={handleInputChange} className="w-full bg-primary border border-border-color rounded-md px-3 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-accent pr-10" />
                <button onClick={() => setShowAnonKey(!showAnonKey)} className="absolute inset-y-0 right-0 px-3 text-text-secondary hover:text-text-primary">
                    {showAnonKey ? <EyeSlashIcon className="w-5 h-5"/> : <EyeIcon className="w-5 h-5" />}
                </button>
              </div>
            </div>

            <div>
              <label htmlFor="secretKey" className="block text-sm font-medium text-text-secondary mb-1">Service Role Key (Optional)</label>
              <div className="relative">
                <input type={showSecretKey ? 'text' : 'password'} id="secretKey" name="secretKey" value={localCreds.secretKey || ''} onChange={handleInputChange} className="w-full bg-primary border border-border-color rounded-md px-3 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-accent pr-10" />
                <button onClick={() => setShowSecretKey(!showSecretKey)} className="absolute inset-y-0 right-0 px-3 text-text-secondary hover:text-text-primary">
                    {showSecretKey ? <EyeSlashIcon className="w-5 h-5"/> : <EyeIcon className="w-5 h-5" />}
                </button>
              </div>
              <p className="text-xs text-text-secondary mt-1">Providing this key enables admin actions, like running the DB schema setup. <strong className="text-yellow-400">Never expose this key in a production frontend.</strong></p>
            </div>
          </div>
          {status === 'error' && error && (
              <div className="mt-4 p-3 bg-danger/10 border border-danger/50 rounded-md text-sm text-danger">
                  <p className="font-semibold">Error:</p>
                  <p>{error}</p>
              </div>
          )}
        </div>

        <div className="bg-tertiary px-6 py-4 flex justify-between items-center rounded-b-lg">
          <div className={`flex items-center gap-2 text-sm font-medium ${currentStatus.color}`}>
            {currentStatus.icon}
            {currentStatus.text}
          </div>
          <div className="flex items-center space-x-4">
            <button onClick={onClose} className="px-4 py-2 rounded-md bg-transparent border border-border-color text-text-primary hover:bg-border-color transition-colors">Cancel</button>
            <button
                onClick={handleSaveAndConnect}
                disabled={isConnecting || !localCreds.url || !localCreds.key}
                className="px-4 py-2 rounded-md transition-colors font-semibold bg-accent text-white hover:bg-accent/80 disabled:bg-gray-500 disabled:cursor-not-allowed flex items-center gap-2"
            >
              {isConnecting ? 'Please wait...' : 'Save & Connect'}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default SupabaseModal;