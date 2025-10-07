import React from 'react';
import { useUsage } from '../contexts/UsageContext';
import './UsageLimitGuard.css';

function UsageLimitGuard({ children, showWarning = true, disabled = false }) {
  const { usage } = useUsage() || {};
  
  if (!usage) {
    // Loading state
    return <div className="usage-limit-guard loading">{children}</div>;
  }

  const isLimitExceeded = !usage.can_use || usage.remaining <= 0;
  const isNearLimit = usage.remaining <= 1 && usage.remaining > 0;

  if (isLimitExceeded) {
    return (
      <div className="usage-limit-guard exceeded">
        <div className="usage-limit-overlay">
          <div className="usage-limit-message">
            <h3>🚫 Usage Limit Reached</h3>
            <p>
              You have used all {usage.limit} of your analyses.
              <br />
              Contact support to increase your limit.
            </p>
            <div className="usage-stats">
              <strong>{usage.usage_count}/{usage.limit} used ({usage.percentage_used}%)</strong>
            </div>
          </div>
        </div>
        <div className="usage-limit-content disabled">
          {children}
        </div>
      </div>
    );
  }

  if (isNearLimit && showWarning) {
    return (
      <div className="usage-limit-guard warning">
        <div className="usage-warning-banner">
          ⚠️ Warning: Only {usage.remaining} analysis remaining!
        </div>
        {children}
      </div>
    );
  }

  return (
    <div className="usage-limit-guard normal">
      {children}
    </div>
  );
}

export default UsageLimitGuard;
