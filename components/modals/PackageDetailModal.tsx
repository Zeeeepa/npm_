import React, { useState, useEffect, useCallback, useRef, useMemo } from 'react';
import { EnrichedNpmPackage, NpmPackage, FileNode, FlatFile } from '../../types';
import { getPackageInfo, getPackageFileTree, getFileContent } from '../../services/searchService';
import LoadingSpinner from '../shared/LoadingSpinner';
import ReadmeRenderer from '../shared/ReadmeRenderer';
import CodeViewer from '../shared/CodeViewer';
import AnalysisPanel, { AnalysisTarget } from './AnalysisPanel';
import DependenciesModal from './DependenciesModal';
import Tabs from '../shared/Tabs';
import { XIcon } from '../shared/icons/XIcon';
import { FolderIcon } from '../shared/icons/FolderIcon';
import { ChevronRightIcon } from '../shared/icons/ChevronRightIcon';
import { SparklesIcon } from '../shared/icons/SparklesIcon';
import { DocumentIcon } from '../shared/icons/DocumentIcon';
import { SortIcon } from '../shared/icons/SortIcon';
import { formatBytes, timeAgo } from '../../utils/formatters';
import { getTimeColor, getSizeColor, getFileCountColor } from '../../utils/colorStyles';

interface PackageDetailModalProps {
  pkg: EnrichedNpmPackage;
  onClose: () => void;
}

type ModalContentView = 
    | { type: 'readme' }
    | { type: 'file', path: string, content: string, lang: string };

const StatItem: React.FC<{ color?: string, value: string | number, label: string, isButton?: boolean }> = ({ color, value, label, isButton }) => (
    <div className={`flex items-baseline gap-1.5 ${isButton ? '' : 'cursor-default'}`}>
        <span className="font-bold text-base text-text-primary" style={{ color: color }}>{value}</span>
        <span className="text-xs text-text-secondary">{label}</span>
    </div>
);

