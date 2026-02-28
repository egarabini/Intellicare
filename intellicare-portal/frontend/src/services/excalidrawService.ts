/**
 * Excalidraw Service
 * 
 * Serviço para comunicação com a API de diagramas Excalidraw.
 */

import axios from 'axios';
import type { ExcalidrawElement } from '@excalidraw/excalidraw/types/element/types';
import type { AppState } from '@excalidraw/excalidraw/types/types';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8012';
const EXCALIDRAW_API = `${API_BASE_URL}/api/v1/excalidraw`;

// Types
export interface ExcalidrawDiagramData {
  type: 'excalidraw';
  version: number;
  source?: string;
  elements: readonly ExcalidrawElement[];
  appState: Partial<AppState>;
  files?: Record<string, any>;
}

export interface CreateDiagramRequest {
  diagram_data: ExcalidrawDiagramData;
  patient_id: string;
  title: string;
  description?: string;
  category?: string;
  author_id?: string;
}

export interface CreateDiagramResponse {
  media_id: string;
  document_reference_id: string;
  diagram_url: string;
}

export interface DiagramResponse {
  id: string;
  data: ExcalidrawDiagramData;
  title: string;
  created: string;
  patient_id: string;
}

export interface DiagramListItem {
  id: string;
  document_reference_id: string;
  title: string;
  description: string;
  category: string;
  created: string;
  author: string;
}

export interface UpdateDiagramRequest {
  diagram_data: ExcalidrawDiagramData;
  title?: string;
}

/**
 * Excalidraw Service Class
 */
class ExcalidrawService {
  /**
   * Criar um novo diagrama
   */
  async createDiagram(request: CreateDiagramRequest): Promise<CreateDiagramResponse> {
    const response = await axios.post<CreateDiagramResponse>(
      `${EXCALIDRAW_API}/diagrams`,
      request
    );
    return response.data;
  }

  /**
   * Recuperar um diagrama por ID
   */
  async getDiagram(mediaId: string): Promise<DiagramResponse> {
    const response = await axios.get<DiagramResponse>(
      `${EXCALIDRAW_API}/diagrams/${mediaId}`
    );
    return response.data;
  }

  /**
   * Listar diagramas de um paciente
   */
  async listPatientDiagrams(
    patientId: string,
    category?: string
  ): Promise<DiagramListItem[]> {
    const params = category ? { category } : {};
    const response = await axios.get<DiagramListItem[]>(
      `${EXCALIDRAW_API}/patients/${patientId}/diagrams`,
      { params }
    );
    return response.data;
  }

  /**
   * Atualizar um diagrama existente
   */
  async updateDiagram(
    mediaId: string,
    request: UpdateDiagramRequest
  ): Promise<void> {
    await axios.put(
      `${EXCALIDRAW_API}/diagrams/${mediaId}`,
      request
    );
  }

  /**
   * Deletar um diagrama
   */
  async deleteDiagram(mediaId: string): Promise<void> {
    await axios.delete(`${EXCALIDRAW_API}/diagrams/${mediaId}`);
  }

  /**
   * Criar URL do WebSocket para colaboração
   */
  getCollaborationWebSocketUrl(
    roomId: string,
    userId: string,
    userName: string,
    patientId?: string
  ): string {
    const wsBaseUrl = API_BASE_URL.replace('http://', 'ws://').replace('https://', 'wss://');
    const params = new URLSearchParams({
      user_id: userId,
      user_name: userName,
    });
    
    if (patientId) {
      params.append('patient_id', patientId);
    }
    
    return `${wsBaseUrl}/api/v1/excalidraw/collaborate/${roomId}?${params.toString()}`;
  }
}

// Export singleton instance
export const excalidrawService = new ExcalidrawService();
export default excalidrawService;

