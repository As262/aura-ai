# Visual Guide: New Features

## 1. ConvoDecoder - Text Paste Feature

### Input Mode Toggle
```
┌─────────────────────────────────────────────┐
│  [ 📤 Upload File ]  [ 📝 Paste Text ]     │
│     (active)           (inactive)           │
└─────────────────────────────────────────────┘
```

When "Paste Text" is selected:

```
┌───────────────────────────────────────────────────────────────┐
│  💬 Paste Your Chat Messages        Platform: [WhatsApp ▼]   │
├───────────────────────────────────────────────────────────────┤
│                                                                │
│  ┌──────────────────────────────────────────────────────────┐ │
│  │ Paste your WhatsApp chat messages here...                │ │
│  │                                                           │ │
│  │ Example:                                                  │ │
│  │ [12:30 PM] John: Hey! How are you?                      │ │
│  │ [12:31 PM] Sarah: I'm good! Just working...             │ │
│  │                                                           │ │
│  │                                                           │ │
│  └──────────────────────────────────────────────────────────┘ │
│                                                                │
│  125 characters                                                │
│  ✓ Ready to analyze                                            │
│                                                                │
│  [ Clear ]                              [ ✓ Analyze Chat ]    │
│                                                                │
│  💡 Tips for best results:                                     │
│  → Copy entire chat conversations (at least 50 characters)    │
│  → Include timestamps if available for better timing analysis │
│  → Longer conversations provide more accurate insights        │
│  → Works with any chat format - we'll decode it!              │
└───────────────────────────────────────────────────────────────┘
```

### Validation States

**Insufficient Characters (< 50):**
```
└─ 25 characters (warning color)
   (minimum 50 characters)
```

**Ready to Analyze (≥ 50):**
```
└─ 125 characters (success color)
   ✓ Ready to analyze
```

---

## 2. Pricing Page - Reset Usage Button

### Desktop Layout
```
┌──────────────────────────────────────────────────────────────────┐
│  Current Usage for Aesthetic Analyzer                            │
│                                                                   │
│  ┌────────────────────────────────┐  ┌────────────────────────┐ │
│  │      3    /    5    •    2     │  │  🔄 Reset Usage       │ │
│  │    Used      Total   Remaining │  │                        │ │
│  └────────────────────────────────┘  └────────────────────────┘ │
└──────────────────────────────────────────────────────────────────┘
```

### Mobile Layout (≤768px)
```
┌─────────────────────────────────────────┐
│  Current Usage for Aesthetic Analyzer   │
│                                          │
│      3    /    5    •    2              │
│    Used      Total   Remaining          │
│                                          │
│  ┌────────────────────────────────────┐ │
│  │      🔄 Reset Usage                │ │
│  └────────────────────────────────────┘ │
└─────────────────────────────────────────┘
```

### Reset Confirmation Dialog
```
┌─────────────────────────────────────────┐
│  🔄 Reset Usage Counts?                 │
│                                          │
│  This will reset:                        │
│  • Aesthetic Analyzer to 5 uses         │
│  • Convo Decoder to 15 uses             │
│                                          │
│  Are you sure you want to continue?     │
│                                          │
│  [ Cancel ]              [ OK ]         │
└─────────────────────────────────────────┘
```

### Success Toast Notification
```
┌─────────────────────────────────────────┐
│  ✅ Usage counts have been reset to     │
│     default!                             │
└─────────────────────────────────────────┘
```

---

## 3. Feature Flow Diagrams

### Text Paste Flow:
```
User Opens ConvoDecoder
         ↓
Clicks "Paste Text" Toggle
         ↓
Selects Platform (WhatsApp, Instagram, etc.)
         ↓
Pastes Chat Messages (min 50 chars)
         ↓
Character Counter Shows Status
         ↓
Clicks "Analyze Chat"
         ↓
Privacy Consent Modal Appears
         ↓
User Accepts Privacy Terms
         ↓
Usage Limit Check
         ↓
Text Converted to File Format
         ↓
Sent to Analysis API
         ↓
Results Displayed
```

