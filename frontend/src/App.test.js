import { render, screen } from '@testing-library/react';
import App from './App';

test('renders the image analysis entry point', () => {
  render(<App />);
  const linkElement = screen.getByRole('link', { name: /analyze images/i });
  expect(linkElement).toBeInTheDocument();
});
