import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { HelpCircle, ChevronDown, Search, MessageSquare } from 'lucide-react';

export default function FaqPage() {
  const [openIndex, setOpenIndex] = useState<number | null>(null);
  const [searchTerm, setSearchTerm] = useState('');

  const faqCategories = [
    {
      category: 'Geral',
      questions: [
        {
          question: 'O que é a IntelliCare?',
          answer: 'A IntelliCare é uma plataforma de agentes inteligentes baseados em inteligência artificial, projetada para transformar a saúde pública brasileira. Nossos agentes auxiliam profissionais de saúde em tarefas como triagem, monitoramento de pacientes crônicos, gestão de qualidade e otimização de recursos.',
        },
        {
          question: 'Quem pode usar a IntelliCare?',
          answer: 'A plataforma é destinada a profissionais e gestores de saúde pública, incluindo: secretarias municipais e estaduais de saúde, hospitais e clínicas, unidades básicas de saúde, profissionais de enfermagem e médicos, gestores de saúde e administradores hospitalares.',
        },
        {
          question: 'A IntelliCare substitui profissionais de saúde?',
          answer: 'Não. Nossos agentes de IA são ferramentas de apoio à decisão, projetadas para auxiliar e potencializar o trabalho dos profissionais de saúde. As decisões finais de tratamento sempre devem ser tomadas por profissionais qualificados.',
        },
      ],
    },
    {
      category: 'Agentes de IA',
      questions: [
        {
          question: 'Quais agentes estão disponíveis?',
          answer: 'Atualmente temos 6 agentes: Wanda (apoio à enfermagem para profissionais), Geralda (apoio à enfermagem para pacientes), Agente de Triagem Inteligente, Agente de Crônicos, Agente de Qualidade Assistencial e Agente de Regulação. Cada um é especializado em uma área específica.',
        },
        {
          question: 'Como os agentes de IA funcionam?',
          answer: 'Nossos agentes utilizam inteligência artificial, machine learning e processamento de linguagem natural para analisar dados de saúde, identificar padrões e fornecer recomendações baseadas em evidências científicas e protocolos clínicos validados.',
        },
        {
          question: 'Posso usar múltiplos agentes simultaneamente?',
          answer: 'Sim! A plataforma foi projetada para que diferentes agentes trabalhem de forma integrada, compartilhando informações relevantes quando apropriado, sempre respeitando a privacidade e segurança dos dados.',
        },
      ],
    },
    {
      category: 'Segurança e Privacidade',
      questions: [
        {
          question: 'Meus dados estão seguros?',
          answer: 'Sim. Implementamos medidas rigorosas de segurança, incluindo criptografia SSL/TLS, armazenamento criptografado, controles de acesso baseados em função, autenticação multifator e monitoramento contínuo. Estamos em conformidade total com a LGPD.',
        },
        {
          question: 'A IntelliCare é compatível com a LGPD?',
          answer: 'Sim, totalmente. Temos um DPO (Encarregado de Proteção de Dados) designado, realizamos avaliações de impacto à proteção de dados, mantemos registros de operações de tratamento e garantimos todos os direitos dos titulares previstos na lei.',
        },
        {
          question: 'Os dados dos pacientes são compartilhados?',
          answer: 'Não. Os dados dos pacientes são processados com anonimização quando possível e nunca são vendidos ou compartilhados com terceiros sem autorização adequada. Qualquer compartilhamento é feito apenas com garantias contratuais de proteção.',
        },
      ],
    },
    {
      category: 'Integração e Técnico',
      questions: [
        {
          question: 'A IntelliCare integra com outros sistemas?',
          answer: 'Sim! Integramos com diversos sistemas de saúde, incluindo: e-SUS APS, sistemas FHIR/HL7, prontuários eletrônicos, sistemas de agendamento e CNES. Também oferecemos API para integrações personalizadas.',
        },
        {
          question: 'Quais são os requisitos técnicos?',
          answer: 'A plataforma é web-based e funciona em qualquer navegador moderno (Chrome, Firefox, Safari, Edge). Não é necessário instalar software. Para integrações, disponibilizamos documentação completa da API.',
        },
        {
          question: 'Como faço para integrar minha unidade de saúde?',
          answer: 'O processo é simples: 1) Preencha o formulário de solicitação, 2) Nossa equipe fará uma avaliação técnica, 3) Configuramos a integração com seus sistemas, 4) Realizamos treinamento com sua equipe, 5) Acompanhamos a implantação.',
        },
      ],
    },
    {
      category: 'Planos e Preços',
      questions: [
        {
          question: 'Quanto custa usar a IntelliCare?',
          answer: 'Oferecemos diferentes modalidades: 1) Uso gratuito para unidades de saúde pública do SUS, 2) Planos corporativos para instituições privadas, 3) Licenciamento por volume para redes de saúde. Entre em contato para uma proposta personalizada.',
        },
        {
          question: 'Existe período de teste?',
          answer: 'Sim! Oferecemos um período de avaliação de 30 dias com acesso completo à plataforma e suporte técnico dedicado. Não é necessário cartão de crédito.',
        },
        {
          question: 'Como posso solicitar participação?',
          answer: 'Acesse a página "Participação" e preencha o formulário correspondente ao seu perfil (Secretaria de Saúde ou Unidade de Saúde). Nossa equipe entrará em contato em até 5 dias úteis.',
        },
      ],
    },
    {
      category: 'Suporte',
      questions: [
        {
          question: 'Como entro em contato com o suporte?',
          answer: 'Você pode: 1) Usar o chat ao vivo na plataforma, 2) Enviar e-mail para suporte@intellicare.com.br, 3) Abrir um chamado pelo sistema, 4) Agendar uma call de suporte. Nosso horário de atendimento é de segunda a sexta, 8h às 18h.',
        },
        {
          question: 'Oferecem treinamento?',
          answer: 'Sim! Oferecemos treinamento inicial gratuito para todas as unidades, workshops mensais sobre novas funcionalidades, webinars sobre boas práticas e documentação completa em vídeo e texto.',
        },
        {
          question: 'Qual o tempo de resposta do suporte?',
          answer: 'Nossos SLAs são: Chamados críticos: até 4 horas, Chamados urgentes: até 24 horas, Chamados normais: até 48 horas, Dúvidas gerais: até 72 horas.',
        },
      ],
    },
  ];

  const filteredFaqs = faqCategories.map((cat) => ({
    ...cat,
    questions: cat.questions.filter(
      (q) =>
        q.question.toLowerCase().includes(searchTerm.toLowerCase()) ||
        q.answer.toLowerCase().includes(searchTerm.toLowerCase())
    ),
  })).filter((cat) => cat.questions.length > 0);

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
            <HelpCircle className="w-8 h-8 text-primary-600" />
          </div>
          <h1 className="text-4xl font-bold text-neutral-900 mb-4">
            Perguntas Frequentes
          </h1>
          <p className="text-lg text-neutral-600">
            Encontre respostas para as dúvidas mais comuns
          </p>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.2 }}
          className="mb-8"
        >
          <div className="relative max-w-2xl mx-auto">
            <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-neutral-400" />
            <input
              type="text"
              placeholder="Buscar perguntas..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full pl-12 pr-4 py-4 rounded-xl border border-neutral-200 focus:border-primary-500 focus:ring-2 focus:ring-primary-200 outline-none transition-all text-lg"
            />
          </div>
        </motion.div>

        <div className="space-y-8">
          {filteredFaqs.map((category, catIndex) => (
            <motion.div
              key={category.category}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5, delay: 0.3 + catIndex * 0.1 }}
            >
              <h2 className="text-xl font-bold text-neutral-900 mb-4 flex items-center gap-2">
                <span className="w-8 h-8 bg-primary-100 rounded-lg flex items-center justify-center text-primary-600 text-sm">
                  {category.category[0]}
                </span>
                {category.category}
              </h2>
              <div className="space-y-3">
                {category.questions.map((faq, index) => {
                  const globalIndex = catIndex * 100 + index;
                  const isOpen = openIndex === globalIndex;
                  return (
                    <div
                      key={index}
                      className="bg-white rounded-xl border border-neutral-200 overflow-hidden"
                    >
                      <button
                        onClick={() => setOpenIndex(isOpen ? null : globalIndex)}
                        className="w-full flex items-center justify-between p-4 text-left hover:bg-neutral-50 transition-colors"
                      >
                        <span className="font-medium text-neutral-900 pr-4">
                          {faq.question}
                        </span>
                        <ChevronDown
                          className={`w-5 h-5 text-neutral-400 flex-shrink-0 transition-transform ${
                            isOpen ? 'rotate-180' : ''
                          }`}
                        />
                      </button>
                      <AnimatePresence>
                        {isOpen && (
                          <motion.div
                            initial={{ height: 0, opacity: 0 }}
                            animate={{ height: 'auto', opacity: 1 }}
                            exit={{ height: 0, opacity: 0 }}
                            transition={{ duration: 0.2 }}
                          >
                            <div className="px-4 pb-4 text-neutral-600 leading-relaxed border-t border-neutral-100 pt-4">
                              {faq.answer}
                            </div>
                          </motion.div>
                        )}
                      </AnimatePresence>
                    </div>
                  );
                })}
              </div>
            </motion.div>
          ))}
        </div>

        {filteredFaqs.length === 0 && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="text-center py-12"
          >
            <p className="text-neutral-500">
              Nenhuma pergunta encontrada para sua busca.
            </p>
          </motion.div>
        )}

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.8 }}
          className="mt-12 bg-primary-50 rounded-xl p-6 border border-primary-100 text-center"
        >
          <MessageSquare className="w-8 h-8 text-primary-600 mx-auto mb-3" />
          <h3 className="font-bold text-primary-900 mb-2">
            Ainda tem dúvidas?
          </h3>
          <p className="text-primary-800 text-sm mb-4">
            Nossa equipe está pronta para ajudar
          </p>
          <a
            href="/contato"
            className="inline-flex items-center gap-2 px-6 py-2 bg-primary-600 text-white font-semibold rounded-lg hover:bg-primary-700 transition-colors"
          >
            Falar com a gente
          </a>
        </motion.div>
      </div>
    </div>
  );
}
