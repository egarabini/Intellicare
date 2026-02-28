/**
 * CollaborativeExcalidraw Component
 * 
 * Componente Excalidraw com colaboração em tempo real via WebSocket.
 */

import React, { useState, useEffect, useCallback, useRef } from 'react';
import { Excalidraw, MainMenu, WelcomeScreen } from '@excalidraw/excalidraw';
import type { ExcalidrawImperativeAPI } from '@excalidraw/excalidraw/types/types';
import type { ExcalidrawElement } from '@excalidraw/excalidraw/types/element/types';
import excalidrawService from '../services/excalidrawService';

export interface CollaborativeExcalidrawProps {
  /** ID da sala de colaboração */
  roomId: string;
  /** ID do usuário */
  userId: string;
  /** Nome do usuário */
  userName: string;
  /** ID do paciente (opcional) */
  patientId?: string;
  /** Callback quando ocorre um erro */
  onError?: (error: Error) => void;
  /** Altura do componente */
  height?: string;
}

interface WebSocketMessage {
  type: 'room-state' | 'user-joined' | 'user-left' | 'diagram-update' | 'cursor-update';
  users?: Array<{ user_id: string; user_name: string; joined_at: string }>;
  user_id?: string;
  user_name?: string;
  data?: {
    elements: readonly ExcalidrawElement[];
    appState: any;
  };
  cursor?: { x: number; y: number };
  timestamp?: string;
}

/**
 * Componente Collaborative Excalidraw
 */
export const CollaborativeExcalidraw: React.FC<CollaborativeExcalidrawProps> = ({
  roomId,
  userId,
  userName,
  patientId,
  onError,
  height = '600px',
}) => {
  const [excalidrawAPI, setExcalidrawAPI] = useState<ExcalidrawImperativeAPI | null>(null);
  const [isConnected, setIsConnected] = useState(false);
  const [activeUsers, setActiveUsers] = useState<string[]>([]);
  const wsRef = useRef<WebSocket | null>(null);
  const isUpdatingRef = useRef(false);

  /**
   * Conectar ao WebSocket
   */
  useEffect(() => {
    if (!roomId || !userId || !userName) return;

    const wsUrl = excalidrawService.getCollaborationWebSocketUrl(
      roomId,
      userId,
      userName,
      patientId
    );

    console.log('Conectando ao WebSocket:', wsUrl);

    const ws = new WebSocket(wsUrl);

    ws.onopen = () => {
      console.log('WebSocket conectado');
      setIsConnected(true);
    };

    ws.onmessage = (event) => {
      try {
        const message: WebSocketMessage = JSON.parse(event.data);
        handleWebSocketMessage(message);
      } catch (error) {
        console.error('Erro ao processar mensagem WebSocket:', error);
      }
    };

    ws.onerror = (error) => {
      console.error('Erro no WebSocket:', error);
      onError?.(new Error('Erro na conexão WebSocket'));
    };

    ws.onclose = () => {
      console.log('WebSocket desconectado');
      setIsConnected(false);
    };

    wsRef.current = ws;

    return () => {
      ws.close();
    };
  }, [roomId, userId, userName, patientId, onError]);

  /**
   * Handler de mensagens WebSocket
   */
  const handleWebSocketMessage = useCallback(
    (message: WebSocketMessage) => {
      if (!excalidrawAPI) return;

      switch (message.type) {
        case 'room-state':
          // Estado inicial da sala
          if (message.users) {
            setActiveUsers(message.users.map((u) => u.user_name));
          }
          break;

        case 'user-joined':
          // Novo usuário entrou
          if (message.user_name) {
            console.log(`${message.user_name} entrou na sala`);
            setActiveUsers((prev) => [...prev, message.user_name!]);
          }
          break;

        case 'user-left':
          // Usuário saiu
          if (message.user_id) {
            setActiveUsers((prev) => prev.filter((name) => name !== message.user_name));
          }
          break;

        case 'diagram-update':
          // Atualização do diagrama de outro usuário
          if (message.data && !isUpdatingRef.current) {
            isUpdatingRef.current = true;
            excalidrawAPI.updateScene({
              elements: message.data.elements as ExcalidrawElement[],
              appState: message.data.appState,
            });
            setTimeout(() => {
              isUpdatingRef.current = false;
            }, 100);
          }
          break;

        case 'cursor-update':
          // Atualização de cursor (TODO: implementar visualização)
          // console.log('Cursor update:', message.user_id, message.cursor);
          break;
      }
    },
    [excalidrawAPI]
  );

  /**
   * Enviar atualização via WebSocket
   */
  const sendUpdate = useCallback(
    (elements: readonly ExcalidrawElement[], appState: any) => {
      if (!wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) return;
      if (isUpdatingRef.current) return; // Evitar loop

      const message = {
        type: 'diagram-update',
        data: {
          elements,
          appState: {
            viewBackgroundColor: appState.viewBackgroundColor,
            gridSize: appState.gridSize,
          },
        },
      };

      wsRef.current.send(JSON.stringify(message));
    },
    []
  );

  /**
   * Handler de mudanças no diagrama
   */
  const handleChange = useCallback(
    (elements: readonly ExcalidrawElement[]) => {
      if (!excalidrawAPI || isUpdatingRef.current) return;

      const appState = excalidrawAPI.getAppState();
      sendUpdate(elements, appState);
    },
    [excalidrawAPI, sendUpdate]
  );

  return (
    <div style={{ height, width: '100%', position: 'relative' }}>
      {/* Status de conexão */}
      <div
        style={{
          position: 'absolute',
          top: 10,
          left: 10,
          padding: '8px 16px',
          backgroundColor: isConnected ? '#4CAF50' : '#f44336',
          color: 'white',
          borderRadius: '4px',
          zIndex: 1000,
          fontSize: '12px',
        }}
      >
        {isConnected ? '🟢 Conectado' : '🔴 Desconectado'}
      </div>

      {/* Usuários ativos */}
      {activeUsers.length > 0 && (
        <div
          style={{
            position: 'absolute',
            top: 10,
            right: 10,
            padding: '8px 16px',
            backgroundColor: 'rgba(0, 0, 0, 0.7)',
            color: 'white',
            borderRadius: '4px',
            zIndex: 1000,
            fontSize: '12px',
          }}
        >
          👥 {activeUsers.length} usuário(s): {activeUsers.join(', ')}
        </div>
      )}

      <Excalidraw
        excalidrawAPI={(api) => setExcalidrawAPI(api)}
        onChange={handleChange}
      >
        <MainMenu>
          <MainMenu.DefaultItems.ClearCanvas />
          <MainMenu.DefaultItems.SaveAsImage />
          <MainMenu.DefaultItems.ChangeCanvasBackground />
        </MainMenu>
        <WelcomeScreen>
          <WelcomeScreen.Hints.MenuHint />
          <WelcomeScreen.Hints.ToolbarHint />
        </WelcomeScreen>
      </Excalidraw>
    </div>
  );
};

export default CollaborativeExcalidraw;

