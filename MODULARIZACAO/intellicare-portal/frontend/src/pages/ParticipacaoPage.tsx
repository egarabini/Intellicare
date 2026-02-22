import { useState } from 'react';
import { motion } from 'framer-motion';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import {
  Building2,
  Hospital,
  Send,
  CheckCircle2,
  MapPin,
  Users,
  Mail,
  Phone,
  User,
  MessageSquare,
} from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
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
import { Checkbox } from '@/components/ui/checkbox';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { BRAZILIAN_STATES, AGENTS } from '@/types/index';

const secretariatSchema = z.object({
  estado: z.string().min(1, 'Selecione o estado'),
  municipio: z.string().min(2, 'Município deve ter no mínimo 2 caracteres'),
  nomeSecretario: z.string().min(3, 'Nome deve ter no mínimo 3 caracteres'),
  email: z.string().email('E-mail inválido'),
  telefone: z.string().min(14, 'Telefone inválido'),
  cargo: z.string().min(2, 'Cargo deve ter no mínimo 2 caracteres'),
  populacao: z.number().min(1, 'População deve ser maior que 0'),
  unidadesSaude: z.number().min(1, 'Número de unidades deve ser maior que 0'),
  interesseAgentes: z.array(z.string()).min(1, 'Selecione pelo menos um agente'),
  mensagem: z.string().optional(),
  aceitouTermos: z.boolean().refine((val) => val === true, {
    message: 'Você deve aceitar os termos',
  }),
});

const unitSchema = z.object({
  cnes: z.string().length(7, 'CNES deve ter 7 dígitos'),
  nomeUnidade: z.string().min(3, 'Nome deve ter no mínimo 3 caracteres'),
  tipoUnidade: z.string().min(1, 'Selecione o tipo de unidade'),
  estado: z.string().min(1, 'Selecione o estado'),
  municipio: z.string().min(2, 'Município deve ter no mínimo 2 caracteres'),
  nomeResponsavel: z.string().min(3, 'Nome deve ter no mínimo 3 caracteres'),
  email: z.string().email('E-mail inválido'),
  telefone: z.string().min(14, 'Telefone inválido'),
  cargo: z.string().min(2, 'Cargo deve ter no mínimo 2 caracteres'),
  interesseAgentes: z.array(z.string()).min(1, 'Selecione pelo menos um agente'),
  mensagem: z.string().optional(),
  aceitouTermos: z.boolean().refine((val) => val === true, {
    message: 'Você deve aceitar os termos',
  }),
});

type SecretariatFormData = z.infer<typeof secretariatSchema>;
type UnitFormData = z.infer<typeof unitSchema>;

const fadeInUp = {
  initial: { opacity: 0, y: 20 },
  animate: { opacity: 1, y: 0 },
  transition: { duration: 0.5 },
};

const formatPhone = (value: string) => {
  const numbers = value.replace(/\D/g, '');
  if (numbers.length <= 10) {
    return numbers.replace(/(\d{2})(\d{4})(\d{4})/, '($1) $2-$3');
  }
  return numbers.replace(/(\d{2})(\d{5})(\d{4})/, '($1) $2-$3');
};

