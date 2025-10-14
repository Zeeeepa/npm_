import React, { useMemo } from 'react';
import hljs from 'highlight.js/lib/core';
import javascript from 'highlight.js/lib/languages/javascript';
import typescript from 'highlight.js/lib/languages/typescript';
import json from 'highlight.js/lib/languages/json';
import css from 'highlight.js/lib/languages/css';
import xml from 'highlight.js/lib/languages/xml'; // for HTML
import markdown from 'highlight.js/lib/languages/markdown';
import shell from 'highlight.js/lib/languages/shell';
import { SparklesIcon } from '../shared/icons/SparklesIcon';

// Register languages
try {
    hljs.registerLanguage('javascript', javascript);
    hljs.registerLanguage('typescript', typescript);
    hljs.registerLanguage('json', json);
    hljs.registerLanguage('css', css);
    hljs.registerLanguage('html', xml);
    hljs.registerLanguage('xml', xml);
    hljs.registerLanguage('markdown', markdown);
    hljs.registerLanguage('shell', shell);
    hljs.registerLanguage('sh', shell);
} catch (e) {
    console.error("Error registering highlight.js languages", e);
}


interface CodeViewerProps {
    code: string;
    language: string;
    path: string;
    onAnalyze: (path: string, content: string) => void;
}

const getHighlightLanguage = (extension: string): string => {
    const langMap: { [key: string]: string } = {
        js: 'javascript',
        jsx: 'javascript',
        ts: 'typescript',
        tsx: 'typescript',
        md: 'markdown',
        sh: 'shell',
        html: 'xml',
    };
    return langMap[extension] || extension;
}

const CodeViewer: React.FC<CodeViewerProps> = ({ code, language, path, onAnalyze }) => {
    const highlightedCodeHTML = useMemo(() => {
        if (!code || code === 'Loading...') {
            return null;
        }
        const highlightLang = getHighlightLanguage(language);
        if (hljs.getLanguage(highlightLang)) {
            try {
                return hljs.highlight(code, { language: highlightLang, ignoreIllegals: true }).value;
            } catch (error) {
                console.error("Failed to highlight code block:", error);
                return null;
            }
        }
        return null;
    }, [code, language]);

    return (
        <div className="h-full flex flex-col bg-secondary text-sm">
            <div className="p-3 border-b border-border-color text-sm text-text-secondary font-mono bg-tertiary flex justify-between items-center">
                <span className="truncate">{path}</span>
                 <button 
                    onClick={() => onAnalyze(path, code)}
                    className="flex items-center gap-1.5 text-xs bg-accent/10 text-accent font-semibold px-2 py-1 rounded-md hover:bg-accent/20 transition-colors shrink-0"
                    title={`Analyze ${path} with Gemini`}
                >
                    <SparklesIcon className="w-4 h-4" />
                    Analyze File
                </button>
            </div>
            <div className="flex-1 overflow-auto">
                <pre className="h-full">
                    {highlightedCodeHTML ? (
                        <code
                            className={`language-${getHighlightLanguage(language)}`}
                            dangerouslySetInnerHTML={{ __html: highlightedCodeHTML }}
                        />
                    ) : (
                        <code className="p-4 block whitespace-pre-wrap">{code}</code>
                    )}
                </pre>
            </div>
        </div>
    );
};

export default CodeViewer;