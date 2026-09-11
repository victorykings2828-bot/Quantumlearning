import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { api } from '@/api/client';
import { useApiQuery } from '@/app/useApi';
import { Loading, PageHeader, Panel } from '@/components/primitives';
import { useTutor } from '@/features/tutor/TutorContext';

interface StoryboardStage {
  id: string;
  stage: string;
  body: string;
  future_concept: string | null;
  table?: { headers: string[]; rows: (string | number)[][] };
}

interface ShorPreview {
  id: string;
  title: string;
  summary: string;
  persistent_label: string;
  opening_note: string;
  storyboard: StoryboardStage[];
  retry_note: string;
  complexity_note: string;
  arithmetic_note: string;
  future_concepts: string[];
  sources: { id: string; title: string; url: string }[];
}

export function ShorLabPage() {
  const { data, loading, error } = useApiQuery<{ algorithms: ShorPreview[] }>('/previews');
  const [reached, setReached] = useState(false);
  const { setContext } = useTutor();

  useEffect(() => {
    setContext({ topicId: null, runId: null, runLabel: null, stepIndex: null });
  }, [setContext]);

  const shor = data?.algorithms.find((entry) => entry.id === 'shor');

  useEffect(() => {
    if (!shor || reached) return;
    // Seen is recorded once the learner reaches the final storyboard stage.
    const handler = () => {
      const marker = document.getElementById('shor-stage-factors');
      if (!marker) return;
      const box = marker.getBoundingClientRect();
      if (box.top < window.innerHeight) {
        setReached(true);
        void api
          .post('/previews/shor/encounters', {
            note: 'Reached the factors stage of the conceptual walkthrough.',
          })
          .catch(() => undefined);
      }
    };
    window.addEventListener('scroll', handler, { passive: true });
    handler();
    return () => window.removeEventListener('scroll', handler);
  }, [shor, reached]);

  if (loading) return <Loading label="Loading the Shor mystery." />;
  if (error || !data) return <p className="note">{error ?? 'Not available.'}</p>;
  if (!shor) return <p className="note">The Shor preview is not published.</p>;

  return (
    <>
      <PageHeader eyebrow="Quantum Lab · Conceptual" title={shor.title} lede={shor.summary} />

      <p className="note note--warning" role="note">
        <strong>{shor.persistent_label}</strong>
      </p>
      <p className="note">{shor.opening_note}</p>

      <ol className="storyboard">
        {shor.storyboard.map((stage, index) => (
          <li key={stage.id} id={`shor-stage-${stage.id}`}>
            <Panel
              title={`${index + 1}. ${stage.stage}`}
              badge={stage.future_concept ?? undefined}
              badgeTone="warning"
            >
              <p>{stage.body}</p>
              {stage.table && (
                <div className="scroll-x">
                  <table className="data-table">
                    <thead>
                      <tr>
                        {stage.table.headers.map((header) => (
                          <th key={header} className="numeric">
                            {header}
                          </th>
                        ))}
                      </tr>
                    </thead>
                    <tbody>
                      {stage.table.rows.map((row) => (
                        <tr key={String(row[0])}>
                          {row.map((cell, cellIndex) => (
                            <td key={cellIndex} className="numeric">
                              {cell}
                            </td>
                          ))}
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </Panel>
          </li>
        ))}
      </ol>

      <Panel title="What a full lesson has to add" badge="Later chapters">
        <p>{shor.retry_note}</p>
        <p className="note">{shor.complexity_note}</p>
        <p className="note note--warning">{shor.arithmetic_note}</p>
        <h3>Concepts you will need</h3>
        <ul className="cluster" style={{ listStyle: 'none', padding: 0 }}>
          {shor.future_concepts.map((concept) => (
            <li key={concept} className="badge">
              {concept}
            </li>
          ))}
        </ul>
      </Panel>

      <Panel
        title="Status"
        badge={reached ? 'Seen' : 'Not yet seen'}
        badgeTone={reached ? 'success' : 'neutral'}
      >
        <p>
          Reaching the end of this walkthrough records <strong>Seen</strong> only. Shor's own
          objectives are taught in Chapter 10.
        </p>
        <p className="button-row">
          <Link className="button button--primary" to="/course">
            Explore the course
          </Link>
        </p>
      </Panel>

      <Panel title="Sources">
        <ul>
          {shor.sources.map((source) => (
            <li key={source.id}>
              <a href={source.url} target="_blank" rel="noreferrer noopener">
                {source.title}
              </a>
            </li>
          ))}
        </ul>
      </Panel>
    </>
  );
}
