import React from 'react';
import SearchBar from '../search/SearchBar';

interface FilterHeaderProps {
  searchMode: string;
  setSearchMode: (m: string) => void;
  weights: { quality: number; popularity: number; maintenance: number; };
  onWeightsChange: React.Dispatch<React.SetStateAction<{ quality: number; popularity: number; maintenance: number; }>>;
  filtersEnabled: { weighting: boolean; };
  setFiltersEnabled: React.Dispatch<React.SetStateAction<{ weighting: boolean; }>>;
  isSearching: boolean;
}

const FilterHeader: React.FC<FilterHeaderProps> = (props) => {
  return (
    <div className="bg-secondary border-b border-border-color px-4 py-2 shrink-0">
       <SearchBar {...props} />
    </div>
  );
};

export default FilterHeader;