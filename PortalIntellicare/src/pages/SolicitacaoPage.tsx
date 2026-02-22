import { useState } from 'react';
import { motion } from 'framer-motion';
import { 
  Building2, 
  User, 
  Mail, 
  Phone, 
  FileText, 
  Search, 
  CheckCircle, 
  AlertCircle,
  Loader2,
  Send,
  ArrowRight
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { 
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { cnesApi, requestsApi, type CreateRequestData } from '@/services/api';
import { TokenVerification } from '@/components/TokenVerification';

interface CnesData {
  cnes: string;
  cnpj: string | null;
  razaoSocial: string;
  nomeFantasia: string | null;
  tipoUnidade: string;
  uf: string;
  municipio: string;
  endereco: string | null;
  telefone: string | null;
  recursos: {
    centroCirurgico: boolean;
    centroObstetrico: boolean;
    centroNeonatal: boolean;
    atendimentoHospitalar: boolean;
    servicoApoio: boolean;
    atendimentoAmbulatorial: boolean;
  };
}

export default function SolicitacaoPage() {
  const [step, setStep] = useState(1);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [protocol, setProtocol] = useState('');

  // CNES
  const [cnes, setCnes] = useState('');
  const [cnesData, setCnesData] = useState<CnesData | null>(null);
  const [isValidatingCnes, setIsValidatingCnes] = useState(false);

  // Form data
  const [formData, setFormData] = useState<Partial<CreateRequestData>>({
    requesterName: '',
    requesterEmail: '',
    requesterPhone: '',
    requesterDocument: '',
    requestType: 'ACCESS_REQUEST',
    description: '',
    priority: 'NORMAL',
  });

  // Validate CNES
  const handleValidateCnes = async () => {
    if (!cnes || cnes.length !== 7) {
      setError('CNES deve ter 7 dígitos');
      return;
    }

    setIsValidatingCnes(true);
    setError('');

    try {
      const response = await cnesApi.validate(cnes);
      if (response.success && response.data) {
        setCnesData(response.data);
        setFormData((prev: CreateRequestData) => ({
          ...prev,
          cnes: response.data.cnes,
          cnpj: response.data.cnpj || undefined,
          establishmentName: response.data.razaoSocial,
          establishmentType: response.data.tipoUnidade,
          uf: response.data.uf,
          municipality: response.data.municipio,
          address: response.data.endereco || undefined,
          phone: response.data.telefone || undefined,
        }));
      }
    } catch (err) {
      setError('CNES não encontrado ou inválido');
      setCnesData(null);
    } finally {
      setIsValidatingCnes(false);
    }
  };

  // Submit request
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    setError('');

    try {
      const data: CreateRequestData = {
        ...formData as CreateRequestData,
        cnes: cnesData!.cnes,
        cnpj: cnesData!.cnpj || undefined,
        establishmentName: cnesData!.razaoSocial,
        establishmentType: cnesData!.tipoUnidade,
        uf: cnesData!.uf,
        municipality: cnesData!.municipio,
        address: cnesData!.endereco || undefined,
        phone: cnesData!.telefone || undefined,
      };

      const response = await requestsApi.create(data);
      if (response.success) {
        setProtocol(response.data.protocol);
        setSuccess('Solicitação criada com sucesso!');
        setStep(3);
      }
    } catch (err: any) {
      setError(err.response?.data?.error || 'Erro ao criar solicitação');
    } finally {
      setIsLoading(false);
    }
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
            <Building2 className="w-8 h-8 text-primary-600" />
          </div>
          <h1 className="text-4xl font-bold text-neutral-900 mb-4">
            Solicitação de Acesso
          </h1>
          <p className="text-lg text-neutral-600">
            Preencha os dados abaixo para solicitar acesso à plataforma IntelliCare
          </p>
        </motion.div>

        {/* Progress Steps */}
        <div className="flex items-center justify-center mb-8">
          <div className="flex items-center space-x-4">
            <div className={`flex items-center ${step >= 1 ? 'text-primary-600' : 'text-neutral-400'}`}>
              <div className={`w-8 h-8 rounded-full flex items-center justify-center ${step >= 1 ? 'bg-primary-100' : 'bg-neutral-200'}`}>
                1
              </div>
              <span className="ml-2 text-sm font-medium">CNES</span>
            </div>
            <ArrowRight className="w-4 h-4 text-neutral-400" />
            <div className={`flex items-center ${step >= 2 ? 'text-primary-600' : 'text-neutral-400'}`}>
              <div className={`w-8 h-8 rounded-full flex items-center justify-center ${step >= 2 ? 'bg-primary-100' : 'bg-neutral-200'}`}>
                2
              </div>
              <span className="ml-2 text-sm font-medium">Dados</span>
            </div>
            <ArrowRight className="w-4 h-4 text-neutral-400" />
            <div className={`flex items-center ${step >= 3 ? 'text-primary-600' : 'text-neutral-400'}`}>
              <div className={`w-8 h-8 rounded-full flex items-center justify-center ${step >= 3 ? 'bg-primary-100' : 'bg-neutral-200'}`}>
                3
              </div>
              <span className="ml-2 text-sm font-medium">Validação</span>
            </div>
          </div>
        </div>

        {error && (
          <Alert variant="destructive" className="mb-6">
            <AlertCircle className="h-4 w-4" />
            <AlertDescription>{error}</AlertDescription>
          </Alert>
        )}

        {success && (
          <Alert className="mb-6 bg-green-50 border-green-200">
            <CheckCircle className="h-4 w-4 text-green-600" />
            <AlertDescription className="text-green-800">{success}</AlertDescription>
          </Alert>
        )}

        {/* Step 1: CNES */}
        {step === 1 && (
          <motion.div
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.5 }}
          >
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Search className="w-5 h-5" />
                  Informe o CNES
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-6">
                <div>
                  <Label htmlFor="cnes">Código CNES *</Label>
                  <div className="flex gap-2 mt-1.5">
                    <Input
                      id="cnes"
                      placeholder="0000000"
                      value={cnes}
                      onChange={(e) => setCnes(e.target.value.replace(/\D/g, '').slice(0, 7))}
                      maxLength={7}
                      className="flex-1"
                    />
                    <Button 
                      onClick={handleValidateCnes}
                      disabled={isValidatingCnes || cnes.length !== 7}
                    >
                      {isValidatingCnes ? (
                        <Loader2 className="w-4 h-4 animate-spin" />
                      ) : (
                        <Search className="w-4 h-4" />
                      )}
                      <span className="ml-2">Buscar</span>
                    </Button>
                  </div>
                  <p className="text-sm text-neutral-500 mt-1">
                    Digite os 7 dígitos do CNES do estabelecimento
                  </p>
                </div>

                {cnesData && (
                  <motion.div
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    className="bg-green-50 border border-green-200 rounded-lg p-4"
                  >
                    <div className="flex items-start gap-3">
                      <CheckCircle className="w-5 h-5 text-green-600 mt-0.5" />
                      <div className="flex-1">
                        <h4 className="font-medium text-green-900">Estabelecimento Encontrado</h4>
                        <div className="mt-2 space-y-1 text-sm text-green-800">
                          <p><strong>{cnesData.razaoSocial}</strong></p>
                          <p>CNES: {cnesData.cnes}</p>
                          <p>Tipo: {cnesData.tipoUnidade}</p>
                          <p>Localização: {cnesData.municipio} - {cnesData.uf}</p>
                          {cnesData.endereco && <p>Endereço: {cnesData.endereco}</p>}
                        </div>
                        <Button 
                          className="mt-4" 
                          onClick={() => setStep(2)}
                        >
                          Continuar
                          <ArrowRight className="w-4 h-4 ml-2" />
                        </Button>
                      </div>
                    </div>
                  </motion.div>
                )}
              </CardContent>
            </Card>
          </motion.div>
        )}

        {/* Step 2: Form */}
        {step === 2 && cnesData && (
          <motion.div
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.5 }}
          >
            <form onSubmit={handleSubmit}>
              <div className="space-y-6">
                {/* Establishment Info (Read Only) */}
                <Card>
                  <CardHeader>
                    <CardTitle className="flex items-center gap-2 text-base">
                      <Building2 className="w-5 h-5" />
                      Dados do Estabelecimento
                    </CardTitle>
                  </CardHeader>
                  <CardContent className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div>
                      <Label>CNES</Label>
                      <Input value={cnesData.cnes} disabled className="bg-neutral-100" />
                    </div>
                    <div>
                      <Label>CNPJ</Label>
                      <Input value={cnesData.cnpj || '-'} disabled className="bg-neutral-100" />
                    </div>
                    <div className="md:col-span-2">
                      <Label>Razão Social</Label>
                      <Input value={cnesData.razaoSocial} disabled className="bg-neutral-100" />
                    </div>
                    <div>
                      <Label>Tipo de Unidade</Label>
                      <Input value={cnesData.tipoUnidade} disabled className="bg-neutral-100" />
                    </div>
                    <div>
                      <Label>Município/UF</Label>
                      <Input value={`${cnesData.municipio} - ${cnesData.uf}`} disabled className="bg-neutral-100" />
                    </div>
                    {cnesData.endereco && (
                      <div className="md:col-span-2">
                        <Label>Endereço</Label>
                        <Input value={cnesData.endereco} disabled className="bg-neutral-100" />
                      </div>
                    )}
                    {cnesData.telefone && (
                      <div>
                        <Label>Telefone</Label>
                        <Input value={cnesData.telefone} disabled className="bg-neutral-100" />
                      </div>
                    )}
                  </CardContent>
                </Card>

                {/* Requester Info */}
                <Card>
                  <CardHeader>
                    <CardTitle className="flex items-center gap-2 text-base">
                      <User className="w-5 h-5" />
                      Dados do Solicitante *
                    </CardTitle>
                  </CardHeader>
                  <CardContent className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div className="md:col-span-2">
                      <Label htmlFor="requesterName">Nome Completo *</Label>
                      <Input
                        id="requesterName"
                        value={formData.requesterName}
                        onChange={(e) => setFormData({ ...formData, requesterName: e.target.value })}
                        required
                      />
                    </div>
                    <div>
                      <Label htmlFor="requesterEmail">E-mail *</Label>
                      <div className="flex items-center gap-2">
                        <Mail className="w-4 h-4 text-neutral-400" />
                        <Input
                          id="requesterEmail"
                          type="email"
                          value={formData.requesterEmail}
                          onChange={(e) => setFormData({ ...formData, requesterEmail: e.target.value })}
                          required
                        />
                      </div>
                    </div>
                    <div>
                      <Label htmlFor="requesterPhone">Telefone</Label>
                      <div className="flex items-center gap-2">
                        <Phone className="w-4 h-4 text-neutral-400" />
                        <Input
                          id="requesterPhone"
                          value={formData.requesterPhone}
                          onChange={(e) => setFormData({ ...formData, requesterPhone: e.target.value })}
                        />
                      </div>
                    </div>
                    <div>
                      <Label htmlFor="requesterDocument">CPF/CNPJ</Label>
                      <Input
                        id="requesterDocument"
                        value={formData.requesterDocument}
                        onChange={(e) => setFormData({ ...formData, requesterDocument: e.target.value })}
                      />
                    </div>
                  </CardContent>
                </Card>

                {/* Request Details */}
                <Card>
                  <CardHeader>
                    <CardTitle className="flex items-center gap-2 text-base">
                      <FileText className="w-5 h-5" />
                      Detalhes da Solicitação *
                    </CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      <div>
                        <Label htmlFor="requestType">Tipo de Solicitação *</Label>
                        <Select
                          value={formData.requestType}
                          onValueChange={(value) => setFormData({ ...formData, requestType: value as CreateRequestData['requestType'] })}
                        >
                          <SelectTrigger>
                            <SelectValue />
                          </SelectTrigger>
                          <SelectContent>
                            <SelectItem value="ACCESS_REQUEST">Solicitação de Acesso</SelectItem>
                            <SelectItem value="DATA_CORRECTION">Correção de Dados</SelectItem>
                            <SelectItem value="TECHNICAL_SUPPORT">Suporte Técnico</SelectItem>
                            <SelectItem value="INTEGRATION_REQUEST">Solicitação de Integração</SelectItem>
                            <SelectItem value="OTHER">Outros</SelectItem>
                          </SelectContent>
                        </Select>
                      </div>
                      <div>
                        <Label htmlFor="priority">Prioridade</Label>
                        <Select
                          value={formData.priority}
                          onValueChange={(value) => setFormData({ ...formData, priority: value as CreateRequestData['priority'] })}
                        >
                          <SelectTrigger>
                            <SelectValue />
                          </SelectTrigger>
                          <SelectContent>
                            <SelectItem value="LOW">Baixa</SelectItem>
                            <SelectItem value="NORMAL">Normal</SelectItem>
                            <SelectItem value="HIGH">Alta</SelectItem>
                            <SelectItem value="URGENT">Urgente</SelectItem>
                          </SelectContent>
                        </Select>
                      </div>
                    </div>
                    <div>
                      <Label htmlFor="description">Descrição *</Label>
                      <Textarea
                        id="description"
                        value={formData.description}
                        onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                        placeholder="Descreva detalhadamente sua solicitação..."
                        rows={5}
                        required
                      />
                    </div>
                  </CardContent>
                </Card>

                <div className="flex gap-4">
                  <Button 
                    type="button" 
                    variant="outline" 
                    onClick={() => setStep(1)}
                  >
                    Voltar
                  </Button>
                  <Button 
                    type="submit" 
                    className="flex-1"
                    disabled={isLoading}
                  >
                    {isLoading ? (
                      <>
                        <Loader2 className="w-4 h-4 animate-spin mr-2" />
                        Enviando...
                      </>
                    ) : (
                      <>
                        <Send className="w-4 h-4 mr-2" />
                        Enviar Solicitação
                      </>
                    )}
                  </Button>
                </div>
              </div>
            </form>
          </motion.div>
        )}

        {/* Step 3: Token Verification */}
        {step === 3 && protocol && (
          <motion.div
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.5 }}
          >
            <TokenVerification 
              protocol={protocol} 
              email={formData.requesterEmail || ''}
              onVerified={() => {
                setSuccess('Email validado com sucesso!');
              }}
            />
          </motion.div>
        )}
      </div>
    </div>
  );
}
