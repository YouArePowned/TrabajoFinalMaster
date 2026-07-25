/**
 * LocalMind-AI — Main App Component
 * React Native Expo app with nanobot integration.
 */

import React from 'react';
import { StatusBar } from 'expo-status-bar';
import { NavigationContainer } from '@react-navigation/native';
import { createNativeStackNavigator } from '@react-navigation/native-stack';
import { SafeAreaProvider } from 'react-native-safe-area-context';

import { AppProvider } from './src/context';
import ChatScreen from './screens/ChatScreen';
import SettingsScreen from './screens/SettingsScreen';
import GuideScreen from './screens/GuideScreen';

const Stack = createNativeStackNavigator();

export default function App() {
  return (
    <AppProvider>
      <SafeAreaProvider>
        <NavigationContainer>
          <Stack.Navigator
            initialRouteName="Chat"
            screenOptions={{
              headerShown: false,
              contentStyle: { backgroundColor: '#0f172a' },
              animation: 'slide_from_right',
            }}
          >
            <Stack.Screen name="Chat" component={ChatScreen} />
            <Stack.Screen
              name="Settings"
              component={SettingsScreen}
              options={{
                headerShown: true,
                title: 'Configuración',
                headerStyle: { backgroundColor: '#1e293b' },
                headerTintColor: '#f1f5f9',
                headerTitleStyle: { fontWeight: 'bold' },
              }}
            />
            <Stack.Screen
              name="Guide"
              component={GuideScreen}
              options={{
                headerShown: true,
                title: 'Guía de Despliegue',
                headerStyle: { backgroundColor: '#1e293b' },
                headerTintColor: '#f1f5f9',
                headerTitleStyle: { fontWeight: 'bold' },
              }}
            />
          </Stack.Navigator>
        </NavigationContainer>
        <StatusBar style="light" />
      </SafeAreaProvider>
    </AppProvider>
  );
}