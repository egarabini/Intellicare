export interface SolicitacaoSecretaria {
  id?: string;
  estado: string;
  municipio: string;
  nomeSecretario: string;
  email: string;
  telefone: string;
  cargo: string;
  populacao: number;
  unidadesSaude: number;
  interesseAgentes: string[];
  mensagem?: string;
  status: 'pendente' | 'em_analise' | 'aprovado' | 'rejeitado';
  createdAt: Date;
  updatedAt: Date;
}

export interface SolicitacaoUnidade {
  id?: string;
  cnes: string;
  nomeUnidade: string;
  tipoUnidade: string;
  estado: string;
  municipio: string;
  nomeResponsavel: string;
  email: string;
  telefone: string;
  cargo: string;
  interesseAgentes: string[];
  mensagem?: string;
  status: 'pendente' | 'em_analise' | 'aprovado' | 'rejeitado';
  createdAt: Date;
  updatedAt: Date;
}

export interface MensagemContato {
  id?: string;
  nome: string;
  email: string;
  telefone?: string;
  assunto: string;
  mensagem: string;
  status: 'pendente' | 'respondido';
  createdAt: Date;
}

export interface UseCase {
  title: string;
  description: string;
}

export interface Agent {
  id: string;
  name: string;
  slug: string;
  description: string;
  role?: string;
  icon: string;
  color: string;
  category: string;
  features: string[];
  benefits: string[];
  useCases: UseCase[];
  dataSources: string[];
  technologies: string[];
  status: 'disponivel' | 'em_desenvolvimento' | 'planejado';
  imageUrl?: string;
  externalLink?: string;
  externalLinkLabel?: string;
}

export interface UseCaseExample {
  id: string;
  title: string;
  description: string;
  agent: string;
  results: {
    metric: string;
    value: string;
    improvement: string;
  }[];
  testimonial?: {
    author: string;
    role: string;
    location: string;
    quote: string;
  };
}

export interface DashboardData {
  totalUnidades: number;
  totalPacientes: number;
  totalAtendimentos: number;
  taxaAdesao: number;
  distribuicao: DistribuicaoItem[];
  topUnidades: TopUnidadeItem[];
  evolucaoMensal: {
    mes: string;
    atendimentos: number;
    pacientes: number;
  }[];
}

export interface DistribuicaoItem {
  estado: string;
  unidades: number;
  pacientes: number;
  atendimentos: number;
}

export interface TopUnidadeItem {
  nome: string;
  cnes: string;
  municipio: string;
  estado: string;
  atendimentos: number;
  pacientes: number;
}

export interface ChronicDashboardData {
  totalPacientesCronicos: number;
  emAcompanhamento: number;
  taxaControle: number;
  prevalencia: PrevalenciaItem[];
  acompanhamento: AcompanhamentoItem[];
}

export interface PrevalenciaItem {
  condicao: string;
  total: number;
  percentual: number;
  tendencia: 'alta' | 'estavel' | 'baixa';
}

export interface AcompanhamentoItem {
  mes: string;
  hipertensao: number;
  diabetes: number;
  obesidade: number;
  tabagismo: number;
}

export interface QualityDashboardData {
  indicadores: IndicadorItem[];
  evolucaoQualidade: {
    mes: string;
    score: number;
  }[];
}

export interface IndicadorItem {
  nome: string;
  valor: number;
  meta: number;
  status: 'critico' | 'atencao' | 'adequado' | 'excelente';
  tendencia: 'alta' | 'estavel' | 'baixa';
}

export const BRAZILIAN_STATES = [
  { value: 'AC', label: 'Acre' },
  { value: 'AL', label: 'Alagoas' },
  { value: 'AP', label: 'Amapá' },
  { value: 'AM', label: 'Amazonas' },
  { value: 'BA', label: 'Bahia' },
  { value: 'CE', label: 'Ceará' },
  { value: 'DF', label: 'Distrito Federal' },
  { value: 'ES', label: 'Espírito Santo' },
  { value: 'GO', label: 'Goiás' },
  { value: 'MA', label: 'Maranhão' },
  { value: 'MT', label: 'Mato Grosso' },
  { value: 'MS', label: 'Mato Grosso do Sul' },
  { value: 'MG', label: 'Minas Gerais' },
  { value: 'PA', label: 'Pará' },
  { value: 'PB', label: 'Paraíba' },
  { value: 'PR', label: 'Paraná' },
  { value: 'PE', label: 'Pernambuco' },
  { value: 'PI', label: 'Piauí' },
  { value: 'RJ', label: 'Rio de Janeiro' },
  { value: 'RN', label: 'Rio Grande do Norte' },
  { value: 'RS', label: 'Rio Grande do Sul' },
  { value: 'RO', label: 'Rondônia' },
  { value: 'RR', label: 'Roraima' },
  { value: 'SC', label: 'Santa Catarina' },
  { value: 'SP', label: 'São Paulo' },
  { value: 'SE', label: 'Sergipe' },
  { value: 'TO', label: 'Tocantins' },
] as const;

