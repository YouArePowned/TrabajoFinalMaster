/**
 * LocalMind-AI — Settings Screen
 * Features provider dropdown, auto-detecting host models, and dynamic config overrides.
 */

import React, { useState, useEffect } from 'react';
import {
  View, Text, TextInput, TouchableOpacity, ScrollView,
  StyleSheet, Alert, ActivityIndicator, Switch,
} from 'react-native';
import { useAppContext } from '../src/context';
import { checkHealth, getBackendConfig } from '../src/api';

function CustomDropdown({ label, hint, options, selected, onSelect }) {
  const [open, setOpen] = useState(false);
  return (
    <View style={s.dropdownContainer}>
      <Text style={s.label}>{label}</Text>
      {hint ? <Text style={s.hint}>{hint}</Text> : null}
      <TouchableOpacity style={s.dropdownButton} onPress={() => setOpen(!open)}>
        <Text style={s.dropdownButtonText}>{selected || 'Seleccionar...'}</Text>
        <Text style={s.dropdownButtonIcon}>{open ? '▲' : '▼'}</Text>
      </TouchableOpacity>
      {open && (
        <View style={s.dropdownList}>
          {options.map((opt) => (
            <TouchableOpacity
              key={opt}
              style={[s.dropdownItem, opt === selected && s.dropdownItemActive]}
              onPress={() => {
                onSelect(opt);
                setOpen(false);
              }}
            >
              <Text style={[s.dropdownItemText, opt === selected && s.dropdownItemTextActive]}>
                {opt}
              </Text>
            </TouchableOpacity>
          ))}
        </View>
      )}
    </View>
  );
}

