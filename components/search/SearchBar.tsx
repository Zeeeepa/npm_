import React from 'react';

interface SearchBarProps {
  searchMode: string;
  setSearchMode: (m: string) => void;
  weights: {
    quality: number;
    popularity: number;
    maintenance: number;
  };
  onWeightsChange: React.Dispatch<React.SetStateAction<{
    quality: number;
    popularity: number;
    maintenance: number;
  }>>;
  filtersEnabled: {
    weighting: boolean;
  };
  setFiltersEnabled: React.Dispatch<React.SetStateAction<{
    weighting: boolean;
  }>>;
  isSearching: boolean;
}

const WeightSlider: React.FC<{
    label: string;
    value: number;
    onChange: (value: number) => void;
    disabled: boolean;
}> = ({ label, value, onChange, disabled }) => (
    <div className={`flex-1 min-w-[120px] ${disabled ? 'opacity-50' : ''}`}>
        <label className="block text-xs font-medium text-text-secondary mb-1 flex justify-between">
            <span>{label}</span>
            <span>{value.toFixed(1)}</span>
        </label>
        <input
            type="range"
            min="0"
            max="2"
            step="0.1"
            value={value}
            onChange={(e) => onChange(parseFloat(e.target.value))}
            disabled={disabled}
            className="w-full h-1.5 bg-tertiary rounded-lg appearance-none cursor-pointer accent-accent disabled:cursor-not-allowed"
        />
    </div>
);


const SearchBar: React.FC<SearchBarProps> = ({ 
    searchMode, setSearchMode, weights, onWeightsChange,
    filtersEnabled, setFiltersEnabled, isSearching
}) => {
  
  const isDiscoveryMode = searchMode === 'discovery';

  const handleWeightChange = (field: 'quality' | 'popularity' | 'maintenance', value: number) => {
    onWeightsChange(prev => ({ ...prev, [field]: value }));
  };

  const searchModes = [
      { id: 'general', label: 'General' },
      { id: 'discovery', label: 'Discovery ✨' },
      { id: 'exact', label: 'Exact Match' },
      { id: 'keywords', label: 'Keywords' },
      { id: 'author', label: 'Author' },
      { id: 'maintainer', label: 'Maintainer' },
      { id: 'scope', label: 'Scope' },
  ];

  return (
    <div className="flex items-center gap-6">
        {/* Mode */}
        <div className="flex items-center gap-2">
             <label htmlFor="search-mode" className="text-xs font-semibold text-text-secondary whitespace-nowrap">Search Mode</label>
             <select 
                id="search-mode"
                value={searchMode}
                onChange={e => setSearchMode(e.target.value)}
                className="bg-primary border border-border-color rounded-md px-3 py-1 text-sm focus:outline-none focus:ring-1 focus:ring-accent"
                disabled={isSearching}
             >
                 {searchModes.map(mode => <option key={mode.id} value={mode.id}>{mode.label}</option>)}
             </select>
        </div>
        
        {/* Weighting */}
        <div className="flex items-center gap-4 flex-1">
            <div className={`flex items-center gap-2 ${isDiscoveryMode ? 'opacity-50' : ''}`}>
                <input 
                    type="checkbox"
                    id="weighting-enable"
                    checked={filtersEnabled.weighting}
                    onChange={(e) => setFiltersEnabled(prev => ({...prev, weighting: e.target.checked}))}
                    disabled={isDiscoveryMode || isSearching}
                    className="h-4 w-4 rounded bg-tertiary border-border-color text-accent focus:ring-accent disabled:cursor-not-allowed"
                />
                <label htmlFor="weighting-enable" className={`text-xs font-semibold text-text-secondary select-none whitespace-nowrap ${isDiscoveryMode || isSearching ? 'cursor-not-allowed' : ''}`}>Search Weighting</label>
            </div>
            <WeightSlider 
                label="Quality"
                value={weights.quality}
                onChange={(v) => handleWeightChange('quality', v)}
                disabled={!filtersEnabled.weighting || isDiscoveryMode || isSearching}
            />
            <WeightSlider 
                label="Popularity"
                value={weights.popularity}
                onChange={(v) => handleWeightChange('popularity', v)}
                disabled={!filtersEnabled.weighting || isDiscoveryMode || isSearching}
            />
            <WeightSlider 
                label="Maintenance"
                value={weights.maintenance}
                onChange={(v) => handleWeightChange('maintenance', v)}
                disabled={!filtersEnabled.weighting || isDiscoveryMode || isSearching}
            />
        </div>
    </div>
  );
};

export default SearchBar;