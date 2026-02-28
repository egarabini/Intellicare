import { motion } from 'framer-motion';
import { Shield, Eye, Lock, Database, UserCheck, Share2 } from 'lucide-react';

export default function PrivacidadePage() {
  const mainSections = [
    {
      icon: Eye,
      title: '1. Informações que Coletamos',
      content: `Coletamos informações necessárias para fornecer nossos serviços de saúde:

• Dados de cadastro: nome, e-mail, telefone, CPF, profissão e registro profissional
• Dados institucionais: unidade de saúde, CNPJ, cargo e função
• Dados de uso: logs de acesso, interações com os agentes de IA, preferências
• Dados técnicos: endereço IP, tipo de navegador, dispositivo utilizado

NÃO coletamos dados sensíveis de saúde de pacientes sem autorização explícita e adequada.`,
    },
    {
      icon: Database,
      title: '2. Como Usamos suas Informações',
      content: `Utilizamos seus dados para:

• Fornecer e melhorar nossos serviços de agentes inteligentes
• Personalizar a experiência do usuário na plataforma
• Enviar comunicações sobre atualizações e novidades
• Analisar padrões de uso para melhorias na plataforma
• Cumprir obrigações legais e regulatórias
• Prevenir fraudes e garantir a segurança da plataforma`,
    },
    {
      icon: Lock,
      title: '3. Segurança dos Dados',
      content: `Implementamos medidas rigorosas de segurança:

• Criptografia SSL/TLS para todas as transmissões de dados
• Armazenamento criptografado em servidores seguros
• Controles de acesso baseados em função e necessidade
• Monitoramento contínuo de ameaças e vulnerabilidades
• Backups regulares e planos de recuperação de desastres
• Treinamento de equipe em práticas de segurança`,
    },
    {
      icon: Share2,
      title: '4. Compartilhamento de Dados',
      content: `Seus dados podem ser compartilhados com:

• Prestadores de serviços essenciais (hospedagem, processamento de dados)
• Autoridades competentes quando legalmente exigido
• Parceiros de pesquisa (dados anonimizados apenas)

NÃO vendemos seus dados pessoais a terceiros. Qualquer compartilhamento é feito com garantias contratuais de proteção.`,
    },
  ];

  const rights = [
    {
      title: 'Acesso',
      description: 'Solicitar cópia dos seus dados pessoais que possuímos',
    },
    {
      title: 'Correção',
      description: 'Corrigir dados incompletos, inexatos ou desatualizados',
    },
    {
      title: 'Exclusão',
      description: 'Solicitar a eliminação dos seus dados em determinadas situações',
    },
    {
      title: 'Portabilidade',
      description: 'Receber seus dados em formato estruturado e de uso comum',
    },
    {
      title: 'Revogação',
      description: 'Revogar consentimento a qualquer momento',
    },
    {
      title: 'Oposição',
      description: 'Opor-se ao tratamento de dados em determinadas hipóteses',
    },
  ];

  const additionalInfo = [
    {
      title: 'Retenção de Dados',
      content: 'Mantemos seus dados apenas pelo tempo necessário para cumprir as finalidades descritas nesta política ou conforme exigido por lei. Dados de cadastro são mantidos enquanto sua conta estiver ativa.',
    },
    {
      title: 'Cookies e Tecnologias Similares',
      content: 'Utilizamos cookies para melhorar sua experiência, analisar o tráfego e personalizar conteúdo. Você pode gerenciar suas preferências de cookies através das configurações do navegador ou da nossa Central de Cookies.',
    },
    {
      title: 'Transferência Internacional',
      content: 'Seus dados são processados principalmente no Brasil. Em casos específicos de transferência internacional, garantimos proteção adequada conforme a LGPD.',
    },
    {
      title: 'Alterações na Política',
      content: 'Podemos atualizar esta política periodicamente. Notificaremos sobre alterações significativas através do e-mail cadastrado ou na própria plataforma.',
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
            <Shield className="w-8 h-8 text-primary-600" />
          </div>
          <h1 className="text-4xl font-bold text-neutral-900 mb-4">
            Política de Privacidade
          </h1>
          <p className="text-lg text-neutral-600">
            Última atualização: {new Date().toLocaleDateString('pt-BR')}
          </p>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.2 }}
          className="bg-white rounded-2xl shadow-sm border border-neutral-200 p-8 mb-8"
        >
          <p className="text-neutral-600 leading-relaxed">
            A IntelliCare valoriza sua privacidade e está comprometida em proteger 
            seus dados pessoais. Esta Política de Privacidade descreve como coletamos, 
            usamos, armazenamos e protegemos suas informações em conformidade com a 
            <strong> Lei Geral de Proteção de Dados (LGPD)</strong> e outras regulamentações 
            aplicáveis.
          </p>
        </motion.div>

        <div className="space-y-6">
          {mainSections.map((section, index) => (
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
                  <div className="text-neutral-600 leading-relaxed whitespace-pre-line">
                    {section.content}
                  </div>
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
            <div className="flex items-start gap-4 mb-6">
              <div className="flex-shrink-0 w-12 h-12 bg-primary-100 rounded-lg flex items-center justify-center">
                <UserCheck className="w-6 h-6 text-primary-600" />
              </div>
              <div className="flex-grow">
                <h2 className="text-xl font-bold text-neutral-900 mb-3">
                  5. Seus Direitos (LGPD)
                </h2>
                <p className="text-neutral-600 leading-relaxed mb-4">
                  De acordo com a Lei Geral de Proteção de Dados, você tem os seguintes direitos:
                </p>
              </div>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {rights.map((right) => (
                <div
                  key={right.title}
                  className="bg-neutral-50 rounded-lg p-4 border border-neutral-100"
                >
                  <h3 className="font-semibold text-neutral-900 mb-1">
                    {right.title}
                  </h3>
                  <p className="text-sm text-neutral-600">{right.description}</p>
                </div>
              ))}
            </div>
            <p className="text-neutral-600 mt-4 text-sm">
              Para exercer seus direitos, envie uma solicitação para:{' '}
              <a
                href="mailto:privacidade@intellicare.com.br"
                className="text-primary-600 hover:underline"
              >
                privacidade@intellicare.com.br
              </a>
            </p>
          </motion.div>

          {additionalInfo.map((info, index) => (
            <motion.div
              key={info.title}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5, delay: 0.8 + index * 0.1 }}
              className="bg-white rounded-xl shadow-sm border border-neutral-200 p-6"
            >
              <h2 className="text-xl font-bold text-neutral-900 mb-3">
                {index + 6}. {info.title}
              </h2>
              <p className="text-neutral-600 leading-relaxed">
                {info.content}
              </p>
            </motion.div>
          ))}
        </div>

        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ duration: 0.6, delay: 1.2 }}
          className="mt-12 bg-primary-50 rounded-xl p-6 border border-primary-100"
        >
          <h3 className="font-bold text-primary-900 mb-2">Contato do DPO</h3>
          <p className="text-primary-800 text-sm mb-2">
            Nosso Encarregado de Proteção de Dados (DPO) está à disposição para 
            esclarecer dúvidas sobre esta política:
          </p>
          <p className="text-primary-700 text-sm">
            E-mail:{' '}
            <a
              href="mailto:dpo@intellicare.com.br"
              className="font-semibold hover:underline"
            >
              dpo@intellicare.com.br
            </a>
          </p>
        </motion.div>
      </div>
    </div>
  );
}
