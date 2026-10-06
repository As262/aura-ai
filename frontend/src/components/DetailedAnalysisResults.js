import React from 'react';
import './DetailedAnalysisResults.css';
import './CompositionTips.css';

const DetailedAnalysisResults = ({ analysis, isLoading }) => {
  if (isLoading) {
    return (
      <div className="detailed-analysis-loading" role="status" aria-live="polite">
        <div className="loading-spinner"></div>
        <p>Analyzing your image with AI...</p>
        <div className="loading-steps">
          <div className="step">🔍 Examining technical quality</div>
          <div className="step">🎯 Analyzing composition</div>
          <div className="step">💡 Evaluating lighting</div>
          <div className="step">🧍 Detecting pose</div>
          <div className="step">🎨 Assessing colors</div>
          <div className="step">📊 Generating recommendations</div>
        </div>
      </div>
    );
  }

  if (!analysis) {
    return (
      <div className="no-analysis">
      </div>
    );
  }

  const { 
    overall_rating, 
    technical_quality, 
    pose_analysis, 
    lighting_analysis, 
    composition_analysis, 
    color_analysis, 
    aesthetic_score
  } = analysis;

  const interpretations = analysis.interpretations || {};
  const priorityActions = analysis.priority_actions || [];
  const skillRecommendations = analysis.skill_recommendations || [];
  const lightingBrightnessScore = lighting_analysis?.mean_brightness === undefined
    ? 0
    : Math.max(0, Math.min(10, 10 - Math.abs(lighting_analysis.mean_brightness - 127) / 12.7));

  const aestheticScoreSection = aesthetic_score ? (
    <div className="analysis-section aesthetic-score">
      <h2>Aesthetic assessment</h2>
      <div className="aesthetic-display">
        <div className="score-circle">
          <span className="score">{aesthetic_score.score}</span>
          <span className="max">/10</span>
        </div>
        <p>{aesthetic_score.interpretation}</p>
      </div>

      {aesthetic_score.factors && (
        <div className="factors-breakdown">
          <h3>Visual diagnostics</h3>
          {Object.entries(aesthetic_score.factors).map(([factor, score]) => {
            const numericScore = typeof score === 'number' ? score : 0;
            return (
              <div key={factor} className="factor-item">
                <span className="factor-name">{factor.replace(/_/g, ' ')}</span>
                <div className="progress-bar" role="progressbar" aria-label={`${factor.replace(/_/g, ' ')} score`} aria-valuemin="0" aria-valuemax="10" aria-valuenow={numericScore}>
                  <div className="progress" style={{width: `${numericScore * 10}%`}}></div>
                </div>
                <span className="factor-score">{typeof score === 'number' ? score.toFixed(1) : score}</span>
              </div>
            );
          })}
        </div>
      )}
    </div>
  ) : null;

  return (
    <div className="detailed-analysis-results" aria-label="Detailed image analysis results">
      {/* Overall Rating Section */}
      <div className="analysis-section overall-rating">
        <h2>Overall Rating</h2>
        <div className="rating-display">
          <div className="score-circle">
            <span className="score">{overall_rating?.score || 0}</span>
            <span className="max">/10</span>
          </div>
          <div className="rating-info">
            <h3>{overall_rating?.category || 'Unknown'}</h3>
            <p>{interpretations.rating_interpretation?.message}</p>
            {interpretations.rating_interpretation?.level && (
              <div className="skill-level">
                Skill Level: <span className="level">{interpretations.rating_interpretation.level}</span>
              </div>
            )}
          </div>
        </div>
        
        {overall_rating?.breakdown && (
          <div className="rating-breakdown">
            <div className="breakdown-item">
              <span>Technical</span>
              <div className="progress-bar" role="progressbar" aria-label="Technical score" aria-valuemin="0" aria-valuemax="10" aria-valuenow={overall_rating.breakdown.technical}>
                <div className="progress" style={{width: `${overall_rating.breakdown.technical * 10}%`}}></div>
              </div>
              <span>{overall_rating.breakdown.technical}</span>
            </div>
            <div className="breakdown-item">
              <span>Aesthetic</span>
              <div className="progress-bar" role="progressbar" aria-label="Aesthetic score" aria-valuemin="0" aria-valuemax="10" aria-valuenow={overall_rating.breakdown.aesthetic}>
                <div className="progress" style={{width: `${overall_rating.breakdown.aesthetic * 10}%`}}></div>
              </div>
              <span>{overall_rating.breakdown.aesthetic}</span>
            </div>
            <div className="breakdown-item">
              <span>Composition</span>
              <div className="progress-bar" role="progressbar" aria-label="Composition score" aria-valuemin="0" aria-valuemax="10" aria-valuenow={overall_rating.breakdown.composition}>
                <div className="progress" style={{width: `${overall_rating.breakdown.composition * 10}%`}}></div>
              </div>
              <span>{overall_rating.breakdown.composition}</span>
            </div>
          </div>
        )}
      </div>

      {/* Priority Suggestions */}
      {priorityActions.length > 0 && (
        <div className="analysis-section priority-suggestions">
          <h2>🎯 Priority Improvements</h2>
          <div className="suggestions-list">
            {priorityActions.map((suggestion, index) => (
              <div key={index} className={`suggestion-item priority-${suggestion.priority?.toLowerCase()}`}>
                <div className="suggestion-header">
                  <span className="rank">#{suggestion.rank}</span>
                  <span className="category">{suggestion.category}</span>
                  <span className={`priority ${suggestion.priority?.toLowerCase()}`}>
                    {suggestion.priority} Priority
                  </span>
                </div>
                <p className="suggestion-text">{suggestion.suggestion}</p>
                <div className="actionable-tip">
                  <strong>How to fix:</strong> {suggestion.actionable}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {aestheticScoreSection}

      {/* Technical Quality */}
      {technical_quality && (
        <div className="analysis-section technical-quality">
          <h2><span className="emoji">🔧</span><span className="title-text">Technical Quality</span></h2>
          
          <div className="technical-metrics">
            {technical_quality.sharpness && (
              <div className="metric">
                <h3 className="metric-label">Sharpness</h3>
                <div className="metric-value">
                  <span className="score">{technical_quality.sharpness.score?.toFixed(1)}/10</span>
                  <span className="level">{technical_quality.sharpness.rating}</span>
                </div>
              </div>
            )}
            
            {technical_quality.noise && (
              <div className="metric">
                <h3 className="metric-label">Noise Level</h3>
                <div className="metric-value">
                  <span className="score">{technical_quality.noise.score?.toFixed(1)}/10</span>
                  <span className="level">{technical_quality.noise.rating}</span>
                  <span className="metric-caption">Measured noise: {technical_quality.noise.level?.toFixed(1)}</span>
                </div>
              </div>
            )}
            
            {technical_quality.brightness && (
              <div className="metric">
                <h3 className="metric-label">Brightness</h3>
                <div className="metric-value">
                  <span className="score">{technical_quality.brightness.score?.toFixed(1)}/10</span>
                  <span className="level">{
                    technical_quality.brightness.value < 90 ? 'Too dark'
                    : technical_quality.brightness.value > 170 ? 'Too bright'
                    : 'Good'
                  }</span>
                  <span className="metric-caption">mean {technical_quality.brightness.value?.toFixed(0)}/255</span>
                </div>
              </div>
            )}

            {technical_quality.contrast && (
              <div className="metric">
                <h3 className="metric-label">Contrast</h3>
                <div className="metric-value">
                  <span className="score">{technical_quality.contrast.score?.toFixed(1)}/10</span>
                  <span className="level">{
                    technical_quality.contrast.value < 30 ? 'Low / flat'
                    : technical_quality.contrast.value > 80 ? 'Harsh'
                    : 'Good'
                  }</span>
                  <span className="metric-caption">std {technical_quality.contrast.value?.toFixed(0)}</span>
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Pose Analysis */}
      {pose_analysis && (
        <div className="analysis-section pose-analysis">
          <h2><span className="emoji">🧍</span><span className="title-text">Pose Analysis</span></h2>
          {pose_analysis.detected ? (
            <>
              <div className="pose-metrics">
                <div className="metric">
                  <h3 className="metric-label">{pose_analysis.score_kind === 'landmark-visibility' ? 'Landmark visibility' : 'Score'}</h3>
                  <span className="score">{pose_analysis.quality_score?.toFixed(1)}/10</span>
                </div>
                {pose_analysis.analysis && (
                  <>
                    <div className="metric">
                      <h3 className="metric-label">Posture</h3>
                      <span className="level">{pose_analysis.analysis.posture}</span>
                    </div>
                    <div className="metric">
                      <h3 className="metric-label">Balance</h3>
                      <span className="level">{pose_analysis.analysis.balance}</span>
                    </div>
                    <div className="metric">
                      <h3 className="metric-label">Symmetry</h3>
                      <span className="level">{pose_analysis.analysis.symmetry}</span>
                    </div>
                    <div className="metric">
                      <h3 className="metric-label">Openness</h3>
                      <span className="level">{pose_analysis.analysis.openness}</span>
                    </div>
                  </>
                )}
              </div>
            </>
          ) : (
            <p className="no-detection">{pose_analysis.available === false
              ? 'Pose detection is unavailable in this environment.'
              : 'No human pose detected in this image.'}</p>
          )}
        </div>
      )}

      {/* Lighting Analysis */}
      {lighting_analysis && (
        <div className="analysis-section lighting-analysis">
          <h2><span className="emoji">💡</span><span className="title-text">Lighting Analysis</span></h2>
          
          {/* Overall Quality Banner */}
          <div className="quality-banner">
            <div className="quality-main">
              <span className="quality-label">Overall Quality</span>
              <span className="quality-score-large">{lighting_analysis.overall_score}/10</span>
              <span className={`quality-badge ${lighting_analysis.quality?.toLowerCase().replace(/\s+/g, '-')}`}>
                {lighting_analysis.quality}
              </span>
            </div>
          </div>
          
          {/* Lighting Metrics Grid */}
          <div className="lighting-metrics-grid">
            {/* Exposure */}
            {lighting_analysis.exposure !== undefined && (
              <div className="metric-card">
                <div className="metric-icon">☀️</div>
                <h3 className="metric-label">Exposure</h3>
                <span className="score">{lighting_analysis.exposure}/10</span>
                <span className="metric-caption">Exposure balance</span>
                <div className="progress-bar" role="progressbar" aria-label="Exposure score" aria-valuemin="0" aria-valuemax="10" aria-valuenow={lighting_analysis.exposure}>
                  <div 
                    className="progress-fill" 
                    style={{width: `${(lighting_analysis.exposure / 10) * 100}%`}}
                  />
                </div>
              </div>
            )}
            
            {/* Evenness */}
            {lighting_analysis.evenness !== undefined && (
              <div className="metric-card">
                <div className="metric-icon">⚖️</div>
                <h3 className="metric-label">Evenness</h3>
                <span className="score">{lighting_analysis.evenness}/10</span>
                <span className="metric-caption">Light distribution</span>
                <div className="progress-bar" role="progressbar" aria-label="Evenness score" aria-valuemin="0" aria-valuemax="10" aria-valuenow={lighting_analysis.evenness}>
                  <div 
                    className="progress-fill" 
                    style={{width: `${(lighting_analysis.evenness / 10) * 100}%`}}
                  />
                </div>
              </div>
            )}
            
            {/* Shadows */}
            {lighting_analysis.shadows && (
              <div className="metric-card">
                <div className="metric-icon">🌑</div>
                <h3 className="metric-label">Shadows</h3>
                <span className="score">{lighting_analysis.shadows.score}/10</span>
                <span className="metric-caption">Clipped: {lighting_analysis.shadows.percentage}%</span>
                <div className="progress-bar" role="progressbar" aria-label="Shadows score" aria-valuemin="0" aria-valuemax="10" aria-valuenow={lighting_analysis.shadows.score}>
                  <div 
                    className="progress-fill shadow" 
                    style={{width: `${(lighting_analysis.shadows.score / 10) * 100}%`}}
                  />
                </div>
              </div>
            )}
            
            {/* Highlights */}
            {lighting_analysis.highlights && (
              <div className="metric-card">
                <div className="metric-icon">✨</div>
                <h3 className="metric-label">Highlights</h3>
                <span className="score">{lighting_analysis.highlights.score}/10</span>
                <span className="metric-caption">Clipped: {lighting_analysis.highlights.percentage}%</span>
                <div className="progress-bar" role="progressbar" aria-label="Highlights score" aria-valuemin="0" aria-valuemax="10" aria-valuenow={lighting_analysis.highlights.score}>
                  <div 
                    className="progress-fill highlight" 
                    style={{width: `${(lighting_analysis.highlights.score / 10) * 100}%`}}
                  />
                </div>
              </div>
            )}
            
            {/* Mean Brightness */}
            {lighting_analysis.mean_brightness !== undefined && (
              <div className="metric-card">
                <div className="metric-icon">💡</div>
                <h3 className="metric-label">Brightness</h3>
                <span className="score">{lightingBrightnessScore.toFixed(1)}/10</span>
                <span className="metric-caption">Mean: {Math.round(lighting_analysis.mean_brightness)}/255</span>
                <div className="progress-bar" role="progressbar" aria-label="Brightness score" aria-valuemin="0" aria-valuemax="10" aria-valuenow={lightingBrightnessScore}>
                  <div className="progress-fill" style={{width: `${lightingBrightnessScore * 10}%`}} />
                </div>
              </div>
            )}
            
            {/* Consistency */}
            {lighting_analysis.consistency !== undefined && (
              <div className="metric-card">
                <div className="metric-icon">📊</div>
                <h3 className="metric-label">Consistency</h3>
                <span className="score">{lighting_analysis.consistency}/10</span>
                <span className="metric-caption">Frame uniformity</span>
                <div className="progress-bar" role="progressbar" aria-label="Consistency score" aria-valuemin="0" aria-valuemax="10" aria-valuenow={lighting_analysis.consistency}>
                  <div 
                    className="progress-fill" 
                    style={{width: `${(lighting_analysis.consistency / 10) * 100}%`}}
                  />
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Composition Analysis */}
      {composition_analysis && (
        <div className="analysis-section composition-analysis">
          <h2><span className="emoji">📐</span><span className="title-text">Composition Analysis</span></h2>
          
          {/* Detected Composition Type */}
          {composition_analysis.detected_type && (
            <div className="detected-composition">
              <div className="composition-header">
                <h3>{composition_analysis.ml_reliable === false ? 'Possible composition style' : 'Detected composition style'}</h3>
                <span className={`composition-badge ${composition_analysis.quality?.toLowerCase().replace(/\s+/g, '-')}`}>
                  {composition_analysis.quality}
                </span>
              </div>
              <div className="composition-details">
                <div className="composition-name">
                  <strong>{composition_analysis.detected_type}</strong>
                  <span className="composition-score">
                    {composition_analysis.score_kind === 'geometric-match-heuristic' ? 'Geometric match' : 'Score'}: {composition_analysis.score}/10
                  </span>
                </div>
                {composition_analysis.method === 'ml' && (
                  <p className="metric-caption">Style confidence: {composition_analysis.ml_confidence}%</p>
                )}
                <p className="composition-description">{composition_analysis.description}</p>
                <p className="composition-ideal"><strong>Best For:</strong> {composition_analysis.ideal_for}</p>
              </div>
              
              {composition_analysis.secondary_type && (
                <div className="secondary-composition">
                  <p><strong>Also shows elements of:</strong> {composition_analysis.secondary_type}</p>
                </div>
              )}
            </div>
          )}
          
          {/* Composition strength across all styles (real geometric scores) */}
          {composition_analysis.all_scores ? (
            <div className="other-styles">
              <h3 className="other-styles-heading">Geometric signals</h3>
              <div className="composition-metrics">
                {Object.entries(composition_analysis.all_scores)
                  .filter(([key]) => key !== composition_analysis.type_key)
                  .sort((a, b) => b[1] - a[1])
                  .map(([key, score]) => {
                    const LABELS = {
                      rule_of_thirds: 'Rule of Thirds',
                      centered: 'Centered',
                      leading_lines: 'Leading Lines',
                      diagonal: 'Diagonal',
                      symmetrical: 'Symmetry',
                      golden_ratio: 'Golden Ratio',
                      fill_the_frame: 'Fill the Frame',
                      frame_within_frame: 'Frame within Frame',
                    };
                    return (
                      <div className="metric" key={key}>
                        <h3 className="metric-label">{LABELS[key] || key.replace(/_/g, ' ')}</h3>
                        <span className="score">{typeof score === 'number' ? score.toFixed(1) : score}/10</span>
                      </div>
                    );
                  })}
              </div>
            </div>
          ) : (
            /* Legacy formats (no all_scores in payload) */
            <div className="composition-metrics">
              {composition_analysis.analysis_details && (
                <>
                  <div className="metric">
                    <h3 className="metric-label">Rule of Thirds</h3>
                    <span className="score">{composition_analysis.analysis_details.rule_of_thirds}/10</span>
                  </div>
                  <div className="metric">
                    <h3 className="metric-label">Symmetry</h3>
                    <span className="score">{composition_analysis.analysis_details.symmetry}/10</span>
                  </div>
                  <div className="metric">
                    <h3 className="metric-label">Leading Lines</h3>
                    <span className="score">{composition_analysis.analysis_details.leading_lines}/10</span>
                  </div>
                  <div className="metric">
                    <h3 className="metric-label">Golden Ratio</h3>
                    <span className="score">{composition_analysis.analysis_details.golden_ratio}/10</span>
                  </div>
                </>
              )}

              {!composition_analysis.analysis_details && composition_analysis.rule_of_thirds && (
                <div className="metric">
                  <h3 className="metric-label">Rule of Thirds</h3>
                  <span className="score">{composition_analysis.rule_of_thirds.score}/10</span>
                  <span className="level">{composition_analysis.rule_of_thirds.compliance}</span>
                </div>
              )}

              {!composition_analysis.analysis_details && composition_analysis.balance && (
                <div className="metric">
                  <h3 className="metric-label">Visual Balance</h3>
                  <span className="score">{composition_analysis.balance.score}/10</span>
                  <span className="level">{composition_analysis.balance.type}</span>
                </div>
              )}

              {!composition_analysis.analysis_details && composition_analysis.symmetry && (
                <div className="metric">
                  <h3 className="metric-label">Symmetry</h3>
                  <span className="score">{composition_analysis.symmetry.score}/10</span>
                  <span className="level">{composition_analysis.symmetry.type}</span>
                </div>
              )}
            </div>
          )}
        </div>
      )}

      {/* Dynamic Tips Section - NEW! */}
      {analysis.tips && analysis.tips.length > 0 && (
        <div className="analysis-section tips-section">
          <h2><span className="emoji">💡</span><span className="title-text">Additional Tips & Suggestions</span></h2>
          <p className="section-intro">Extra guidance beyond the priority improvements above</p>
          
          <div className="tips-container">
            {analysis.tips.map((tip, index) => (
              <div key={index} className={`tip-card priority-${tip.priority?.toLowerCase()}`}>
                <div className="tip-header">
                  <span className={`priority-badge ${tip.priority?.toLowerCase()}`}>
                    {tip.priority} Priority
                  </span>
                  <span className="category-badge">{tip.category}</span>
                </div>
                
                <div className="tip-content">
                  <div className="current-status">
                    <strong>Current:</strong> {tip.current}
                  </div>
                  
                  <div className="tip-suggestion">
                    <strong>💡 Tip:</strong> {tip.tip}
                  </div>
                  
                  {tip.alternative && tip.alternative.type && tip.alternative.score && (
                    <div className="tip-alternative">
                      <strong>Better Composition:</strong>
                      <div className="alternative-details">
                        <p><strong>{tip.alternative.type}</strong> (Score: {tip.alternative.score}/10)</p>
                        <p>{tip.alternative.reason}</p>
                        <div className="how-to">
                          <strong>How to achieve this:</strong> {tip.alternative.how_to}
                        </div>
                      </div>
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Color Analysis */}
      {color_analysis && (
        <div className="analysis-section color-analysis">
          <h2><span className="emoji">🎨</span><span className="title-text">Color Analysis</span></h2>
          
          {color_analysis.dominant_colors && (
            <div className="color-palette">
              <h3 className="metric-label">Dominant Colors</h3>
              <div className="colors-grid">
                {color_analysis.dominant_colors.map((color, index) => (
                  <div key={index} className="color-item">
                    <div 
                      className="color-swatch" 
                      style={{backgroundColor: color.hex}}
                    ></div>
                    <div className="color-info">
                      <span className="color-name">{color.name || color.hex?.toUpperCase()}</span>
                      <span className="color-percentage">{color.percentage}%</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
          
          <div className="color-metrics">
            {color_analysis.harmony && (
              <div className="metric">
                <h3 className="metric-label">Color Harmony</h3>
                <span className="score">{color_analysis.harmony.score}/10</span>
                <span className="level">{color_analysis.harmony.type}</span>
              </div>
            )}
            
            {color_analysis.saturation && (
              <div className="metric">
                <h3 className="metric-label">Saturation</h3>
                <span className="score">{color_analysis.saturation.score}/10</span>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Skill Recommendations */}
      {skillRecommendations.length > 0 && (
        <div className="analysis-section skill-recommendations">
          <h2>📚 Learning Recommendations</h2>
          <div className="skills-grid">
            {skillRecommendations.map((skill, index) => (
              <div key={index} className="skill-card">
                <h3 className="skill-heading">{skill.skill}</h3>
                <p>{skill.focus}</p>
                <div className="resources">
                  <strong>Study:</strong>
                  <ul>
                    {skill.resources.map((resource, i) => (
                      <li key={i}>{resource}</li>
                    ))}
                  </ul>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

    </div>
  );
};

export default DetailedAnalysisResults;
