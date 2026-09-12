import { Link } from 'react-router-dom';
import { useApiQuery } from '@/app/useApi';
import { Loading, PageHeader } from '@/components/primitives';
import type { ChapterEntry, CourseResponse } from '@/api/types';

export function CoursePage() {
  const { data, loading, error } = useApiQuery<CourseResponse>('/course');

  if (loading) return <Loading label="Loading the course overview." />;
  if (error || !data) return <p className="note">{error ?? 'Course not available.'}</p>;

  return (
    <>
      <PageHeader eyebrow="Course overview" title={data.title} lede={data.subtitle} />
      <p className="note">{data.route_note}</p>
      <p className="note note--success">{data.browsing_note}</p>

      <ol className="chapter-list">
        {data.chapters.map((chapter) => (
          <li key={chapter.id}>
            <ChapterRow chapter={chapter} skillLabels={data.skill_labels} />
          </li>
        ))}
      </ol>
      <p className="note">{data.skill_label_note}</p>
    </>
  );
}

function ChapterRow({
  chapter,
  skillLabels,
}: {
  chapter: ChapterEntry;
  skillLabels: Record<string, string>;
}) {
  const published = chapter.publication === 'published';
  const progress = chapter.progress;
  const nextTopic = progress?.next_topic_id;
  const started = (progress?.topics_complete ?? 0) > 0;

  return (
    <article className="chapter">
      <header className="chapter__head">
        <div>
          <p className="eyebrow">Chapter {chapter.number}</p>
          <h2>{chapter.title}</h2>
        </div>
        <span className={published ? 'badge badge--success' : 'badge badge--warning'}>
          {published ? 'Published' : 'Coming soon'}
        </span>
      </header>

      <p>{chapter.outcome}</p>

      <dl className="chapter__meta">
        <div>
          <dt>Subtopics</dt>
          <dd>{chapter.topic_count}</dd>
        </div>
        <div>
          <dt>Prerequisites</dt>
          <dd>
            {chapter.prerequisite_skills.length === 0 ? (
              'None beyond the beginner bridge'
            ) : (
              <ul className="plain-list">
                {chapter.prerequisite_skills.map((skill) => (
                  <li key={skill}>{skillLabels[skill] ?? skill}</li>
                ))}
              </ul>
            )}
          </dd>
        </div>
        <div>
          <dt>You will be able to</dt>
          <dd>{chapter.demonstration}</dd>
        </div>
        {progress && (
          <div>
            <dt>Your progress</dt>
            <dd>
              {progress.topics_complete} of {progress.topics_total} topics complete
            </dd>
          </div>
        )}
      </dl>

      <details className="chapter__subtopics">
        <summary>Show the {chapter.topic_count} subtopics</summary>
        {chapter.topics ? (
          <ul className="topic-list">
            {chapter.topics.map((topic) => (
              <li key={topic.topic_id}>
                <Link to={`/learn/${chapter.id}/${topic.topic_id}`}>
                  {topic.number} {topic.title}
                </Link>
                <span className="cluster">
                  <span className="badge">
                    {topic.steps_completed}/{topic.steps_required} steps
                  </span>
                  <span className="badge">
                    {topic.tasks_passed}/{topic.tasks_required} tasks
                  </span>
                  <span
                    className={
                      topic.status === 'complete'
                        ? 'badge badge--success'
                        : topic.status === 'in_progress'
                          ? 'badge badge--navy'
                          : 'badge'
                    }
                  >
                    {topic.status.replace('_', ' ')}
                  </span>
                </span>
              </li>
            ))}
          </ul>
        ) : (
          <ul className="topic-list">
            {chapter.subtopic_titles.map((title) => (
              <li key={title}>
                <span>{title}</span>
              </li>
            ))}
          </ul>
        )}
      </details>

      <p
        className={
          chapter.access.readiness === 'prerequisites_needed' ? 'note note--warning' : 'note'
        }
      >
        {chapter.access.reason}
      </p>

      {published ? (
        <p className="button-row">
          <Link
            className="button button--primary"
            to={nextTopic ? `/learn/${chapter.id}/${nextTopic}` : `/course/${chapter.id}`}
          >
            {started && nextTopic
              ? `Continue Topic ${nextTopic.replace('-', '.')}`
              : `Start Chapter ${chapter.number}`}
          </Link>
          <Link className="button" to={`/course/${chapter.id}`}>
            Chapter detail
          </Link>
          <Link className="button" to={`/evidence/${chapter.id}`}>
            Check understanding
          </Link>
        </p>
      ) : null}
    </article>
  );
}
