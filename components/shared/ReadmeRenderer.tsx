import React, { useMemo } from 'react';
import { marked } from 'marked';
import DOMPurify from 'dompurify';
import hljs from 'highlight.js/lib/core';

interface ReadmeRendererProps {
    markdownText?: string;
}

// Configure marked to use highlight.js for code blocks
marked.setOptions({
  highlight: function(code, lang) {
    const language = hljs.getLanguage(lang) ? lang : 'plaintext';
    try {
      return hljs.highlight(code, { language }).value;
    } catch (e) {
      return hljs.highlightAuto(code).value;
    }
  },
  langPrefix: 'hljs language-', // for CSS classes
  pedantic: false,
  gfm: true,
  breaks: false,
  sanitize: false,
  smartLists: true,
  smartypants: false,
  xhtml: false
});

const ReadmeRenderer: React.FC<ReadmeRendererProps> = ({ markdownText }) => {
    const sanitizedHtml = useMemo(() => {
        if (!markdownText) {
            return '<p class="text-text-secondary">No README provided for this package.</p>';
        }

        try {
            const rawHtml = marked.parse(markdownText, { async: false }) as string;
            // Add a hook to open links in a new tab
            DOMPurify.addHook('afterSanitizeAttributes', function (node) {
              if ('target' in node) {
                node.setAttribute('target', '_blank');
                node.setAttribute('rel', 'noopener noreferrer');
              }
            });
            return DOMPurify.sanitize(rawHtml);
        } catch (e) {
            console.error("Markdown parsing error:", e);
            return '<p class="text-danger">Error rendering README.</p>';
        }
    }, [markdownText]);

    return (
        <div 
            className="readme-content"
            dangerouslySetInnerHTML={{ __html: sanitizedHtml }} 
        />
    );
};

export default ReadmeRenderer;