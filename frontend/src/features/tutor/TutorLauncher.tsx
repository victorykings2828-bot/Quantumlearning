import { useCallback, useEffect, useRef, useState } from 'react';
import { api, ApiError } from '@/api/client';
import { Markdown } from '@/components/primitives';
import type { TutorAnswer } from '@/api/types';
import { useTutor } from './TutorContext';

interface Turn {
  id: string;
  role: 'user' | 'assistant';
  text: string;
  answer?: TutorAnswer;
  scopeLabel?: string;
}

const SUGGESTIONS = [
  'Why did the minus disappear?',
  'Is H a random coin flip?',
  'Why are my counts not exactly half?',
];

export function TutorLauncher() {
  const tutor = useTutor();
  const [turns, setTurns] = useState<Turn[]>([]);
  const [message, setMessage] = useState('');
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const drawerRef = useRef<HTMLDivElement>(null);
  const launcherRef = useRef<HTMLButtonElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);
  const requestId = useRef(0);

  const close = useCallback(() => {
    tutor.setOpen(false);
  }, [tutor]);

  // Focus returns to the control that opened the drawer, but only after the
  // render that unhides it: focusing a hidden element silently does nothing.
  const wasOpen = useRef(false);
  useEffect(() => {
    if (wasOpen.current && !tutor.open) {
      launcherRef.current?.focus();
    }
    wasOpen.current = tutor.open;
  }, [tutor.open]);

  useEffect(() => {
    if (!tutor.open) return;
    inputRef.current?.focus();
    const onKeyDown = (event: KeyboardEvent) => {
      if (event.key === 'Escape') {
        event.preventDefault();
        close();
      }
    };
    document.addEventListener('keydown', onKeyDown);
    return () => document.removeEventListener('keydown', onKeyDown);
  }, [tutor.open, close]);

  const ask = useCallback(
    async (text: string) => {
      const trimmed = text.trim();
      if (!trimmed || busy) return;
      const id = ++requestId.current;
      // The scope is captured now so a later edit cannot relabel this answer.
      const capturedRun = tutor.runId;
      const capturedLabel = tutor.runLabel;
      const capturedStep = tutor.stepIndex;

      setTurns((current) => [...current, { id: `u${id}`, role: 'user', text: trimmed }]);
      setMessage('');
      setBusy(true);
      setError(null);

      try {
        const answer = await api.post<TutorAnswer>('/tutor/turns', {
          message: trimmed,
          topic_id: tutor.topicId,
          run_id: capturedRun,
          step_index: capturedStep,
          mode: tutor.mode ?? 'practice',
        });
        setTurns((current) => [
          ...current,
          {
            id: `a${id}`,
            role: 'assistant',
            text: answer.answer_markdown,
            answer,
            scopeLabel:
              capturedRun && capturedLabel
                ? `Explaining ${capturedLabel}${capturedStep !== null ? `, step ${capturedStep}` : ''}`
                : undefined,
          },
        ]);
      } catch (cause) {
        setError(
          cause instanceof ApiError
            ? cause.message
            : 'The tutor request failed. Your work is saved and unaffected.',
        );
      } finally {
        setBusy(false);
      }
    },
    [busy, tutor.topicId, tutor.runId, tutor.runLabel, tutor.stepIndex, tutor.mode],
  );

  return (
    <>
      {/* Hidden while the drawer is open so it cannot cover a result panel.
          It stays in the tree so focus can return to it on close. */}
      <button
        type="button"
        ref={launcherRef}
        className="tutor-launcher"
        hidden={tutor.open}
        onClick={() => tutor.setOpen(true)}
        aria-expanded={tutor.open}
        aria-controls="tutor-drawer"
      >
        Ask the course tutor
      </button>

      {tutor.open && (
        <div
          className="tutor-drawer"
          id="tutor-drawer"
          role="dialog"
          aria-modal="false"
          aria-label="Course tutor"
          ref={drawerRef}
        >
          <header className="tutor-drawer__head">
            <div>
              <h2 className="panel__title">Course tutor</h2>
              <p className="note" style={{ margin: 0 }}>
                {tutor.topicId
                  ? `Scope: Topic ${tutor.topicId.replace('-', '.')}`
                  : 'Scope: course overview'}
                {tutor.runLabel ? ` · ${tutor.runLabel}` : ''}
                {tutor.mode === 'test' ? ' · test mode' : ''}
              </p>
            </div>
            <button type="button" className="button button--small" onClick={close}>
              Close
            </button>
          </header>

          <div className="tutor-drawer__body">
            {turns.length === 0 && (
              <p className="note">
                I can help with this course, its experiments, and the mathematics it needs. I
                cannot change grades, mastery, or unlocks, and I will redirect anything
                unrelated.
              </p>
            )}
            {turns.map((turn) =>
              turn.role === 'user' ? (
                <div key={turn.id} className="tutor-turn tutor-turn--user">
                  <p>{turn.text}</p>
                </div>
              ) : (
                <div key={turn.id} className="tutor-turn tutor-turn--assistant">
                  <p className="tutor-turn__label">
                    <span
                      className={
                        turn.answer?.source_label === 'authored'
                          ? 'badge badge--warning'
                          : 'badge badge--navy'
                      }
                    >
                      {turn.answer?.source_label === 'authored'
                        ? 'Authored course help'
                        : `Live model · ${turn.answer?.provider_model ?? turn.answer?.provider}`}
                    </span>
                    {turn.scopeLabel && <span className="badge">{turn.scopeLabel}</span>}
                  </p>
                  {turn.answer?.notice && (
                    <p className="note note--warning">{turn.answer.notice}</p>
                  )}
                  <Markdown text={turn.text} />
                  {turn.answer?.facts && turn.answer.facts.length > 0 && (
                    <details>
                      <summary>Verified run values used in this answer</summary>
                      <ul>
                        {turn.answer.facts.map((fact) => (
                          <li key={fact.id}>
                            {fact.label}: <span className="mono">{fact.value}</span>
                          </li>
                        ))}
                      </ul>
                    </details>
                  )}
                  {turn.answer?.citations && turn.answer.citations.length > 0 && (
                    <div className="tutor-citations">
                      <h3>Sources</h3>
                      <ul>
                        {turn.answer.citations.map((citation) => (
                          <li key={citation.passage_id}>
                            <span className="mono">{citation.passage_id}</span> —{' '}
                            {citation.title}
                            {citation.sources.map((source) => (
                              <span key={source.url}>
                                {' '}
                                (
                                <a href={source.url} target="_blank" rel="noreferrer noopener">
                                  {source.title}
                                </a>
                                )
                              </span>
                            ))}
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}
                  {turn.answer?.followup_question && (
                    <p className="note">{turn.answer.followup_question}</p>
                  )}
                </div>
              ),
            )}
            {busy && (
              <p className="note" role="status" aria-live="polite">
                Preparing an answer. Nothing is shown until it has been validated.
              </p>
            )}
            {error && (
              <p className="note note--warning" role="alert">
                {error}
              </p>
            )}
          </div>

          <form
            className="tutor-drawer__composer"
            onSubmit={(event) => {
              event.preventDefault();
              void ask(message);
            }}
          >
            <label className="visually-hidden" htmlFor="tutor-message">
              Ask the course tutor
            </label>
            <textarea
              id="tutor-message"
              ref={inputRef}
              value={message}
              rows={2}
              maxLength={2000}
              placeholder="Ask about this topic, your run, or the course mathematics"
              onChange={(event) => setMessage(event.target.value)}
              onKeyDown={(event) => {
                if (event.key === 'Enter' && !event.shiftKey) {
                  event.preventDefault();
                  void ask(message);
                }
              }}
            />
            <div className="button-row">
              <button type="submit" className="button button--primary" disabled={busy}>
                Ask
              </button>
              {SUGGESTIONS.map((suggestion) => (
                <button
                  key={suggestion}
                  type="button"
                  className="button button--small"
                  onClick={() => void ask(suggestion)}
                  disabled={busy}
                >
                  {suggestion}
                </button>
              ))}
            </div>
          </form>
        </div>
      )}
    </>
  );
}
