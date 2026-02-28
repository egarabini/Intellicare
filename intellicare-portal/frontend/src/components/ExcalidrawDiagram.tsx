/**
 * ExcalidrawDiagram Component
 * 
 * Componente React para criar e editar diagramas Excalidraw integrados com FHIR.
 */

import React, { useState, useEffect, useCallback, useRef } from 'react';
import { Excalidraw, MainMenu, WelcomeScreen } from '@excalidraw/excalidraw';
import type { ExcalidrawImperativeAPI } from '@excalidraw/excalidraw/types/types';
import type { ExcalidrawElement } from '@excalidraw/excalidraw/types/element/types';
import excalidrawService, { type ExcalidrawDiagramData } from '../services/excalidrawService';

export interface ExcalidrawDiagramProps {
  /** ID do diagrama (para edição) */
  diagramId?: string;
  /** ID do paciente */
  patientId: string;
  /** Título do diagrama */
  title?: string;
  /** Categoria do diagrama */
  category?: string;
  /** ID do autor */
  authorId?: string;
  /** Callback quando o diagrama é salvo */
  onSave?: (mediaId: string) => void;
  /** Callback quando ocorre um erro */
  onError?: (error: Error) => void;
  /** Altura do componente */
  height?: string;
}

/**
 * Componente Excalidraw Diagram
 */
export const ExcalidrawDiagram: React.FC<ExcalidrawDiagramProps> = ({
  diagramId,
  patientId,
  title = 'Novo Diagrama',
  category = 'clinical-diagram',
  authorId,
  onSave,
  onError,
  height = '600px',
}) => {
  const [excalidrawAPI, setExcalidrawAPI] = useState<ExcalidrawImperativeAPI | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const saveTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const currentMediaIdRef = useRef<string | undefined>(diagramId);

  // Carregar diagrama existente
  useEffect(() => {
    if (diagramId && excalidrawAPI) {
      loadDiagram(diagramId);
    }
  }, [diagramId, excalidrawAPI]);

  /**
   * Carregar diagrama do backend
   */
  const loadDiagram = async (mediaId: string) => {
    if (!excalidrawAPI) return;

    setIsLoading(true);
    try {
      const diagram = await excalidrawService.getDiagram(mediaId);
      
      // Atualizar cena do Excalidraw
      excalidrawAPI.updateScene({
        elements: diagram.data.elements as ExcalidrawElement[],
        appState: diagram.data.appState,
      });

      currentMediaIdRef.current = mediaId;
    } catch (error) {
      console.error('Erro ao carregar diagrama:', error);
      onError?.(error as Error);
    } finally {
      setIsLoading(false);
    }
  };

  /**
   * Salvar diagrama no backend
   */
  const saveDiagram = useCallback(async () => {
    if (!excalidrawAPI) return;

    setIsSaving(true);
    try {
      const elements = excalidrawAPI.getSceneElements();
      const appState = excalidrawAPI.getAppState();

      const diagramData: ExcalidrawDiagramData = {
        type: 'excalidraw',
        version: 2,
        source: 'https://excalidraw.com',
        elements,
        appState: {
          viewBackgroundColor: appState.viewBackgroundColor,
          gridSize: appState.gridSize,
        },
      };

      if (currentMediaIdRef.current) {
        // Atualizar diagrama existente
        await excalidrawService.updateDiagram(currentMediaIdRef.current, {
          diagram_data: diagramData,
          title,
        });
      } else {
        // Criar novo diagrama
        const response = await excalidrawService.createDiagram({
          diagram_data: diagramData,
          patient_id: patientId,
          title,
          category,
          author_id: authorId,
        });

        currentMediaIdRef.current = response.media_id;
        onSave?.(response.media_id);
      }

      console.log('Diagrama salvo com sucesso');
    } catch (error) {
      console.error('Erro ao salvar diagrama:', error);
      onError?.(error as Error);
    } finally {
      setIsSaving(false);
    }
  }, [excalidrawAPI, patientId, title, category, authorId, onSave, onError]);

  /**
   * Handler de mudanças no diagrama (com debounce)
   */
  const handleChange = useCallback(
    (elements: readonly ExcalidrawElement[]) => {
      // Limpar timeout anterior
      if (saveTimeoutRef.current) {
        clearTimeout(saveTimeoutRef.current);
      }

      // Agendar save após 2 segundos de inatividade
      saveTimeoutRef.current = setTimeout(() => {
        saveDiagram();
      }, 2000);
    },
    [saveDiagram]
  );

  // Cleanup
  useEffect(() => {
    return () => {
      if (saveTimeoutRef.current) {
        clearTimeout(saveTimeoutRef.current);
      }
    };
  }, []);

  return (
    <div style={{ height, width: '100%', position: 'relative' }}>
      {isLoading && (
        <div style={{
          position: 'absolute',
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          backgroundColor: 'rgba(255, 255, 255, 0.9)',
          zIndex: 1000,
        }}>
          <p>Carregando diagrama...</p>
        </div>
      )}

      {isSaving && (
        <div style={{
          position: 'absolute',
          top: 10,
          right: 10,
          padding: '8px 16px',
          backgroundColor: '#4CAF50',
          color: 'white',
          borderRadius: '4px',
          zIndex: 1000,
        }}>
          Salvando...
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

export default ExcalidrawDiagram;

