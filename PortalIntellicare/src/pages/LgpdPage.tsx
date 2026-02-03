import { motion } from 'framer-motion';
import { Scale, FileText, UserCheck, AlertTriangle, BookOpen, Shield } from 'lucide-react';

export default function LgpdPage() {
  const lgpdSections = [
    {
      icon: BookOpen,
      title: 'O que é a LGPD?',
      content: `A Lei Geral de Proteção de Dados (Lei nº 13.709/2018) é a legislação brasileira que regula o tratamento de dados pessoais. Ela estabelece regras sobre a coleta, armazenamento, uso e compartilhamento de dados pessoais, garantindo maior transparência e controle aos titulares.

A LGPD é inspirada na GDPR (Regulamento Geral de Proteção de Dados da União Europeia) e representa um marco importante na proteção da privacidade no Brasil.`,
    },
    {
      icon: FileText,
      title: 'Base Legal para Tratamento',
      content: `A IntelliCare trata dados pessoais com base nas seguintes hipóteses legais previstas na LGPD:

• <strong>Execução de contrato</strong> ou procedimentos preliminares
• <strong>Cumprimento de obrigação legal</strong> ou regulatória
• <strong>Exercício regular de direitos</strong> em processos judiciais
• <strong>Proteção da vida</strong> ou da incolumidade física do titular
• <strong>Legítimo interesse</strong> da IntelliCare ou de terceiros
• <strong>Consentimento</strong> do titular, quando necessário`,
    },
    {
      icon: UserCheck,
      title: 'Direitos do Titular',
      content: `De acordo com o artigo 18 da LGPD, você tem os seguintes direitos:

<strong>I.</strong> Confirmação da existência de tratamento
<strong>II.</strong> Acesso aos dados
<strong>III.</strong> Correção de dados incompletos, inexatos ou desatualizados
<strong>IV.</strong> Anonimização, bloqueio ou eliminação de dados desnecessários
<strong>V.</strong> Portabilidade dos dados
<strong>VI.</strong> Eliminação dos dados pessoais
<strong>VII.</strong> Informação sobre compartilhamento
<strong>VIII.</strong> Informação sobre a possibilidade de não fornecer consentimento
<strong>IX.</strong> Revogação do consentimento`,
    },
    {
      icon: Shield,
      title: 'Medidas de Segurança',
      content: `Implementamos as seguintes medidas técnicas e administrativas para proteger seus dados:

<strong>Técnicas:</strong>
• Criptografia em trânsito (TLS 1.3) e em repouso (AES-256)
• Controles de acesso baseados em função (RBAC)
• Autenticação multifator (MFA)
• Monitoramento contínuo de ameaças
• Testes regulares de penetração

<strong>Administrativas:</strong>
• Políticas de segurança da informação
• Treinamento de colaboradores
• Acordos de confidencialidade
• Gestão de incidentes`,
    },
  ];

  const dataTypes = [
    {
      category: 'Dados Pessoais Básicos',
      examples: ['Nome completo', 'CPF', 'E-mail', 'Telefone', 'Endereço'],
      purpose: 'Identificação e comunicação',
    },
    {
      category: 'Dados Profissionais',
      examples: ['Registro profissional', 'Cargo', 'Instituição', 'Especialidade'],
      purpose: 'Verificação de credenciais',
    },
    {
      category: 'Dados de Uso',
      examples: ['Logs de acesso', 'Interações', 'Preferências', 'Configurações'],
      purpose: 'Melhoria da plataforma',
    },
    {
      category: 'Dados Técnicos',
      examples: ['Endereço IP', 'Navegador', 'Dispositivo', 'Sistema operacional'],
      purpose: 'Segurança e diagnóstico',
    },
  ];

  const retentionPeriods = [
    {
      dataType: 'Dados de cadastro',
      period: 'Enquanto a conta estiver ativa + 5 anos',
      legalBasis: 'Cumprimento de obrigações legais',
    },
    {
      dataType: 'Logs de acesso',
      period: '6 meses',
      legalBasis: 'Marco Civil da Internet',
    },
    {
      dataType: 'Dados de comunicação',
      period: '3 anos',
      legalBasis: 'Código Civil',
    },
    {
      dataType: 'Backups',
      period: 'Até 30 dias',
      legalBasis: 'Recuperação de desastres',
    },
  ];

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
            <Scale className="w-8 h-8 text-primary-600" />
          </div>
          <h1 className="text-4xl font-bold text-neutral-900 mb-4">
            LGPD - Lei Geral de Proteção de Dados
          </h1>
          <p className="text-lg text-neutral-600">
            Compromisso com a proteção de dados pessoais
          </p>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.2 }}
          className="bg-gradient-to-r from-primary-600 to-secondary-600 rounded-2xl shadow-lg p-8 mb-8 text-white"
        >
          <p className="text-lg leading-relaxed">
            A IntelliCare está totalmente comprometida com a conformidade à Lei Geral 
            de Proteção de Dados (LGPD). Esta página detalha nossas práticas de 
            tratamento de dados e como garantimos seus direitos como titular.
          </p>
        </motion.div>

        <div className="space-y-6">
          {lgpdSections.map((section, index) => (
            <motion.div
              key={section.title}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5, delay: 0.3 + index * 0.1 }}
              className="bg-white rounded-xl shadow-sm border border-neutral-200 p-6"
            >
              <div className="flex items-start gap-4">
                <div className="flex-shrink-0 w-12 h-12 bg-primary-100 rounded-lg flex items-center justify-center">
                  <section.icon className="w-6 h-6 text-primary-600" />
                </div>
                <div className="flex-grow">
                  <h2 className="text-xl font-bold text-neutral-900 mb-3">
                    {section.title}
                  </h2>
                  <div
                    className="text-neutral-600 leading-relaxed whitespace-pre-line"
                    dangerouslySetInnerHTML={{ __html: section.content }}
                  />
                </div>
              </div>
            </motion.div>
          ))}

          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: 0.7 }}
            className="bg-white rounded-xl shadow-sm border border-neutral-200 p-6"
          >
            <h2 className="text-xl font-bold text-neutral-900 mb-4">
              Tipos de Dados que Tratamos
            </h2>
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="border-b border-neutral-200">
                    <th className="text-left py-3 px-4 font-semibold text-neutral-900">
                      Categoria
                    </th>
                    <th className="text-left py-3 px-4 font-semibold text-neutral-900">
                      Exemplos
                    </th>
                    <th className="text-left py-3 px-4 font-semibold text-neutral-900">
                      Finalidade
                    </th>
                  </tr>
                </thead>
                <tbody>
                  {dataTypes.map((type, index) => (
                    <tr key={index} className="border-b border-neutral-100 last:border-0">
                      <td className="py-3 px-4 text-neutral-900 font-medium">
                        {type.category}
                      </td>
                      <td className="py-3 px-4 text-neutral-600 text-sm">
                        {type.examples.join(', ')}
                      </td>
                      <td className="py-3 px-4 text-neutral-600 text-sm">
                        {type.purpose}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: 0.8 }}
            className="bg-white rounded-xl shadow-sm border border-neutral-200 p-6"
          >
            <h2 className="text-xl font-bold text-neutral-900 mb-4">
              Prazos de Retenção
            </h2>
            <div className="space-y-3">
              {retentionPeriods.map((item, index) => (
                <div
                  key={index}
                  className="flex flex-col sm:flex-row sm:items-center justify-between p-3 bg-neutral-50 rounded-lg"
                >
                  <div>
                    <span className="font-medium text-neutral-900">{item.dataType}</span>
                    <span className="text-neutral-500 text-sm block sm:inline sm:ml-2">
                      ({item.legalBasis})
                    </span>
                  </div>
                  <span className="text-primary-600 font-medium text-sm mt-1 sm:mt-0">
                    {item.period}
                  </span>
                </div>
              ))}
            </div>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: 0.9 }}
            className="bg-white rounded-xl shadow-sm border border-neutral-200 p-6"
          >
            <div className="flex items-start gap-4">
              <div className="flex-shrink-0 w-12 h-12 bg-primary-100 rounded-lg flex items-center justify-center">
                <AlertTriangle className="w-6 h-6 text-primary-600" />
              </div>
              <div>
                <h2 className="text-xl font-bold text-neutral-900 mb-3">
                  Comunicação de Incidentes
                </h2>
                <p className="text-neutral-600 leading-relaxed mb-4">
                  Em caso de incidente de segurança que possa resultar em risco ou dano 
                  relevante aos titulares, comunicaremos:
                </p>
                <ul className="space-y-2 text-neutral-600">
                  <li className="flex items-start gap-2">
                    <span className="text-primary-500">✓</span>
                    <span>A ANPD (Autoridade Nacional de Proteção de Dados) em até 72 horas</span>
                  </li>
                  <li className="flex items-start gap-2">
                    <span className="text-primary-500">✓</span>
                    <span>Os titulares afetados de forma clara e objetiva</span>
                  </li>
                </ul>
              </div>
            </div>
          </motion.div>
        </div>

        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ duration: 0.6, delay: 1 }}
          className="mt-12 bg-primary-50 rounded-xl p-6 border border-primary-100"
        >
          <h3 className="font-bold text-primary-900 mb-2">Exercício de Direitos</h3>
          <p className="text-primary-800 text-sm mb-3">
            Para exercer seus direitos como titular de dados pessoais, entre em contato 
            com nosso Encarregado de Proteção de Dados (DPO):
          </p>
          <div className="space-y-1 text-sm">
            <p className="text-primary-700">
              <strong>E-mail:</strong>{' '}
              <a href="mailto:dpo@intellicare.com.br" className="hover:underline">
                dpo@intellicare.com.br
              </a>
            </p>
            <p className="text-primary-700">
              <strong>Endereço:</strong> Av. Paulista, 1000 - São Paulo/SP
            </p>
            <p className="text-primary-700">
              <strong>ANPD:</strong>{' '}
              <a
                href="https://www.gov.br/anpd"
                target="_blank"
                rel="noopener noreferrer"
                className="hover:underline"
              >
                www.gov.br/anpd
              </a>
            </p>
          </div>
        </motion.div>

        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ duration: 0.6, delay: 1.1 }}
          className="mt-8 text-center text-sm text-neutral-500"
        >
          <p>
            Para mais detalhes, consulte também nossa{' '}
            <a href="/privacidade" className="text-primary-600 hover:underline">
              Política de Privacidade
            </a>{' '}
            e{' '}
            <a href="/termos" className="text-primary-600 hover:underline">
              Termos de Uso
            </a>
            .
          </p>
        </motion.div>
      </div>
    </div>
  );
}