export default function ParticipacaoPage() {
  const [submitted, setSubmitted] = useState(false);
  const [protocolo, setProtocolo] = useState('');

  const {
    register: registerSecretariat,
    handleSubmit: handleSubmitSecretariat,
    formState: { errors: errorsSecretariat },
    setValue: setValueSecretariat,
    watch: watchSecretariat,
    reset: resetSecretariat,
  } = useForm<SecretariatFormData>({
    resolver: zodResolver(secretariatSchema),
    defaultValues: {
      interesseAgentes: [],
      aceitouTermos: false,
    },
  });

  const {
    register: registerUnit,
    handleSubmit: handleSubmitUnit,
    formState: { errors: errorsUnit },
    setValue: setValueUnit,
    watch: watchUnit,
    reset: resetUnit,
  } = useForm<UnitFormData>({
    resolver: zodResolver(unitSchema),
    defaultValues: {
      interesseAgentes: [],
      aceitouTermos: false,
    },
  });

  const selectedAgentsSecretariat = watchSecretariat('interesseAgentes') || [];
  const selectedAgentsUnit = watchUnit('interesseAgentes') || [];

  const onSubmitSecretariat = (data: SecretariatFormData) => {
    const newProtocolo = `SEC-${Date.now()}`;
    setProtocolo(newProtocolo);
    setSubmitted(true);
    console.log('Secretaria:', data);
  };

  const onSubmitUnit = (data: UnitFormData) => {
    const newProtocolo = `UNI-${Date.now()}`;
    setProtocolo(newProtocolo);
    setSubmitted(true);
    console.log('Unidade:', data);
  };

  const handleReset = () => {
    setSubmitted(false);
    setProtocolo('');
    resetSecretariat();
    resetUnit();
  };

  if (submitted) {
    return (
      <div className="min-h-screen bg-gray-50 py-16">
        <div className="container mx-auto px-4 max-w-2xl">
          <motion.div
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ duration: 0.5 }}
          >
            <Card className="text-center">
              <CardContent className="pt-12 pb-12">
                <CheckCircle2 className="h-20 w-20 text-green-500 mx-auto mb-6" />
                <h2 className="text-3xl font-bold text-gray-900 mb-4">
                  Solicitação Enviada com Sucesso!
                </h2>
                <p className="text-lg text-gray-600 mb-6">
                  Obrigado pelo interesse no INTELLICARE. Sua solicitação foi registrada.
                </p>
                <div className="bg-gray-100 rounded-lg p-6 mb-8">
                  <p className="text-sm text-gray-500 mb-2">Número de Protocolo</p>
                  <p className="text-3xl font-bold text-primary-600">{protocolo}</p>
                </div>
                <p className="text-gray-600 mb-8">
                  Guarde este número para acompanhar o status da sua solicitação.
                  Entraremos em contato em até 5 dias úteis.
                </p>
                <Button onClick={handleReset} size="lg">
                  Nova Solicitação
                </Button>
              </CardContent>
            </Card>
          </motion.div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="bg-gradient-to-r from-primary-600 to-primary-800 py-16">
        <div className="container mx-auto px-4">
          <motion.div {...fadeInUp}>
            <h1 className="text-4xl md:text-5xl font-bold text-white mb-4">
              Solicite sua Participação
            </h1>
            <p className="text-xl text-white/90 max-w-3xl">
              Junte-se à revolução do cuidado em saúde. Preencha o formulário abaixo para
              integrar sua secretaria ou unidade de saúde ao INTELLICARE.
            </p>
          </motion.div>
        </div>
      </div>

      <div className="container mx-auto px-4 -mt-8">
        <motion.div {...fadeInUp} transition={{ delay: 0.1 }}>
          <Tabs defaultValue="secretaria" className="w-full">
            <TabsList className="grid w-full max-w-md mx-auto grid-cols-2 bg-white shadow-lg">
              <TabsTrigger value="secretaria" className="flex items-center gap-2">
                <Building2 className="h-4 w-4" />
                Secretaria de Saúde
              </TabsTrigger>
              <TabsTrigger value="unidade" className="flex items-center gap-2">
                <Hospital className="h-4 w-4" />
                Unidade de Saúde
              </TabsTrigger>
            </TabsList>

            <TabsContent value="secretaria" className="mt-8">
              <Card>
                <CardHeader>
                  <CardTitle className="text-2xl">Solicitação para Secretaria de Saúde</CardTitle>
                </CardHeader>
                <CardContent>
                  <form onSubmit={handleSubmitSecretariat(onSubmitSecretariat)} className="space-y-6">
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                      <div className="space-y-2">
                        <Label htmlFor="estado">
                          <MapPin className="h-4 w-4 inline mr-1" />
                          Estado
                        </Label>
                        <Select
                          onValueChange={(value) => setValueSecretariat('estado', value)}
                        >
                          <SelectTrigger>
                            <SelectValue placeholder="Selecione o estado" />
                          </SelectTrigger>
                          <SelectContent>
                            {BRAZILIAN_STATES.map((state) => (
                              <SelectItem key={state.value} value={state.value}>
                                {state.label}
                              </SelectItem>
                            ))}
                          </SelectContent>
                        </Select>
                        {errorsSecretariat.estado && (
                          <p className="text-sm text-red-500">{errorsSecretariat.estado.message}</p>
                        )}
                      </div>

                      <div className="space-y-2">
                        <Label htmlFor="municipio">Município</Label>
                        <Input
                          id="municipio"
                          {...registerSecretariat('municipio')}
                          placeholder="Nome do município"
                        />
                        {errorsSecretariat.municipio && (
                          <p className="text-sm text-red-500">
                            {errorsSecretariat.municipio.message}
                          </p>
                        )}
                      </div>

                      <div className="space-y-2">
                        <Label htmlFor="nomeSecretario">
                          <User className="h-4 w-4 inline mr-1" />
                          Nome do Secretário
                        </Label>
                        <Input
                          id="nomeSecretario"
                          {...registerSecretariat('nomeSecretario')}
                          placeholder="Nome completo"
                        />
                        {errorsSecretariat.nomeSecretario && (
                          <p className="text-sm text-red-500">
                            {errorsSecretariat.nomeSecretario.message}
                          </p>
                        )}
                      </div>

                      <div className="space-y-2">
                        <Label htmlFor="cargo">Cargo</Label>
                        <Input
                          id="cargo"
                          {...registerSecretariat('cargo')}
                          placeholder="Ex: Secretário Municipal de Saúde"
                        />
                        {errorsSecretariat.cargo && (
                          <p className="text-sm text-red-500">{errorsSecretariat.cargo.message}</p>
                        )}
                      </div>

                      <div className="space-y-2">
                        <Label htmlFor="email">
                          <Mail className="h-4 w-4 inline mr-1" />
                          E-mail
                        </Label>
                        <Input
                          id="email"
                          type="email"
                          {...registerSecretariat('email')}
                          placeholder="email@exemplo.com"
                        />
                        {errorsSecretariat.email && (
                          <p className="text-sm text-red-500">{errorsSecretariat.email.message}</p>
                        )}
                      </div>

                      <div className="space-y-2">
                        <Label htmlFor="telefone">
                          <Phone className="h-4 w-4 inline mr-1" />
                          Telefone
                        </Label>
                        <Input
                          id="telefone"
                          {...registerSecretariat('telefone')}
                          placeholder="(00) 00000-0000"
                          onChange={(e) => {
                            e.target.value = formatPhone(e.target.value);
                          }}
                        />
                        {errorsSecretariat.telefone && (
                          <p className="text-sm text-red-500">
                            {errorsSecretariat.telefone.message}
                          </p>
                        )}
                      </div>

                      <div className="space-y-2">
                        <Label htmlFor="populacao">
                          <Users className="h-4 w-4 inline mr-1" />
                          População Atendida
                        </Label>
                        <Input
                          id="populacao"
                          type="number"
                          {...registerSecretariat('populacao', { valueAsNumber: true })}
                          placeholder="Número de habitantes"
                        />
                        {errorsSecretariat.populacao && (
                          <p className="text-sm text-red-500">
                            {errorsSecretariat.populacao.message}
                          </p>
                        )}
                      </div>

                      <div className="space-y-2">
                        <Label htmlFor="unidadesSaude">
                          <Building2 className="h-4 w-4 inline mr-1" />
                          Número de Unidades de Saúde
                        </Label>
                        <Input
                          id="unidadesSaude"
                          type="number"
                          {...registerSecretariat('unidadesSaude', { valueAsNumber: true })}
                          placeholder="Quantidade de unidades"
                        />
                        {errorsSecretariat.unidadesSaude && (
                          <p className="text-sm text-red-500">
                            {errorsSecretariat.unidadesSaude.message}
                          </p>
                        )}
                      </div>
                    </div>

                    <div className="space-y-3">
                      <Label>Agentes de IA de Interesse</Label>
                      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                        {AGENTS.map((agent) => (
                          <div key={agent.id} className="flex items-start space-x-2">
                            <Checkbox
                              id={`agent-sec-${agent.id}`}
                              checked={selectedAgentsSecretariat.includes(agent.id)}
                              onCheckedChange={(checked) => {
                                const current = selectedAgentsSecretariat;
                                if (checked) {
                                  setValueSecretariat('interesseAgentes', [...current, agent.id]);
                                } else {
                                  setValueSecretariat(
                                    'interesseAgentes',
                                    current.filter((id) => id !== agent.id)
                                  );
                                }
                              }}
                            />
                            <div className="grid gap-1.5 leading-none">
                              <label
                                htmlFor={`agent-sec-${agent.id}`}
                                className="text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70"
                              >
                                {agent.name}
                              </label>
                              <p className="text-xs text-muted-foreground">{agent.role}</p>
                            </div>
                          </div>
                        ))}
                      </div>
                      {errorsSecretariat.interesseAgentes && (
                        <p className="text-sm text-red-500">
                          {errorsSecretariat.interesseAgentes.message}
                        </p>
                      )}
                    </div>

                    <div className="space-y-2">
                      <Label htmlFor="mensagem">
                        <MessageSquare className="h-4 w-4 inline mr-1" />
                        Mensagem Adicional (Opcional)
                      </Label>
                      <Textarea
                        id="mensagem"
                        {...registerSecretariat('mensagem')}
                        placeholder="Conte-nos mais sobre suas necessidades e expectativas..."
                        rows={4}
                      />
                    </div>

                    <div className="flex items-start space-x-2">
                      <Checkbox
                        id="termos-secretaria"
                        checked={watchSecretariat('aceitouTermos')}
                        onCheckedChange={(checked) =>
                          setValueSecretariat('aceitouTermos', checked as boolean)
                        }
                      />
                      <div className="grid gap-1.5 leading-none">
                        <label
                          htmlFor="termos-secretaria"
                          className="text-sm font-medium leading-none"
                        >
                          Aceito os termos de uso e política de privacidade
                        </label>
                        <p className="text-xs text-muted-foreground">
                          Ao enviar, você concorda com o processamento dos dados fornecidos.
                        </p>
                      </div>
                    </div>
                    {errorsSecretariat.aceitouTermos && (
                      <p className="text-sm text-red-500">
                        {errorsSecretariat.aceitouTermos.message}
                      </p>
                    )}

                    <Button type="submit" size="lg" className="w-full md:w-auto">
                      <Send className="h-4 w-4 mr-2" />
                      Enviar Solicitação
                    </Button>
                  </form>
                </CardContent>
              </Card>
            </TabsContent>

            <TabsContent value="unidade" className="mt-8">
              <Card>
                <CardHeader>
                  <CardTitle className="text-2xl">Solicitação para Unidade de Saúde</CardTitle>
                </CardHeader>
                <CardContent>
                  <form onSubmit={handleSubmitUnit(onSubmitUnit)} className="space-y-6">
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                      <div className="space-y-2">
                        <Label htmlFor="cnes">CNES</Label>
                        <Input
                          id="cnes"
                          {...registerUnit('cnes')}
                          placeholder="0000000"
                          maxLength={7}
                        />
                        {errorsUnit.cnes && (
                          <p className="text-sm text-red-500">{errorsUnit.cnes.message}</p>
                        )}
                      </div>

                      <div className="space-y-2">
                        <Label htmlFor="nomeUnidade">Nome da Unidade</Label>
                        <Input
                          id="nomeUnidade"
                          {...registerUnit('nomeUnidade')}
                          placeholder="Nome completo da unidade"
                        />
                        {errorsUnit.nomeUnidade && (
                          <p className="text-sm text-red-500">{errorsUnit.nomeUnidade.message}</p>
                        )}
                      </div>

                      <div className="space-y-2">
                        <Label htmlFor="tipoUnidade">Tipo de Unidade</Label>
                        <Select
                          onValueChange={(value) => setValueUnit('tipoUnidade', value)}
                        >
                          <SelectTrigger>
                            <SelectValue placeholder="Selecione o tipo" />
                          </SelectTrigger>
                          <SelectContent>
                            <SelectItem value="UBS">UBS - Unidade Básica de Saúde</SelectItem>
                            <SelectItem value="ESF">ESF - Estratégia Saúde da Família</SelectItem>
                            <SelectItem value="POLICLINICA">Policlínica</SelectItem>
                            <SelectItem value="HOSPITAL">Hospital</SelectItem>
                            <SelectItem value="OUTRO">Outro</SelectItem>
                          </SelectContent>
                        </Select>
                        {errorsUnit.tipoUnidade && (
                          <p className="text-sm text-red-500">{errorsUnit.tipoUnidade.message}</p>
                        )}
                      </div>

                      <div className="space-y-2">
                        <Label htmlFor="estado-unidade">
                          <MapPin className="h-4 w-4 inline mr-1" />
                          Estado
                        </Label>
                        <Select onValueChange={(value) => setValueUnit('estado', value)}>
                          <SelectTrigger>
                            <SelectValue placeholder="Selecione o estado" />
                          </SelectTrigger>
                          <SelectContent>
                            {BRAZILIAN_STATES.map((state) => (
                              <SelectItem key={state.value} value={state.value}>
                                {state.label}
                              </SelectItem>
                            ))}
                          </SelectContent>
                        </Select>
                        {errorsUnit.estado && (
                          <p className="text-sm text-red-500">{errorsUnit.estado.message}</p>
                        )}
                      </div>

                      <div className="space-y-2">
                        <Label htmlFor="municipio-unidade">Município</Label>
                        <Input
                          id="municipio-unidade"
                          {...registerUnit('municipio')}
                          placeholder="Nome do município"
                        />
                        {errorsUnit.municipio && (
                          <p className="text-sm text-red-500">{errorsUnit.municipio.message}</p>
                        )}
                      </div>

                      <div className="space-y-2">
                        <Label htmlFor="nomeResponsavel">
                          <User className="h-4 w-4 inline mr-1" />
                          Nome do Responsável
                        </Label>
                        <Input
                          id="nomeResponsavel"
                          {...registerUnit('nomeResponsavel')}
                          placeholder="Nome completo"
                        />
                        {errorsUnit.nomeResponsavel && (
                          <p className="text-sm text-red-500">
                            {errorsUnit.nomeResponsavel.message}
                          </p>
                        )}
                      </div>

                      <div className="space-y-2">
                        <Label htmlFor="cargo-unidade">Cargo</Label>
                        <Input
                          id="cargo-unidade"
                          {...registerUnit('cargo')}
                          placeholder="Ex: Diretor da Unidade"
                        />
                        {errorsUnit.cargo && (
                          <p className="text-sm text-red-500">{errorsUnit.cargo.message}</p>
                        )}
                      </div>

                      <div className="space-y-2">
                        <Label htmlFor="email-unidade">
                          <Mail className="h-4 w-4 inline mr-1" />
                          E-mail
                        </Label>
                        <Input
                          id="email-unidade"
                          type="email"
                          {...registerUnit('email')}
                          placeholder="email@exemplo.com"
                        />
                        {errorsUnit.email && (
                          <p className="text-sm text-red-500">{errorsUnit.email.message}</p>
                        )}
                      </div>

                      <div className="space-y-2">
                        <Label htmlFor="telefone-unidade">
                          <Phone className="h-4 w-4 inline mr-1" />
                          Telefone
                        </Label>
                        <Input
                          id="telefone-unidade"
                          {...registerUnit('telefone')}
                          placeholder="(00) 00000-0000"
                          onChange={(e) => {
                            e.target.value = formatPhone(e.target.value);
                          }}
                        />
                        {errorsUnit.telefone && (
                          <p className="text-sm text-red-500">{errorsUnit.telefone.message}</p>
                        )}
                      </div>
                    </div>

                    <div className="space-y-3">
                      <Label>Agentes de IA de Interesse</Label>
                      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                        {AGENTS.map((agent) => (
                          <div key={agent.id} className="flex items-start space-x-2">
                            <Checkbox
                              id={`agent-uni-${agent.id}`}
                              checked={selectedAgentsUnit.includes(agent.id)}
                              onCheckedChange={(checked) => {
                                const current = selectedAgentsUnit;
                                if (checked) {
                                  setValueUnit('interesseAgentes', [...current, agent.id]);
                                } else {
                                  setValueUnit(
                                    'interesseAgentes',
                                    current.filter((id) => id !== agent.id)
                                  );
                                }
                              }}
                            />
                            <div className="grid gap-1.5 leading-none">
                              <label
                                htmlFor={`agent-uni-${agent.id}`}
                                className="text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70"
                              >
                                {agent.name}
                              </label>
                              <p className="text-xs text-muted-foreground">{agent.role}</p>
                            </div>
                          </div>
                        ))}
                      </div>
                      {errorsUnit.interesseAgentes && (
                        <p className="text-sm text-red-500">
                          {errorsUnit.interesseAgentes.message}
                        </p>
                      )}
                    </div>

                    <div className="space-y-2">
                      <Label htmlFor="mensagem-unidade">
                        <MessageSquare className="h-4 w-4 inline mr-1" />
                        Mensagem Adicional (Opcional)
                      </Label>
                      <Textarea
                        id="mensagem-unidade"
                        {...registerUnit('mensagem')}
                        placeholder="Conte-nos mais sobre suas necessidades e expectativas..."
                        rows={4}
                      />
                    </div>

                    <div className="flex items-start space-x-2">
                      <Checkbox
                        id="termos-unidade"
                        checked={watchUnit('aceitouTermos')}
                        onCheckedChange={(checked) =>
                          setValueUnit('aceitouTermos', checked as boolean)
                        }
                      />
                      <div className="grid gap-1.5 leading-none">
                        <label htmlFor="termos-unidade" className="text-sm font-medium leading-none">
                          Aceito os termos de uso e política de privacidade
                        </label>
                        <p className="text-xs text-muted-foreground">
                          Ao enviar, você concorda com o processamento dos dados fornecidos.
                        </p>
                      </div>
                    </div>
                    {errorsUnit.aceitouTermos && (
                      <p className="text-sm text-red-500">{errorsUnit.aceitouTermos.message}</p>
                    )}

                    <Button type="submit" size="lg" className="w-full md:w-auto">
                      <Send className="h-4 w-4 mr-2" />
                      Enviar Solicitação
                    </Button>
                  </form>
                </CardContent>
              </Card>
            </TabsContent>
          </Tabs>
        </motion.div>
      </div>
    </div>
  );
}
