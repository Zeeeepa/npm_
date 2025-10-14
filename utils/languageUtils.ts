export const LANGUAGE_OPTIONS = [
    { value: '', label: 'Any Language', symbol: '🌐' },
    { value: 'python', label: 'Python (.py)', symbol: '🐍' },
    { value: 'javascript', label: 'JavaScript (.js, .jsx)', symbol: '🟨' },
    { value: 'typescript', label: 'TypeScript (.ts, .tsx)', symbol: '🟩' },
    { value: 'go', label: 'Go (.go)', symbol: '🐹' },
    { value: 'shell', label: 'Shell (.sh)', symbol: '🐚' },
    { value: 'java', label: 'Java (.java)', symbol: '☕' },
    { value: 'c++', label: 'C++ (.cpp, .h)', symbol: '➕' },
    { value: 'c#', label: 'C# (.cs)', symbol: '♯' },
    { value: 'ruby', label: 'Ruby (.rb)', symbol: '💎' },
    { value: 'html', label: 'HTML (.html)', symbol: '📄' },
    { value: 'css', label: 'CSS (.css)', symbol: '🎨' },
    { value: 'php', label: 'PHP (.php)', symbol: '🐘' },
    { value: 'rust', label: 'Rust (.rs)', symbol: '🦀' },
    { value: 'swift', label: 'Swift (.swift)', symbol: '🐦' },
    { value: 'kotlin', label: 'Kotlin (.kt)', symbol: '🤖' },
    { value: 'markdown', label: 'Markdown (.md)', symbol: '📝' },
    { value: 'sql', label: 'SQL (.sql)', symbol: '🗃️' },
    { value: 'json', label: 'JSON (.json)', symbol: '📦' },
    { value: 'yaml', label: 'YAML (.yml, .yaml)', symbol: '⚙️' },
    { value: 'dockerfile', label: 'Dockerfile', symbol: '🐳' },
];

const extensionMap: Record<string, string> = {
    py: '🐍',
    js: '🟨',
    jsx: '🟨',
    ts: '🟩',
    tsx: '🟩',
    go: '🐹',
    sh: '🐚',
    java: '☕',
    cpp: '➕',
    h: '➕',
    cs: '♯',
    rb: '💎',
    html: '📄',
    css: '🎨',
    php: '🐘',
    rs: '🦀',
    swift: '🐦',
    kt: '🤖',
    md: '📝',
    sql: '🗃️',
    json: '📦',
    yml: '⚙️',
    yaml: '⚙️',
};

export const getLanguageEmoji = (filePath: string): string => {
    const fileName = filePath.split('/').pop()?.toLowerCase() || '';

    if (fileName === 'dockerfile') {
        return '🐳';
    }
    if (fileName === '.gitignore') {
        return '🚫';
    }

    const extension = fileName.split('.').pop();
    if (extension && extensionMap[extension]) {
        return extensionMap[extension];
    }
    return '📄'; // Default file emoji
};
