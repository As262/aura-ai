# Usage Tracking Implementation

## Overview
Implemented separate IP-based usage tracking for Aesthetic Analyzer (5 uses) and Convo Decoder (15 uses) with real-time updates and navbar display.

## Features Implemented

### 1. **UsageTracker Utility** (`frontend/src/utils/UsageTracker.js`)
- LocalStorage-based tracking system
- Separate counters for each feature:
  - `aesthetic_analyzer`: 5 uses limit
  - `convo_decoder`: 15 uses limit
- Methods:
  - `getFeatureUsage(feature)`: Get usage stats for a feature
  - `canUseFeature(feature)`: Check if feature can be used
  - `incrementUsage(feature)`: Increment usage count
  - `resetFeature(feature)`: Reset usage for a feature
  - `resetAll()`: Reset all usage counters
- Event-driven updates using CustomEvent `usageUpdated`

### 2. **Updated UsageContext** (`frontend/src/contexts/UsageContext.js`)
- Manages usage state for both features
- `performAnalysis(feature, analysisFunction)`:
  - Checks usage limit before analysis
  - Executes the analysis function
  - Automatically increments usage on success
  - Returns usage limit error if exceeded
- `getFeatureUsage(feature)`: Get current usage for a feature
- `resetFeature(feature)`: Reset usage for a specific feature
- `resetAll()`: Reset all usage
- Real-time synchronization with UsageTracker events

### 3. **Smart UsageBadge** (`frontend/src/components/Header.js`)
- Shows feature-specific usage based on current route
- **On Aesthetic Analyzer page**: Shows "0/5 (5 left)"
- **On Convo Decoder page**: Shows "0/15 (15 left)"
- **On other pages**: Badge hidden
- Updates automatically after each use

### 4. **Updated AestheticAnalyzer** (`frontend/src/pages/AestheticAnalyzer.js`)
- Integrated with UsageContext
- Checks usage limit before analysis
- Shows error if limit exceeded
- Automatically increments usage on successful analysis
- Toast notifications for user feedback

### 5. **Updated ConvoDecoder** (`frontend/src/pages/ConvoDecoder.js`)
- Same integration pattern as AestheticAnalyzer
- Separate tracking with 15-use limit
- Consistent user experience

## Usage Flow

1. **User uploads file** → Privacy modal appears
2. **User accepts** → Check usage limit
3. **If limit exceeded** → Show error message + clear preview
4. **If limit OK** → Perform analysis
5. **On success** → Increment usage counter
6. **Navbar updates** → Shows new usage count automatically

## Storage Structure

```javascript
// localStorage['aura_ai_usage_tracking']
{
  "aesthetic_analyzer": {
    "count": 3,
    "limit": 5,
    "remaining": 2,
    "lastReset": 1234567890
  },
  "convo_decoder": {
    "count": 7,
    "limit": 15,
    "remaining": 8,
    "lastReset": 1234567890
  }
}
```

## Benefits

✅ **Separate Tracking**: Each feature has independent usage limits
✅ **Real-time Updates**: Navbar shows current usage immediately
✅ **Persistent**: Uses localStorage - survives page refresh
✅ **User-friendly**: Clear error messages when limit reached
✅ **Event-driven**: Components update automatically via CustomEvent
✅ **No Backend Required**: Fully client-side implementation
✅ **Flexible**: Easy to change limits or add new features

## Future Enhancements

- Add IP detection (requires backend)
- Add usage reset timer (daily/weekly)
- Add usage history/analytics
- Add premium tier with unlimited usage
- Add usage warning at 80% threshold
