/**
 * LocalMind-AI - Theme Configuration
 * Centralized theme constants
 */

export const theme = {
  // Colors
  colors: {
    // Primary colors
    primary: '#1a1a2e',
    secondary: '#16213e',
    accent: '#0f3460',
    highlight: '#e94560',

    // Background colors
    background: '#0f0f1a',
    surface: '#1a1a2e',
    card: '#16213e',

    // Text colors
    text: {
      primary: '#ffffff',
      secondary: '#a0a0a0',
      muted: '#666666'
    },

    // Status colors
    success: '#4ade80',
    warning: '#fbbf24',
    error: '#ef4444',
    info: '#38bdf8',

    // Chat colors
    userBubble: '#0f3460',
    assistantBubble: '#16213e',
    systemBubble: '#2d2d44'
  },

  // Typography
  typography: {
    fontSizes: {
      xs: 12,
      sm: 14,
      md: 16,
      lg: 18,
      xl: 20,
      xxl: 24
    },
    fontWeights: {
      normal: '400',
      medium: '500',
      semibold: '600',
      bold: '700'
    }
  },

  // Spacing
  spacing: {
    xs: 4,
    sm: 8,
    md: 12,
    lg: 16,
    xl: 20,
    xxl: 24
  },

  // Border radius
  borderRadius: {
    sm: 4,
    md: 8,
    lg: 12,
    xl: 16,
    full: 9999
  },

  // Shadows
  shadows: {
    sm: {
      shadowColor: '#000',
      shadowOffset: { width: 0, height: 1 },
      shadowOpacity: 0.2,
      shadowRadius: 2,
      elevation: 2
    },
    md: {
      shadowColor: '#000',
      shadowOffset: { width: 0, height: 2 },
      shadowOpacity: 0.25,
      shadowRadius: 4,
      elevation: 4
    },
    lg: {
      shadowColor: '#000',
      shadowOffset: { width: 0, height: 4 },
      shadowOpacity: 0.3,
      shadowRadius: 8,
      elevation: 8
    }
  },

  // Animation durations
  animation: {
    fast: 150,
    normal: 300,
    slow: 500
  }
};

export default theme;