### Reset Usage Flow:
```
User Opens Pricing Page
         ↓
Scrolls to "Current Usage" Section
         ↓
Clicks "Reset Usage" Button
         ↓
Confirmation Dialog Appears
         ↓
User Clicks "OK"
         ↓
UsageContext.resetAll() Called
         ↓
localStorage Updated
         ↓
UI Refreshes with New Counts
         ↓
Success Toast Shown
```

---

## 4. Color Scheme

### Dark Mode:
- **Toggle Active**: Neon Green (rgba(0, 255, 136, 0.15))
- **Text Input Border**: Neon Green (rgba(0, 255, 136, 0.2))
- **Analyze Button**: Green Gradient (#00ff88 → rgba(0, 255, 136, 0.7))
- **Reset Button**: Purple-Green Gradient (rgba(138, 43, 226) → rgba(0, 255, 136))
- **Warning Text**: Amber (#fbbf24)
- **Success Text**: Neon Green (#00ff88)

### Light Mode:
- **Toggle Active**: Light Green/Purple (rgba(0, 255, 136, 0.1) → rgba(138, 43, 226, 0.1))
- **Text Input Border**: Light Gray (rgba(0, 0, 0, 0.15))
- **Backgrounds**: Light tint (rgba(0, 0, 0, 0.02-0.05))

---

## 5. Interactive Elements

### Hover Effects:

**Mode Toggle Button:**
```
Inactive → Hover → Active
   ↓         ↓       ↓
 Gray    Light    Neon
         Gray    Green
```

**Reset Button:**
```
Hover Effect:
- Icon rotates -180°
- Lift effect (translateY: -2px)
- Glow shadow increases
```

**Analyze Button:**
```
Hover Effect:
- Lift effect (translateY: -2px)
- Shadow increases
- Gradient intensifies
```

### Focus States:

**Textarea:**
```
Default:
- Border: rgba(0, 255, 136, 0.2)

Focus:
- Border: #00ff88 (neon green)
- Shadow: 0 0 20px rgba(0, 255, 136, 0.2)
- Background darkens slightly
```

**Platform Dropdown:**
```
Focus:
- Border: #00ff88
- Shadow: 0 0 0 3px rgba(0, 255, 136, 0.1)
```

---

## 6. Responsive Breakpoints

### Desktop (> 768px):
- Side-by-side layout
- Full-width toggle with icons
- Larger font sizes
- More padding

### Tablet (≤ 768px):
- Stacked layout begins
- Toggle fills width
- Buttons expand to full width
- Reset button below usage stats

### Mobile Portrait (≤ 480px):
- Compact spacing
- Smaller font sizes
- Textarea height reduced to 200px
- All buttons full width
- Icon sizes reduced

---

## 7. Accessibility Features

✅ **Keyboard Navigation**: All buttons are focusable
✅ **Screen Reader Support**: Semantic HTML with ARIA labels
✅ **Color Contrast**: Meets WCAG AA standards
✅ **Touch Targets**: Minimum 44px for mobile
✅ **Focus Indicators**: Visible focus states
✅ **Error Messages**: Clear validation feedback
✅ **Disabled States**: Visual indication when buttons disabled

---

## 8. Animation Timing

- **Transitions**: 0.3s ease (consistent across all elements)
- **Icon Rotation**: -180° on hover (reset button)
- **Lift Effects**: 2px translateY
- **Focus Glow**: Instant (no transition for better feedback)
- **Spinner**: 0.6s linear infinite

---

## 9. Typography

### ConvoDecoder Text Input:
- **Title**: 1.3rem, weight 600
- **Textarea**: 0.95rem, monospace font (Consolas, Monaco, Courier New)
- **Placeholder**: 0.9rem, lighter color
- **Character Counter**: 1.1rem, weight 600
- **Hints**: 0.8rem
- **Tips**: 0.9rem

### Pricing Reset Button:
- **Button Text**: 0.95rem, weight 600
- **Icon**: 18px × 18px

---

## 10. Platform Support

### Supported Chat Platforms:
1. 🟢 **WhatsApp** (default)
2. 📸 **Instagram**
3. 💬 **Messenger**
4. ✈️ **Telegram**
5. 🎮 **Discord**
6. 📱 **Other**

Each platform can have custom parsing logic in the backend if needed.

---

**Created**: October 14, 2025
**Designer**: Aura AI Team
