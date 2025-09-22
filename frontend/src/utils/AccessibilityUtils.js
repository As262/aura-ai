// Accessibility utilities for AuraAI
class AccessibilityUtils {
  
  // Generate unique IDs for form elements and ARIA relationships
  static generateId(prefix = 'aura') {
    const timestamp = Date.now().toString(36);
    const random = Math.random().toString(36).substr(2, 5);
    return `${prefix}-${timestamp}-${random}`;
  }

  // Create proper ARIA label relationships
  static createAriaRelationship(elementId, type = 'describedby') {
    return {
      id: elementId,
      [`aria-${type}`]: elementId
    };
  }

  // Announce to screen readers
  static announceToScreenReader(message, priority = 'polite') {
    const announcement = document.createElement('div');
    announcement.setAttribute('aria-live', priority);
    announcement.setAttribute('aria-atomic', 'true');
    announcement.className = 'sr-only';
    announcement.textContent = message;
    
    document.body.appendChild(announcement);
    
    // Remove after announcement
    setTimeout(() => {
      document.body.removeChild(announcement);
    }, 1000);
  }

  // Manage focus for SPA navigation
  static manageFocus(targetElement, options = {}) {
    const { 
      skipElement = false, 
      preventScroll = false,
      restoreFocus = true 
    } = options;

    // Store current focus for restoration
    const previousFocus = document.activeElement;

    if (!skipElement && targetElement) {
      // Make element focusable if needed
      if (!targetElement.hasAttribute('tabindex') && 
          !['A', 'BUTTON', 'INPUT', 'SELECT', 'TEXTAREA'].includes(targetElement.tagName)) {
        targetElement.setAttribute('tabindex', '-1');
      }

      // Focus the element
      targetElement.focus({ preventScroll });
    }

    // Return function to restore focus
    return () => {
      if (restoreFocus && previousFocus && document.body.contains(previousFocus)) {
        previousFocus.focus({ preventScroll });
      }
    };
  }

  // Trap focus within a container (for modals, etc.)
  static trapFocus(container, options = {}) {
    const { 
      initialFocus = null,
      returnFocus = true,
      escapeKeyCallback = null 
    } = options;

    const focusableSelectors = [
      'a[href]',
      'button:not([disabled])',
      'input:not([disabled])',
      'select:not([disabled])',
      'textarea:not([disabled])',
      '[tabindex]:not([tabindex="-1"])',
      '[contenteditable="true"]'
    ].join(', ');

    const focusableElements = container.querySelectorAll(focusableSelectors);
    const firstFocusable = focusableElements[0];
    const lastFocusable = focusableElements[focusableElements.length - 1];

    // Store the previously focused element
    const previouslyFocused = document.activeElement;

    // Focus initial element
    if (initialFocus && container.contains(initialFocus)) {
      initialFocus.focus();
    } else if (firstFocusable) {
      firstFocusable.focus();
    }

    const handleKeydown = (e) => {
      if (e.key === 'Tab') {
        if (e.shiftKey) {
          // Shift + Tab
          if (document.activeElement === firstFocusable) {
            e.preventDefault();
            lastFocusable.focus();
          }
        } else {
          // Tab
          if (document.activeElement === lastFocusable) {
            e.preventDefault();
            firstFocusable.focus();
          }
        }
      } else if (e.key === 'Escape' && escapeKeyCallback) {
        escapeKeyCallback();
      }
    };

    document.addEventListener('keydown', handleKeydown);

    // Return cleanup function
    return () => {
      document.removeEventListener('keydown', handleKeydown);
      
      if (returnFocus && previouslyFocused && document.body.contains(previouslyFocused)) {
        previouslyFocused.focus();
      }
    };
  }

  // Check if user prefers reduced motion
  static prefersReducedMotion() {
    return window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  }

  // Check if user prefers high contrast
  static prefersHighContrast() {
    return window.matchMedia('(prefers-contrast: high)').matches;
  }

  // Get color scheme preference
  static getColorSchemePreference() {
    if (window.matchMedia('(prefers-color-scheme: dark)').matches) {
      return 'dark';
    }
    if (window.matchMedia('(prefers-color-scheme: light)').matches) {
      return 'light';
    }
    return 'no-preference';
  }

