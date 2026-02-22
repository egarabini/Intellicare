import { useState } from 'react';
import { motion } from 'framer-motion';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  LineChart,
  Line,
  PieChart,
  Pie,
  Cell,
  AreaChart,
  Area,
} from 'recharts';
import {
  Activity,
  Users,
  Building2,
  TrendingUp,
  Heart,
  CheckCircle2,
  Clock,
} from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Button } from '@/components/ui/button';

const mockAttendanceData = {
  totalUnidades: 156,
  totalPacientes: 45234,
  totalAtendimentos: 125678,
  taxaAdesao: 87.5,
  distribuicao: [
    { estado: 'SP', unidades: 45, pacientes: 15234, atendimentos: 45678 },
    { estado: 'RJ', unidades: 28, pacientes: 8765, atendimentos: 23456 },
    { estado: 'MG', unidades: 35, pacientes: 9876, atendimentos: 28976 },
    { estado: 'BA', unidades: 22, pacientes: 6543, atendimentos: 18765 },
    { estado: 'RS', unidades: 26, pacientes: 4816, atendimentos: 8803 },
  ],
  evolucaoMensal: [
    { mes: 'Jan', atendimentos: 9800, pacientes: 42000 },
    { mes: 'Fev', atendimentos: 10200, pacientes: 42800 },
    { mes: 'Mar', atendimentos: 10500, pacientes: 43500 },
    { mes: 'Abr', atendimentos: 10800, pacientes: 44100 },
    { mes: 'Mai', atendimentos: 11200, pacientes: 44600 },
    { mes: 'Jun', atendimentos: 11500, pacientes: 45000 },
  ],
};

const mockChronicData = {
  totalPacientesCrônicos: 12345,
  taxaControle: 78.5,
  reducaoInternacoes: 32,
  prevalencia: [
    { name: 'Diabetes', value: 5234, percentual: 42.4 },
    { name: 'Hipertensão', value: 4567, percentual: 37.0 },
    { name: 'Asma', value: 1234, percentual: 10.0 },
    { name: 'Outros', value: 1310, percentual: 10.6 },
  ],
  acompanhamento: [
    { mes: 'Jan', controlados: 8900, naoControlados: 2100 },
    { mes: 'Fev', atendimentos: 9100, naoControlados: 2000 },
    { mes: 'Mar', atendimentos: 9300, naoControlados: 1900 },
    { mes: 'Abr', atendimentos: 9500, naoControlados: 1800 },
    { mes: 'Mai', atendimentos: 9600, naoControlados: 1700 },
    { mes: 'Jun', atendimentos: 9700, naoControlados: 1600 },
  ],
};

const mockQualityData = {
  mediaIndicadores: 85.6,
  unidadesAcimaMeta: 142,
  melhoriaAnual: 12.5,
  indicadores: [
    { nome: 'Acesso', valor: 92, meta: 90 },
    { nome: 'Resolutividade', valor: 87, meta: 85 },
    { nome: 'Satisfação', valor: 89, meta: 85 },
    { nome: 'Segurança', valor: 85, meta: 80 },
    { nome: 'Eficiência', valor: 82, meta: 80 },
  ],
  evolucaoTrimestral: [
    { trimestre: 'T1 2024', geral: 82, acesso: 88, resolutividade: 84 },
    { trimestre: 'T2 2024', geral: 84, acesso: 90, resolutividade: 86 },
    { trimestre: 'T3 2024', geral: 85, acesso: 91, resolutividade: 87 },
    { trimestre: 'T4 2024', geral: 86, acesso: 92, resolutividade: 87 },
  ],
};

const COLORS = ['#0047bd', '#00b88d', '#ff6d00', '#737373'];

