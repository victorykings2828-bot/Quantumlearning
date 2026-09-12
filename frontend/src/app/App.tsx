import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom';
import { Shell } from './Shell';
import { SessionProvider } from './session';
import { TutorProvider } from '@/features/tutor/TutorContext';
import { IntroductionPage } from '@/features/introduction/IntroductionPage';
import { CoursePage } from '@/features/course/CoursePage';
import { ChapterPage } from '@/features/course/ChapterPage';
import { ChapterLesson } from '@/features/lesson/ChapterLesson';
import { UnderstandingPage } from '@/features/assessment/UnderstandingPage';
import { LessonPage } from '@/features/lesson/LessonPage';
import { LabCatalogPage } from '@/features/lab/LabCatalogPage';
import { GroverLabPage } from '@/features/lab/GroverLabPage';
import { ShorLabPage } from '@/features/lab/ShorLabPage';
import { PlaygroundPage } from '@/features/lab/PlaygroundPage';
import { BridgePage } from '@/features/introduction/BridgePage';
import { AssessmentPage } from '@/features/assessment/AssessmentPage';
import { ProgressPage } from '@/features/progress/ProgressPage';
import { NotFoundPage } from '@/features/introduction/NotFoundPage';

export function App() {
  return (
    <BrowserRouter>
      <SessionProvider>
        <TutorProvider>
          <Routes>
            <Route element={<Shell />}>
              <Route path="/" element={<IntroductionPage />} />
              <Route path="/bridge" element={<BridgePage />} />
              <Route path="/course" element={<CoursePage />} />
              <Route path="/course/:chapterId" element={<ChapterPage />} />
              <Route path="/learn/chapter-1/:topicId" element={<LessonPage />} />
              <Route path="/learn/:chapterId/:topicId" element={<ChapterLesson />} />
              <Route path="/evidence/:chapterId" element={<UnderstandingPage />} />
              <Route path="/assessments/chapter-1" element={<AssessmentPage />} />
              <Route path="/lab" element={<LabCatalogPage />} />
              <Route path="/lab/grover" element={<GroverLabPage />} />
              <Route path="/lab/shor" element={<ShorLabPage />} />
              <Route path="/lab/playground" element={<PlaygroundPage />} />
              <Route path="/progress" element={<ProgressPage />} />
              <Route path="/index.html" element={<Navigate to="/" replace />} />
              <Route path="*" element={<NotFoundPage />} />
            </Route>
          </Routes>
        </TutorProvider>
      </SessionProvider>
    </BrowserRouter>
  );
}
