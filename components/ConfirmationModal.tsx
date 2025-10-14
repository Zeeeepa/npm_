import React from 'react';

interface ConfirmationModalProps {
  isOpen: boolean;
  onClose: () => void;
  onConfirm: () => void;
  title: string;
  message: string;
  confirmText?: string;
  confirmButtonClass?: string;
}

const ConfirmationModal: React.FC<ConfirmationModalProps> = ({ 
  isOpen, 
  onClose, 
  onConfirm, 
  title, 
  message, 
  confirmText = "Confirm", 
  confirmButtonClass = "bg-danger text-white hover:bg-danger/80" 
}) => {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-70 z-50 flex justify-center items-center p-4" onClick={onClose}>
      <div className="bg-secondary rounded-lg shadow-2xl border border-border-color w-full max-w-md" onClick={e => e.stopPropagation()}>
        <div className="p-6">
          <h2 className="text-xl font-bold text-text-primary mb-4">{title}</h2>
          <p className="text-text-secondary mb-6">{message}</p>
        </div>
        <div className="bg-tertiary px-6 py-4 flex justify-end items-center space-x-4 rounded-b-lg">
          <button
            onClick={onClose}
            className="px-4 py-2 rounded-md bg-transparent border border-border-color text-text-primary hover:bg-border-color transition-colors"
          >
            Cancel
          </button>
          <button
            onClick={onConfirm}
            className={`px-4 py-2 rounded-md transition-colors font-semibold ${confirmButtonClass}`}
          >
            {confirmText}
          </button>
        </div>
      </div>
    </div>
  );
};

export default ConfirmationModal;