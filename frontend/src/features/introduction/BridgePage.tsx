import { useState } from 'react';
import { Link } from 'react-router-dom';
import { useApiQuery } from '@/app/useApi';
import { Loading, Markdown, PageHeader, Panel } from '@/components/primitives';

interface BridgeCheck {
  id: string;
  preparation: string;
  prompt: string;
  kind: string;
  unit?: string;
  options?: { id: string; label: string }[];
  recovery: string;
}

interface BridgeResponse {
  title: string;
  subtitle: string;
  note: string;
  not_required_markdown: string;
  checks: BridgeCheck[];
  vocabulary: { term: string; definition: string; first_lesson: string }[];
  use_cases: { area: string; teach: string; boundary: string; source_id: string }[];
}

export function BridgePage() {
  const { data, loading, error } = useApiQuery<BridgeResponse>('/beginner-bridge');
  const [revealed, setRevealed] = useState<Record<string, boolean>>({});

  if (loading) return <Loading label="Loading the beginner bridge." />;
  if (error || !data) return <p className="note">{error ?? 'Not available.'}</p>;

  return (
    <>
      <PageHeader eyebrow="Beginner bridge" title={data.title} lede={data.subtitle} />
      <p className="note note--success">{data.note}</p>

      <Panel title="Five short checks" badge="Ungraded">
        <ol className="check-list">
          {data.checks.map((check) => (
            <li key={check.id}>
              <p className="check-list__preparation">{check.preparation}</p>
              <p>{check.prompt}</p>
              {check.options && (
                <ul className="option-list">
                  {check.options.map((option) => (
                    <li key={option.id}>{option.label}</li>
                  ))}
                </ul>
              )}
              <button
                type="button"
                className="button button--small"
                aria-expanded={Boolean(revealed[check.id])}
                onClick={() =>
                  setRevealed((current) => ({ ...current, [check.id]: !current[check.id] }))
                }
              >
                {revealed[check.id] ? 'Hide the explanation' : 'Show the explanation'}
              </button>
              {revealed[check.id] && <p className="note note--hint">{check.recovery}</p>}
            </li>
          ))}
        </ol>
      </Panel>

      <Panel title="What you do not need">
        <Markdown text={data.not_required_markdown} />
      </Panel>

      <Panel title="Vocabulary introduced now, expanded later">
        <div className="scroll-x">
          <table className="data-table">
            <thead>
              <tr>
                <th>Term</th>
                <th>Beginner definition</th>
                <th>First formal lesson</th>
              </tr>
            </thead>
            <tbody>
              {data.vocabulary.map((entry) => (
                <tr key={entry.term}>
                  <td>
                    <strong>{entry.term}</strong>
                  </td>
                  <td>{entry.definition}</td>
                  <td>{entry.first_lesson}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Panel>

      <Panel title="Where these ideas are used" badge="Honest boundaries">
        <div className="scroll-x">
          <table className="data-table">
            <thead>
              <tr>
                <th>Area</th>
                <th>What we teach</th>
                <th>The boundary</th>
              </tr>
            </thead>
            <tbody>
              {data.use_cases.map((entry) => (
                <tr key={entry.area}>
                  <td>
                    <strong>{entry.area}</strong>
                  </td>
                  <td>{entry.teach}</td>
                  <td>{entry.boundary}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Panel>

      <p>
        <Link className="button button--primary" to="/course">
          Explore the course
        </Link>
      </p>
    </>
  );
}
