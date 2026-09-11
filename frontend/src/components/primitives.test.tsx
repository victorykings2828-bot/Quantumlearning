import { render, screen } from '@testing-library/react';
import { describe, expect, it } from 'vitest';
import { Markdown } from './primitives';

describe('Markdown', () => {
  it('renders headings, bold text and inline code', () => {
    const { container } = render(
      <Markdown text={'### Heading\n\nSome **bold** and `code` text.'} />,
    );
    expect(screen.getByRole('heading', { name: 'Heading' })).toBeInTheDocument();
    expect(container.querySelector('strong')?.textContent).toBe('bold');
    expect(container.querySelector('code')?.textContent).toBe('code');
  });

  it('never interprets raw HTML', () => {
    const { container } = render(
      <Markdown text={'<script>window.hacked = true</script><b>not bold</b>'} />,
    );
    expect(container.querySelector('script')).toBeNull();
    expect(container.querySelector('b')).toBeNull();
    expect(container.textContent).toContain('<script>');
  });

  it('renders a table', () => {
    render(
      <Markdown
        text={'| Circuit | Final P(1) |\n|---|---|\n| H -> H | 0 |\n| H -> Z -> H | 1 |'}
      />,
    );
    expect(screen.getByRole('columnheader', { name: 'Circuit' })).toBeInTheDocument();
    expect(screen.getByRole('cell', { name: 'H -> Z -> H' })).toBeInTheDocument();
  });

  it('only links to http and https targets', () => {
    const { container } = render(
      <Markdown text={'[safe](https://example.com) and [unsafe](javascript:alert(1))'} />,
    );
    const links = Array.from(container.querySelectorAll('a'));
    expect(links).toHaveLength(1);
    expect(links[0].getAttribute('href')).toBe('https://example.com');
  });
});

describe('Markdown emphasis', () => {
  it('renders single-asterisk emphasis as italics', () => {
    const { container } = render(
      <Markdown text={'the quantity being squared is the *magnitude* of the amplitude'} />,
    );
    expect(container.querySelector('em')?.textContent).toBe('magnitude');
    expect(container.textContent).not.toContain('*');
  });

  it('still renders double-asterisk emphasis as bold', () => {
    const { container } = render(<Markdown text={'a **bold** word and an *italic* one'} />);
    expect(container.querySelector('strong')?.textContent).toBe('bold');
    expect(container.querySelector('em')?.textContent).toBe('italic');
  });
});
