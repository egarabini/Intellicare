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
    role: 'Orquestradora Clínica Inteligente',
    description: 'Homenagem a Wanda de Aguiar Horta, enfermeira brasileira pioneira na sistematização da assistência de enfermagem. Orquestra todos os agentes e ferramentas MCP, coordenando clínica, gestão e território para respostas integradas e rastreáveis.',
    icon: '👩‍⚕️',
    color: 'primary',
    category: 'Orquestração',
    imageUrl: '/src/assets/wandaAtual.jpg',
    features: [
      'Orquestração de subagentes especializados via LangGraph',
      'Coordenação de ferramentas MCP (FHIR, RNDS, Careplanner)',
      'Regra IPS-First: sempre carrega contexto do paciente antes de analisar',
      'Raciocínio multi-domínio: clínica, gestão e território',
      'Resposta consolidada única e rastreável',
    ],
    benefits: [
      'Integração de múltiplas fontes de dados em resposta única',
      'Segurança clínica pela regra IPS-First',
      'Redução de tempo de busca e cruzamento de informações',
      'Rastreabilidade completa das decisões',
    ],
    useCases: [
      {
        title: 'Raciocínio Multi-Domínio',
        description: 'Consulta simultânea a hospital, governo e território para visão 360° do paciente',
      },
      {
        title: 'Coordenação de Cuidado',
        description: 'Orquestração de especialistas conforme intenção clínica e operacional',
      },
      {
        title: 'Apoio à Decisão Integrada',
        description: 'Consolidação de dados clínicos, gestão e qualidade em orientação acionável',
      },
    ],
    dataSources: ['FHIR Server', 'RNDS', 'Careplanner', 'Prontuário Eletrônico', 'CNES'],
    technologies: ['LangGraph', 'LangChain', 'MCP', 'FHIR R4', 'Python'],
    status: 'disponivel',
    externalLink: 'https://alice.com.br/blog/pessoas/wanda-horta-enfermeira-cuidado-saude/',
    externalLinkLabel: 'Conheça a história de Wanda de Aguiar Horta',
  },
  {
    id: '2',
    name: 'Florence',
    slug: 'florence',
    role: 'Inteligência Clínica Profunda',
    description: 'Homenagem a Florence Nightingale, fundadora da enfermagem moderna e pioneira no uso de dados para melhorar a saúde. Aprofunda a análise clínica, interpreta exames laboratoriais e identifica tendências para apoiar a decisão médica com evidências.',
    icon: '🔬',
    color: 'primary',
    category: 'Assistencial',
    imageUrl: '/src/assets/florence.png',
    features: [
      'Análise profunda de exames laboratoriais e evolução clínica',
      'Identificação de tendências e sinais críticos',
      'Cruzamento de histórico clínico com contexto atual',
      'Apoio à decisão médica baseada em evidências',
      'Integração com IPS (International Patient Summary)',
    ],
    benefits: [
      'Detecção precoce de deterioração clínica',
      'Redução de erros de interpretação laboratorial',
      'Visão longitudinal do paciente com tendências',
      'Apoio objetivo à tomada de decisão médica',
    ],
    useCases: [
      {
        title: 'Análise de Exames',
        description: 'Interpretação inteligente de resultados laboratoriais com contexto clínico',
      },
      {
        title: 'Evolução Clínica',
        description: 'Acompanhamento de tendências e alertas sobre deterioração',
      },
      {
        title: 'Apoio Diagnóstico',
        description: 'Cruzamento de dados para sugestões diagnósticas baseadas em evidências',
      },
    ],
    dataSources: ['FHIR Server', 'Laboratórios', 'Prontuário Eletrônico', 'IPS', 'Protocolos Clínicos'],
    technologies: ['LangChain', 'RAG', 'FHIR R4', 'NLP', 'Python'],
    status: 'disponivel',
    externalLink: 'https://pt.wikipedia.org/wiki/Florence_Nightingale',
    externalLinkLabel: 'Conheça a história de Florence Nightingale',
  },
  {
    id: '3',
    name: 'Oswaldo',
    slug: 'oswaldo',
    role: 'Motor Genérico de Doenças Crônicas',
    description: 'Homenagem a Oswaldo Cruz, médico sanitarista que revolucionou a saúde pública no Brasil. Motor genérico e extensível de monitoramento de doenças crônicas via Disease Profiles YAML, com estadiamento plugável por doença.',
    icon: '❤️',
    color: 'error',
    category: 'Assistencial',
    imageUrl: '/src/assets/oswaldo.png',
    features: [
      'Motor genérico: CKD, Diabetes e Hipertensão via configuração YAML',
      'Estadiamento plugável: KDIGO (CKD), ADA (DM2), ESC/ESH (HAS)',
      'Tendências longitudinais com cálculo de velocidade de progressão',
      'Alertas com severidade e recomendações acionáveis',
      'Confidence score baseado em volume e qualidade dos dados',
    ],
    benefits: [
      'Novas doenças entram apenas com arquivo de configuração',
      'Padronização de estadiamento conforme guidelines internacionais',
      'Detecção precoce de progressão acelerada',
      'Redução de internações evitáveis por complicações',
    ],
    useCases: [
      {
        title: 'Doença Renal Crônica',
        description: 'Estadiamento KDIGO (G1-G5/A1-A3), monitoramento de eGFR e albuminúria',
      },
      {
        title: 'Diabetes Mellitus Tipo 2',
        description: 'Controle glicêmico via HbA1c, estadiamento ADA e prevenção de complicações',
      },
      {
        title: 'Hipertensão Arterial',
        description: 'Classificação ESC/ESH, tendência pressórica e ajuste terapêutico',
      },
    ],
    dataSources: ['FHIR Server', 'Laboratórios', 'Disease Profiles YAML', 'Prontuário Eletrônico'],
    technologies: ['Python', 'Strategy Pattern', 'FHIR R4', 'YAML', 'Streamlit'],
    status: 'disponivel',
    externalLink: 'https://pt.wikipedia.org/wiki/Oswaldo_Cruz',
    externalLinkLabel: 'Conheça a história de Oswaldo Cruz',
  },
  {
    id: '4',
    name: 'Zilda',
    slug: 'zilda',
    role: 'Dados de Saúde Brasileira',
    description: 'Homenagem a Zilda Arns, médica pediatra e sanitarista fundadora da Pastoral da Criança. Especialista em contexto territorial e rede assistencial brasileira, consultando CNES, DATASUS e dados regionais para decisões mais realistas.',
    icon: '🗺️',
    color: 'success',
    category: 'Gestão',
    imageUrl: '/src/assets/zilda.png',
    features: [
      'Consulta e validação de dados CNES em tempo real',
      'Contexto territorial e rede assistencial por região',
      'Enriquecimento de dados de unidades de saúde',
      'Mapeamento de capacidade instalada por território',
      'Integração com dados do DATASUS e e-SUS',
    ],
    benefits: [
      'Decisões conectadas ao contexto real da rede de saúde',
      'Validação automática de unidades e profissionais',
      'Visão territorial para planejamento assistencial',
      'Redução de encaminhamentos inadequados',
    ],
    useCases: [
      {
        title: 'Mapeamento de Rede',
        description: 'Identificação de unidades, especialidades e capacidade por região',
      },
      {
        title: 'Validação CNES',
        description: 'Verificação e enriquecimento automático de cadastros de unidades',
      },
      {
        title: 'Planejamento Territorial',
        description: 'Análise de cobertura e vazios assistenciais por região de saúde',
      },
    ],
    dataSources: ['CNES', 'DATASUS', 'e-SUS APS', 'IBGE', 'Secretarias de Saúde'],
    technologies: ['Python', 'APIs DATASUS', 'FHIR R4', 'Geolocalização', 'Analytics'],
    status: 'disponivel',
    externalLink: 'https://pt.wikipedia.org/wiki/Zilda_Arns',
    externalLinkLabel: 'Conheça a história de Zilda Arns',
  },
  {
    id: '5',
    name: 'Geralda',
    slug: 'geralda',
    role: 'Acompanhamento do Paciente',
    description: 'Homenagem a Geralda Lopes da Silva, enfermeira brasileira dedicada ao cuidado e à educação em saúde. Sustenta a continuidade do cuidado e o vínculo com o paciente, traduzindo orientações em ações práticas e fortalecendo a adesão terapêutica.',
    icon: '👩‍⚕️',
    color: 'secondary',
    category: 'Assistencial',
    imageUrl: '/src/assets/fotoGeralda.png',
    features: [
      'Organização inteligente do cuidado diário do paciente',
      'Lembretes personalizados para medicamentos e cuidados',
      'Comunicação proativa entre equipe e paciente',
      'Preparação de pacientes para consultas e exames',
      'Educação em saúde personalizada e acessível',
    ],
    benefits: [
      'Melhoria na adesão ao tratamento',
      'Redução de faltas em consultas e exames',
      'Empoderamento do paciente no autocuidado',
      'Fortalecimento do vínculo equipe-paciente',
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
    dataSources: ['e-SUS APS', 'Prontuário Eletrônico', 'FHIR CarePlan', 'Protocolos de Cuidado'],
    technologies: ['Python', 'NLP', 'FHIR R4', 'Notificações', 'LangChain'],
    status: 'disponivel',
    externalLink: 'https://www.coren-mt.gov.br/nota-de-pesar-pelo-falecimento-da-professora-geralda-lopes-da-silva/',
    externalLinkLabel: 'Conheça a história de Geralda Lopes da Silva',
  },
  {
    id: '6',
    name: 'Donabedian',
    slug: 'donabedian',
    role: 'Qualidade em Saúde',
    description: 'Homenagem a Avedis Donabedian, pai da garantia da qualidade em saúde. Monitora indicadores de qualidade assistencial baseados na tríade Estrutura-Processo-Resultado e nos 7 pilares da qualidade, orientando melhoria contínua com dados.',
    icon: '🏆',
    color: 'success',
    category: 'Gestão',
    imageUrl: '/src/assets/donabedian.jpg',
    features: [
      'Avaliação baseada nos 7 pilares de Donabedian',
      'Análise automatizada de indicadores de qualidade (IQASUS, PMAQ)',
      'Benchmarking com melhores práticas nacionais e internacionais',
      'Relatórios automatizados para gestores e equipes',
      'Alertas de não-conformidade com protocolos clínicos',
    ],
    benefits: [
      'Governança por indicadores objetivos',
      'Melhoria contínua baseada em dados e evidências',
      'Conformidade com protocolos e acreditações',
      'Visão integrada de eficiência e valor assistencial',
    ],
    useCases: [
      {
        title: 'Gestão Hospitalar',
        description: 'Monitoramento de indicadores de qualidade e segurança do paciente',
      },
      {
        title: 'Acreditação de Serviços',
        description: 'Preparação e manutenção de certificações de qualidade (ONA, JCI)',
      },
      {
        title: 'Auditoria Clínica',
        description: 'Análise de conformidade com protocolos e diretrizes clínicas',
      },
    ],
    dataSources: ['Prontuário Eletrônico', 'CNES', 'SIH', 'SIA', 'Sistemas de Qualidade'],
    technologies: ['Python', 'Analytics', 'FHIR R4', 'Business Intelligence', 'LangChain'],
    status: 'disponivel',
    externalLink: 'https://blogdaqualidade.com.br/saude-os-7-pilares-da-qualidade-de-avedis-donabedian/',
    externalLinkLabel: 'Conheça os 7 pilares de Donabedian',
  },
  {
    id: '7',
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
    status: 'em_desenvolvimento',
  },
  {
    id: '8',
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
