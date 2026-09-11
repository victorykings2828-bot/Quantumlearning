import { useState } from 'react';
import { Link } from 'react-router-dom';
import { api } from '@/api/client';
import { useApiQuery } from '@/app/useApi';
import { useSession } from '@/app/session';
import { ErrorBanner, Loading, PageHeader, Panel } from '@/components/primitives';
import type { ChapterProgress } from '@/api/types';

interface ProgressResponse {
  chapter: ChapterProgress;
  previews: {
    algorithm_id: string;
    status: string;
    run_id: string | null;
    parameters: Record<string, unknown>;
    notes: string[];
    reflection: string | null;
  }[];
  assessment_attempts: {
    attempt_id: string;
    form: string;
    mode: string;
    status: string;
    submitted_at: string | null;
    score: number | null;
    max_score: number | null;
    passed: boolean | null;
  }[];
  evidence_rule: {
    required_independent: number;
    required_distinct_families: number;
    note: string;
  };
  demonstrated_skills: string[];
  disclosure: string;
}

export function ProgressPage() {
  const { data, loading, error, reload } = useApiQuery<ProgressResponse>('/progress');
  const session = useSession();
  const [confirming, setConfirming] = useState(false);
  const [resetting, setResetting] = useState(false);

  if (loading) return <Loading label="Loading your progress." />;
  if (error) return <ErrorBanner message={error} />;
  if (!data) return null;

  const next = data.chapter.next_topic_id;

  return (
    <>
      <PageHeader
        eyebrow="My progress"
        title="What you have done, and what it is evidence of."
        lede="Activity completion, independent evidence, and review recommendations are kept apart. Asking for a hint is never counted as a failure."
      />

      <Panel
        title="Chapter 1"
        badge={`${data.chapter.topics_complete}/${data.chapter.topics_total} topics complete`}
        badgeTone={
          data.chapter.topics_complete === data.chapter.topics_total ? 'success' : 'neutral'
        }
      >
        <div className="scroll-x">
          <table className="data-table">
            <thead>
              <tr>
                <th>Topic</th>
                <th className="numeric">Steps</th>
                <th className="numeric">Checks passed</th>
                <th>Status</th>
              </tr>
            </thead>
            <tbody>
              {data.chapter.topics.map((topic) => (
                <tr key={topic.topic_id}>
                  <td>
                    <Link to={`/learn/chapter-1/${topic.topic_id}`}>
                      {topic.number} {topic.title}
                    </Link>
                  </td>
                  <td className="numeric">
                    {topic.steps_completed}/{topic.steps_required}
                  </td>
                  <td className="numeric">
                    {topic.tasks_passed}/{topic.tasks_required}
                  </td>
                  <td>
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
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        {next && (
          <p className="button-row">
            <Link className="button button--primary" to={`/learn/chapter-1/${next}`}>
              Resume Topic {next.replace('-', '.')}
            </Link>
          </p>
        )}
      </Panel>

      <Panel title="Skill evidence" badge="Independent versus assisted">
        <p className="note">{data.evidence_rule.note}</p>
        <div className="scroll-x">
          <table className="data-table">
            <thead>
              <tr>
                <th>Skill</th>
                <th className="numeric">Independent</th>
                <th className="numeric">Assisted</th>
                <th>Item families</th>
                <th>Demonstrated</th>
              </tr>
            </thead>
            <tbody>
              {data.chapter.skills.map((skill) => (
                <tr key={skill.skill_id}>
                  <td className="mono">{skill.skill_id}</td>
                  <td className="numeric">
                    {skill.independent_count}/{skill.required_independent}
                  </td>
                  <td className="numeric">{skill.assisted_count}</td>
                  <td className="note" style={{ margin: 0 }}>
                    {skill.item_families.length > 0 ? skill.item_families.join(', ') : '—'}
                  </td>
                  <td>
                    <span className={skill.demonstrated ? 'badge badge--success' : 'badge'}>
                      {skill.demonstrated ? 'Demonstrated' : 'Not yet'}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <p className="note">
          A skill counts as demonstrated after {data.evidence_rule.required_independent}{' '}
          unassisted successes from {data.evidence_rule.required_distinct_families} different
          item families. An equivalent diagnostic can substitute for practice you have already
          demonstrated.
        </p>
      </Panel>

      <Panel title="Algorithm previews" badge="Evidence status">
        {data.previews.length === 0 ? (
          <p className="note">You have not opened a preview yet.</p>
        ) : (
          <ul className="entry-list">
            {data.previews.map((preview) => (
              <li key={preview.algorithm_id}>
                <div>
                  <h3>{preview.algorithm_id}</h3>
                  {preview.notes.length > 0 && (
                    <ul>
                      {preview.notes.map((note) => (
                        <li key={note} className="note" style={{ margin: 0 }}>
                          {note}
                        </li>
                      ))}
                    </ul>
                  )}
                </div>
                <div className="cluster">
                  <span className="badge badge--success">{preview.status}</span>
                  {preview.run_id && (
                    <Link className="button button--small" to="/lab/grover">
                      Reopen your saved run
                    </Link>
                  )}
                </div>
              </li>
            ))}
          </ul>
        )}
        <p className="note">
          Seen means you opened the preview and reached its main result. Completing Chapter 1
          does not promote a preview to Can Explain or Mastered.
        </p>
      </Panel>

      <Panel title="Assessment attempts">
        {data.assessment_attempts.length === 0 ? (
          <p className="note">
            No attempt yet.{' '}
            <Link to="/assessments/chapter-1">Open the Chapter 1 assessment</Link>.
          </p>
        ) : (
          <div className="scroll-x">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Form</th>
                  <th>Mode</th>
                  <th>Status</th>
                  <th className="numeric">Score</th>
                  <th>Outcome</th>
                </tr>
              </thead>
              <tbody>
                {data.assessment_attempts.map((attempt) => (
                  <tr key={attempt.attempt_id}>
                    <td>{attempt.form}</td>
                    <td>{attempt.mode}</td>
                    <td>{attempt.status}</td>
                    <td className="numeric">
                      {attempt.score === null ? '—' : `${attempt.score}/${attempt.max_score}`}
                    </td>
                    <td>
                      {attempt.passed === null ? (
                        '—'
                      ) : (
                        <span
                          className={
                            attempt.passed ? 'badge badge--success' : 'badge badge--warning'
                          }
                        >
                          {attempt.passed ? 'Passed' : 'Not yet'}
                        </span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Panel>

      <Panel title="This guest session" badge="Anonymous">
        <p className="note">{data.disclosure}</p>
        <p className="note mono">Principal {session.principalId ?? 'unknown'}</p>
        {!confirming ? (
          <button type="button" className="button" onClick={() => setConfirming(true)}>
            Reset my demo progress
          </button>
        ) : (
          <div className="note note--warning">
            <p>
              This permanently deletes this guest&rsquo;s topics, runs, attempts, evidence and
              tutor history. It affects nobody else and cannot be undone.
            </p>
            <div className="button-row">
              <button
                type="button"
                className="button button--primary"
                disabled={resetting}
                onClick={async () => {
                  setResetting(true);
                  await api.post('/reset-progress');
                  setResetting(false);
                  setConfirming(false);
                  reload();
                }}
              >
                {resetting ? 'Resetting…' : 'Yes, delete my progress'}
              </button>
              <button type="button" className="button" onClick={() => setConfirming(false)}>
                Cancel
              </button>
            </div>
          </div>
        )}
      </Panel>
    </>
  );
}