  // Validate color contrast ratio
  static calculateContrastRatio(color1, color2) {
    // Helper function to convert hex to RGB
    const hexToRgb = (hex) => {
      const result = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(hex);
      return result ? {
        r: parseInt(result[1], 16),
        g: parseInt(result[2], 16),
        b: parseInt(result[3], 16)
      } : null;
    };

    // Helper function to get relative luminance
    const getLuminance = (r, g, b) => {
      const [rs, gs, bs] = [r, g, b].map(c => {
        c = c / 255;
        return c <= 0.03928 ? c / 12.92 : Math.pow((c + 0.055) / 1.055, 2.4);
      });
      return 0.2126 * rs + 0.7152 * gs + 0.0722 * bs;
    };

    const rgb1 = hexToRgb(color1);
    const rgb2 = hexToRgb(color2);

    if (!rgb1 || !rgb2) return 1; // Invalid colors

    const lum1 = getLuminance(rgb1.r, rgb1.g, rgb1.b);
    const lum2 = getLuminance(rgb2.r, rgb2.g, rgb2.b);

    const brightest = Math.max(lum1, lum2);
    const darkest = Math.min(lum1, lum2);

    return (brightest + 0.05) / (darkest + 0.05);
  }

  // Check if contrast ratio meets WCAG standards
  static isContrastRatioCompliant(ratio, level = 'AA', size = 'normal') {
    const standards = {
      'AA': { normal: 4.5, large: 3 },
      'AAA': { normal: 7, large: 4.5 }
    };

    return ratio >= standards[level][size];
  }

  // Keyboard navigation helpers
  static getNavigableElements(container = document) {
    const selector = [
      'a[href]',
      'button:not([disabled])',
      'input:not([disabled])',
      'select:not([disabled])',
      'textarea:not([disabled])',
      '[tabindex]:not([tabindex="-1"])',
      'summary',
      '[contenteditable="true"]'
    ].join(', ');

    return Array.from(container.querySelectorAll(selector));
  }

  // Handle arrow key navigation for custom components
  static handleArrowKeyNavigation(event, elements, currentIndex, options = {}) {
    const { 
      vertical = false, 
      horizontal = true, 
      loop = true,
      callback = null 
    } = options;

    let newIndex = currentIndex;

    switch (event.key) {
      case 'ArrowDown':
        if (vertical) {
          event.preventDefault();
          newIndex = loop && currentIndex === elements.length - 1 ? 0 : Math.min(currentIndex + 1, elements.length - 1);
        }
        break;
      case 'ArrowUp':
        if (vertical) {
          event.preventDefault();
          newIndex = loop && currentIndex === 0 ? elements.length - 1 : Math.max(currentIndex - 1, 0);
        }
        break;
      case 'ArrowRight':
        if (horizontal) {
          event.preventDefault();
          newIndex = loop && currentIndex === elements.length - 1 ? 0 : Math.min(currentIndex + 1, elements.length - 1);
        }
        break;
      case 'ArrowLeft':
        if (horizontal) {
          event.preventDefault();
          newIndex = loop && currentIndex === 0 ? elements.length - 1 : Math.max(currentIndex - 1, 0);
        }
        break;
      case 'Home':
        event.preventDefault();
        newIndex = 0;
        break;
      case 'End':
        event.preventDefault();
        newIndex = elements.length - 1;
        break;
    }

    if (newIndex !== currentIndex && elements[newIndex]) {
      elements[newIndex].focus();
      if (callback) callback(newIndex, elements[newIndex]);
    }

    return newIndex;
  }

  // Screen reader utilities
  static hideFromScreenReader(element) {
    element.setAttribute('aria-hidden', 'true');
  }

  static showToScreenReader(element) {
    element.removeAttribute('aria-hidden');
  }

  // Skip link functionality
  static createSkipLink(targetId, text = 'Skip to main content') {
    const skipLink = document.createElement('a');
    skipLink.href = `#${targetId}`;
    skipLink.textContent = text;
    skipLink.className = 'skip-link';
    
    skipLink.addEventListener('click', (e) => {
      e.preventDefault();
      const target = document.getElementById(targetId);
      if (target) {
        target.focus();
        target.scrollIntoView({ behavior: 'smooth' });
      }
    });

    return skipLink;
  }

  // Live region helpers
  static createLiveRegion(id, priority = 'polite') {
    const region = document.createElement('div');
    region.id = id;
    region.setAttribute('aria-live', priority);
    region.setAttribute('aria-atomic', 'true');
    region.className = 'sr-only';
    document.body.appendChild(region);
    return region;
  }

  static updateLiveRegion(id, message) {
    const region = document.getElementById(id);
    if (region) {
      region.textContent = message;
    }
  }
}

export default AccessibilityUtils;