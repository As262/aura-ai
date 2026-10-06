import ApiService from './ApiService';

test('a learned aesthetic rating does not infer the photographers skill level', () => {
  const interpretation = ApiService.interpretRating(4.8, 'learned-nima');
  expect(interpretation.message).toContain('4.8/10');
  expect(interpretation.level).toBeUndefined();
});

test('uncertain style feedback does not declare a composition quality problem', () => {
  const interpretation = ApiService.interpretComposition({
    method: 'ml', detected_type: 'Golden Ratio', ml_reliable: false, ml_confidence: 42,
    score: 0, score_kind: 'geometric-match-heuristic',
  });
  expect(interpretation).toContain('Possible style: Golden Ratio');
  expect(interpretation).not.toContain('needs work');
});

test('landmark visibility does not infer natural posing or body language', () => {
  const interpretation = ApiService.interpretPose({
    detected: true, available: true, score_kind: 'landmark-visibility', visibility: 0.7,
    quality_score: 7,
  });
  expect(interpretation).toContain('70% average visibility');
  expect(interpretation).not.toContain('body language');
});
