import { render, screen } from '@testing-library/react';
import DetailedAnalysisResults from './DetailedAnalysisResults';

test('shows uncertainty separately from geometric match strength', () => {
  render(<DetailedAnalysisResults analysis={{
    overall_rating: { score: 4.7, category: 'Fair' },
    composition_analysis: {
      detected_type: 'Leading Lines', type_key: 'leading_lines',
      method: 'ml', ml_reliable: false, ml_confidence: 45.2,
      score: 9, score_kind: 'geometric-match-heuristic',
      all_scores: { leading_lines: 9, diagonal: 6 },
    },
  }} />);
  expect(screen.getByRole('heading', { name: 'Possible composition style' })).toBeInTheDocument();
  expect(screen.getByText('Style confidence: 45.2%')).toBeInTheDocument();
  expect(screen.getByText('Geometric match: 9/10')).toBeInTheDocument();
});

test('unavailable pose detector does not claim there is no person', () => {
  render(<DetailedAnalysisResults analysis={{
    overall_rating: { score: 4.7, category: 'Fair' },
    pose_analysis: { detected: false, available: false },
  }} />);
  expect(screen.getByText('Pose detection is unavailable in this environment.')).toBeInTheDocument();
  expect(screen.queryByText('No human pose detected in this image.')).not.toBeInTheDocument();
});
