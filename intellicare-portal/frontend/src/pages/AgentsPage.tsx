import { motion } from 'framer-motion';
import { ArrowLeft, Quote } from 'lucide-react';
import { Link } from 'react-router-dom';

const agents = [
  {
    id: 'oswaldo',
    name: 'Dr. Oswaldo',
    role: 'Gestão de Crônicos',
    image: '/agents/oswaldo_cartoon.png',
    inspiration: 'Oswaldo Cruz (1872-1917)',
    bio: 'Inspirado no médico sanitarista brasileiro que erradicou epidemias, o Agente Oswaldo monitora incansavelmente a saúde dos pacientes crônicos, identificando riscos silenciosos antes que se tornem crises.',
    color: 'from-blue-500 to-cyan-500',
    route: '/oswaldo'
  },
  {
    id: 'florence',
    name: 'Enf. Florence',
    role: 'Triagem Laboratorial',
    image: '/agents/Florence_cartoon.png',
    inspiration: 'Florence Nightingale (1820-1910)',
    bio: 'Homenagem à fundadora da enfermagem moderna e pioneira no uso de estatísticas visuais. Florence analisa exames laboratoriais com precisão matemática, garantindo que nenhum detalhe passe despercebido.',
    color: 'from-emerald-500 to-teal-500',
    route: '/florence'
  },
  {
    id: 'zilda',
    name: 'Dra. Zilda',
    role: 'Saúde Pública & Território',
    image: '/agents/zilda_cartoon.png',
    inspiration: 'Zilda Arns (1934-2010)',
    bio: 'Pediatra e sanitarista, fundadora da Pastoral da Criança. A Agente Zilda conecta o cuidado individual ao contexto territorial, trazendo dados do IBGE, CNES e RNDS para uma visão comunitária completa.',
    color: 'from-rose-500 to-pink-500',
    route: '/zilda'
  },
  {
    id: 'nise',
    name: 'Dra. Nise',
    role: 'Orquestração do Cuidado',
    image: '/agents/nise_cartoon.png',
    inspiration: 'Nise da Silveira (1905-1999)',
    bio: 'Psiquiatra revolucionária que humanizou o tratamento mental. Nise orquestra a jornada do paciente com empatia, garantindo que fluxos clínicos não sejam apenas processos, mas atos de cuidado.',
    color: 'from-purple-500 to-violet-500',
    route: '/nise'
  },
  {
    id: 'geralda',
    name: 'Agente Geralda',
    role: 'Atenção Primária',
    image: '/agents/geralda_cartoon.png',
    inspiration: 'A "Generalista" Brasileira',
    bio: 'Representando a força da Atenção Primária, Geralda é a guardiã do plano de cuidados longitudinal. Ela garante a adesão ao tratamento e mantém o vínculo contínuo com a família.',
    color: 'from-amber-500 to-orange-500',
    route: '/geralda'
  },
  {
    id: 'grahame',
    name: 'Sir Grahame',
    role: 'Interoperabilidade',
    image: '/agents/grahame_cartoon.png',
    inspiration: 'Grahame Grieve (Criador do FHIR)',
    bio: 'O arquiteto da linguagem universal da saúde. Grahame traduz dialetos complexos para o padrão HL7 FHIR, permitindo que todos os sistemas e agentes conversem entre si sem barreiras.',
    color: 'from-orange-500 to-red-500',
    route: '/grahame'
  },
  {
    id: 'wanda',
    name: 'Enf. Wanda',
    role: 'Sistematização (SAE)',
    image: '/agents/wanda_cartoon.png',
    inspiration: 'Wanda Horta (1926-1981)',
    bio: 'Introduziu a Teoria das Necessidades Humanas Básicas. O módulo Wanda (em breve) automatizará a Sistematização da Assistência de Enfermagem, focando no ser humano como um todo.',
    color: 'from-indigo-500 to-blue-600',
    route: '/wanda'
  },
  {
    id: 'donabedian',
    name: 'Prof. Donabedian',
    role: 'Qualidade & Auditoria',
    image: '/agents/agente_donabedian_ia.png',
    inspiration: 'Avedis Donabedian (1919-2000)',
    bio: 'Pai da qualidade em saúde. Este agente (futuro) avaliará a Estrutura, Processo e Resultados de cada atendimento, garantindo a excelência clínica do Intellicare.',
    color: 'from-slate-500 to-gray-600',
    route: '/donabedian'
  },
  {
    id: 'minerva',
    name: 'Minerva',
    role: 'Inteligência Documental',
    image: '/agents/minerva_cartoon.png',
    inspiration: 'Deusa da Sabedoria',
    bio: 'Com sua visão aguçada (OCR), Minerva transforma documentos desestruturados em conhecimento acionável, trazendo luz aos dados ocultos em PDFs e imagens.',
    color: 'from-yellow-500 to-amber-400',
    route: '/minerva'
  },
  {
    id: 'pierre',
    name: 'Pierre',
    role: 'Inteligência Coletiva',
    image: '/agents/pierre_cartoon.png',
    inspiration: 'Pierre Lévy (Filósofo)',
    bio: 'Inspirado no teórico da Cibercultura e Inteligência Coletiva. Pierre é o cérebro central que sintetiza o conhecimento de todos os outros agentes para apoiar a decisão clínica.',
    color: 'from-cyan-400 to-blue-500',
    route: '/pierre'
  },
  {
    id: 'hippocrates',
    name: 'Dr. Hipócrates',
    role: 'Comunicação Ética',
    image: '/agents/hipocrates_cartoon.png',
    inspiration: 'Hipócrates de Cós (460-370 a.C.)',
    bio: 'Pai da medicina e da ética médica. Este agente garante que a comunicação com o paciente seja clara, empática e respeite o princípio de não causar dano.',
    color: 'from-sky-500 to-indigo-500',
    route: '/hippocrates'
  }
];

