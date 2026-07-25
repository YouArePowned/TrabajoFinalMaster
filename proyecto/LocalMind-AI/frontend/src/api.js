/**
 * LocalMind-AI — API / WebSocket Service
 * Communicates with nanobot gateway via WebSocket (streaming)
 * and OpenAI-compatible REST API (fallback & settings).
 */

import AsyncStorage from '@react-native-async-storage/async-storage';

// ---------------------------------------------------------------------------
// Default configuration (overridable from Settings screen)
// ---------------------------------------------------------------------------
const DEFAULTS = {
  wsUrl: 'ws://localhost:8765/ws',
  apiUrl: 'http://localhost:8900',
  ollamaUrl: 'http://localhost:11434',
  model: 'qwen3:4b',
};

// ---------------------------------------------------------------------------
// Settings persistence helpers
// ---------------------------------------------------------------------------
const SETTINGS_KEY = '@localmind_settings';

export async function loadSettings() {
  let localSettings = {};
  try {
    const raw = await AsyncStorage.getItem(SETTINGS_KEY);
    if (raw) localSettings = JSON.parse(raw);
  } catch (e) {
    console.log('[API] Error loading settings from AsyncStorage:', e);
  }

  // Fetch the active config from the backend
  try {
    const response = await fetch(`${DEFAULTS.apiUrl}/localmind/config`, { method: 'GET' });
    if (response.ok) {
      const backendConfig = await response.json();
      const merged = {
        ...DEFAULTS,
        ...localSettings,
        provider: backendConfig.backend_type,
        model: backendConfig.selected_model,
        apiKey: backendConfig.apiKey,
        enableEngram: backendConfig.enable_engram === 1,
        ollamaModels: backendConfig.ollama?.models || [],
        mlxModels: backendConfig.mlx?.models || [],
      };
      // Keep AsyncStorage in sync
      await AsyncStorage.setItem(SETTINGS_KEY, JSON.stringify(merged));
      return merged;
    }
  } catch (e) {
    console.log('[API] Could not fetch active config from backend:', e);
  }

  // Fallback to local settings only
  return {
    ...DEFAULTS,
    provider: 'ollama',
    apiKey: '',
    enableEngram: true,
    ollamaModels: [],
    mlxModels: [],
    ...localSettings,
  };
}

export async function saveSettings(settings) {
  try {
    await AsyncStorage.setItem(SETTINGS_KEY, JSON.stringify(settings));
    
    // Post to the backend
    await fetch(`${settings.apiUrl}/localmind/config`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        backend_type: settings.provider || 'ollama',
        selected_model: settings.model,
        apiKey: settings.apiKey || '',
        enable_engram: settings.enableEngram ? 1 : 0,
      }),
    });
  } catch (e) {
    console.error('[API] Error saving settings to backend:', e);
  }
}

/**
 * Fetch the configuration dynamically from the backend at runtime.
 */
export async function getBackendConfig(apiUrl) {
  try {
    const response = await fetch(`${apiUrl}/localmind/config`);
    if (response.ok) {
      return await response.json();
    }
  } catch (e) {
    console.warn('[API] getBackendConfig failed:', e);
  }
  return null;
}

// ---------------------------------------------------------------------------
// WebSocket Manager — real-time streaming chat via nanobot gateway
// ---------------------------------------------------------------------------
export class NanobotWebSocket {
  constructor() {
    this.ws = null;
    this.chatId = null;
    this.clientId = 'localmind-app';
    this.listeners = {
      onReady: null,
      onMessage: null,
      onDelta: null,
      onStreamEnd: null,
      onError: null,
      onClose: null,
    };
    this._reconnectTimer = null;
    this._wsUrl = DEFAULTS.wsUrl;
  }

  /**
   * Connect to the nanobot WebSocket gateway.
   * @param {string} wsUrl - WebSocket URL
   */
  connect(wsUrl) {
    this._wsUrl = wsUrl || this._wsUrl;
    this.disconnect();

    const url = `${this._wsUrl}?client_id=${this.clientId}&chat_id=default`;
    this.ws = new WebSocket(url);

    this.ws.onopen = () => {
      console.log('[WS] Connected');
      clearTimeout(this._reconnectTimer);
    };

    this.ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        switch (data.event) {
          case 'ready':
            this.chatId = data.chat_id;
            this.listeners.onReady?.(data);
            break;
          case 'message':
            this.listeners.onMessage?.(data);
            break;
          case 'delta':
            this.listeners.onDelta?.(data);
            break;
          case 'stream_end':
            this.listeners.onStreamEnd?.(data);
            break;
          case 'error':
            this.listeners.onError?.(data);
            break;
          default:
            console.log('[WS] Unknown event:', data.event);
        }
      } catch (err) {
        console.error('[WS] Parse error:', err);
      }
    };

    this.ws.onerror = (error) => {
      console.error('[WS] Error:', error.message);
      this.listeners.onError?.({ detail: error.message });
    };

    this.ws.onclose = (event) => {
      console.log('[WS] Closed:', event.code);
      this.listeners.onClose?.(event);
      // Auto-reconnect after 3 seconds
      this._reconnectTimer = setTimeout(() => this.connect(this._wsUrl), 3000);
    };
  }

  /**
   * Send a message on the current chat.
   * @param {string} content - Message text
   */
  send(content) {
    if (!this.ws || this.ws.readyState !== WebSocket.OPEN) {
      throw new Error('WebSocket not connected');
    }
    const payload = this.chatId
      ? { type: 'message', chat_id: this.chatId, content }
      : { content };
    this.ws.send(JSON.stringify(payload));
  }

  /**
   * Create a new chat session.
   */
  newChat() {
    if (this.ws?.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify({ type: 'new_chat' }));
    }
  }

  /** Disconnect and stop reconnection */
  disconnect() {
    clearTimeout(this._reconnectTimer);
    if (this.ws) {
      this.ws.onclose = null; // prevent auto-reconnect
      this.ws.close();
      this.ws = null;
    }
  }

  /** Check if connected */
  get isConnected() {
    return this.ws?.readyState === WebSocket.OPEN;
  }
}

// ---------------------------------------------------------------------------
// REST API — OpenAI-compatible endpoints on nanobot serve
// ---------------------------------------------------------------------------

/**
 * Send a chat message via REST (non-streaming fallback).
 */
export async function sendChatRest(apiUrl, message, sessionId = 'app:default') {
  const response = await fetch(`${apiUrl}/v1/chat/completions`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      messages: [{ role: 'user', content: message }],
      session_id: sessionId,
    }),
  });
  if (!response.ok) throw new Error(`API error: ${response.status}`);
  const data = await response.json();
  return data.choices?.[0]?.message?.content || '';
}

/**
 * Health check.
 */
export async function checkHealth(apiUrl) {
  try {
    const response = await fetch(`${apiUrl}/health`, { timeout: 5000 });
    return response.ok;
  } catch {
    return false;
  }
}

/**
 * Get available models from Ollama.
 */
export async function getOllamaModels(ollamaUrl) {
  try {
    const response = await fetch(`${ollamaUrl}/api/tags`);
    if (!response.ok) return [];
    const data = await response.json();
    return (data.models || []).map((m) => m.name);
  } catch {
    return [];
  }
}

// ---------------------------------------------------------------------------
// Singleton WebSocket instance
// ---------------------------------------------------------------------------
export const nanobotWs = new NanobotWebSocket();

export default {
  nanobotWs,
  sendChatRest,
  checkHealth,
  getOllamaModels,
  getBackendConfig,
  loadSettings,
  saveSettings,
  DEFAULTS,
};