export default function SettingsScreen() {
  const { state, actions } = useAppContext();
  
  // Local form state
  const [form, setForm] = useState({
    provider: state.settings.provider || 'ollama',
    model: state.settings.model || '',
    apiKey: state.settings.apiKey || '',
    enableEngram: state.settings.enableEngram ?? true,
    wsUrl: state.settings.wsUrl || 'ws://localhost:8765/ws',
    apiUrl: state.settings.apiUrl || 'http://localhost:8900',
    ollamaModels: state.settings.ollamaModels || [],
    mlxModels: state.settings.mlxModels || [],
  });

  const [loadingConfig, setLoadingConfig] = useState(false);
  const [testResult, setTestResult] = useState(null);

  // Keep form in sync when global context settings finish loading
  useEffect(() => {
    setForm({
      provider: state.settings.provider || 'ollama',
      model: state.settings.model || '',
      apiKey: state.settings.apiKey || '',
      enableEngram: state.settings.enableEngram ?? true,
      wsUrl: state.settings.wsUrl || 'ws://localhost:8765/ws',
      apiUrl: state.settings.apiUrl || 'http://localhost:8900',
      ollamaModels: state.settings.ollamaModels || [],
      mlxModels: state.settings.mlxModels || [],
    });
  }, [state.settings]);

  // Query backend dynamically to fetch active configuration and downloaded models
  const refreshBackendData = async () => {
    setLoadingConfig(true);
    const data = await getBackendConfig(form.apiUrl);
    setLoadingConfig(false);
    
    if (data) {
      setForm((prev) => ({
        ...prev,
        provider: data.backend_type,
        model: data.selected_model,
        apiKey: data.apiKey,
        enableEngram: data.enable_engram === 1,
        ollamaModels: data.ollama?.models || [],
        mlxModels: data.mlx?.models || [],
      }));
      Alert.alert('Datos cargados', 'Modelos locales detectados y configuración importada.');
    } else {
      Alert.alert('Error', 'No se pudo conectar al servidor de LocalMind en ' + form.apiUrl);
    }
  };

  // Test WebSocket REST gateway connection
  const testConnection = async () => {
    setTestResult('testing');
    const healthy = await checkHealth(form.apiUrl);
    setTestResult(healthy ? 'ok' : 'fail');
    setTimeout(() => setTestResult(null), 3000);
  };

  // Save config
  const save = async () => {
    await actions.updateSettings(form);
    Alert.alert(
      'Configuración guardada',
      'Configuración guardada. El contenedor del agente se reiniciará en 3 segundos para aplicar los cambios.'
    );
  };

  // Determine which model options to present based on provider selection
  const currentModelOptions = form.provider === 'ollama' ? form.ollamaModels : form.mlxModels;

  return (
    <ScrollView style={s.container} contentContainerStyle={s.content}>
      <Text style={s.title}>⚙️ Configuración del Agente</Text>

      {/* Connection Status indicator */}
      <View style={s.statusRow}>
        <View style={[s.statusDot, { backgroundColor: state.isConnected ? '#4ade80' : '#f87171' }]} />
        <Text style={s.statusText}>
          {state.isConnected ? 'Conectado al gateway' : 'Desconectado'}
        </Text>
      </View>

      {/* Refresh backend data */}
      <TouchableOpacity style={s.btnRefresh} onPress={refreshBackendData} disabled={loadingConfig}>
        {loadingConfig ? (
          <ActivityIndicator color="#fff" size="small" />
        ) : (
          <Text style={s.btnRefreshText}>🔄 Detectar modelos locales del Host</Text>
        )}
      </TouchableOpacity>

      {/* Provider Selector */}
      <CustomDropdown
        label="Proveedor del LLM"
        hint="Motor de inferencia que LocalMind usará en el host."
        options={['ollama', 'mlx']}
        selected={form.provider}
        onSelect={(p) => {
          // Adjust model default when switching provider
          const defaultModel = p === 'ollama' 
            ? (form.ollamaModels[0] || 'qwen2.5:7b') 
            : (form.mlxModels[0] || 'mlx-community/Ornith-1.0-9B-6bit');
          setForm({ ...form, provider: p, model: defaultModel });
        }}
      />

      {/* Model Selector */}
      {currentModelOptions.length > 0 ? (
        <CustomDropdown
          label="Modelo"
          hint={`Modelos descargados detectados para ${form.provider.toUpperCase()}:`}
          options={currentModelOptions}
          selected={form.model}
          onSelect={(m) => setForm({ ...form, model: m })}
        />
      ) : (
        <View style={s.customModelBox}>
          <Text style={s.label}>Nombre del Modelo</Text>
          <Text style={s.hint}>No se detectaron modelos descargados. Introduce el nombre manualmente:</Text>
          <TextInput
            style={s.input}
            value={form.model}
            onChangeText={(v) => setForm({ ...form, model: v })}
            placeholder={form.provider === 'ollama' ? 'qwen2.5:7b' : 'mlx-community/Ornith-1.0-9B-6bit'}
            placeholderTextColor="#666"
            autoCapitalize="none"
          />
        </View>
      )}

      {/* oMLX API Key field (only shown for MLX provider) */}
      {form.provider === 'mlx' && (
        <View style={s.apiKeyBox}>
          <Text style={s.label}>API Key de oMLX</Text>
          <Text style={s.hint}>Requerido si tu servidor de oMLX tiene autenticación activa.</Text>
          <TextInput
            style={s.input}
            value={form.apiKey}
            onChangeText={(v) => setForm({ ...form, apiKey: v })}
            placeholder="Introduce tu token o API Key"
            placeholderTextColor="#666"
            secureTextEntry
            autoCapitalize="none"
          />
        </View>
      )}

      {/* Memory (Engram) Switch */}
      <View style={s.switchRow}>
        <View style={s.switchInfo}>
          <Text style={s.switchLabel}>Memoria persistente (Engram)</Text>
          <Text style={s.switchHint}>El agente recordará hechos de sesiones pasadas.</Text>
        </View>
        <Switch
          value={form.enableEngram}
          onValueChange={(v) => setForm({ ...form, enableEngram: v })}
          trackColor={{ false: '#334155', true: '#3b82f6' }}
          thumbColor={form.enableEngram ? '#60a5fa' : '#94a3b8'}
        />
      </View>

      {/* Technical endpoints */}
      <Text style={s.sectionHeader}>Ajustes de Red del Agente</Text>

      <Text style={s.label}>WebSocket Gateway URL</Text>
      <TextInput
        style={s.input}
        value={form.wsUrl}
        onChangeText={(v) => setForm({ ...form, wsUrl: v })}
        placeholder="ws://localhost:8765/ws"
        placeholderTextColor="#666"
        autoCapitalize="none"
      />

      <Text style={s.label}>REST API URL</Text>
      <TextInput
        style={s.input}
        value={form.apiUrl}
        onChangeText={(v) => setForm({ ...form, apiUrl: v })}
        placeholder="http://localhost:8900"
        placeholderTextColor="#666"
        autoCapitalize="none"
      />

      {/* Test Connection Button */}
      <TouchableOpacity style={s.btnTest} onPress={testConnection}>
        <Text style={s.btnTestText}>
          {testResult === 'testing' ? '⏳ Probando conexión...'
            : testResult === 'ok' ? '✅ Conexión con Agente OK'
            : testResult === 'fail' ? '❌ Servidor no responde'
            : '🔌 Probar conexión con Servidor'}
        </Text>
      </TouchableOpacity>

      {/* Save Button */}
      <TouchableOpacity style={s.btnSave} onPress={save}>
        <Text style={s.btnSaveText}>💾 Guardar y Aplicar</Text>
      </TouchableOpacity>

      {/* Info Panel */}
      <View style={s.infoBox}>
        <Text style={s.infoTitle}>ℹ️ Configuración Local del Host</Text>
        <Text style={s.infoText}>
          Asegúrate de que el motor de inferencia (Ollama o oMLX) esté corriendo en el host local. 
          Al guardar, LocalMind regenerará el archivo de configuración y reiniciará el agente de forma automática.
        </Text>
      </View>
    </ScrollView>
  );
}