export const UNIT_TYPES = [
  { value: 'ubs', label: 'UBS - Unidade Básica de Saúde' },
  { value: 'upa', label: 'UPA - Unidade de Pronto Atendimento' },
  { value: 'hospital', label: 'Hospital' },
  { value: 'policlinica', label: 'Policlínica' },
  { value: 'caps', label: 'CAPS - Centro de Atenção Psicossocial' },
  { value: 'ceo', label: 'CEO - Centro de Especialidades Odontológicas' },
  { value: 'outros', label: 'Outros' },
] as const;

export const CONTACT_SUBJECTS = [
  { value: 'duvida', label: 'Dúvida sobre os agentes' },
  { value: 'suporte', label: 'Suporte técnico' },
  { value: 'parceria', label: 'Proposta de parceria' },
  { value: 'feedback', label: 'Feedback' },
  { value: 'outros', label: 'Outros assuntos' },
] as const;

export const AGENTS: Agent[] = [
  {
    id: '1',
    name: 'Wanda',
    slug: 'wanda',
    role: 'Apoio à Enfermagem',
    description: 'Homenagem a Wanda de Aguiar Horta, enfermeira brasileira pioneira na sistematização da assistência de enfermagem. Atua como um sistema de apoio à decisão para o enfermeiro clínico, fortalecendo a coordenação do cuidado, o raciocínio clínico e a gestão colaborativa.',
    icon: '👩‍⚕️',
    color: 'primary',
    category: 'Assistencial',
    imageUrl: '/src/assets/wandaAtual.jpg',
    features: [
      'Sistema de apoio à decisão clínica baseado em evidências',
      'Coordenação inteligente do cuidado de enfermagem',
      'Raciocínio clínico assistido por IA',
      'Gestão colaborativa da equipe de enfermagem',
      'Integração com protocolos de SAE (Sistematização da Assistência de Enfermagem)',
    ],
    benefits: [
      'Fortalecimento da autonomia do enfermeiro',
      'Melhoria na qualidade do cuidado de enfermagem',
      'Redução de intercorrências clínicas',
      'Otimização do tempo da equipe de enfermagem',
    ],
    useCases: [
      {
        title: 'Sistematização da Assistência de Enfermagem',
        description: 'Apoio à implementação da SAE com diagnósticos, prescrições e avaliações',
      },
      {
        title: 'Raciocínio Clínico',
        description: 'Auxílio na análise de sinais e sintomas para tomada de decisão',
      },
      {
        title: 'Gestão da Equipe',
        description: 'Coordenação e distribuição inteligente de tarefas da equipe de enfermagem',
      },
    ],
    dataSources: ['Prontuário Eletrônico', 'Sistemas FHIR', 'Protocolos de Enfermagem', 'Histórico do Paciente'],
    technologies: ['IA', 'Machine Learning', 'FHIR', 'NLP', 'SAE'],
    status: 'disponivel',
    externalLink: 'https://alice.com.br/blog/pessoas/wanda-horta-enfermeira-cuidado-saude/',
    externalLinkLabel: 'Conheça a história de Wanda de Aguiar Horta',
  },
  {
    id: '2',
    name: 'Geralda',
    slug: 'geralda',
    role: 'Apoio à Enfermagem',
    description: 'Homenagem a Geralda Lopes da Silva, enfermeira brasileira dedicada ao cuidado e à educação em saúde. Auxilia na organização do cuidado diário, gera lembretes, organiza informações de saúde e prepara pacientes para consultas e exames.',
    icon: '👩‍⚕️',
    color: 'secondary',
    category: 'Assistencial',
    imageUrl: '/src/assets/fotoGeralda.png',
    features: [
      'Organização inteligente do cuidado diário do paciente',
      'Lembretes personalizados para medicamentos e cuidados',
      'Organização de informações de saúde do paciente',
      'Preparação de pacientes para consultas e exames',
      'Educação em saúde personalizada',
    ],
    benefits: [
      'Melhoria na adesão ao tratamento',
      'Redução de faltas em consultas e exames',
      'Empoderamento do paciente no autocuidado',
      'Organização eficiente da rotina de cuidados',
    ],
    useCases: [
      {
        title: 'Gestão do Cuidado Diário',
        description: 'Organização e acompanhamento das atividades diárias de cuidado',
      },
      {
        title: 'Preparação para Consultas',
        description: 'Orientações e checklists para preparação pré-consulta',
      },
      {
        title: 'Educação em Saúde',
        description: 'Materiais educativos personalizados para cada paciente',
      },
    ],
    dataSources: ['e-SUS APS', 'Prontuário Eletrônico', 'Agendas', 'Protocolos de Cuidado'],
    technologies: ['IA', 'NLP', 'Mobile', 'Notificações Push'],
    status: 'disponivel',
    externalLink: 'https://www.coren-mt.gov.br/nota-de-pesar-pelo-falecimento-da-professora-geralda-lopes-da-silva/',
    externalLinkLabel: 'Conheça a história de Geralda Lopes da Silva',
  },
  {
    id: '3',
    name: 'Agente de Triagem Inteligente',
    slug: 'triagem',
    description: 'Automatiza a triagem de pacientes usando IA para classificação de risco e priorização de atendimento baseada em protocolos clínicos validados.',
    icon: '🩺',
    color: 'primary',
    category: 'Assistencial',
    features: [
      'Classificação automática de risco usando algoritmos de IA',
      'Priorização inteligente baseada em protocolos de Manchester',
      'Integração com prontuário eletrônico e sistemas FHIR',
      'Redução significativa do tempo de espera',
      'Alertas em tempo real para casos críticos',
    ],
    benefits: [
      'Redução de 40% no tempo médio de triagem',
      'Aumento de 30% na precisão da classificação de risco',
      'Melhoria de 25% na satisfação do paciente',
      'Diminuição de eventos adversos por triagem inadequada',
    ],
    useCases: [
      {
        title: 'Pronto-Atendimento 24h',
        description: 'Triagem automatizada em unidades de emergência com alto volume de pacientes',
      },
      {
        title: 'UPAs e Hospitais',
        description: 'Classificação de risco em tempo real para otimização do fluxo de atendimento',
      },
      {
        title: 'Telemedicina',
        description: 'Triagem remota para consultas virtuais e orientação de encaminhamento',
      },
    ],
    dataSources: ['Prontuário Eletrônico', 'Sistemas FHIR', 'Protocolos Clínicos', 'Histórico do Paciente'],
    technologies: ['IA', 'Machine Learning', 'FHIR', 'HL7', 'NLP'],
    status: 'disponivel',
  },
  {
    id: '4',
    name: 'Agente de Crônicos',
    slug: 'cronicos',
    description: 'Monitora e acompanha pacientes com doenças crônicas, promovendo adesão ao tratamento e prevenção de complicações através de intervenções personalizadas.',
    icon: '❤️',
    color: 'error',
    category: 'Assistencial',
    features: [
      'Monitoramento contínuo de indicadores vitais e laboratoriais',
      'Alertas automáticos de não-adesão ao tratamento',
      'Planos de cuidado personalizados baseados em evidências',
      'Integração com dispositivos wearables e IoT',
      'Comunicação proativa com pacientes via múltiplos canais',
    ],
    benefits: [
      'Redução de 35% nas internações evitáveis',
      'Aumento de 50% na adesão ao tratamento medicamentoso',
      'Melhoria de 40% nos indicadores de controle glicêmico e pressórico',
      'Redução de custos com complicações e emergências',
    ],
    useCases: [
      {
        title: 'Hipertensão Arterial',
        description: 'Monitoramento de pressão arterial e adesão a anti-hipertensivos',
      },
      {
        title: 'Diabetes Mellitus',
        description: 'Controle glicêmico, acompanhamento de HbA1c e prevenção de complicações',
      },
      {
        title: 'Doenças Cardiovasculares',
        description: 'Gestão de fatores de risco e prevenção secundária',
      },
      {
        title: 'Obesidade',
        description: 'Acompanhamento nutricional e incentivo à atividade física',
      },
    ],
    dataSources: ['e-SUS APS', 'SISAB', 'Dispositivos IoT', 'Laboratórios', 'Prontuário Eletrônico'],
    technologies: ['IA', 'IoT', 'FHIR', 'Telemedicina', 'Analytics'],
    status: 'disponivel',
  },
  {
    id: '5',
    name: 'Agente de Qualidade Assistencial',
    slug: 'qualidade',
    description: 'Monitora indicadores de qualidade assistencial em tempo real e sugere melhorias baseadas em evidências científicas e melhores práticas nacionais e internacionais. Inspirado nos 7 pilares da qualidade de Avedis Donabedian.',
    icon: '🏆',
    color: 'success',
    category: 'Gestão',
    features: [
      'Análise automatizada de indicadores de qualidade (IQASUS, PMAQ)',
      'Benchmarking com melhores práticas nacionais e internacionais',
      'Sugestões de melhoria baseadas em evidências científicas',
      'Relatórios automatizados para gestores e equipes',
      'Alertas de não-conformidade com protocolos clínicos',
    ],
    benefits: [
      'Aumento de 25% nos indicadores de qualidade assistencial',
      'Redução de 30% em eventos adversos evitáveis',
      'Melhoria na conformidade com protocolos clínicos',
      'Facilitação de processos de acreditação (ONA, JCI)',
    ],
    useCases: [
      {
        title: 'Gestão Hospitalar',
        description: 'Monitoramento de indicadores de qualidade e segurança do paciente',
      },
      {
        title: 'Acreditação de Serviços',
        description: 'Preparação e manutenção de certificações de qualidade',
      },
      {
        title: 'Auditoria Clínica',
        description: 'Análise de conformidade com protocolos e diretrizes clínicas',
      },
    ],
    dataSources: ['Prontuário Eletrônico', 'CNES', 'SIH', 'SIA', 'Sistemas de Qualidade'],
    technologies: ['IA', 'Big Data', 'Analytics', 'FHIR', 'Business Intelligence'],
    status: 'disponivel',
  },
  {
    id: '6',
    name: 'Agente de Regulação',
    slug: 'regulacao',
    description: 'Otimiza o fluxo de pacientes entre diferentes níveis de atenção à saúde, reduzindo filas e tempo de espera através de algoritmos inteligentes de alocação.',
    icon: '🔄',
    color: 'secondary',
    category: 'Gestão',
    features: [
      'Gestão inteligente de filas e priorização clínica',
      'Otimização de recursos e ocupação de leitos',
      'Integração entre níveis de atenção (primária, secundária, terciária)',
      'Priorização baseada em critérios clínicos e tempo de espera',
      'Transparência e rastreabilidade do processo regulatório',
    ],
    benefits: [
      'Redução de 45% no tempo médio de espera',
      'Otimização de 30% na taxa de ocupação de leitos',
      'Melhoria de 35% no acesso a consultas especializadas',
      'Redução de absenteísmo em consultas agendadas',
    ],
    useCases: [
      {
        title: 'Consultas Especializadas',
        description: 'Regulação e agendamento de consultas com especialistas',
      },
      {
        title: 'Gestão de Leitos',
        description: 'Otimização da ocupação hospitalar e transferências',
      },
      {
        title: 'Exames de Alta Complexidade',
        description: 'Priorização e agendamento de exames especializados',
      },
    ],
    dataSources: ['SISREG', 'CNES', 'SIH', 'Sistemas de Agendamento', 'Prontuário Eletrônico'],
    technologies: ['IA', 'Otimização', 'FHIR', 'Integração', 'Algoritmos de Fila'],
    status: 'em_desenvolvimento',
  },
];

