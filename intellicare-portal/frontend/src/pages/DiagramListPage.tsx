/**
 * DiagramListPage
 * 
 * Página para listar diagramas de um paciente.
 */

import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import excalidrawService, { type DiagramListItem } from '../services/excalidrawService';

export const DiagramListPage: React.FC = () => {
  const { patientId } = useParams<{ patientId: string }>();
  const navigate = useNavigate();
  const [diagrams, setDiagrams] = useState<DiagramListItem[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedCategory, setSelectedCategory] = useState<string>('');

  useEffect(() => {
    if (patientId) {
      loadDiagrams();
    }
  }, [patientId, selectedCategory]);

  const loadDiagrams = async () => {
    if (!patientId) return;

    setIsLoading(true);
    setError(null);

    try {
      const data = await excalidrawService.listPatientDiagrams(
        patientId,
        selectedCategory || undefined
      );
      setDiagrams(data);
    } catch (err) {
      setError('Erro ao carregar diagramas');
      console.error(err);
    } finally {
      setIsLoading(false);
    }
  };

  const handleDelete = async (mediaId: string) => {
    if (!confirm('Tem certeza que deseja deletar este diagrama?')) return;

    try {
      await excalidrawService.deleteDiagram(mediaId);
      loadDiagrams(); // Recarregar lista
    } catch (err) {
      alert('Erro ao deletar diagrama');
      console.error(err);
    }
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('pt-BR', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  const getCategoryLabel = (category: string) => {
    const labels: Record<string, string> = {
      'clinical-diagram': 'Diagrama Clínico',
      'treatment-plan': 'Plano de Tratamento',
      'radiology-annotation': 'Anotação Radiológica',
      'patient-education': 'Educação do Paciente',
      'surgical-planning': 'Planejamento Cirúrgico',
    };
    return labels[category] || category;
  };

  if (!patientId) {
    return (
      <div className="p-8">
        <h1 className="text-2xl font-bold text-red-600">Erro: ID do paciente não fornecido</h1>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 py-6">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold text-gray-900">Diagramas Clínicos</h1>
              <p className="mt-1 text-sm text-gray-500">Paciente: {patientId}</p>
            </div>
            <button
              onClick={() => navigate(`/patients/${patientId}/diagrams/new`)}
              className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 font-medium"
            >
              + Novo Diagrama
            </button>
          </div>

          {/* Filtros */}
          <div className="mt-4 flex items-center gap-4">
            <label className="text-sm font-medium text-gray-700">Filtrar por categoria:</label>
            <select
              value={selectedCategory}
              onChange={(e) => setSelectedCategory(e.target.value)}
              className="px-3 py-2 text-sm border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="">Todas</option>
              <option value="clinical-diagram">Diagrama Clínico</option>
              <option value="treatment-plan">Plano de Tratamento</option>
              <option value="radiology-annotation">Anotação Radiológica</option>
              <option value="patient-education">Educação do Paciente</option>
              <option value="surgical-planning">Planejamento Cirúrgico</option>
            </select>
          </div>
        </div>
      </div>

      {/* Content */}
      <div className="max-w-7xl mx-auto px-4 py-8">
        {isLoading ? (
          <div className="text-center py-12">
            <p className="text-gray-500">Carregando diagramas...</p>
          </div>
        ) : error ? (
          <div className="text-center py-12">
            <p className="text-red-600">{error}</p>
            <button
              onClick={loadDiagrams}
              className="mt-4 px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
            >
              Tentar novamente
            </button>
          </div>
        ) : diagrams.length === 0 ? (
          <div className="text-center py-12">
            <p className="text-gray-500">Nenhum diagrama encontrado</p>
            <button
              onClick={() => navigate(`/patients/${patientId}/diagrams/new`)}
              className="mt-4 px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
            >
              Criar primeiro diagrama
            </button>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {diagrams.map((diagram) => (
              <div
                key={diagram.id}
                className="bg-white rounded-lg shadow-sm border border-gray-200 hover:shadow-md transition-shadow"
              >
                <div className="p-6">
                  <h3 className="text-lg font-semibold text-gray-900 mb-2">{diagram.title}</h3>
                  <p className="text-sm text-gray-600 mb-4">{diagram.description}</p>
                  
                  <div className="space-y-2 text-xs text-gray-500">
                    <div>
                      <span className="font-medium">Categoria:</span>{' '}
                      {getCategoryLabel(diagram.category)}
                    </div>
                    <div>
                      <span className="font-medium">Criado em:</span>{' '}
                      {formatDate(diagram.created)}
                    </div>
                  </div>

                  <div className="mt-4 flex gap-2">
                    <button
                      onClick={() => navigate(`/patients/${patientId}/diagrams/${diagram.id}`)}
                      className="flex-1 px-3 py-2 bg-blue-600 text-white text-sm rounded-md hover:bg-blue-700"
                    >
                      Abrir
                    </button>
                    <button
                      onClick={() => handleDelete(diagram.id)}
                      className="px-3 py-2 bg-red-600 text-white text-sm rounded-md hover:bg-red-700"
                    >
                      Deletar
                    </button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default DiagramListPage;

