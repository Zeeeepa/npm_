import React, { useState, useEffect, useMemo, useRef } from 'react';
// FIX: Import NpmPackage to get access to the 'time' property from the full package info.
import { NpmPackage, NpmPackageVersion } from '../../types';
// FIX: Import getPackageInfo to fetch the full package data, not just version details.
import { getPackageInfo, NpmApiError, NetworkError } from '../../services/searchService';
import { processWithConcurrency } from '../../utils/asyncUtils';
import LoadingSpinner from '../shared/LoadingSpinner';
import { XIcon } from '../shared/icons/XIcon';
import { formatBytes, timeAgo } from '../../utils/formatters';

interface DependenciesModalProps {
    isOpen: boolean;
    onClose: () => void;
    dependencies: Record<string, string>;
    devDependencies: Record<string, string>;
}

// FIX: Add optional 'time' property to store modification date.
interface EnrichedDependency {
    name: string;
    version: string;
    details: NpmPackageVersion | null;
    time?: { modified: string };
}

const DependenciesModal: React.FC<DependenciesModalProps> = ({ isOpen, onClose, dependencies, devDependencies }) => {
    const [isLoading, setIsLoading] = useState(false);
    const [enrichedDeps, setEnrichedDeps] = useState<EnrichedDependency[]>([]);
    const [enrichedDevDeps, setEnrichedDevDeps] = useState<EnrichedDependency[]>([]);
    const [error, setError] = useState<string | null>(null);
    const controllerRef = useRef<AbortController | null>(null);
    const firstErrorRef = useRef<Error | null>(null);

    useEffect(() => {
        if (!isOpen) {
            if (controllerRef.current) {
                controllerRef.current.abort();
            }
            return;
        }

        const controller = new AbortController();
        controllerRef.current = controller;
        firstErrorRef.current = null;

        const fetchAllDependencies = async () => {
            setIsLoading(true);
            setEnrichedDeps([]);
            setEnrichedDevDeps([]);
            setError(null);

            const depsToFetch = Object.entries(dependencies || {}).filter((e): e is [string, string] => typeof e[1] === 'string');
            const devDepsToFetch = Object.entries(devDependencies || {}).filter((e): e is [string, string] => typeof e[1] === 'string');
            
            const handleProcessorError = (item: [string, string], error: Error) => {
                if (controller.signal.aborted) return;
                
                // Only handle the first critical error (like network) to avoid spamming state updates
                if (!firstErrorRef.current && (error instanceof NetworkError || error instanceof NpmApiError)) {
                    firstErrorRef.current = error;
                    controller.abort(); // Stop further processing

                    let errorMessage = 'An unknown error occurred. Please try again.';
                    if (error instanceof NetworkError) {
                        errorMessage = error.message;
                    } else if (error instanceof NpmApiError) {
                        errorMessage = `The NPM registry returned an error (Status: ${error.status}). Please try again later.`;
                    }
                    setError(errorMessage);
                }
            };

            const processList = async (list: [string, string][], setter: React.Dispatch<React.SetStateAction<EnrichedDependency[]>>) => {
                let batch: EnrichedDependency[] = [];
                await processWithConcurrency({
                    items: list,
                    processor: ([name]) => getPackageInfo(name, controller.signal),
                    concurrency: 8,
                    onResult: ([name, version], pkg: NpmPackage) => {
                        if (controller.signal.aborted) return;
                        const latestVersionTag = pkg['dist-tags']?.latest;
                        const details = (latestVersionTag && pkg.versions?.[latestVersionTag]) || null;
                        
                        batch.push({ name, version, details, time: { modified: pkg.time.modified } });
                        if (batch.length >= 10) {
                            setter(prev => [...prev, ...batch]);
                            batch = [];
                        }
                    },
                    onError: handleProcessorError,
                    signal: controller.signal,
                });
                if (batch.length > 0 && !controller.signal.aborted) {
                    setter(prev => [...prev, ...batch]);
                }
            };
            
            await Promise.all([
                processList(depsToFetch, setEnrichedDeps),
                processList(devDepsToFetch, setEnrichedDevDeps),
            ]);

            if (!controller.signal.aborted || firstErrorRef.current) {
                setIsLoading(false);
            }
        };

        fetchAllDependencies();

        return () => {
            controller.abort();
        };

    }, [isOpen, dependencies, devDependencies]);

    if (!isOpen) return null;

    return (
        <div className="fixed inset-0 bg-black bg-opacity-70 z-[60] flex justify-center items-center p-4" onClick={onClose}>
            <div className="bg-secondary rounded-lg shadow-2xl border border-border-color w-full max-w-4xl h-[80vh] flex flex-col overflow-hidden" onClick={e => e.stopPropagation()}>
                <header className="flex justify-between items-center p-4 border-b border-border-color shrink-0">
                    <h2 className="text-lg font-bold">Dependencies</h2>
                    <button onClick={onClose} className="p-1 rounded-full hover:bg-tertiary">
                        <XIcon className="w-6 h-6" />
                    </button>
                </header>
                <div className="flex-1 overflow-y-auto">
                    {isLoading && enrichedDeps.length === 0 && enrichedDevDeps.length === 0 ? (
                        <div className="flex justify-center items-center h-full"><LoadingSpinner /></div>
                    ) : error ? (
                        <div className="p-4 m-4 bg-danger/10 border border-danger text-danger text-sm rounded-md">
                            <p className="font-semibold">Could not load dependencies</p>
                            <p>{error}</p>
                        </div>
                    ) : (
                        <div className="p-4 grid grid-cols-1 lg:grid-cols-2 gap-6">
                            <DependencyList title="Dependencies" dependencies={enrichedDeps} />
                            <DependencyList title="Dev Dependencies" dependencies={enrichedDevDeps} />
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
};

const DependencyList: React.FC<{title: string, dependencies: EnrichedDependency[]}> = ({ title, dependencies }) => {
    const totalDeps = Object.keys(dependencies).length;
    if (totalDeps === 0) {
        return (
            <div>
                <h3 className="text-md font-semibold text-text-primary mb-2">{title} (0)</h3>
                <p className="text-sm text-text-secondary">None</p>
            </div>
        );
    }
    
    return (
        <div className="flex flex-col gap-2">
            <h3 className="text-md font-semibold text-text-primary mb-2">{title} ({dependencies.length})</h3>
            <div className="space-y-2">
                {dependencies
                    .sort((a,b) => a.name.localeCompare(b.name))
                    .map(dep => <DependencyItem key={dep.name} dep={dep} />
                )}
            </div>
        </div>
    );
};

const DependencyItem: React.FC<{ dep: EnrichedDependency }> = ({ dep }) => (
    <div className="bg-tertiary p-2 rounded-md text-xs border border-border-color/50">
        <div className="flex justify-between items-baseline">
            <p className="font-semibold text-text-primary truncate" title={dep.name}>{dep.name}</p>
            <p className="text-text-secondary pl-2">{dep.version}</p>
        </div>
        {dep.details ? (
            <div className="flex justify-between items-baseline text-text-secondary mt-1">
                <span>{formatBytes(dep.details.dist.unpackedSize)} | {dep.details.dist.fileCount} files</span>
                {/* FIX: Use dep.time.modified which is now available on EnrichedDependency */}
                <span>{dep.time ? timeAgo(dep.time.modified) : ''}</span>
            </div>
        ) : (
             <div className="flex justify-between items-baseline text-text-secondary mt-1 animate-pulse">
                <span className="h-3 w-24 bg-border-color rounded"></span>
                <span className="h-3 w-16 bg-border-color rounded"></span>
            </div>
        )}
    </div>
);

export default DependenciesModal;