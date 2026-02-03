import { useState } from 'react';
import { useParams } from 'react-router-dom';
import { motion } from 'framer-motion';
import { 
  Search, 
  Clock, 
  CheckCircle, 
  AlertCircle, 
  Loader2,
  ArrowLeft,
  RefreshCw,
  FileText,
  Building2,
  User,
  Mail
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Badge } from '@/components/ui/badge';
import { requestsApi } from '@/services/backendApi';
import type { RequestStatus, RequestLog } from '@/services/backendApi';

const statusConfig: Record<string, { label: string; color: string; icon: React.ElementType }> = {
  PENDING: { label: 'Aguardando Validação', color: 'bg-yellow-100 text-yellow-800', icon: Clock },
  EMAIL_VERIFIED: { label: 'Email Validado', color: 'bg-blue-100 text-blue-800', icon: CheckCircle },
  IN_ANALYSIS: { label: 'Em Análise', color: 'bg-purple-100 text-purple-800', icon: FileText },
  WAITING_INFO: { label: 'Aguardando Informações', color: 'bg-orange-100 text-orange-800', icon: AlertCircle },
  APPROVED: { label: 'Aprovado', color: 'bg-green-100 text-green-800', icon: CheckCircle },
  REJECTED: { label: 'Rejeitado', color: 'bg-red-100 text-red-800', icon: AlertCircle },
  COMPLETED: { label: 'Concluído', color: 'bg-green-100 text-green-800', icon: CheckCircle },
  CANCELLED: { label: 'Cancelado', color: 'bg-neutral-100 text-neutral-800', icon: AlertCircle },
};

