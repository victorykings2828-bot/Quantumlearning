import { useEffect } from 'react';
import { Link } from 'react-router-dom';
import { useApiQuery } from '@/app/useApi';
import { useSession } from '@/app/useSession';
import { Loading, Markdown, PageHeader, Panel } from '@/components/primitives';
import { GroverExperiment } from '@/features/lab/GroverExperiment';
import { useTutor } from '@/features/tutor/useTutor';

interface IntroductionResponse {
  eyebrow: string;
  title: string;
  lede: string;
  sections: { id: string; heading: string; body_markdown: string }[];
  journey: { stage: string; experience: string; completion_meaning: string }[];
  primary_cta: { label: string; route: string };
  secondary_cta: { label: string; route: string; shown_when: string };
  sources: { id: string; title: string; url: string }[];
}

interface MeResponse {
  topics_complete: number;
  topics_total: number;
  next_topic_id: string | null;
}

export function IntroductionPage() {
  const { data, loading, error } = useApiQuery<IntroductionResponse>('/introduction');
  const session = useSession();
  const me = useApiQuery<MeResponse>(session.status === 'ready' ? '/me' : null, [
    session.status,
  ]);
  const { setContext } = useTutor();

  useEffect(() => {
    setContext({ topicId: null, runId: null, runLabel: null, stepIndex: null });
  }, [setContext]);

  if (loading) return <Loading label="Loading the introduction." />;
  if (error || !data) return <p className="note">{error ?? 'Introduction not available.'}</p>;

  const returning = (me.data?.topics_complete ?? 0) > 0;

  return (
    <>
      <PageHeader eyebrow={data.eyebrow} title={data.title} lede={data.lede} />

      <div className="grid-two">
        {data.sections.map((section) => (
          <Panel key={section.id} title={section.heading} id={`intro-${section.id}`}>
            <Markdown text={section.body_markdown} />
          </Panel>
        ))}
      </div>

      <Panel title="How the journey works" badge="Orientation">
        <div className="scroll-x">
          <table className="data-table">
            <thead>
              <tr>
                <th>Stage</th>
                <th>What you do</th>
                <th>What completing it means</th>
              </tr>
            </thead>
            <tbody>
              {data.journey.map((stage) => (
                <tr key={stage.stage}>
                  <td>
                    <strong>{stage.stage}</strong>
                  </td>
                  <td>{stage.experience}</td>
                  <td>{stage.completion_meaning}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Panel>

      <h2 id="search-preview" style={{ marginTop: 'var(--s7)' }}>
        Start with a search experiment
      </h2>
      <p className="lede">
        One item in an unsorted list satisfies a hidden yes/no test. Compare checking candidates
        one at a time with a small Grover experiment you can steer. Nothing here is graded.
      </p>

      <GroverExperiment />

      <Panel title="Your first Grover mystery" badge="Saved with your run">
        <p>
          The oracle changed a sign before any probability changed. Why did the next operation
          make that sign matter?
        </p>
        <p className="note">
          Keep that question. Chapter 1 builds the answer, and Topic 1.8 brings you back to this
          experiment to close it.
        </p>
        <p className="button-row">
          <Link className="button" to="/lab/grover">
            Open the full search preview
          </Link>
          <Link className="button" to="/lab/shor">
            See the Shor mystery
          </Link>
          <Link className="button" to="/bridge">
            Check the beginner bridge
          </Link>
        </p>
      </Panel>

      <Panel title="Ready to begin" badge="Next step">
        <p className="lede">
          The introduction ends here. The course overview shows every chapter, what is
          implemented, and what is still to come.
        </p>
        <p className="button-row">
          <Link className="button button--primary" to={data.primary_cta.route}>
            {data.primary_cta.label}
          </Link>
          {returning && me.data?.next_topic_id && (
            <Link className="button" to={`/learn/chapter-1/${me.data.next_topic_id}`}>
              Resume Topic {me.data.next_topic_id.replace('-', '.')}
            </Link>
          )}
        </p>
        <p className="note">{session.disclosure}</p>
      </Panel>

      <Panel title="Sources for the claims on this page">
        <ul>
          {data.sources.map((source) => (
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
