/**
 * LocalMind-AI — Chat Screen
 * Real-time streaming chat via nanobot WebSocket gateway.
 * Premium UI with collapsible Chain-of-Thought (CoT) accordion.
 */

import React, { useState, useRef, useEffect } from 'react';
import {
  View, Text, TextInput, TouchableOpacity, FlatList,
  StyleSheet, KeyboardAvoidingView, Platform, ActivityIndicator,
} from 'react-native';
import { useAppContext } from '../src/context';

// Helper function to extract thinking / reasoning block
function parseReasoning(content) {
  if (!content) return { reasoning: '', cleanText: '' };
  
  // Match <think>...</think> or unclosed <think>... for streaming
  const thinkRegex = /<think>([\s\S]*?)(<\/think>|$)/i;
  const match = content.match(thinkRegex);
  
  if (match) {
    const reasoning = match[1].trim();
    // Remove the <think>...</think> block from the final text
    const cleanText = content.replace(thinkRegex, '').trim();
    return { reasoning, cleanText };
  }
  
  return { reasoning: '', cleanText: content };
}

function MessageBubble({ message }) {
  const isUser = message.role === 'user';
  const [showThinking, setShowThinking] = useState(false);

  if (isUser) {
    return (
      <View style={[s.bubble, s.bubbleUser]}>
        <Text style={[s.bubbleText, s.bubbleTextUser]}>
          {message.content}
        </Text>
        {message.timestamp && (
          <Text style={s.bubbleTime}>
            {new Date(message.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
          </Text>
        )}
      </View>
    );
  }

  const { reasoning, cleanText } = parseReasoning(message.content);

  return (
    <View style={[s.bubble, s.bubbleAssistant]}>
      <Text style={s.bubbleLabel}>🤖 LocalMind</Text>
      
      {reasoning ? (
        <View style={s.reasoningContainer}>
          <TouchableOpacity style={s.reasoningHeader} onPress={() => setShowThinking(!showThinking)}>
            <Text style={s.reasoningHeaderTitle}>
              {showThinking ? '🧠 Ocultar razonamiento' : '🧠 Mostrar razonamiento'}
            </Text>
            <Text style={s.reasoningHeaderIcon}>{showThinking ? '▲' : '▼'}</Text>
          </TouchableOpacity>
          
          {showThinking && (
            <View style={s.reasoningBody}>
              <Text style={s.reasoningText}>{reasoning}</Text>
            </View>
          )}
        </View>
      ) : null}

      {cleanText ? (
        <Text style={s.bubbleText}>{cleanText}</Text>
      ) : null}

      {message.timestamp && (
        <Text style={s.bubbleTime}>
          {new Date(message.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
        </Text>
      )}
    </View>
  );
}

function StreamingBubble({ text }) {
  if (!text) return null;
  const { reasoning, cleanText } = parseReasoning(text);

  return (
    <View style={[s.bubble, s.bubbleAssistant]}>
      <Text style={s.bubbleLabel}>🤖 LocalMind</Text>
      
      {reasoning ? (
        <View style={s.reasoningContainer}>
          <View style={s.reasoningHeader}>
            <Text style={s.reasoningHeaderTitle}>🧠 Razonando...</Text>
          </View>
          <View style={s.reasoningBody}>
            <Text style={s.reasoningText}>{reasoning}</Text>
          </View>
        </View>
      ) : null}

      {cleanText ? (
        <Text style={s.bubbleText}>{cleanText}</Text>
      ) : null}

      <View style={s.streamingDot} />
    </View>
  );
}

export default function ChatScreen({ navigation }) {
  const { state, actions } = useAppContext();
  const [input, setInput] = useState('');
  const flatListRef = useRef(null);

  const lastMessage = state.messages.length > 0 ? state.messages[state.messages.length - 1] : null;
  const hasButtons = lastMessage && lastMessage.role === 'assistant' && lastMessage.buttons && lastMessage.buttons.length > 0;
  const buttonRows = hasButtons ? lastMessage.buttons : [];

  // Auto-scroll on new messages or streaming
  useEffect(() => {
    if (flatListRef.current && (state.messages.length > 0 || state.streamingText)) {
      setTimeout(() => flatListRef.current?.scrollToEnd({ animated: true }), 100);
    }
  }, [state.messages.length, state.streamingText]);

  const handleSend = () => {
    const text = input.trim();
    if (!text || state.isLoading) return;
    setInput('');
    actions.sendMessage(text);
  };

  const handleNewChat = () => {
    actions.clearMessages();
  };

  // Combine messages + streaming for display
  const renderData = [...state.messages];

  return (
    <KeyboardAvoidingView
      style={s.container}
      behavior={Platform.OS === 'ios' ? 'padding' : undefined}
      keyboardVerticalOffset={90}
    >
      {/* Header bar */}
      <View style={s.header}>
        <View style={s.headerLeft}>
          <View style={[s.dot, { backgroundColor: state.isConnected ? '#4ade80' : '#f87171' }]} />
          <Text style={s.headerTitle}>LocalMind-AI</Text>
        </View>
        <View style={s.headerRight}>
          <TouchableOpacity style={s.headerBtn} onPress={() => navigation.navigate('Guide')}>
            <Text style={s.headerBtnText}>📖</Text>
          </TouchableOpacity>
          <TouchableOpacity style={s.headerBtn} onPress={handleNewChat}>
            <Text style={s.headerBtnText}>🗑️</Text>
          </TouchableOpacity>
          <TouchableOpacity style={s.headerBtn} onPress={() => navigation.navigate('Settings')}>
            <Text style={s.headerBtnText}>⚙️</Text>
          </TouchableOpacity>
        </View>
      </View>

      {/* Messages */}
      <FlatList
        ref={flatListRef}
        data={renderData}
        keyExtractor={(_, i) => String(i)}
        renderItem={({ item }) => <MessageBubble message={item} />}
        contentContainerStyle={s.messageList}
        ListEmptyComponent={
          <View style={s.emptyContainer}>
            <Text style={s.emptyEmoji}>🧠</Text>
            <Text style={s.emptyTitle}>LocalMind-AI</Text>
            <Text style={s.emptySubtitle}>
              Tu asistente personal con CoT-RAG{'\n'}ejecutándose en local
            </Text>
            <Text style={s.emptyHint}>Escribe un mensaje para empezar</Text>
          </View>
        }
        ListFooterComponent={
          state.streamingText ? <StreamingBubble text={state.streamingText} /> : null
        }
      />

      {/* Error banner */}
      {state.error && (
        <TouchableOpacity style={s.errorBanner} onPress={actions.clearError}>
          <Text style={s.errorText}>⚠️ {state.error}</Text>
        </TouchableOpacity>
      )}

      {/* Input bar / Confirmation bar */}
      {hasButtons ? (
        <View style={s.confirmationBar}>
          <Text style={s.confirmationTitle}>Confirmación Requerida:</Text>
          <View style={s.buttonContainer}>
            {buttonRows.map((row, rIdx) => (
              <View key={rIdx} style={s.buttonRow}>
                {row.map((btnText, bIdx) => {
                  let btnStyle = s.confirmBtn;
                  let textStyle = s.confirmBtnText;
                  if (btnText.toLowerCase().includes('rechazar')) {
                    btnStyle = [s.confirmBtn, s.confirmBtnReject];
                  } else if (btnText.toLowerCase().includes('siempre')) {
                    btnStyle = [s.confirmBtn, s.confirmBtnAlways];
                  }
                  
                  return (
                    <TouchableOpacity
                      key={bIdx}
                      style={btnStyle}
                      onPress={() => {
                        actions.sendMessage(btnText);
                      }}
                    >
                      <Text style={textStyle}>{btnText}</Text>
                    </TouchableOpacity>
                  );
                })}
              </View>
            ))}
          </View>
        </View>
      ) : (
        <View style={s.inputBar}>
          <TextInput
            style={s.textInput}
            value={input}
            onChangeText={setInput}
            placeholder="Escribe un mensaje..."
            placeholderTextColor="#64748b"
            multiline
            maxLength={4000}
            onSubmitEditing={handleSend}
            returnKeyType="send"
            blurOnSubmit
          />
          <TouchableOpacity
            style={[s.sendBtn, (!input.trim() || state.isLoading) && s.sendBtnDisabled]}
            onPress={handleSend}
            disabled={!input.trim() || state.isLoading}
          >
            {state.isLoading
              ? <ActivityIndicator color="#fff" size="small" />
              : <Text style={s.sendBtnText}>▶</Text>}
          </TouchableOpacity>
        </View>
      )}
    </KeyboardAvoidingView>
  );
}

const s = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#0f172a' },
  // Header
  header: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', paddingHorizontal: 16, paddingVertical: 12, backgroundColor: '#1e293b', borderBottomWidth: 1, borderBottomColor: '#334155' },
  headerLeft: { flexDirection: 'row', alignItems: 'center', gap: 8 },
  headerTitle: { color: '#f1f5f9', fontSize: 18, fontWeight: 'bold' },
  headerRight: { flexDirection: 'row', gap: 12, alignItems: 'center' },
  headerBtn: { padding: 4 },
  headerBtnText: { fontSize: 20 },
  dot: { width: 8, height: 8, borderRadius: 4 },
  // Messages
  messageList: { padding: 16, paddingBottom: 8 },
  bubble: { maxWidth: '85%', borderRadius: 16, padding: 14, marginBottom: 10 },
  bubbleUser: { backgroundColor: '#3b82f6', alignSelf: 'flex-end', borderBottomRightRadius: 4 },
  bubbleAssistant: { backgroundColor: '#1e293b', alignSelf: 'flex-start', borderBottomLeftRadius: 4, borderWidth: 1, borderColor: '#334155' },
  bubbleLabel: { color: '#94a3b8', fontSize: 11, marginBottom: 4 },
  bubbleText: { color: '#e2e8f0', fontSize: 15, lineHeight: 22 },
  bubbleTextUser: { color: '#ffffff' },
  bubbleTime: { color: '#64748b', fontSize: 10, marginTop: 6, textAlign: 'right' },
  streamingDot: { width: 6, height: 6, borderRadius: 3, backgroundColor: '#3b82f6', marginTop: 6 },
  // Reasoning Block Style
  reasoningContainer: {
    backgroundColor: 'rgba(51, 65, 85, 0.5)',
    borderLeftWidth: 3,
    borderLeftColor: '#3b82f6',
    borderRadius: 8,
    marginBottom: 10,
    overflow: 'hidden',
    borderWidth: 1,
    borderColor: 'rgba(255, 255, 255, 0.05)',
  },
  reasoningHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: 10,
  },
  reasoningHeaderTitle: {
    color: '#38bdf8',
    fontSize: 13,
    fontWeight: 'bold',
  },
  reasoningHeaderIcon: {
    color: '#38bdf8',
    fontSize: 12,
  },
  reasoningBody: {
    paddingHorizontal: 10,
    paddingBottom: 10,
  },
  reasoningText: {
    color: '#94a3b8',
    fontSize: 13,
    lineHeight: 18,
    fontStyle: 'italic',
  },
  // Empty state
  emptyContainer: { flex: 1, alignItems: 'center', justifyContent: 'center', paddingTop: 120 },
  emptyEmoji: { fontSize: 60, marginBottom: 16 },
  emptyTitle: { color: '#f1f5f9', fontSize: 28, fontWeight: 'bold', marginBottom: 8 },
  emptySubtitle: { color: '#94a3b8', fontSize: 15, textAlign: 'center', lineHeight: 22 },
  emptyHint: { color: '#64748b', fontSize: 13, marginTop: 24 },
  // Error
  errorBanner: { backgroundColor: '#7f1d1d', padding: 12, marginHorizontal: 16, borderRadius: 10, marginBottom: 8 },
  errorText: { color: '#fecaca', fontSize: 13 },
  // Input bar
  inputBar: { flexDirection: 'row', alignItems: 'flex-end', padding: 12, paddingBottom: Platform.OS === 'ios' ? 28 : 12, backgroundColor: '#1e293b', borderTopWidth: 1, borderTopColor: '#334155' },
  textInput: { flex: 1, backgroundColor: '#0f172a', color: '#f1f5f9', borderRadius: 20, paddingHorizontal: 16, paddingVertical: 12, fontSize: 15, maxHeight: 100, borderWidth: 1, borderColor: '#334155' },
  sendBtn: { backgroundColor: '#3b82f6', borderRadius: 20, width: 44, height: 44, alignItems: 'center', justifyContent: 'center', marginLeft: 8 },
  sendBtnDisabled: { backgroundColor: '#334155' },
  sendBtnText: { color: '#fff', fontSize: 18 },
  
  // Confirmation bar
  confirmationBar: {
    padding: 16,
    paddingBottom: Platform.OS === 'ios' ? 28 : 16,
    backgroundColor: '#1e293b',
    borderTopWidth: 1,
    borderTopColor: '#334155',
    alignItems: 'stretch',
  },
  confirmationTitle: {
    color: '#94a3b8',
    fontSize: 13,
    fontWeight: 'bold',
    textAlign: 'center',
    marginBottom: 10,
  },
  buttonContainer: {
    flexDirection: 'column',
  },
  buttonRow: {
    flexDirection: 'row',
    justifyContent: 'center',
    gap: 8,
    flexWrap: 'wrap',
  },
  confirmBtn: {
    flex: 1,
    minWidth: 100,
    backgroundColor: '#10b981', // Emerald green
    borderRadius: 20,
    paddingVertical: 12,
    paddingHorizontal: 16,
    alignItems: 'center',
    justifyContent: 'center',
  },
  confirmBtnReject: {
    backgroundColor: '#ef4444', // Red
  },
  confirmBtnAlways: {
    backgroundColor: '#64748b', // Slate
  },
  confirmBtnText: {
    color: '#ffffff',
    fontSize: 14,
    fontWeight: 'bold',
  },
});