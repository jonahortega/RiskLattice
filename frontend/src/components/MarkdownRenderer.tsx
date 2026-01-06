import React from 'react'

interface MarkdownRendererProps {
  content: string
  className?: string
}

export function MarkdownRenderer({ content, className = '' }: MarkdownRendererProps) {
  // Simple markdown parser for basic formatting
  const parseMarkdown = (text: string): React.ReactNode[] => {
    const parts: React.ReactNode[] = []
    let currentIndex = 0
    
    // Split by double newlines first for paragraphs
    const paragraphs = text.split(/\n\n+/)
    
    return paragraphs.map((paragraph, pIdx) => {
      if (!paragraph.trim()) return null
      
      // Process inline formatting within paragraph
      const lines = paragraph.split('\n')
      
      return (
        <div key={pIdx} className="mb-2 last:mb-0">
          {lines.map((line, lIdx) => {
            if (!line.trim()) return <br key={lIdx} />
            
            // Check for headers
            if (line.startsWith('### ')) {
              return (
                <h3 key={lIdx} className="font-bold text-lg mt-2 mb-1 text-cyan-200">
                  {parseInline(line.substring(4))}
                </h3>
              )
            }
            if (line.startsWith('## ')) {
              return (
                <h2 key={lIdx} className="font-bold text-xl mt-3 mb-2 text-cyan-200">
                  {parseInline(line.substring(3))}
                </h2>
              )
            }
            if (line.startsWith('# ')) {
              return (
                <h1 key={lIdx} className="font-bold text-2xl mt-4 mb-2 text-cyan-200">
                  {parseInline(line.substring(2))}
                </h1>
              )
            }
            
            // Check for bullet points
            if (line.trim().startsWith('- ')) {
              return (
                <div key={lIdx} className="ml-4 mb-1">
                  <span className="text-cyan-400 mr-2">•</span>
                  <span>{parseInline(line.trim().substring(2))}</span>
                </div>
              )
            }
            
            // Regular line
            return (
              <p key={lIdx} className="mb-1">
                {parseInline(line)}
              </p>
            )
          })}
        </div>
      )
    }).filter(Boolean)
  }
  
  // Parse inline formatting (bold, links) - improved version
  const parseInline = (text: string): React.ReactNode[] => {
    const parts: React.ReactNode[] = []
    let lastIndex = 0
    
    // Find all matches (bold and links)
    const matches: Array<{ start: number, end: number, type: 'bold' | 'link', content: string, url?: string }> = []
    
    // Match bold **text** (non-greedy)
    const boldRegex = /\*\*([^*]+)\*\*/g
    let match
    while ((match = boldRegex.exec(text)) !== null) {
      matches.push({
        start: match.index,
        end: match.index + match[0].length,
        type: 'bold',
        content: match[1]
      })
    }
    
    // Match links [text](url)
    const linkRegex = /\[([^\]]+)\]\(([^)]+)\)/g
    while ((match = linkRegex.exec(text)) !== null) {
      matches.push({
        start: match.index,
        end: match.index + match[0].length,
        type: 'link',
        content: match[1],
        url: match[2]
      })
    }
    
    // Sort by position
    matches.sort((a, b) => a.start - b.start)
    
    // Remove overlapping matches (prefer links over bold)
    const filteredMatches: typeof matches = []
    matches.forEach(m => {
      const overlaps = filteredMatches.some(fm => 
        (m.start < fm.end && m.end > fm.start)
      )
      if (!overlaps || m.type === 'link') {
        if (m.type === 'link') {
          // Remove any bold that overlaps with this link
          const index = filteredMatches.findIndex(fm => 
            fm.type === 'bold' && (m.start < fm.end && m.end > fm.start)
          )
          if (index >= 0) {
            filteredMatches.splice(index, 1)
          }
        }
        filteredMatches.push(m)
      }
    })
    
    // Build parts
    filteredMatches.forEach((match, idx) => {
      // Add text before match
      if (match.start > lastIndex) {
        const beforeText = text.substring(lastIndex, match.start)
        if (beforeText) {
          parts.push(beforeText)
        }
      }
      
      // Add the match
      if (match.type === 'bold') {
        parts.push(
          <strong key={`bold-${idx}`} className="font-semibold text-cyan-200">
            {match.content}
          </strong>
        )
      } else if (match.type === 'link') {
        parts.push(
          <a
            key={`link-${idx}`}
            href={match.url}
            target="_blank"
            rel="noopener noreferrer"
            className="text-cyan-400 hover:text-cyan-300 underline break-all overflow-wrap-anywhere word-break-break-all"
          >
            {match.content || match.url}
          </a>
        )
      }
      
      lastIndex = match.end
    })
    
    // Add remaining text
    if (lastIndex < text.length) {
      const remaining = text.substring(lastIndex)
      if (remaining) {
        parts.push(remaining)
      }
    }
    
    return parts.length > 0 ? parts : [text]
  }
  
  return (
    <div className={`markdown-content break-words overflow-wrap-anywhere word-break-break-word ${className}`}>
      {parseMarkdown(content)}
    </div>
  )
}

