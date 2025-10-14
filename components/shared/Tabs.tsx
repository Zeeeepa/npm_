
import React, { useState } from 'react';

interface Tab {
    id: string;
    name: string;
}

interface TabsProps {
    tabs: Tab[];
    children: (activeTabId: string) => React.ReactNode;
}

const Tabs: React.FC<TabsProps> = ({ tabs, children }) => {
    const [activeTab, setActiveTab] = useState(tabs[0].id);

    return (
        <>
            <div className="border-b border-border-color shrink-0">
                <nav className="flex space-x-2 px-4" aria-label="Tabs">
                    {tabs.map(tab => (
                        <button
                            key={tab.id}
                            onClick={() => setActiveTab(tab.id)}
                            className={`
                                ${activeTab === tab.id ? 'border-accent text-accent' : 'border-transparent text-text-secondary hover:text-text-primary hover:border-border-color'}
                                whitespace-nowrap py-3 px-4 border-b-2 font-medium text-sm transition-colors
                            `}
                            aria-current={activeTab === tab.id ? 'page' : undefined}
                        >
                            {tab.name}
                        </button>
                    ))}
                </nav>
            </div>
            {children(activeTab)}
        </>
    );
};

export default Tabs;
