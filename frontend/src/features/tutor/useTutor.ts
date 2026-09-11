import { useContext } from 'react';
import { TutorCtx, type TutorState } from './context';

export function useTutor(): TutorState {
  const context = useContext(TutorCtx);
  if (!context) {
    throw new Error('useTutor must be used inside TutorProvider');
  }
  return context;
}
