import React, { useState, useEffect } from 'react';

export function useLocalStorage<T>(key: string, initialValue: T): [T, React.Dispatch<React.SetStateAction<T>>] {
  const [storedValue, setStoredValue] = useState<T>(() => {
    if (typeof window === 'undefined') {
      return initialValue;
    }
    try {
      const item = window.localStorage.getItem(key);
      if (item) {
          const parsedItem = JSON.parse(item);
          // Merge with initial value to pick up new keys, only for non-array objects.
          // This makes the hook more robust if the shape of the stored data changes.
          if (
              typeof initialValue === 'object' && initialValue !== null && !Array.isArray(initialValue) &&
              typeof parsedItem === 'object' && parsedItem !== null && !Array.isArray(parsedItem)
          ) {
              return { ...initialValue, ...parsedItem };
          }
          return parsedItem;
      }
      return initialValue;
    } catch (error) {
      console.error(error);
      return initialValue;
    }
  });

  useEffect(() => {
    try {
      window.localStorage.setItem(key, JSON.stringify(storedValue));
    } catch (error) {
      console.error(error);
    }
  }, [key, storedValue]);

  return [storedValue, setStoredValue];
}
