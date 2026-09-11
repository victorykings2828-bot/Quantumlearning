import { Link } from 'react-router-dom';
import { PageHeader } from '@/components/primitives';

export function NotFoundPage() {
  return (
    <>
      <PageHeader
        eyebrow="Not found"
        title="There is nothing at this address."
        lede="This route does not exist in the demo. It is not a lesson waiting to be unlocked."
      />
      <p>
        <Link to="/course">Return to the course overview</Link> to see what is implemented and
        what is still marked Coming soon.
      </p>
    </>
  );
}
