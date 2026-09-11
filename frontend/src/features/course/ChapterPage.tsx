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
  progress?: ChapterProgress;
}

export function ChapterPage() {
  const { chapterId } = useParams<{ chapterId: string }>();
  const { data, loading, error } = useApiQuery<ChapterResponse>(
    chapterId ? `/course/${chapterId}` : null,
    [chapterId],
  );

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
                  <Link className="button button--primary" to={`/learn/chapter-1/${topic.id}`}>
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
        <Link className="button button--primary" to="/assessments/chapter-1">
          Chapter 1 assessment
        </Link>
      </p>
    </>
  );
}