const s = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#0f172a' },
  content: { padding: 20, paddingBottom: 60 },
  title: { fontSize: 24, fontWeight: 'bold', color: '#f1f5f9', marginBottom: 20 },
  statusRow: { flexDirection: 'row', alignItems: 'center', marginBottom: 20, backgroundColor: '#1e293b', padding: 12, borderRadius: 10 },
  statusDot: { width: 10, height: 10, borderRadius: 5, marginRight: 10 },
  statusText: { color: '#cbd5e1', fontSize: 14 },
  
  label: { color: '#e2e8f0', fontSize: 15, fontWeight: '600', marginTop: 14, marginBottom: 4 },
  hint: { color: '#64748b', fontSize: 12, marginBottom: 8, lineHeight: 16 },
  input: {
    backgroundColor: '#1e293b', color: '#f1f5f9', borderRadius: 10,
    padding: 14, fontSize: 15, borderWidth: 1, borderColor: '#334155',
  },
  sectionHeader: { color: '#94a3b8', fontSize: 16, fontWeight: 'bold', marginTop: 32, marginBottom: 4, borderBottomWidth: 1, borderBottomColor: '#334155', paddingBottom: 6 },
  
  // Custom Dropdown Picker Styling
  dropdownContainer: { marginTop: 14 },
  dropdownButton: {
    flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center',
    backgroundColor: '#1e293b', borderRadius: 10, padding: 14, borderWidth: 1, borderColor: '#334155'
  },
  dropdownButtonText: { color: '#f1f5f9', fontSize: 15 },
  dropdownButtonIcon: { color: '#94a3b8', fontSize: 12 },
  dropdownList: { backgroundColor: '#1e293b', borderRadius: 10, padding: 6, marginTop: 4, borderWidth: 1, borderColor: '#334155' },
  dropdownItem: { paddingVertical: 10, paddingHorizontal: 12, borderRadius: 8, marginVertical: 2 },
  dropdownItemActive: { backgroundColor: '#3b82f6' },
  dropdownItemText: { color: '#cbd5e1', fontSize: 14 },
  dropdownItemTextActive: { color: '#ffffff', fontWeight: '600' },
  
  // Switch
  switchRow: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', backgroundColor: '#1e293b', borderRadius: 12, padding: 16, marginTop: 24, borderWidth: 1, borderColor: '#334155' },
  switchInfo: { flex: 1, marginRight: 8 },
  switchLabel: { color: '#e2e8f0', fontSize: 15, fontWeight: '600', marginBottom: 2 },
  switchHint: { color: '#64748b', fontSize: 12 },
  
  // Buttons
  btnRefresh: { backgroundColor: '#1e293b', borderRadius: 10, padding: 12, alignItems: 'center', justifyContent: 'center', borderDos: 1, borderColor: '#3b82f6', borderStyle: 'dashed', borderWidth: 1 },
  btnRefreshText: { color: '#38bdf8', fontSize: 14, fontWeight: '600' },
  btnTest: { backgroundColor: '#334155', borderRadius: 12, padding: 16, alignItems: 'center', marginTop: 24 },
  btnTestText: { color: '#e2e8f0', fontSize: 15, fontWeight: '600' },
  btnSave: { backgroundColor: '#3b82f6', borderRadius: 12, padding: 16, alignItems: 'center', marginTop: 12 },
  btnSaveText: { color: '#ffffff', fontSize: 16, fontWeight: 'bold' },
  
  infoBox: { backgroundColor: '#1e293b', borderRadius: 12, padding: 16, marginTop: 24, borderWidth: 1, borderColor: '#334155' },
  infoTitle: { color: '#e2e8f0', fontSize: 14, fontWeight: '600', marginBottom: 8 },
  infoText: { color: '#94a3b8', fontSize: 13, lineHeight: 20 },
  apiKeyBox: { marginTop: 4 },
  customModelBox: { marginTop: 4 },
});