const DashboardsPage = () => {
  const [periodoSelecionado, setPeriodoSelecionado] = useState('30d');

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Hero Section */}
      <section className="bg-gradient-to-br from-primary-900 via-primary-800 to-secondary-900 py-20">
        <div className="container mx-auto px-4">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6 }}
            className="text-center max-w-4xl mx-auto"
          >
            <h1 className="text-4xl md:text-5xl font-bold text-white mb-6">
              Dashboards de Saúde
            </h1>
            <p className="text-xl text-neutral-200 mb-8">
              Acompanhe em tempo real os indicadores de saúde pública e o impacto
              dos agentes de IA na rede de atenção
            </p>
            <div className="flex flex-wrap justify-center gap-4">
              {['7d', '30d', '90d'].map((periodo) => (
                <Button
                  key={periodo}
                  variant={periodoSelecionado === periodo ? 'default' : 'outline'}
                  onClick={() => setPeriodoSelecionado(periodo)}
                  className={
                    periodoSelecionado === periodo
                      ? 'bg-white text-primary-700'
                      : 'border-white text-white hover:bg-white/10'
                  }
                >
                  Últimos {periodo === '7d' ? '7 dias' : periodo === '30d' ? '30 dias' : '90 dias'}
                </Button>
              ))}
            </div>
          </motion.div>
        </div>
      </section>

      {/* Dashboard Content */}
      <section className="py-16">
        <div className="container mx-auto px-4">
          <Tabs defaultValue="atendimentos" className="w-full">
            <TabsList className="grid w-full grid-cols-3 mb-8">
              <TabsTrigger value="atendimentos">Atendimentos</TabsTrigger>
              <TabsTrigger value="cronicos">Crônicos</TabsTrigger>
              <TabsTrigger value="qualidade">Qualidade</TabsTrigger>
            </TabsList>

            {/* Atendimentos Tab */}
            <TabsContent value="atendimentos" className="space-y-6">
              {/* KPIs */}
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
                <Card>
                  <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                    <CardTitle className="text-sm font-medium">
                      Unidades Participantes
                    </CardTitle>
                    <Building2 className="h-4 w-4 text-muted-foreground" />
                  </CardHeader>
                  <CardContent>
                    <div className="text-2xl font-bold">
                      {mockAttendanceData.totalUnidades}
                    </div>
                    <p className="text-xs text-muted-foreground">
                      +12% em relação ao mês anterior
                    </p>
                  </CardContent>
                </Card>

                <Card>
                  <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                    <CardTitle className="text-sm font-medium">
                      Pacientes Atendidos
                    </CardTitle>
                    <Users className="h-4 w-4 text-muted-foreground" />
                  </CardHeader>
                  <CardContent>
                    <div className="text-2xl font-bold">
                      {mockAttendanceData.totalPacientes.toLocaleString('pt-BR')}
                    </div>
                    <p className="text-xs text-muted-foreground">
                      +8.5% em relação ao mês anterior
                    </p>
                  </CardContent>
                </Card>

                <Card>
                  <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                    <CardTitle className="text-sm font-medium">
                      Total de Atendimentos
                    </CardTitle>
                    <Activity className="h-4 w-4 text-muted-foreground" />
                  </CardHeader>
                  <CardContent>
                    <div className="text-2xl font-bold">
                      {mockAttendanceData.totalAtendimentos.toLocaleString('pt-BR')}
                    </div>
                    <p className="text-xs text-muted-foreground">
                      +15.3% em relação ao mês anterior
                    </p>
                  </CardContent>
                </Card>

                <Card>
                  <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                    <CardTitle className="text-sm font-medium">
                      Taxa de Adesão
                    </CardTitle>
                    <TrendingUp className="h-4 w-4 text-muted-foreground" />
                  </CardHeader>
                  <CardContent>
                    <div className="text-2xl font-bold">
                      {mockAttendanceData.taxaAdesao}%
                    </div>
                    <p className="text-xs text-muted-foreground">
                      +2.1% em relação ao mês anterior
                    </p>
                  </CardContent>
                </Card>
              </div>

              {/* Charts */}
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                <Card>
                  <CardHeader>
                    <CardTitle>Distribuição por Estado</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <ResponsiveContainer width="100%" height={300}>
                      <BarChart data={mockAttendanceData.distribuicao}>
                        <CartesianGrid strokeDasharray="3 3" />
                        <XAxis dataKey="estado" />
                        <YAxis />
                        <Tooltip />
                        <Bar dataKey="unidades" fill="#0047bd" />
                        <Bar dataKey="pacientes" fill="#00b88d" />
                      </BarChart>
                    </ResponsiveContainer>
                  </CardContent>
                </Card>

                <Card>
                  <CardHeader>
                    <CardTitle>Evolução Mensal</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <ResponsiveContainer width="100%" height={300}>
                      <AreaChart data={mockAttendanceData.evolucaoMensal}>
                        <CartesianGrid strokeDasharray="3 3" />
                        <XAxis dataKey="mes" />
                        <YAxis />
                        <Tooltip />
                        <Area
                          type="monotone"
                          dataKey="atendimentos"
                          stroke="#0047bd"
                          fill="#0047bd"
                          fillOpacity={0.3}
                        />
                        <Area
                          type="monotone"
                          dataKey="pacientes"
                          stroke="#00b88d"
                          fill="#00b88d"
                          fillOpacity={0.3}
                        />
                      </AreaChart>
                    </ResponsiveContainer>
                  </CardContent>
                </Card>
              </div>
            </TabsContent>

            {/* Crônicos Tab */}
            <TabsContent value="cronicos" className="space-y-6">
              {/* KPIs */}
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
                <Card>
                  <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                    <CardTitle className="text-sm font-medium">
                      Pacientes Crônicos
                    </CardTitle>
                    <Heart className="h-4 w-4 text-muted-foreground" />
                  </CardHeader>
                  <CardContent>
                    <div className="text-2xl font-bold">
                      {mockChronicData.totalPacientesCrônicos.toLocaleString('pt-BR')}
                    </div>
                    <p className="text-xs text-muted-foreground">
                      27% dos pacientes atendidos
                    </p>
                  </CardContent>
                </Card>

                <Card>
                  <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                    <CardTitle className="text-sm font-medium">
                      Taxa de Controle
                    </CardTitle>
                    <CheckCircle2 className="h-4 w-4 text-muted-foreground" />
                  </CardHeader>
                  <CardContent>
                    <div className="text-2xl font-bold">
                      {mockChronicData.taxaControle}%
                    </div>
                    <p className="text-xs text-muted-foreground">
                      Meta: 75% | +3.5% vs mês anterior
                    </p>
                  </CardContent>
                </Card>

                <Card>
                  <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                    <CardTitle className="text-sm font-medium">
                      Redução de Internações
                    </CardTitle>
                    <TrendingUp className="h-4 w-4 text-muted-foreground" />
                  </CardHeader>
                  <CardContent>
                    <div className="text-2xl font-bold">
                      {mockChronicData.reducaoInternacoes}%
                    </div>
                    <p className="text-xs text-muted-foreground">
                      Comparado ao ano anterior
                    </p>
                  </CardContent>
                </Card>

                <Card>
                  <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                    <CardTitle className="text-sm font-medium">
                      Tempo Médio de Acompanhamento
                    </CardTitle>
                    <Clock className="h-4 w-4 text-muted-foreground" />
                  </CardHeader>
                  <CardContent>
                    <div className="text-2xl font-bold">4.2 meses</div>
                    <p className="text-xs text-muted-foreground">
                      Aumento de 15% na continuidade
                    </p>
                  </CardContent>
                </Card>
              </div>

              {/* Charts */}
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                <Card>
                  <CardHeader>
                    <CardTitle>Prevalência de Condições</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <ResponsiveContainer width="100%" height={300}>
                      <PieChart>
                        <Pie
                          data={mockChronicData.prevalencia}
                          cx="50%"
                          cy="50%"
                          labelLine={false}
                          label={(entry: any) => `${entry.name}: ${entry.value}`}
                          outerRadius={80}
                          fill="#8884d8"
                          dataKey="value"
                        >
                          {mockChronicData.prevalencia.map((_entry, index) => (
                            <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                          ))}
                        </Pie>
                        <Tooltip />
                      </PieChart>
                    </ResponsiveContainer>
                  </CardContent>
                </Card>

                <Card>
                  <CardHeader>
                    <CardTitle>Acompanhamento Mensal</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <ResponsiveContainer width="100%" height={300}>
                      <LineChart data={mockChronicData.acompanhamento}>
                        <CartesianGrid strokeDasharray="3 3" />
                        <XAxis dataKey="mes" />
                        <YAxis />
                        <Tooltip />
                        <Line
                          type="monotone"
                          dataKey="controlados"
                          stroke="#0047bd"
                          strokeWidth={2}
                        />
                        <Line
                          type="monotone"
                          dataKey="naoControlados"
                          stroke="#ff6d00"
                          strokeWidth={2}
                        />
                      </LineChart>
                    </ResponsiveContainer>
                  </CardContent>
                </Card>
              </div>
            </TabsContent>

            {/* Qualidade Tab */}
            <TabsContent value="qualidade" className="space-y-6">
              {/* KPIs */}
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
                <Card>
                  <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                    <CardTitle className="text-sm font-medium">
                      Média de Indicadores
                    </CardTitle>
                    <CheckCircle2 className="h-4 w-4 text-muted-foreground" />
                  </CardHeader>
                  <CardContent>
                    <div className="text-2xl font-bold">
                      {mockQualityData.mediaIndicadores}%
                    </div>
                    <p className="text-xs text-muted-foreground">
                      Meta geral: 85%
                    </p>
                  </CardContent>
                </Card>

                <Card>
                  <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                    <CardTitle className="text-sm font-medium">
                      Unidades Acima da Meta
                    </CardTitle>
                    <Building2 className="h-4 w-4 text-muted-foreground" />
                  </CardHeader>
                  <CardContent>
                    <div className="text-2xl font-bold">
                      {mockQualityData.unidadesAcimaMeta}
                    </div>
                    <p className="text-xs text-muted-foreground">
                      91% das unidades participantes
                    </p>
                  </CardContent>
                </Card>

                <Card>
                  <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                    <CardTitle className="text-sm font-medium">
                      Melhoria Anual
                    </CardTitle>
                    <TrendingUp className="h-4 w-4 text-muted-foreground" />
                  </CardHeader>
                  <CardContent>
                    <div className="text-2xl font-bold">
                      +{mockQualityData.melhoriaAnual}%
                    </div>
                    <p className="text-xs text-muted-foreground">
                      Comparado ao ano anterior
                    </p>
                  </CardContent>
                </Card>

                <Card>
                  <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                    <CardTitle className="text-sm font-medium">
                      Satisfação do Usuário
                    </CardTitle>
                    <Users className="h-4 w-4 text-muted-foreground" />
                  </CardHeader>
                  <CardContent>
                    <div className="text-2xl font-bold">89%</div>
                    <p className="text-xs text-muted-foreground">
                      Baseado em 45.234 respostas
                    </p>
                  </CardContent>
                </Card>
              </div>

              {/* Charts */}
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                <Card>
                  <CardHeader>
                    <CardTitle>Indicadores por Categoria</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <ResponsiveContainer width="100%" height={300}>
                      <BarChart data={mockQualityData.indicadores} layout="vertical">
                        <CartesianGrid strokeDasharray="3 3" />
                        <XAxis type="number" domain={[0, 100]} />
                        <YAxis dataKey="nome" type="category" width={100} />
                        <Tooltip />
                        <Bar dataKey="valor" fill="#0047bd" name="Valor" />
                        <Bar dataKey="meta" fill="#00b88d" name="Meta" />
                      </BarChart>
                    </ResponsiveContainer>
                  </CardContent>
                </Card>

                <Card>
                  <CardHeader>
                    <CardTitle>Evolução Trimestral</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <ResponsiveContainer width="100%" height={300}>
                      <LineChart data={mockQualityData.evolucaoTrimestral}>
                        <CartesianGrid strokeDasharray="3 3" />
                        <XAxis dataKey="trimestre" />
                        <YAxis domain={[70, 100]} />
                        <Tooltip />
                        <Line
                          type="monotone"
                          dataKey="geral"
                          stroke="#0047bd"
                          strokeWidth={3}
                          name="Geral"
                        />
                        <Line
                          type="monotone"
                          dataKey="acesso"
                          stroke="#00b88d"
                          strokeWidth={2}
                          name="Acesso"
                        />
                        <Line
                          type="monotone"
                          dataKey="resolutividade"
                          stroke="#ff6d00"
                          strokeWidth={2}
                          name="Resolutividade"
                        />
                      </LineChart>
                    </ResponsiveContainer>
                  </CardContent>
                </Card>
              </div>
            </TabsContent>
          </Tabs>
        </div>
      </section>
    </div>
  );
};

export default DashboardsPage;
