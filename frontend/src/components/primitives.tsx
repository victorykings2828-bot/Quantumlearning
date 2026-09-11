import type { ReactNode } from 'react';

export function Panel({
  title,
  badge,
  badgeTone = 'neutral',
  actions,
  children,
  id,
}: {
  title?: string;
  badge?: string;
  badgeTone?: 'neutral' | 'success' | 'warning' | 'navy';
  actions?: ReactNode;
  children: ReactNode;
  id?: string;
}) {
  const toneClass = badgeTone === 'neutral' ? 'badge' : `badge badge--${badgeTone}`;
  return (
    <section className="panel" id={id} aria-labelledby={id ? `${id}-title` : undefined}>
      {(title || badge || actions) && (
        <header className="panel__head">
          {title && (
            <h2 className="panel__title" id={id ? `${id}-title` : undefined}>
              {title}
            </h2>
          )}
          <div className="cluster">
            {actions}
            {badge && <span className={toneClass}>{badge}</span>}
          </div>
        </header>
      )}
      <div className="panel__body">{children}</div>
    </section>
  );
}

export function PageHeader({
  eyebrow,
  title,
  lede,
}: {
  eyebrow: string;
  title: string;
  lede?: string;
}) {
  return (
    <header className="page-header">
      <p className="eyebrow">{eyebrow}</p>
      <h1>{title}</h1>
      {lede && <p className="lede">{lede}</p>}
      <hr className="rule" />
    </header>
  );
}

export function ErrorBanner({ message }: { message: string }) {
  return (
    <div className="error-banner" role="alert">
      {message}
    </div>
  );
}

export function Loading({ label }: { label: string }) {
  return (
    <p className="note" role="status" aria-live="polite">
      {label}
    </p>
  );
}

/**
 * Minimal, safe Markdown rendering.
 *
 * Raw HTML is never interpreted. Only headings, paragraphs, lists, tables,
 * inline code, bold and links to http(s) targets are recognised.
 */
export function Markdown({ text }: { text: string }) {
  const blocks = text.split(/\n{2,}/);
  return (
    <div className="markdown">
      {blocks.map((block, index) => {
        const trimmed = block.trim();
        if (!trimmed) return null;
        if (trimmed.startsWith('### ')) {
          return <h3 key={index}>{inline(trimmed.slice(4))}</h3>;
        }
        if (trimmed.startsWith('## ')) {
          return <h3 key={index}>{inline(trimmed.slice(3))}</h3>;
        }
        if (trimmed.startsWith('|')) {
          return <MarkdownTable key={index} source={trimmed} />;
        }
        if (/^([-*]\s)/.test(trimmed)) {
          const items = trimmed.split('\n').map((line) => line.replace(/^[-*]\s+/, ''));
          return (
            <ul key={index}>
              {items.map((item, itemIndex) => (
                <li key={itemIndex}>{inline(item)}</li>
              ))}
            </ul>
          );
        }
        return <p key={index}>{inline(trimmed)}</p>;
      })}
    </div>
  );
}

function MarkdownTable({ source }: { source: string }) {
  const rows = source
    .split('\n')
    .map((line) => line.trim())
    .filter((line) => line.startsWith('|'))
    .map((line) =>
      line
        .slice(1, line.endsWith('|') ? -1 : undefined)
        .split('|')
        .map((cell) => cell.trim()),
    );
  if (rows.length < 2) return <p>{source}</p>;
  const [head, , ...body] = rows;
  return (
    <div className="scroll-x">
      <table className="data-table">
        <thead>
          <tr>
            {head.map((cell, index) => (
              <th key={index}>{inline(cell)}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {body.map((row, rowIndex) => (
            <tr key={rowIndex}>
              {row.map((cell, cellIndex) => (
                <td key={cellIndex}>{inline(cell)}</td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function inline(text: string): ReactNode[] {
  const pattern = /(\*\*[^*]+\*\*|\*[^*\n]+\*|`[^`]+`|\[[^\]]+\]\(https?:\/\/[^)]+\))/g;
  const parts = text.split(pattern).filter((part) => part !== '');
  return parts.map((part, index) => {
    if (part.startsWith('**') && part.endsWith('**')) {
      return <strong key={index}>{part.slice(2, -2)}</strong>;
    }
    if (part.startsWith('*') && part.endsWith('*')) {
      return <em key={index}>{part.slice(1, -1)}</em>;
    }
    if (part.startsWith('`') && part.endsWith('`')) {
      return <code key={index}>{part.slice(1, -1)}</code>;
    }
    const link = /^\[([^\]]+)\]\((https?:\/\/[^)]+)\)$/.exec(part);
    if (link) {
      return (
        <a key={index} href={link[2]} target="_blank" rel="noreferrer noopener">
          {link[1]}
        </a>
      );
    }
    return <span key={index}>{part}</span>;
  });
}
