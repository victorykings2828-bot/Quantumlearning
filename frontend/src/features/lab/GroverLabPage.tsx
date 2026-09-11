import { useEffect } from 'react';
import { Link } from 'react-router-dom';
import { useApiQuery } from '@/app/useApi';
import { Loading, Markdown, PageHeader, Panel } from '@/components/primitives';
import { GroverExperiment } from './GroverExperiment';
import { useTutor } from '@/features/tutor/useTutor';

interface PreviewAlgorithm {
  id: string;
  title: string;
  kind: string;
  summary: string;
  problem_markdown?: string;
  paradox_note?: string;
  classical_markdown?: string;
  quantum_markdown?: string;
  worked_example_markdown?: string;
  overshoot_note?: string;
  cost_note?: string;
  closing_question?: string;
  closing_question_note?: string;
  sources: { id: string; title: string; url: string }[];
}

export function GroverLabPage() {
  const { data, loading, error } = useApiQuery<{ algorithms: PreviewAlgorithm[] }>('/previews');
  const { setContext } = useTutor();

  useEffect(() => {
    setContext({ topicId: null });
  }, [setContext]);

  if (loading) return <Loading label="Loading the search preview." />;
  if (error || !data) return <p className="note">{error ?? 'Not available.'}</p>;

  const grover = data.algorithms.find((entry) => entry.id === 'grover');
  if (!grover) return <p className="note">The search preview is not published.</p>;

  return (
    <>
      <PageHeader eyebrow="Quantum Lab · Preview" title={grover.title} lede={grover.summary} />

      <Panel title="The problem both methods solve">
        <Markdown text={grover.problem_markdown ?? ''} />
        {grover.paradox_note && <p className="note note--warning">{grover.paradox_note}</p>}
      </Panel>

      <GroverExperiment />

      <div className="grid-two">
        <Panel title="The classical side">
          <Markdown text={grover.classical_markdown ?? ''} />
        </Panel>
        <Panel title="What Grover is doing">
          <Markdown text={grover.quantum_markdown ?? ''} />
        </Panel>
      </div>

      <Panel title="Explain the numbers" badge="Worked example">
        <Markdown text={grover.worked_example_markdown ?? ''} />
      </Panel>

      <Panel title="Reading the cost honestly">
        {grover.overshoot_note && <p className="note">{grover.overshoot_note}</p>}
        {grover.cost_note && <p className="note note--warning">{grover.cost_note}</p>}
      </Panel>

      <Panel title="Your mystery" badge="Seen">
        <p className="lede">{grover.closing_question}</p>
        <p className="note">{grover.closing_question_note}</p>
        <p className="button-row">
          <Link className="button button--primary" to="/course">
            Explore the course
          </Link>
        </p>
      </Panel>

      <Panel title="Sources">
        <ul>
          {grover.sources.map((source) => (
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
