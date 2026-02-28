/**
 * DiagramPage
 * 
 * Página de exemplo para criar e editar diagramas Excalidraw.
 */

import React, { useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import ExcalidrawDiagram from '../components/ExcalidrawDiagram';
import CollaborativeExcalidraw from '../components/CollaborativeExcalidraw';

export const DiagramPage: React.FC = () => {
  const { patientId, diagramId } = useParams<{ patientId: string; diagramId?: string }>();
  const navigate = useNavigate();
  const [mode, setMode] = useState<'single' | 'collaborative'>('single');
  const [title, setTitle] = useState('Novo Diagrama Clínico');
  const [category, setCategory] = useState('clinical-diagram');

  // Mock user data (em produção, viria do contexto de autenticação)
  const currentUser = {
    id: 'user-123',
    name: 'Dr. Silva',
  };

  const handleSave = (mediaId: string) => {
    console.log('Diagrama salvo:', mediaId);
    // Navegar para a lista de diagramas ou mostrar mensagem de sucesso
  };

  const handleError = (error: Error) => {
    console.error('Erro:', error);
    alert(`Erro: ${error.message}`);
  };

  if (!patientId) {
    return (
      <div className="p-8">
        <h1 className="text-2xl font-bold text-red-600">Erro: ID do paciente não fornecido</h1>
      </div>
    );
  }

  return (
    <div className="h-screen flex flex-col">
      {/* Header */}
      <div className="bg-white border-b border-gray-200 p-4">
        <div className="max-w-7xl mx-auto flex items-center justify-between">
          <div className="flex items-center gap-4">
            <button
              onClick={() => navigate(-1)}
              className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50"
            >
              ← Voltar
            </button>
            <h1 className="text-2xl font-bold text-gray-900">
              {diagramId ? 'Editar Diagrama' : 'Novo Diagrama'}
            </h1>
          </div>

          <div className="flex items-center gap-4">
            {/* Modo de colaboração */}
            <div className="flex items-center gap-2">
              <label className="text-sm font-medium text-gray-700">Modo:</label>
              <select
                value={mode}
                onChange={(e) => setMode(e.target.value as 'single' | 'collaborative')}
                className="px-3 py-2 text-sm border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="single">Individual</option>
                <option value="collaborative">Colaborativo</option>
              </select>
            </div>

            {/* Título */}
            <input
              type="text"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder="Título do diagrama"
              className="px-3 py-2 text-sm border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              style={{ width: '300px' }}
            />

            {/* Categoria */}
            <select
              value={category}
              onChange={(e) => setCategory(e.target.value)}
              className="px-3 py-2 text-sm border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="clinical-diagram">Diagrama Clínico</option>
              <option value="treatment-plan">Plano de Tratamento</option>
              <option value="radiology-annotation">Anotação Radiológica</option>
              <option value="patient-education">Educação do Paciente</option>
              <option value="surgical-planning">Planejamento Cirúrgico</option>
            </select>
          </div>
        </div>
      </div>

      {/* Diagrama */}
      <div className="flex-1 bg-gray-50">
        {mode === 'single' ? (
          <ExcalidrawDiagram
            diagramId={diagramId}
            patientId={patientId}
            title={title}
            category={category}
            authorId={currentUser.id}
            onSave={handleSave}
            onError={handleError}
            height="100%"
          />
        ) : (
          <CollaborativeExcalidraw
            roomId={diagramId || `new-${patientId}-${Date.now()}`}
            userId={currentUser.id}
            userName={currentUser.name}
            patientId={patientId}
            onError={handleError}
            height="100%"
          />
        )}
      </div>

      {/* Footer com informações */}
      <div className="bg-white border-t border-gray-200 p-2">
        <div className="max-w-7xl mx-auto flex items-center justify-between text-xs text-gray-500">
          <div>
            Paciente: <span className="font-medium">{patientId}</span>
          </div>
          <div>
            {mode === 'single' ? (
              <span>💾 Salvamento automático ativado</span>
            ) : (
              <span>🔄 Colaboração em tempo real ativada</span>
            )}
          </div>
          <div>
            Categoria: <span className="font-medium">{category}</span>
          </div>
        </div>
      </div>
    </div>
  );
};

export default DiagramPage;

