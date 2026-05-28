import React from 'react';

function renderInline(text) {
  const parts = text.split(/(\*\*[^*]+\*\*)/g);
  return parts.map((part, i) => {
    if (part.startsWith('**') && part.endsWith('**')) {
      return <strong key={i} style={{ fontWeight: 700, color: '#1a1a18' }}>{part.slice(2, -2)}</strong>;
    }
    return <React.Fragment key={i}>{part}</React.Fragment>;
  });
}

function parseBlocks(text) {
  const lines = text.replace(/\r\n/g, '\n').split('\n');
  const blocks = [];
  let i = 0;

  while (i < lines.length) {
    const line = lines[i];

    if (!line.trim()) { i++; continue; }

    // Headings
    if (line.startsWith('### ')) {
      blocks.push({ type: 'h3', content: line.slice(4) });
      i++;
    } else if (line.startsWith('## ')) {
      blocks.push({ type: 'h2', content: line.slice(3) });
      i++;
    } else if (line.startsWith('# ')) {
      blocks.push({ type: 'h2', content: line.slice(2) });
      i++;
    }
    // List items (- / • / * / 1.)
    else if (/^[-•*]\s/.test(line) || /^\d+\.\s/.test(line)) {
      const items = [];
      while (i < lines.length && (/^[-•*]\s/.test(lines[i]) || /^\d+\.\s/.test(lines[i]))) {
        items.push(lines[i].replace(/^[-•*]\s+/, '').replace(/^\d+\.\s+/, ''));
        i++;
      }
      blocks.push({ type: 'list', items });
    }
    // Paragraph: collect non-special consecutive lines
    else {
      const paraLines = [];
      while (
        i < lines.length &&
        lines[i].trim() &&
        !lines[i].startsWith('#') &&
        !/^[-•*]\s/.test(lines[i]) &&
        !/^\d+\.\s/.test(lines[i])
      ) {
        paraLines.push(lines[i]);
        i++;
      }
      blocks.push({ type: 'p', content: paraLines.join(' ') });
    }
  }

  return blocks;
}

export default function FeedbackCard({ feedback }) {
  if (!feedback) return null;

  const blocks = parseBlocks(feedback);

  return (
    <div style={{
      background: '#fff',
      borderRadius: '16px',
      padding: '1.5rem',
      boxShadow: '0 1px 3px rgba(0,0,0,0.06)',
      borderLeft: '4px solid #1D9E75',
    }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '1rem' }}>
        <span style={{ fontSize: '1.2rem' }}>💬</span>
        <p style={{
          fontSize: '0.8rem',
          fontWeight: '600',
          textTransform: 'uppercase',
          letterSpacing: '0.08em',
          color: '#888780',
        }}>
          Feedback del entrenador virtual
        </p>
      </div>

      <div style={{ display: 'flex', flexDirection: 'column', gap: '0.7rem' }}>
        {blocks.map((block, i) => {
          if (block.type === 'h2' || block.type === 'h3') {
            return (
              <p key={i} style={{
                fontSize: '0.9rem',
                fontWeight: '700',
                color: '#1a1a18',
                marginTop: i > 0 ? '0.4rem' : 0,
              }}>
                {renderInline(block.content)}
              </p>
            );
          }
          if (block.type === 'list') {
            return (
              <ul key={i} style={{ paddingLeft: '0.25rem', listStyle: 'none', display: 'flex', flexDirection: 'column', gap: '0.4rem' }}>
                {block.items.map((item, j) => (
                  <li key={j} style={{ display: 'flex', gap: '0.5rem', fontSize: '0.92rem', lineHeight: 1.65, color: '#3d3d3a' }}>
                    <span style={{ color: '#1D9E75', fontWeight: '700', flexShrink: 0, marginTop: '0.05em' }}>›</span>
                    <span>{renderInline(item)}</span>
                  </li>
                ))}
              </ul>
            );
          }
          return (
            <p key={i} style={{ fontSize: '0.92rem', lineHeight: 1.7, color: '#3d3d3a' }}>
              {renderInline(block.content)}
            </p>
          );
        })}
      </div>
    </div>
  );
}
