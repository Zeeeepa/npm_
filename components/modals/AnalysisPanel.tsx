import React, { useState, useEffect, useCallback } from 'react';
import { NpmPackage } from '../../types';
import { summarizeNpmPackage, explainFile } from '../../services/geminiService';
import { SparklesIcon } from '../shared/icons/SparklesIcon';
import LoadingSpinner from '../shared/LoadingSpinner';
import ReadmeRenderer from '../shared/ReadmeRenderer';

export type AnalysisTarget = 
    | { type: 'package'; pkg: NpmPackage; filePaths: string[] } 
    | { type: 'file'; pkg: NpmPackage; path: string; content: string };

interface AnalysisPanelProps {
    analysisTarget: AnalysisTarget;
    onClose: () => void;
}

const AnalysisPanel: React.FC<AnalysisPanelProps> = ({
    analysisTarget,
    onClose,
}) => {
    const [isLoading, setIsLoading] = useState(false);
    const [result, setResult] = useState<string | null>(null);
    const [error, setError] = useState<string | null>(null);

    const handleAnalysis = useCallback(async () => {
        setIsLoading(true);
        setError(null);
        setResult(null);
        try {
            let summary: string;
            if (analysisTarget.type === 'package') {
                summary = await summarizeNpmPackage(analysisTarget.pkg, analysisTarget.filePaths);
            } else {
                summary = await explainFile(analysisTarget.path, analysisTarget.content);
            }
            setResult(summary);
        } catch (e) {
            setError(e instanceof Error ? e.message : 'An unknown error occurred during analysis.');
        } finally {
            setIsLoading(false);
        }
    }, [analysisTarget]);

    useEffect(() => {
        handleAnalysis();
    }, [handleAnalysis]);

    const title = analysisTarget.type === 'package' ? 'Package Analysis' : 'File Analysis';
    const targetName = analysisTarget.type === 'package' ? analysisTarget.pkg.name : analysisTarget.path;

    return (
        <div className="w-full md:w-2/5 flex flex-col bg-tertiary border-l border-border-color shrink-0">
            <header className="p-4 border-b border-border-color shrink-0">
                <h3 className="font-bold text-lg flex items-center gap-2">
                    <SparklesIcon className="w-6 h-6 text-accent" />
                    {title}
                </h3>
                <p className="text-sm text-text-secondary truncate" title={targetName}>{targetName}</p>
            </header>

            <div className="flex-1 p-4 overflow-y-auto">
                {isLoading ? (
                    <div className="flex flex-col items-center justify-center h-full">
                        <LoadingSpinner className="h-8 w-8 text-accent" />
                        <p className="mt-4 text-text-secondary">Analyzing with Gemini...</p>
                    </div>
                ) : error ? (
                    <div className="bg-danger/10 border border-danger text-danger p-3 rounded-md text-sm">
                        <p className="font-semibold">Analysis Failed</p>
                        <p>{error}</p>
                    </div>
                ) : result ? (
                    <ReadmeRenderer markdownText={result} />
                ) : null}
            </div>

            <footer className="p-4 border-t border-border-color space-y-3 shrink-0">
                <button
                    onClick={handleAnalysis}
                    disabled={isLoading}
                    className="w-full bg-accent text-white font-semibold px-4 py-2 rounded-md hover:bg-accent/80 transition-colors disabled:bg-gray-500 disabled:cursor-not-allowed flex items-center justify-center gap-2"
                >
                    <SparklesIcon className="w-5 h-5" />
                    Regenerate
                </button>
                <button
                    onClick={onClose}
                    className="w-full bg-transparent border border-border-color text-text-primary hover:bg-border-color px-4 py-2 rounded-md transition-colors"
                >
                    Close Panel
                </button>
            </footer>
        </div>
    );
};

export default AnalysisPanel;