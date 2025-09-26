import React from 'react';
import './DetailedAnalysisResults.css';

const DetailedAnalysisResults = ({ analysis, isLoading }) => {
  if (isLoading) {
    return (
      <div className="detailed-analysis-loading">
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
        <p>Upload an image to get detailed AI analysis and improvement suggestions!</p>
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
    aesthetic_score,
    improvement_suggestions 
  } = analysis;

  const interpretations = analysis.interpretations || {};
  const priorityActions = analysis.priority_actions || [];
  const skillRecommendations = analysis.skill_recommendations || [];

  return (
    <div className="detailed-analysis-results">
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
            <div className="skill-level">
              Skill Level: <span className="level">{interpretations.rating_interpretation?.level}</span>
            </div>
          </div>
        </div>
        
        {overall_rating?.breakdown && (
          <div className="rating-breakdown">
            <div className="breakdown-item">
              <span>Technical</span>
              <div className="progress-bar">
                <div className="progress" style={{width: `${overall_rating.breakdown.technical * 10}%`}}></div>
              </div>
              <span>{overall_rating.breakdown.technical}</span>
            </div>
            <div className="breakdown-item">
              <span>Aesthetic</span>
              <div className="progress-bar">
                <div className="progress" style={{width: `${overall_rating.breakdown.aesthetic * 10}%`}}></div>
              </div>
              <span>{overall_rating.breakdown.aesthetic}</span>
            </div>
            <div className="breakdown-item">
              <span>Composition</span>
              <div className="progress-bar">
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

      {/* Technical Quality */}
      {technical_quality && (
        <div className="analysis-section technical-quality">
          <h2>🔧 Technical Quality</h2>
          <p className="section-summary">{interpretations.technical_summary}</p>
          
          <div className="technical-metrics">
            {technical_quality.sharpness && (
              <div className="metric">
                <h4>Sharpness</h4>
                <div className="metric-value">
                  <span className="score">{technical_quality.sharpness.score?.toFixed(1)}</span>
                  <span className="level">{technical_quality.sharpness.level}</span>
                </div>
              </div>
            )}
            
            {technical_quality.noise && (
              <div className="metric">
                <h4>Noise Level</h4>
                <div className="metric-value">
                  <span className="score">{technical_quality.noise.level?.toFixed(1)}</span>
                  <span className="level">{technical_quality.noise.rating}</span>
                </div>
              </div>
            )}
            
            {technical_quality.brightness && (
              <div className="metric">
                <h4>Brightness</h4>
                <div className="metric-value">
                  <span className="score">{technical_quality.brightness.value?.toFixed(0)}</span>
                  <span className="level">{technical_quality.brightness.rating}</span>
                </div>
              </div>
            )}
            
            {technical_quality.contrast && (
              <div className="metric">
                <h4>Contrast</h4>
                <div className="metric-value">
                  <span className="score">{technical_quality.contrast.value?.toFixed(0)}</span>
                  <span className="level">{technical_quality.contrast.rating}</span>
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Pose Analysis */}
      {pose_analysis && (
        <div className="analysis-section pose-analysis">
          <h2>🧍 Pose Analysis</h2>
          {pose_analysis.detected ? (
            <>
              <p className="section-summary">{interpretations.pose_feedback}</p>
              <div className="pose-metrics">
                <div className="metric">
                  <h4>Quality Score</h4>
                  <span className="score">{pose_analysis.quality_score?.toFixed(1)}/10</span>
                </div>
                {pose_analysis.analysis && (
                  <>
                    <div className="metric">
                      <h4>Posture</h4>
                      <span className="level">{pose_analysis.analysis.posture}</span>
                    </div>
                    <div className="metric">
                      <h4>Balance</h4>
                      <span className="level">{pose_analysis.analysis.balance}</span>
                    </div>
                    <div className="metric">
                      <h4>Symmetry</h4>
                      <span className="level">{pose_analysis.analysis.symmetry}</span>
                    </div>
                    <div className="metric">
                      <h4>Openness</h4>
                      <span className="level">{pose_analysis.analysis.openness}</span>
                    </div>
                  </>
                )}
              </div>
            </>
          ) : (
            <p className="no-detection">No human pose detected in this image.</p>
          )}
        </div>
      )}

      {/* Lighting Analysis */}
      {lighting_analysis && (
        <div className="analysis-section lighting-analysis">
          <h2>💡 Lighting Analysis</h2>
          <p className="section-summary">{interpretations.lighting_feedback}</p>
          
          <div className="lighting-metrics">
            <div className="metric">
              <h4>Overall Quality</h4>
              <span className="level">{lighting_analysis.overall_quality}</span>
            </div>
            
            {lighting_analysis.brightness && (
              <div className="metric">
                <h4>Brightness Distribution</h4>
                <span className="level">{lighting_analysis.brightness.distribution}</span>
              </div>
            )}
            
            {lighting_analysis.shadows && (
              <div className="metric">
                <h4>Shadows</h4>
                <span className="score">{lighting_analysis.shadows.percentage}%</span>
                <span className="level">{lighting_analysis.shadows.level}</span>
              </div>
            )}
            
            {lighting_analysis.color_temperature && (
              <div className="metric">
                <h4>Color Temperature</h4>
                <span className="score">{lighting_analysis.color_temperature.kelvin}K</span>
                <span className="level">{lighting_analysis.color_temperature.description}</span>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Composition Analysis */}
      {composition_analysis && (
        <div className="analysis-section composition-analysis">
          <h2>📐 Composition Analysis</h2>
          <p className="section-summary">{interpretations.composition_tips}</p>
          
          <div className="composition-metrics">
            {composition_analysis.rule_of_thirds && (
              <div className="metric">
                <h4>Rule of Thirds</h4>
                <span className="score">{composition_analysis.rule_of_thirds.score}/10</span>
                <span className="level">{composition_analysis.rule_of_thirds.compliance}</span>
              </div>
            )}
            
            {composition_analysis.balance && (
              <div className="metric">
                <h4>Visual Balance</h4>
                <span className="score">{composition_analysis.balance.score}/10</span>
                <span className="level">{composition_analysis.balance.type}</span>
              </div>
            )}
            
            {composition_analysis.symmetry && (
              <div className="metric">
                <h4>Symmetry</h4>
                <span className="score">{composition_analysis.symmetry.score}/10</span>
                <span className="level">{composition_analysis.symmetry.type}</span>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Color Analysis */}
      {color_analysis && (
        <div className="analysis-section color-analysis">
          <h2>🎨 Color Analysis</h2>
          <p className="section-summary">{interpretations.color_insights}</p>
          
          {color_analysis.dominant_colors && (
            <div className="color-palette">
              <h4>Dominant Colors</h4>
              <div className="colors-grid">
                {color_analysis.dominant_colors.map((color, index) => (
                  <div key={index} className="color-item">
                    <div 
                      className="color-swatch" 
                      style={{backgroundColor: color.hex}}
                    ></div>
                    <div className="color-info">
                      <span className="color-name">{color.name}</span>
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
                <h4>Color Harmony</h4>
                <span className="score">{color_analysis.harmony.score}/10</span>
                <span className="level">{color_analysis.harmony.type}</span>
              </div>
            )}
            
            {color_analysis.saturation && (
              <div className="metric">
                <h4>Saturation</h4>
                <span className="score">{color_analysis.saturation.score}/10</span>
                <span className="level">{color_analysis.saturation.level}</span>
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
                <h4>{skill.skill}</h4>
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

      {/* Aesthetic Score Details */}
      {aesthetic_score && (
        <div className="analysis-section aesthetic-score">
          <h2>✨ Aesthetic Score Breakdown</h2>
          <div className="aesthetic-display">
            <div className="score-circle">
              <span className="score">{aesthetic_score.score}</span>
              <span className="max">/10</span>
            </div>
            <p>{aesthetic_score.interpretation}</p>
          </div>
          
          {aesthetic_score.factors && (
            <div className="factors-breakdown">
              {Object.entries(aesthetic_score.factors).map(([factor, score]) => (
                <div key={factor} className="factor-item">
                  <span className="factor-name">{factor.replace('_', ' ')}</span>
                  <div className="progress-bar">
                    <div className="progress" style={{width: `${score * 10}%`}}></div>
                  </div>
                  <span className="factor-score">{score.toFixed(1)}</span>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default DetailedAnalysisResults;