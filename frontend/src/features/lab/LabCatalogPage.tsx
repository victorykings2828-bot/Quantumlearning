import { Link } from 'react-router-dom';
import { useApiQuery } from '@/app/useApi';
import { Loading, PageHeader, Panel } from '@/components/primitives';

interface CatalogEntry {
  id: string;
  title: string;
  kind: string;
  publication: string;
  summary: string;
  result_label: string | null;
  status: string | null;
  chapter?: number;
}

interface CatalogResponse {
  entries: CatalogEntry[];
  modes: { id: string; label: string; meaning: string }[];
  evidence_levels: { id: string; label: string; evidence: string }[];
  evidence_note: string;
}

const ROUTES: Record<string, string> = {
  grover: '/lab/grover',
  shor: '/lab/shor',
};

export function LabCatalogPage() {
  const { data, loading, error } = useApiQuery<CatalogResponse>('/lab/catalog');

  if (loading) return <Loading label="Loading the lab catalog." />;
  if (error || !data) return <p className="note">{error ?? 'Not available.'}</p>;

  const published = data.entries.filter((entry) => entry.publication === 'published');
  const planned = data.entries.filter((entry) => entry.publication !== 'published');

  return (
    <>
      <PageHeader
        eyebrow="Quantum Lab"
        title="Algorithms, protocols, and subroutines."
        lede="Previews are open to everyone and are never graded. Entries marked Coming soon are not implemented; there is no working experience hidden behind the label."
      />

      <Panel title="Available now" badge={`${published.length} published`}>
        <ul className="entry-list">
          {published.map((entry) => (
            <li key={entry.id}>
              <div>
                <h3>
                  <Link to={ROUTES[entry.id] ?? '/lab'}>{entry.title}</Link>
                </h3>
                <p className="note" style={{ marginTop: 0 }}>
                  {entry.summary}
                </p>
              </div>
              <div className="cluster">
                <span className="badge">{entry.kind}</span>
                {entry.result_label && (
                  <span className="badge">{entry.result_label.replace(/_/g, ' ')}</span>
                )}
                {entry.status && <span className="badge badge--success">{entry.status}</span>}
              </div>
            </li>
          ))}
        </ul>
      </Panel>

      <Panel title="Planned" badge={`${planned.length} coming soon`} badgeTone="warning">
        <ul className="entry-list">
          {planned.map((entry) => (
            <li key={entry.id}>
              <div>
                <h3>{entry.title}</h3>
                <p className="note" style={{ marginTop: 0 }}>
                  {entry.summary}
                </p>
              </div>
              <div className="cluster">
                <span className="badge">{entry.kind}</span>
                {entry.chapter && <span className="badge">Chapter {entry.chapter}</span>}
                <span className="badge badge--warning">Coming soon</span>
              </div>
            </li>
          ))}
        </ul>
      </Panel>

      <div className="grid-two">
        <Panel title="Lab modes">
          <dl className="definition-list">
            {data.modes.map((mode) => (
              <div key={mode.id}>
                <dt>{mode.label}</dt>
                <dd>{mode.meaning}</dd>
              </div>
            ))}
          </dl>
        </Panel>
        <Panel title="Evidence levels">
          <dl className="definition-list">
            {data.evidence_levels.map((level) => (
              <div key={level.id}>
                <dt>{level.label}</dt>
                <dd>{level.evidence}</dd>
              </div>
            ))}
          </dl>
          <p className="note">{data.evidence_note}</p>
        </Panel>
      </div>
    </>
  );
}
