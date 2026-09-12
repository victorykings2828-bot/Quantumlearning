import { useEffect, useState } from 'react';
import { Link, useParams, useSearchParams } from 'react-router-dom';
import { api } from '@/api/client';
import { useApiQuery } from '@/app/useApi';
import { Loading, PageHeader, Panel, ErrorBanner } from '@/components/primitives';
import { useTutor } from '@/features/tutor/useTutor';

interface Item {
  id: string;
  topic_id: string;
  question: string;
  prompt: string;
  options: string[];
}
interface Attempt {
  id: string;
  item_id: string;
  explanation: string;
  assisted: boolean;
  evaluation: {
    status: string;
    mcq_correct: boolean;
    followup: string;
    rating?: {
      criteria: { id: string; score: number; feedback: string }[];
      critical_misconception: boolean;
    };
  };
}
interface Evidence {
  concepts: {
    topic_id: string;
    reviewed_families: number;
    required_families: number;
    review_needed: boolean;
    demonstrated: boolean;
  }[];
  items: Item[];
  attempts: Attempt[];
  note: string;
}

export function UnderstandingPage() {
  const { chapterId } = useParams();
  const [search] = useSearchParams();
  const { data, loading, error, reload } = useApiQuery<Evidence>(
    `/understanding/${chapterId}`,
    [chapterId],
  );
  const [chosen, setChosen] = useState('');
  const [selection, setSelection] = useState(-1);
  const [explanation, setExplanation] = useState('');
  const [assisted, setAssisted] = useState(false);
  const [busy, setBusy] = useState(false);
  const [failure, setFailure] = useState('');
  const [saved, setSaved] = useState<Attempt | null>(null);
  const { setContext } = useTutor();
  const item =
    data?.items.find((i) => i.id === chosen) ??
    data?.items.find((i) => i.topic_id === search.get('topic')) ??
    data?.items[0];
  useEffect(() => {
    if (item)
      setContext({
        topicId: item.topic_id,
        runId: null,
        runLabel: null,
        stepIndex: null,
        mode: assisted ? 'practice' : 'test',
      });
  }, [item, setContext, assisted]);
  if (loading) return <Loading label="Loading understanding checks." />;
  if (error) return <ErrorBanner message={error} />;
  if (!data || !item) return null;
  async function submit() {
    if (!item) return;
    setBusy(true);
    setFailure('');
    try {
      const result = await api.post<Attempt>(`/understanding/${chapterId}`, {
        item_id: item.id,
        selection,
        explanation,
        assisted,
        idempotency_key: crypto.randomUUID(),
      });
      setSaved(result);
      reload();
    } catch (e) {
      setFailure(String(e));
    } finally {
      setBusy(false);
    }
  }
  return (
    <>
      <PageHeader
        eyebrow={`Chapter ${chapterId?.split('-')[1]}`}
        title="Show how you understand it"
        lede="Predict, explain your reasoning, then apply it to a changed situation."
      />
      <p className="note">{data.note}</p>
      <Panel title="Choose a question">
        <label>
          Question
          <select
            value={item.id}
            disabled={busy}
            onChange={(e) => {
              setChosen(e.target.value);
              setSelection(-1);
              setExplanation('');
              setSaved(null);
            }}
          >
            {data.items.map((i) => (
              <option key={i.id} value={i.id}>
                Topic {i.topic_id.replace('-', '.')} · variant {i.id.endsWith('A') ? 'A' : 'B'}
              </option>
            ))}
          </select>
        </label>
      </Panel>
      <Panel title="Prediction and explanation">
        <fieldset disabled={busy || Boolean(saved)}>
          <legend>{item.question}</legend>
          {item.options.map((option, i) => (
            <label className="evidence-option" key={option}>
              <input
                type="radio"
                name="prediction"
                checked={selection === i}
                onChange={() => setSelection(i)}
              />
              {option}
            </label>
          ))}
          <label>
            {item.prompt}
            <textarea
              rows={6}
              maxLength={4000}
              value={explanation}
              onChange={(e) => setExplanation(e.target.value)}
            />
          </label>
          <label>
            <input
              type="checkbox"
              checked={assisted}
              onChange={(e) => setAssisted(e.target.checked)}
            />{' '}
            Supported practice: I used help with this answer
          </label>
          <p className="note">
            Short, clear reasoning is enough. Grammar and answer length are not scientific
            criteria. A revealed or repeated question counts as practice.
          </p>
          <button
            className="button button--primary"
            disabled={selection < 0 || !explanation.trim() || busy}
            onClick={submit}
          >
            {busy ? 'Saving and evaluating…' : 'Save my answer'}
          </button>
        </fieldset>
        {failure && <ErrorBanner message={failure} />}
      </Panel>
      {saved && (
        <Panel
          title="Your evidence is saved"
          badge={saved.evaluation.status.replaceAll('_', ' ')}
        >
          <p>
            MCQ: {saved.evaluation.mcq_correct ? 'correct' : 'review needed'}. This alone does
            not establish understanding.
          </p>
          {saved.evaluation.rating?.criteria.map((c) => (
            <p key={c.id}>
              <strong>
                {c.id}: {c.score}/2.
              </strong>{' '}
              {c.feedback}
            </p>
          ))}
          {saved.evaluation.status === 'awaiting_evaluation' && (
            <p>
              Your explanation is stored. AI evaluation is not configured; no explanation grade
              has been invented.
            </p>
          )}
          {saved.evaluation.status === 'needs_review' && (
            <p>
              The explanation needs review. Your response is safe; this is neither a pass nor a
              zero.
            </p>
          )}
          <h3>Try a changed situation</h3>
          <p>{saved.evaluation.followup}</p>
          <p>
            Choose the other variant for fresh evidence. Helped or repeated answers remain
            practice.
          </p>
        </Panel>
      )}
      <Panel title="Reviewed understanding evidence">
        <p>
          Two independent, reviewed question families are needed per topic. A provisional AI
          score alone does not complete a topic.
        </p>
        <ul>
          {data.concepts.map((c) => (
            <li key={c.topic_id}>
              Topic {c.topic_id.replace('-', '.')}: {c.reviewed_families}/{c.required_families}{' '}
              reviewed families ·{' '}
              {c.review_needed
                ? 'review needed'
                : c.demonstrated
                  ? 'evidence demonstrated'
                  : 'more evidence needed'}
            </li>
          ))}
        </ul>
      </Panel>
      <Panel title="Saved responses">
        <ul>
          {data.attempts.map((a) => (
            <li key={a.id}>
              <strong>{a.item_id}</strong> · {a.assisted ? 'practice' : 'independent attempt'} ·{' '}
              {a.evaluation.status.replaceAll('_', ' ')}
              <details>
                <summary>Read my response</summary>
                <p>{a.explanation}</p>
              </details>
            </li>
          ))}
        </ul>
      </Panel>
      <Link className="button" to={`/course/${chapterId}`}>
        Back to chapter
      </Link>
    </>
  );
}
