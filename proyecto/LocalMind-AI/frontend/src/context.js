/**
 * LocalMind-AI — Context Provider
 * Global state management for the app, integrated with nanobot WebSocket.
 */

import React, { createContext, useContext, useReducer, useCallback, useEffect, useRef } from 'react';
import { nanobotWs, loadSettings, saveSettings, checkHealth, DEFAULTS } from './api';

// ---------------------------------------------------------------------------
// Initial state
// ---------------------------------------------------------------------------
const initialState = {
  messages: [],
  isLoading: false,
  streamingText: '',
  error: null,

  settings: { ...DEFAULTS },

  isConnected: false,
  agentHealthy: false,
};

// ---------------------------------------------------------------------------
// Actions
// ---------------------------------------------------------------------------
const A = {
  ADD_MESSAGE: 'ADD_MESSAGE',
  UPDATE_STREAMING: 'UPDATE_STREAMING',
  COMMIT_STREAMING: 'COMMIT_STREAMING',
  SET_LOADING: 'SET_LOADING',
  SET_ERROR: 'SET_ERROR',
  CLEAR_MESSAGES: 'CLEAR_MESSAGES',
  UPDATE_SETTINGS: 'UPDATE_SETTINGS',
  SET_CONNECTED: 'SET_CONNECTED',
  SET_AGENT_HEALTHY: 'SET_AGENT_HEALTHY',
};

function reducer(state, action) {
  switch (action.type) {
    case A.ADD_MESSAGE:
      return { ...state, messages: [...state.messages, action.payload] };
    case A.UPDATE_STREAMING:
      return { ...state, streamingText: state.streamingText + action.payload };
    case A.COMMIT_STREAMING:
      return {
        ...state,
        messages: [
          ...state.messages,
          { role: 'assistant', content: state.streamingText, timestamp: new Date().toISOString() },
        ],
        streamingText: '',
        isLoading: false,
      };
    case A.SET_LOADING:
      return { ...state, isLoading: action.payload, ...(action.payload ? { streamingText: '' } : {}) };
    case A.SET_ERROR:
      return { ...state, error: action.payload, isLoading: false };
    case A.CLEAR_MESSAGES:
      return { ...state, messages: [], streamingText: '' };
    case A.UPDATE_SETTINGS:
      return { ...state, settings: { ...state.settings, ...action.payload } };
    case A.SET_CONNECTED:
      return { ...state, isConnected: action.payload };
    case A.SET_AGENT_HEALTHY:
      return { ...state, agentHealthy: action.payload };
    default:
      return state;
  }
}

// ---------------------------------------------------------------------------
// Context
// ---------------------------------------------------------------------------
const AppContext = createContext(null);

export function AppProvider({ children }) {
  const [state, dispatch] = useReducer(reducer, initialState);
  const settingsRef = useRef(state.settings);

  // Keep ref in sync
  useEffect(() => { settingsRef.current = state.settings; }, [state.settings]);

  // Load persisted settings on mount
  useEffect(() => {
    (async () => {
      const saved = await loadSettings();
      dispatch({ type: A.UPDATE_SETTINGS, payload: saved });
    })();
  }, []);

  // Connect WebSocket when settings change
  useEffect(() => {
    const { wsUrl } = state.settings;

    nanobotWs.listeners.onReady = () => {
      dispatch({ type: A.SET_CONNECTED, payload: true });
    };
    nanobotWs.listeners.onDelta = (data) => {
      dispatch({ type: A.UPDATE_STREAMING, payload: data.text || '' });
    };
    nanobotWs.listeners.onStreamEnd = () => {
      dispatch({ type: A.COMMIT_STREAMING });
    };
    nanobotWs.listeners.onMessage = (data) => {
      // Non-streaming full message
      dispatch({
        type: A.ADD_MESSAGE,
        payload: {
          role: 'assistant',
          content: data.text,
          buttons: data.buttons || [],
          timestamp: new Date().toISOString()
        },
      });
      dispatch({ type: A.SET_LOADING, payload: false });
    };
    nanobotWs.listeners.onError = (data) => {
      dispatch({ type: A.SET_ERROR, payload: data.detail || 'Connection error' });
    };
    nanobotWs.listeners.onClose = () => {
      dispatch({ type: A.SET_CONNECTED, payload: false });
    };

    nanobotWs.connect(wsUrl);

    return () => nanobotWs.disconnect();
  }, [state.settings.wsUrl]);

  // Periodic health check
  useEffect(() => {
    const check = async () => {
      const ok = await checkHealth(state.settings.apiUrl);
      dispatch({ type: A.SET_AGENT_HEALTHY, payload: ok });
    };
    check();
    const id = setInterval(check, 30000);
    return () => clearInterval(id);
  }, [state.settings.apiUrl]);

  // ---------------------------------------------------------------------------
  // Action creators
  // ---------------------------------------------------------------------------
  const actions = {
    sendMessage: useCallback((text) => {
      dispatch({
        type: A.ADD_MESSAGE,
        payload: { role: 'user', content: text, timestamp: new Date().toISOString() },
      });
      dispatch({ type: A.SET_LOADING, payload: true });
      try {
        nanobotWs.send(text);
      } catch (err) {
        dispatch({ type: A.SET_ERROR, payload: err.message });
      }
    }, []),

    clearMessages: useCallback(() => {
      dispatch({ type: A.CLEAR_MESSAGES });
      nanobotWs.newChat();
    }, []),

    updateSettings: useCallback(async (patch) => {
      dispatch({ type: A.UPDATE_SETTINGS, payload: patch });
      const merged = { ...settingsRef.current, ...patch };
      await saveSettings(merged);
    }, []),

    setError: useCallback((err) => {
      dispatch({ type: A.SET_ERROR, payload: err });
    }, []),

    clearError: useCallback(() => {
      dispatch({ type: A.SET_ERROR, payload: null });
    }, []),
  };

  return (
    <AppContext.Provider value={{ state, actions }}>
      {children}
    </AppContext.Provider>
  );
}

export function useAppContext() {
  const ctx = useContext(AppContext);
  if (!ctx) throw new Error('useAppContext must be used within AppProvider');
  return ctx;
}

export default AppContext;