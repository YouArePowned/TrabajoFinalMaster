/**
 * LocalMind-AI — Guide / Get Started Screen
 * Beautiful guide on how to install, configure, and use LocalMind-AI.
 */

import React from 'react';
import { View, Text, ScrollView, StyleSheet, TouchableOpacity } from 'react-native';

export default function GuideScreen({ navigation }) {
  return (
    <ScrollView style={s.container} contentContainerStyle={s.content}>
      <Text style={s.title}>📖 Get Started & Guía de Uso</Text>
      <Text style={s.subtitle}>
        Todo lo que necesitas saber para desplegar y usar tu asistente local inteligente.
      </Text>

      {/* Card 1: Qué es LocalMind-AI */}
      <View style={s.card}>
        <Text style={s.cardTitle}>🧠 ¿Qué es LocalMind-AI?</Text>
        <Text style={s.cardText}>
          Es un asistente personal de inteligencia artificial multitarea diseñado para ejecutarse 
          completamente en local sobre tu propio hardware, priorizando la privacidad y la velocidad.
        </Text>
        <Text style={s.cardText}>
          Combina la orquestación avanzada de agentes de <Text style={s.bold}>Nanobot</Text>, la flexibilidad de herramientas <Text style={s.bold}>MCP</Text> (como Engram para memoria a largo plazo) y la aceleración de hardware nativa (usando <Text style={s.bold}>MLX</Text> en macOS y <Text style={s.bold}>Ollama</Text> en Windows/macOS).
        </Text>
      </View>

      {/* Card 2: Arquitectura Híbrida */}
      <View style={s.card}>
        <Text style={s.cardTitle}>⚡ Arquitectura Híbrida (Máximo Rendimiento)</Text>
        <Text style={s.cardText}>
          Para no perder velocidad de inferencia, LocalMind-AI separa las cargas:
        </Text>
        <Text style={s.cardBullet}>• <Text style={s.bold}>LLM en el Host:</Text> El motor (Ollama / MLX) corre nativo en tu sistema operativo principal para acceder al 100% de la GPU (Metal / CUDA).</Text>
        <Text style={s.cardBullet}>• <Text style={s.bold}>Agente en Docker:</Text> Nanobot y las herramientas MCP corren dentro de un contenedor aislado y ligero para facilitar la portabilidad.</Text>
      </View>

      {/* Card 3: Instalación Rápida con CLI */}
      <View style={s.card}>
        <Text style={s.cardTitle}>🚀 Instalación y Despliegue con CLI</Text>
        <Text style={s.cardText}>
          Hemos creado una herramienta CLI interactiva para que no tengas que configurar nada a mano. Abre tu terminal en la raíz del proyecto y ejecuta:
        </Text>
        
        <View style={s.codeBlock}>
          <Text style={s.codeText}># En macOS / Linux:</Text>
          <Text style={s.codeText}>./localmind-cli/install.sh</Text>
          <Text style={s.codeText}></Text>
          <Text style={s.codeText}># En Windows (desde PowerShell):</Text>
          <Text style={s.codeText}>powershell -File localmind-cli\install.ps1</Text>
        </View>

        <Text style={s.cardText}>
          El instalador detectará tus capacidades de hardware, instalará dependencias faltantes 
          (Docker, Node.js, pnpm) mediante gestores como Homebrew o Winget, descargará los modelos 
          seleccionados y configurará los puertos automáticamente.
        </Text>
      </View>

      {/* Card 4: Comandos de Control */}
      <View style={s.card}>
        <Text style={s.cardTitle}>💻 Comandos de Control de la CLI</Text>
        <Text style={s.cardText}>
          Una vez completada la instalación, dispondrás de un ejecutable principal en la raíz para controlar los servicios:
        </Text>
        
        <View style={s.codeBlock}>
          <Text style={s.codeText}>./localmind start   # Enciende el motor LLM y el Agente Docker</Text>
          <Text style={s.codeText}>./localmind stop    # Apaga todos los servicios</Text>
          <Text style={s.codeText}>./localmind status  # Comprueba la salud del sistema</Text>
          <Text style={s.codeText}>./localmind web     # Inicia este frontend en puerto 8081</Text>
          <Text style={s.codeText}>./localmind config  # Lanza de nuevo el configurador TUI</Text>
        </View>
      </View>

      {/* Card 5: Panel de Configuración Web */}
      <View style={s.card}>
        <Text style={s.cardTitle}>⚙️ Configuración Dinámica de la App</Text>
        <Text style={s.cardText}>
          Desde el panel de configuración web (icono de engranaje arriba a la derecha) puedes ajustar los parámetros en caliente:
        </Text>
        <Text style={s.cardBullet}>• Usa <Text style={s.bold}>"Detectar modelos locales del Host"</Text> para traer automáticamente la lista de modelos descargados en tu máquina para Ollama y oMLX.</Text>
        <Text style={s.cardBullet}>• El selector de proveedores te permite cambiar entre Ollama y oMLX de manera dinámica. Los campos y listas de modelos se ajustarán de forma automática.</Text>
        <Text style={s.cardBullet}>• Al hacer clic en <Text style={s.bold}>"Guardar y Aplicar"</Text>, el backend guardará los cambios en los archivos de configuración del host y el contenedor se reiniciará automáticamente para aplicarlos en 3 segundos.</Text>
      </View>

      {/* Card 6: Memoria y MCPs */}
      <View style={s.card}>
        <Text style={s.cardTitle}>💾 Memoria Persistente (Engram)</Text>
        <Text style={s.cardText}>
          LocalMind-AI incorpora soporte para el protocolo MCP. Si activaste la persistencia, 
          el agente utilizará el servidor <Text style={s.bold}>Engram</Text> para retener conceptos u observaciones 
          entre conversaciones. Este almacenamiento persiste en tu host (`~/.localmind/engram/` o `%USERPROFILE%\.localmind\engram\`), por lo que no se pierde al apagar los contenedores Docker.
        </Text>
      </View>

      {/* Botón de volver */}
      <TouchableOpacity style={s.btnBack} onPress={() => navigation.goBack()}>
        <Text style={s.btnBackText}>Volver al Chat</Text>
      </TouchableOpacity>
    </ScrollView>
  );
}

const s = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#0f172a' },
  content: { padding: 20, paddingBottom: 60 },
  title: { fontSize: 26, fontWeight: 'bold', color: '#f1f5f9', marginBottom: 8 },
  subtitle: { fontSize: 15, color: '#94a3b8', lineHeight: 22, marginBottom: 24 },
  bold: { fontWeight: 'bold', color: '#f1f5f9' },
  // Card styling (glassmorphism look)
  card: {
    backgroundColor: '#1e293b',
    borderRadius: 12,
    padding: 18,
    marginBottom: 20,
    borderWidth: 1,
    borderColor: '#334155',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.1,
    shadowRadius: 10,
    elevation: 3,
  },
  cardTitle: { fontSize: 17, fontWeight: 'bold', color: '#3b82f6', marginBottom: 12 },
  cardText: { fontSize: 14, color: '#cbd5e1', lineHeight: 22, marginBottom: 10 },
  cardBullet: { fontSize: 14, color: '#cbd5e1', lineHeight: 22, marginLeft: 10, marginBottom: 6 },
  // Code block
  codeBlock: {
    backgroundColor: '#0f172a',
    borderRadius: 8,
    padding: 12,
    marginVertical: 12,
    borderWidth: 1,
    borderColor: '#1e293b',
  },
  codeText: { fontFamily: 'monospace', color: '#38bdf8', fontSize: 13 },
  // Back button
  btnBack: { backgroundColor: '#3b82f6', borderRadius: 10, padding: 15, alignItems: 'center', marginTop: 10 },
  btnBackText: { color: '#ffffff', fontSize: 16, fontWeight: 'bold' },
});