export default function AcompanhamentoPage() {
  const { protocol: urlProtocol } = useParams<{ protocol?: string }>();
  const [protocol, setProtocol] = useState(urlProtocol || '');
  const [request, setRequest] = useState<RequestStatus | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');
  const [searched, setSearched] = useState(false);

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!protocol.trim()) return;

    setIsLoading(true);
    setError('');
    setSearched(true);

    try {
      const response = await requestsApi.getStatus(protocol);
      if (response.success) {
        setRequest(response.data);
      }
    } catch (err: any) {
      setError(err.response?.data?.error || 'Solicitação não encontrada');
      setRequest(null);
    } finally {
      setIsLoading(false);
    }
  };

  const handleRefresh = async () => {
    if (!protocol) return;
    
    setIsLoading(true);
    try {
      const response = await requestsApi.getStatus(protocol);
      if (response.success) {
        setRequest(response.data);
      }
    } catch (err) {
      setError('Erro ao atualizar');
    } finally {
      setIsLoading(false);
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

  return (
    <div className="min-h-screen bg-gradient-to-b from-neutral-50 to-white py-16">
      <div className="container max-w-4xl">
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6 }}
          className="text-center mb-12"
        >
          <div className="inline-flex items-center justify-center w-16 h-16 bg-primary-100 rounded-full mb-4">
            <Search className="w-8 h-8 text-primary-600" />
          </div>
          <h1 className="text-4xl font-bold text-neutral-900 mb-4">
            Acompanhar Solicitação
          </h1>
          <p className="text-lg text-neutral-600">
            Consulte o status da sua solicitação usando o protocolo
          </p>
        </motion.div>

        {/* Search Form */}
        <Card className="mb-8">
          <CardContent className="pt-6">
            <form onSubmit={handleSearch} className="flex gap-4">
              <div className="flex-1">
                <Label htmlFor="protocol" className="sr-only">Protocolo</Label>
                <Input
                  id="protocol"
                  placeholder="Digite o protocolo (ex: REQ-2025-123456)"
                  value={protocol}
                  onChange={(e) => setProtocol(e.target.value)}
                  className="text-lg"
                />
              </div>
              <Button 
                type="submit" 
                disabled={isLoading || !protocol.trim()}
                size="lg"
              >
                {isLoading ? (
                  <Loader2 className="w-5 h-5 animate-spin" />
                ) : (
                  <>
                    <Search className="w-5 h-5 mr-2" />
                    Buscar
                  </>
                )}
              </Button>
            </form>
          </CardContent>
        </Card>

        {error && (
          <Alert variant="destructive" className="mb-6">
            <AlertCircle className="h-4 w-4" />
            <AlertDescription>{error}</AlertDescription>
          </Alert>
        )}

        {/* Results */}
        {request && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5 }}
            className="space-y-6"
          >
            {/* Status Header */}
            <Card className="border-l-4 border-l-primary-500">
              <CardContent className="pt-6">
                <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
                  <div>
                    <p className="text-sm text-neutral-500 mb-1">Protocolo</p>
                    <h2 className="text-2xl font-bold text-neutral-900">{request.protocol}</h2>
                  </div>
                  <div className="flex items-center gap-3">
                    {(() => {
                      const config = statusConfig[request.status] || statusConfig.PENDING;
                      const Icon = config.icon;
                      return (
                        <Badge className={`${config.color} text-sm px-3 py-1`}>
                          <Icon className="w-4 h-4 mr-1" />
                          {config.label}
                        </Badge>
                      );
                    })()}
                    <Button 
                      variant="outline" 
                      size="sm"
                      onClick={handleRefresh}
                      disabled={isLoading}
                    >
                      <RefreshCw className={`w-4 h-4 ${isLoading ? 'animate-spin' : ''}`} />
                    </Button>
                  </div>
                </div>
              </CardContent>
            </Card>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {/* Request Info */}
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2 text-base">
                    <FileText className="w-5 h-5" />
                    Informações da Solicitação
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-3">
                  <div>
                    <p className="text-sm text-neutral-500">Tipo</p>
                    <p className="font-medium">{request.requestType}</p>
                  </div>
                  <div>
                    <p className="text-sm text-neutral-500">Descrição</p>
                    <p className="text-sm">{request.description}</p>
                  </div>
                  <div>
                    <p className="text-sm text-neutral-500">Data de Criação</p>
                    <p className="font-medium">{formatDate(request.createdAt)}</p>
                  </div>
                  <div>
                    <p className="text-sm text-neutral-500">Última Atualização</p>
                    <p className="font-medium">{formatDate(request.updatedAt)}</p>
                  </div>
                </CardContent>
              </Card>

              {/* Requester Info */}
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2 text-base">
                    <User className="w-5 h-5" />
                    Dados do Solicitante
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-3">
                  <div>
                    <p className="text-sm text-neutral-500">Nome</p>
                    <p className="font-medium">{request.requesterName}</p>
                  </div>
                  <div>
                    <p className="text-sm text-neutral-500">Email</p>
                    <div className="flex items-center gap-2">
                      <Mail className="w-4 h-4 text-neutral-400" />
                      <p className="font-medium">{request.requesterEmail}</p>
                    </div>
                  </div>
                  <div>
                    <p className="text-sm text-neutral-500">Email Validado</p>
                    <p className="font-medium">
                      {request.emailVerified ? (
                        <span className="text-green-600 flex items-center gap-1">
                          <CheckCircle className="w-4 h-4" />
                          Sim
                        </span>
                      ) : (
                        <span className="text-yellow-600 flex items-center gap-1">
                          <Clock className="w-4 h-4" />
                          Aguardando
                        </span>
                      )}
                    </p>
                  </div>
                </CardContent>
              </Card>
            </div>

            {/* Establishment Info */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2 text-base">
                  <Building2 className="w-5 h-5" />
                  Estabelecimento
                </CardTitle>
              </CardHeader>
              <CardContent>
                <p className="font-medium text-lg">{request.establishmentName}</p>
              </CardContent>
            </Card>

            {/* Timeline */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2 text-base">
                  <Clock className="w-5 h-5" />
                  Histórico de Atualizações
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {request.logs.map((log: RequestLog, index: number) => {
                    const config = statusConfig[log.status as keyof typeof statusConfig] || statusConfig.PENDING;
                    const Icon = config.icon;
                    const isLast = index === request.logs.length - 1;
                    
                    return (
                      <div key={index} className="flex gap-4">
                        <div className="flex flex-col items-center">
                          <div className={`w-8 h-8 rounded-full flex items-center justify-center ${config.color}`}>
                            <Icon className="w-4 h-4" />
                          </div>
                          {!isLast && (
                            <div className="w-0.5 h-full bg-neutral-200 mt-2" />
                          )}
                        </div>
                        <div className="flex-1 pb-6">
                          <div className="flex items-center gap-2 mb-1">
                            <Badge variant="outline" className={config.color}>
                              {config.label}
                            </Badge>
                            <span className="text-sm text-neutral-500">
                              {formatDate(log.createdAt)}
                            </span>
                          </div>
                          <p className="text-neutral-700">{log.message}</p>
                        </div>
                      </div>
                    );
                  })}
                </div>
              </CardContent>
            </Card>

            <div className="flex justify-center">
              <Button variant="outline" onClick={() => window.history.back()}>
                <ArrowLeft className="w-4 h-4 mr-2" />
                Voltar
              </Button>
            </div>
          </motion.div>
        )}

        {!request && searched && !isLoading && !error && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="text-center py-12"
          >
            <AlertCircle className="w-12 h-12 text-neutral-400 mx-auto mb-4" />
            <p className="text-neutral-600">Nenhuma solicitação encontrada com esse protocolo.</p>
          </motion.div>
        )}
      </div>
    </div>
  );
}