export default function AgentsPage() {
  return (
    <div className="min-h-screen bg-slate-900 text-slate-200 p-6 md:p-12 font-sans">
      <div className="max-w-7xl mx-auto">

        <header className="mb-16 text-center">
          <Link to="/" className="inline-flex items-center gap-2 text-slate-400 hover:text-white mb-6 transition-colors">
            <ArrowLeft className="w-4 h-4" /> Voltar ao Portal
          </Link>
          <motion.h1
            initial={{ opacity: 0, y: -20 }}
            animate={{ opacity: 1, y: 0 }}
            className="text-4xl md:text-6xl font-black text-transparent bg-clip-text bg-gradient-to-r from-blue-400 via-purple-400 to-rose-400 mb-4"
          >
            A Liga da Inteligência
          </motion.h1>
          <motion.p
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.2 }}
            className="text-lg text-slate-400 max-w-2xl mx-auto"
          >
            Conheça os agentes especializados que compõem o ecossistema Intellicare.
            Cada um carrega o legado de um gigante da saúde.
          </motion.p>
        </header>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
          {agents.map((agent, index) => (
            <Link to={agent.route} key={agent.id}>
              <motion.div
                initial={{ opacity: 0, y: 30 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: index * 0.1 }}
                className="group relative bg-slate-800/40 border border-slate-700 rounded-2xl overflow-hidden hover:border-slate-500 transition-all duration-300 backdrop-blur-sm cursor-pointer"
              >
                {/* Background Gradient Effect */}
                <div className={`absolute inset-0 bg-gradient-to-br ${agent.color} opacity-0 group-hover:opacity-5 transition-opacity duration-500`} />

                <div className="p-6 relative z-10">
                  <div className="flex items-center gap-4 mb-6">
                    <div className={`w-20 h-20 rounded-full p-1 bg-gradient-to-br ${agent.color}`}>
                      <img
                        src={agent.image}
                        alt={agent.name}
                        className="w-full h-full object-cover rounded-full bg-slate-900 border-2 border-slate-900"
                      />
                    </div>
                    <div>
                      <h3 className="text-xl font-bold text-white group-hover:text-transparent group-hover:bg-clip-text group-hover:bg-gradient-to-r group-hover:from-white group-hover:to-slate-300 transition-colors">
                        {agent.name}
                      </h3>
                      <span className={`text-xs font-bold uppercase tracking-wider bg-clip-text text-transparent bg-gradient-to-r ${agent.color}`}>
                        {agent.role}
                      </span>
                    </div>
                  </div>

                  <div className="relative">
                    <Quote className="absolute -top-2 -left-2 w-6 h-6 text-slate-700 opacity-50" />
                    <p className="text-sm text-slate-300 leading-relaxed pl-4 mb-4">
                      {agent.bio}
                    </p>
                  </div>

                  <div className="pt-4 border-t border-slate-700/50 flex items-center justify-between text-xs text-slate-500 font-mono">
                    <span>INSPIRED BY</span>
                    <span className="text-slate-400">{agent.inspiration}</span>
                  </div>
                </div>
              </motion.div>
            </Link>
          ))}
        </div>

      </div>
    </div>
  );
}
