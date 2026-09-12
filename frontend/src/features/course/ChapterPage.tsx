import { useEffect } from 'react';
import { useTutor } from '@/features/tutor/useTutor';
import { Link, useParams } from 'react-router-dom';
import { useApiQuery } from '@/app/useApi';
import { Loading, PageHeader, Panel } from '@/components/primitives';
import type { ChapterProgress, TopicSummary } from '@/api/types';

interface ChapterResponse {
  id: string;
  number: number;
  title: string;
  outcome: string;
  scope_note: string;
  notation_contract: string;
  estimated_minutes: [number, number];
  topics: {
    id: string;
    number: string;
    title: string;
    slug: string;
    objective: string;
    learning_objectives: string[];
    prerequisite_skills: string[];
    skills: string[];
    estimated_minutes: number;
  }[];
  recap?: [string, string][];
  progress?: ChapterProgress;
}

export function ChapterPage() {
  const { chapterId } = useParams<{ chapterId: string }>();
  const { data, loading, error } = useApiQuery<ChapterResponse>(
    chapterId ? `/course/${chapterId}` : null,
    [chapterId],
  );

  const { setContext } = useTutor();
  useEffect(() => {
    setContext({
      topicId: data?.topics[0]?.id ?? null,
      runId: null,
      runLabel: null,
      stepIndex: null,
      mode: 'practice',
    });
  }, [data, setContext]);
  if (loading) return <Loading label="Loading the chapter." />;
  if (error) {
    return (
      <>
        <PageHeader
          eyebrow="Not implemented"
          title="This chapter is not built yet."
          lede={error}
        />
        <p>
          <Link className="button button--primary" to="/course">
            Back to the course overview
          </Link>
        </p>
      </>
    );
  }
  if (!data) return null;

  const summaries = new Map<string, TopicSummary>(
    (data.progress?.topics ?? []).map((topic) => [topic.topic_id, topic]),
  );

  return (
    <>
      <PageHeader eyebrow={`Chapter ${data.number}`} title={data.title} lede={data.outcome} />
      <p className="note note--warning">{data.scope_note}</p>

      <Panel title="Useful ideas — with a quick refresher">
        <p>
          No entry test is required. These reminders give you a starting point; unfamiliar ideas
          are explained in the lessons.
        </p>
        <dl>
          {data.recap?.map(([term, recall]) => (
            <div key={term}>
              <dt>
                <strong>{term}</strong>
              </dt>
              <dd>{recall}</dd>
            </div>
          ))}
        </dl>
        <p>
          Try a quick recall: if two equally likely outcomes exhaust the possibilities, each has
          probability 1/2.
        </p>
        <details>
          <summary>
            {data.number === 1
              ? 'Check your recall: if P(0)=1/4, what is P(1)?'
              : 'Check your recall: what is |i/2|²?'}
          </summary>
          <p>
            {data.number === 1
              ? '3/4. The two probabilities must sum to one.'
              : '1/4. Square the magnitude: 0²+(1/2)²=1/4.'}
          </p>
        </details>
        <p className="button-row">
          <Link className="button" to="/bridge">
            Review the basics
          </Link>
          <Link
            className="button button--primary"
            to={`/learn/${data.id}/${data.topics[0].id}`}
          >
            Start this chapter
          </Link>
        </p>
      </Panel>
      <Panel title="Notation used throughout this chapter">
        <p className="mono">{data.notation_contract}</p>
        <p className="note">
          Estimated time: {data.estimated_minutes[0]}–{data.estimated_minutes[1]} minutes across
          multiple visits.
        </p>
      </Panel>

      <ol className="topic-cards">
        {data.topics.map((topic) => {
          const summary = summaries.get(topic.id);
          return (
            <li key={topic.id}>
              <Panel
                title={`${topic.number} ${topic.title}`}
                badge={summary ? summary.status.replace('_', ' ') : 'not started'}
                badgeTone={summary?.status === 'complete' ? 'success' : 'neutral'}
              >
                <p>{topic.objective}</p>
                <h3>You will be able to</h3>
                <ul>
                  {topic.learning_objectives.map((objective) => (
                    <li key={objective}>{objective}</li>
                  ))}
                </ul>
                <p className="note">
                  Skills: {topic.skills.join(', ')} · about {topic.estimated_minutes} minutes
                </p>
                <p>
                  <Link className="button button--primary" to={`/learn/${data.id}/${topic.id}`}>
                    {summary?.status === 'complete' ? 'Review this topic' : 'Open this topic'}
                  </Link>
                </p>
              </Panel>
            </li>
          );
        })}
      </ol>

      <p className="button-row">
        <Link className="button" to="/course">
          Back to the course overview
        </Link>
        <Link className="button button--primary" to={`/evidence/${data.id}`}>
          Check your understanding
        </Link>
      </p>
    </>
  );
}