const PackageDetailModal: React.FC<PackageDetailModalProps> = ({ pkg, onClose }) => {
    const [packageInfo, setPackageInfo] = useState<NpmPackage | null>(null);
    const [isLoading, setIsLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [contentView, setContentView] = useState<ModalContentView>({ type: 'readme' });
    
    const [analysisTarget, setAnalysisTarget] = useState<AnalysisTarget | null>(null);
    const [flatFiles, setFlatFiles] = useState<FlatFile[]>([]);
    
    const fileFetchControllerRef = useRef<AbortController | null>(null);

    const modalContainerRef = useRef<HTMLDivElement>(null);
    const [sidebarWidth, setSidebarWidth] = useState(300);
    const isResizingRef = useRef(false);
    
    const [isDepsModalOpen, setIsDepsModalOpen] = useState(false);

    const handleResizeMouseMove = useCallback((e: MouseEvent) => {
        if (!isResizingRef.current || !modalContainerRef.current) return;
        
        const modalRect = modalContainerRef.current.getBoundingClientRect();
        let newWidth = e.clientX - modalRect.left;
        const minWidth = 200;
        const maxWidth = modalRect.width * 0.6;

        if (newWidth < minWidth) newWidth = minWidth;
        if (newWidth > maxWidth) newWidth = maxWidth;
        
        setSidebarWidth(newWidth);
    }, []);

    const handleResizeMouseUp = useCallback(() => {
        isResizingRef.current = false;
        window.removeEventListener('mousemove', handleResizeMouseMove);
        window.removeEventListener('mouseup', handleResizeMouseUp);
        document.body.style.cursor = 'default';
        document.body.style.userSelect = 'auto';
    }, [handleResizeMouseMove]);

    const handleResizeMouseDown = useCallback((e: React.MouseEvent) => {
        e.preventDefault();
        isResizingRef.current = true;
        window.addEventListener('mousemove', handleResizeMouseMove);
        window.addEventListener('mouseup', handleResizeMouseUp);
        document.body.style.cursor = 'col-resize';
        document.body.style.userSelect = 'none';
    }, [handleResizeMouseMove, handleResizeMouseUp]);
    
    useEffect(() => {
        return () => {
            window.removeEventListener('mousemove', handleResizeMouseMove);
            window.removeEventListener('mouseup', handleResizeMouseUp);
        };
    }, [handleResizeMouseMove, handleResizeMouseUp]);


    useEffect(() => {
        const controller = new AbortController();
        const fetchDetails = async () => {
            setIsLoading(true);
            setError(null);
            try {
                const info = await getPackageInfo(pkg.package.name, controller.signal);
                setPackageInfo(info);
            } catch (err) {
                if (err.name !== 'AbortError') {
                    setError(err instanceof Error ? err.message : 'Failed to load package details.');
                }
            } finally {
                if (!controller.signal.aborted) {
                    setIsLoading(false);
                }
            }
        };
        fetchDetails().catch(err => {
            if (err.name !== 'AbortError') {
                console.error("Failed to fetch package details:", err);
            }
        });

        return () => {
            controller.abort();
        }
    }, [pkg.package.name]);

    const docsCount = useMemo(() => {
        if (!flatFiles.length) return 0;
        return flatFiles.map(f => f.path).filter(path => {
            const lowerPath = path.toLowerCase();
            // A file is considered a doc if it's in a /docs folder or is a markdown file (but not the root README)
            return (lowerPath.startsWith('/docs/') || lowerPath.startsWith('/doc/')) || 
                   ( (lowerPath.endsWith('.md') || lowerPath.endsWith('.mdx')) && lowerPath !== '/readme.md' );
        }).length;
    }, [flatFiles]);

    const handleFileSelect = useCallback(async (path: string) => {
        if (!packageInfo) return;
        const latestVersion = packageInfo['dist-tags']?.latest;
        if (!latestVersion) return;
        
        // Abort previous file fetch if it's running
        if (fileFetchControllerRef.current) {
            fileFetchControllerRef.current.abort();
        }
        const controller = new AbortController();
        fileFetchControllerRef.current = controller;

        setContentView({ type: 'file', path, content: 'Loading...', lang: '' });

        try {
            const content = await getFileContent(packageInfo.name, latestVersion, path, controller.signal);
            const extension = path.split('.').pop() || '';
            if (!controller.signal.aborted) {
                setContentView({ type: 'file', path, content, lang: extension });
            }
        } catch (err) {
            if (err.name !== 'AbortError') {
                const errorMsg = err instanceof Error ? err.message : 'Could not load file content.';
                setContentView({ type: 'file', path, content: `Error: ${errorMsg}`, lang: 'text' });
            }
        }
    }, [packageInfo]);

    const handleAnalyzePackage = () => {
        if (!packageInfo) return;
        setAnalysisTarget({ type: 'package', pkg: packageInfo, filePaths: flatFiles.map(f => f.path) });
    };

    const handleAnalyzeFile = (path: string, content: string) => {
        if (!packageInfo) return;
        setAnalysisTarget({ type: 'file', pkg: packageInfo, path, content });
    };


    const renderContent = () => {
        if (isLoading) {
            return <div className="flex items-center justify-center h-full"><LoadingSpinner /></div>;
        }
        if (error) {
            return <div className="p-4 text-center text-danger">{error}</div>;
        }
        if (!packageInfo) {
            return <div className="p-4 text-center text-text-secondary">No package information available.</div>;
        }

        const latestVersion = packageInfo['dist-tags']?.latest;
        const versionData = latestVersion ? packageInfo.versions[latestVersion] : null;
        
        const depCount = Object.keys(versionData?.dependencies || {}).length;
        const devDepCount = Object.keys(versionData?.devDependencies || {}).length;

        const timeColor = getTimeColor(pkg.package.date);
        const sizeColor = versionData ? getSizeColor(versionData.dist.unpackedSize) : undefined;
        const fileCountColor = versionData ? getFileCountColor(versionData.dist.fileCount) : undefined;

        return (
            <div className="flex flex-1 overflow-hidden">
                <div className="flex-1 flex flex-col overflow-hidden">
                    {/* Header */}
                    <header className="p-4 border-b border-border-color shrink-0">
                        <div className="flex justify-between items-start">
                            <div className="min-w-0">
                                <h2 className="text-xl font-bold text-text-primary truncate">{packageInfo.name} <span className="text-base font-normal text-text-secondary">v{latestVersion}</span></h2>
                                <p className="text-sm text-text-secondary mt-1 max-w-xl">{packageInfo.description}</p>
                            </div>
                            <div className="flex items-center gap-2 shrink-0 ml-4">
                                <button
                                    onClick={handleAnalyzePackage}
                                    className="bg-accent/10 text-accent font-semibold px-3 py-1.5 rounded-md hover:bg-accent/20 transition-colors flex items-center gap-2 text-sm"
                                    title="Analyze package with Gemini"
                                >
                                    <SparklesIcon className="w-5 h-5" />
                                    <span className="hidden sm:inline">Analyze Package</span>
                                </button>
                                <button onClick={onClose} className="p-1 rounded-full hover:bg-tertiary text-text-secondary hover:text-text-primary"><XIcon className="w-6 h-6" /></button>
                            </div>
                        </div>
                         {/* STATS BAR */}
                        <div className="flex flex-wrap gap-x-6 gap-y-2 mt-4 text-sm">
                            {versionData && (
                                <StatItem color={sizeColor} value={formatBytes(versionData.dist.unpackedSize)} label="Size" />
                            )}
                            {versionData && (
                                <StatItem color={fileCountColor} value={versionData.dist.fileCount} label="Files" />
                            )}
                            {docsCount > 0 && (
                                 <StatItem value={docsCount} label="Docs" />
                            )}
                            <StatItem color={timeColor} value={timeAgo(pkg.package.date)} label="Old" />
                            {(depCount > 0 || devDepCount > 0) && (
                                <button onClick={() => setIsDepsModalOpen(true)} className="hover:bg-tertiary -m-2 p-2 rounded-md transition-colors">
                                    <StatItem value={`${depCount} deps, ${devDepCount} devDeps`} label="" isButton={true} />
                                </button>
                            )}
                        </div>
                    </header>
                    
                    {/* Body */}
                    <div className="flex flex-1 overflow-hidden">
                        <div 
                            style={{ width: `${sidebarWidth}px` }}
                            className="flex-shrink-0 border-r border-border-color flex flex-col"
                        >
                             <Tabs tabs={[{ id: 'tree', name: "Project's Tree" }, { id: 'list', name: 'All File List' }]}>
                                {(activeTabId) => (
                                    <div className="flex-1 overflow-y-auto">
                                        {activeTabId === 'tree' && (
                                            <ModalFileExplorer
                                                packageName={packageInfo.name}
                                                version={latestVersion || ''}
                                                onFileSelect={handleFileSelect}
                                                onTreeLoad={setFlatFiles}
                                            />
                                        )}
                                        {activeTabId === 'list' && (
                                            <ModalFileFlatList
                                                files={flatFiles}
                                                onFileSelect={handleFileSelect}
                                            />
                                        )}
                                    </div>
                                )}
                            </Tabs>
                        </div>
                         <div
                            onMouseDown={handleResizeMouseDown}
                            className="w-1.5 cursor-col-resize bg-tertiary hover:bg-accent transition-colors flex-shrink-0"
                            title="Resize panel"
                        />
                        <div className="flex-1 flex flex-col overflow-hidden">
                            <div className="p-3 border-b border-border-color shrink-0 bg-tertiary">
                                <button 
                                    onClick={() => setContentView({type: 'readme'})}
                                    className={`px-3 py-1 text-xs rounded-md mr-2 ${contentView.type === 'readme' ? 'bg-accent text-white font-semibold' : 'bg-secondary text-text-secondary'}`}
                                >
                                    README
                                </button>
                                {contentView.type === 'file' && (
                                    <span className="text-xs text-text-primary font-mono truncate">{contentView.path}</span>
                                )}
                            </div>
                            <div className="flex-1 overflow-y-auto p-4 bg-primary">
                                {contentView.type === 'readme' && <ReadmeRenderer markdownText={packageInfo.readme} />}
                                {contentView.type === 'file' && <CodeViewer code={contentView.content} language={contentView.lang} path={contentView.path} onAnalyze={handleAnalyzeFile} />}
                            </div>
                        </div>
                    </div>
                </div>
                {analysisTarget && (
                    <AnalysisPanel
                        analysisTarget={analysisTarget}
                        onClose={() => setAnalysisTarget(null)}
                    />
                )}
                {versionData && (
                    <DependenciesModal
                        isOpen={isDepsModalOpen}
                        onClose={() => setIsDepsModalOpen(false)}
                        dependencies={versionData.dependencies || {}}
                        devDependencies={versionData.devDependencies || {}}
                    />
                )}
            </div>
        );
    }

    return (
        <div className="fixed inset-0 bg-black bg-opacity-70 z-50 flex justify-center items-center p-4" onClick={onClose}>
            <div ref={modalContainerRef} className="bg-secondary rounded-lg shadow-2xl border border-border-color w-full max-w-6xl h-[90vh] flex overflow-hidden" onClick={e => e.stopPropagation()}>
                {renderContent()}
            </div>
        </div>
    );
};


// --- Sub-components for Modal ---

const IGNORED_FILES = ['.gitignore', 'license', 'license.md', '.npmignore', 'package-lock.json', '.ds_store', 'readme.md'];

const filterNodes = (nodes: FileNode[]): FileNode[] => {
    const result: FileNode[] = [];
    for (const node of nodes) {
        const fileName = node.path.split('/').pop()?.toLowerCase() || '';
        if (IGNORED_FILES.includes(fileName)) {
            continue; // Skip ignored file
        }
        if (node.type === 'directory' && node.files) {
            const filteredChildren = filterNodes(node.files);
            // Only include directories that are not empty after filtering
            if (filteredChildren.length > 0) {
                result.push({ ...node, files: filteredChildren });
            }
        } else {
            result.push(node); // It's a file that wasn't ignored
        }
    }
    return result;
};

interface ModalFileExplorerProps {
    packageName: string;
    version: string;
    onFileSelect: (path: string) => void;
    onTreeLoad: (files: FlatFile[]) => void;
}

const ModalFileExplorer: React.FC<ModalFileExplorerProps> = ({ packageName, version, onFileSelect, onTreeLoad }) => {
    const [tree, setTree] = useState<FileNode | null>(null);
    const [isLoading, setIsLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [expandedNodes, setExpandedNodes] = useState<Record<string, boolean>>({});

    useEffect(() => {
        const controller = new AbortController();
        const fetchTree = async () => {
            if (!version) {
                setIsLoading(false);
                setError("No version specified.");
                return;
            };
            setIsLoading(true);
            setError(null);
            try {
                const fileTree = await getPackageFileTree(packageName, version, controller.signal);
                if (controller.signal.aborted) return;

                const initialTree = {...fileTree};
                
                const files: FlatFile[] = [];
                const traverseForPaths = (nodes: FileNode[]) => {
                    for (const node of nodes) {
                        if (node.type === 'file') {
                            files.push({ path: node.path, size: node.size });
                        } else if (node.files) {
                            traverseForPaths(node.files);
                        }
                    }
                };
                if (initialTree.files) {
                    traverseForPaths(initialTree.files);
                }
                onTreeLoad(files);

                // Filter the tree for display
                if (initialTree.files) {
                    initialTree.files = filterNodes(initialTree.files);
                }
                setTree(initialTree);

                // Auto-expand first level
                const initialExpanded: Record<string, boolean> = {};
                if (initialTree?.files) {
                    for (const node of initialTree.files) {
                        if (node.type === 'directory') {
                            initialExpanded[node.path] = true;
                        }
                    }
                }
                setExpandedNodes(initialExpanded);

            } catch (err) {
                 if (err.name !== 'AbortError') {
                    setError(err instanceof Error ? err.message : 'Could not load file tree.');
                 }
            } finally {
                if (!controller.signal.aborted) {
                    setIsLoading(false);
                }
            }
        };

        fetchTree().catch(err => {
            if (err.name !== 'AbortError') {
                console.error("Failed to fetch file tree:", err);
                setError(err.message || 'Failed to load file tree');
            }
        });

        return () => {
            controller.abort();
        }
    }, [packageName, version, onTreeLoad]);
    
    const handleToggleNode = (path: string) => {
        setExpandedNodes(prev => ({ ...prev, [path]: !prev[path] }));
    };

    const handleToggleAll = (expand: boolean) => {
        const newExpandedNodes: Record<string, boolean> = {};
        if (expand && tree?.files) {
            const traverse = (nodes: FileNode[]) => {
                for (const node of nodes) {
                    if (node.type === 'directory') {
                        newExpandedNodes[node.path] = true;
                        if (node.files) traverse(node.files);
                    }
                }
            };
            traverse(tree.files);
        }
        setExpandedNodes(newExpandedNodes);
    };

    if (isLoading) return <div className="flex justify-center p-4"><LoadingSpinner /></div>;
    if (error) return <div className="p-4 text-xs text-danger">{error}</div>;

    return (
        <div className="p-2 font-mono text-sm">
            <div className="flex items-center gap-2 px-2 py-1 border-b border-border-color mb-1">
                <button onClick={() => handleToggleAll(true)} className="text-xs text-text-secondary hover:text-text-primary">Expand All</button>
                <span className="text-text-secondary">|</span>
                <button onClick={() => handleToggleAll(false)} className="text-xs text-text-secondary hover:text-text-primary">Collapse All</button>
            </div>
            {tree?.files && tree.files.map(node => (
                <TreeNode 
                    key={node.path} 
                    node={node} 
                    onFileClick={onFileSelect} 
                    level={0}
                    expandedNodes={expandedNodes}
                    onToggleNode={handleToggleNode}
                />
            ))}
        </div>
    );
}

interface TreeNodeProps {
    node: FileNode;
    onFileClick: (path: string) => void;
    level: number;
    expandedNodes: Record<string, boolean>;
    onToggleNode: (path: string) => void;
}

const TreeNode: React.FC<TreeNodeProps> = ({ node, onFileClick, level, expandedNodes, onToggleNode }) => {
    const isDirectory = node.type === 'directory';
    const isOpen = isDirectory && !!expandedNodes[node.path];

    const handleClick = () => {
        if (isDirectory) {
            onToggleNode(node.path);
        } else {
            onFileClick(node.path);
        }
    };

    const Icon = isDirectory ? FolderIcon : DocumentIcon;

    return (
        <div>
            <div
                onClick={handleClick}
                style={{ paddingLeft: `${level * 1.25}rem`}}
                className="flex items-center gap-2 py-1 px-2 rounded-md hover:bg-tertiary cursor-pointer text-xs"
            >
                {isDirectory && <ChevronRightIcon className={`w-3 h-3 shrink-0 transition-transform ${isOpen ? 'rotate-90' : ''}`} />}
                {!isDirectory && <div className="w-3 h-3 shrink-0" />}
                <Icon className="w-4 h-4 shrink-0 text-text-secondary" />
                <span className="truncate">{node.path.split('/').pop()}</span>
            </div>
            {isDirectory && isOpen && node.files && (
                <div>
                    {node.files.map(child => <TreeNode key={child.path} node={child} onFileClick={onFileClick} level={level + 1} expandedNodes={expandedNodes} onToggleNode={onToggleNode} />)}
                </div>
            )}
        </div>
    );
};

interface ModalFileFlatListProps {
  files: FlatFile[];
  onFileSelect: (path: string) => void;
}

const ModalFileFlatList: React.FC<ModalFileFlatListProps> = ({ files, onFileSelect }) => {
  type SortKey = 'path' | 'size' | 'type';
  const [sortKey, setSortKey] = useState<SortKey>('path');
  const [sortDir, setSortDir] = useState<'asc' | 'desc'>('asc');

  const getFileType = (path: string) => path.split('.').pop() || '';

  const sortedFiles = useMemo(() => {
    return [...files].sort((a, b) => {
      let valA: string | number;
      let valB: string | number;

      switch (sortKey) {
        case 'size':
          valA = a.size ?? -1;
          valB = b.size ?? -1;
          break;
        case 'type':
          valA = getFileType(a.path);
          valB = getFileType(b.path);
          break;
        case 'path':
        default:
          valA = a.path;
          valB = b.path;
          break;
      }
      
      if (typeof valA === 'string' && typeof valB === 'string') {
        const compareResult = valA.localeCompare(valB, undefined, { numeric: true });
        return sortDir === 'asc' ? compareResult : -compareResult;
      }
      if (valA < valB) return sortDir === 'asc' ? -1 : 1;
      if (valA > valB) return sortDir === 'asc' ? 1 : -1;
      return 0;
    });
  }, [files, sortKey, sortDir]);

  const handleSort = (key: SortKey) => {
    if (key === sortKey) {
      setSortDir(prev => (prev === 'asc' ? 'desc' : 'asc'));
    } else {
      setSortKey(key);
      setSortDir('asc');
    }
  };
  
  const SortButton: React.FC<{ sortField: SortKey, label: string, className?: string }> = ({ sortField, label, className = '' }) => (
    <button onClick={() => handleSort(sortField)} className={`flex items-center gap-1 ${className}`}>
      <span className={sortKey === sortField ? 'text-accent font-bold' : ''}>{label}</span>
      {sortKey === sortField && (
        <SortIcon direction={sortDir} className="w-3 h-3"/>
      )}
    </button>
  );

  return (
    <div className="text-sm font-mono flex flex-col h-full">
      <div className="grid grid-cols-[1fr_80px_60px] gap-2 p-2 border-b border-border-color text-xs text-text-secondary sticky top-0 bg-secondary">
        <SortButton sortField="path" label="Path" />
        <SortButton sortField="size" label="Size" className="justify-end"/>
        <SortButton sortField="type" label="Type" className="justify-end"/>
      </div>
      <div className="flex-1 overflow-y-auto">
        {sortedFiles.map(file => (
          <button 
            key={file.path} 
            onClick={() => onFileSelect(file.path)}
            className="w-full grid grid-cols-[1fr_80px_60px] gap-2 py-1 px-2 text-xs rounded-md hover:bg-tertiary text-left items-center"
          >
            <span className="truncate flex items-center gap-2" title={file.path}>
                <DocumentIcon className="w-3.5 h-3.5 shrink-0 text-text-secondary" />
                {file.path}
            </span>
            <span className="text-right text-text-secondary">{formatBytes(file.size ?? 0)}</span>
            <span className="text-right text-text-secondary truncate">{getFileType(file.path)}</span>
          </button>
        ))}
      </div>
    </div>
  );
};


export default PackageDetailModal;