// Referência aos 7 Pilares da Qualidade de Donabedian
export const DONABEDIAN_REFERENCE = {
  name: 'Avedis Donabedian',
  title: 'Pai da Garantia da Qualidade em Saúde',
  imageUrl: '/src/assets/donabedian.jpg',
  link: 'https://blogdaqualidade.com.br/saude-os-7-pilares-da-qualidade-de-avedis-donabedian/',
  description: 'O modelo de Donabedian é a base para a avaliação da qualidade em saúde no INTELLICARE, fundamentado na tríade Estrutura-Processo-Resultado.',
  pillars: [
    {
      name: 'Eficácia',
      description: 'Proporcionar serviços de saúde baseados em evidências científicas aos que necessitam',
    },
    {
      name: 'Eficiência',
      description: 'Maximizar o benefício da saúde utilizando os recursos disponíveis de forma otimizada',
    },
    {
      name: 'Acesso',
      description: 'Garantir que os serviços de saúde sejam obtidos no momento adequado',
    },
    {
      name: 'Aceitabilidade',
      description: 'Respeitar as preferências e necessidades dos pacientes e profissionais',
    },
    {
      name: 'Equidade',
      description: 'Distribuir os serviços de saúde de forma justa entre diferentes grupos populacionais',
    },
    {
      name: 'Abrangência',
      description: 'Oferecer uma gama completa de serviços de saúde necessários',
    },
    {
      name: 'Segurança',
      description: 'Minimizar riscos e danos associados aos serviços de saúde',
    },
  ],
} as const;
