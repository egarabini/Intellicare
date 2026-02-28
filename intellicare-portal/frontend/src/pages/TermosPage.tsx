import { motion } from 'framer-motion';
import { Scale, FileText, AlertCircle, CheckCircle } from 'lucide-react';

export default function TermosPage() {
  const sections = [
    {
      icon: FileText,
      title: '1. Aceitação dos Termos',
      content: `Ao acessar e utilizar a plataforma IntelliCare, você concorda em cumprir e estar vinculado a estes Termos de Uso. Se você não concordar com qualquer parte destes termos, não deverá usar nossos serviços. Estes termos se aplicam a todos os usuários da plataforma, incluindo gestores de saúde, profissionais de saúde e pacientes.`,
    },
    {
      icon: AlertCircle,
      title: '2. Uso da Plataforma',
      content: `A IntelliCare é uma plataforma de apoio à decisão em saúde que utiliza inteligência artificial para auxiliar profissionais de saúde. O uso da plataforma é destinado exclusivamente para fins profissionais e educacionais na área da saúde. É proibido:

• Usar a plataforma para fins ilegais ou não autorizados
• Tentar acessar áreas restritas sem autorização
• Interferir ou interromper o funcionamento da plataforma
• Copiar, modificar ou distribuir conteúdo sem permissão
• Usar a plataforma para fornecer diagnósticos médicos definitivos sem supervisão profissional`,
    },
    {
      icon: CheckCircle,
      title: '3. Responsabilidades do Usuário',
      content: `Os usuários são responsáveis por:

• Fornecer informações verdadeiras e atualizadas
• Manter a confidencialidade de suas credenciais de acesso
• Usar a plataforma de acordo com as leis e regulamentações de saúde aplicáveis
• Não compartilhar dados de pacientes sem autorização adequada
• Reportar qualquer problema de segurança ou funcionamento`,
    },
    {
      icon: Scale,
      title: '4. Limitação de Responsabilidade',
      content: `A IntelliCare é uma ferramenta de apoio à decisão e não substitui o julgamento clínico de profissionais de saúde qualificados. Os agentes de IA fornecem recomendações baseadas em dados, mas as decisões finais de tratamento devem sempre ser tomadas por profissionais de saúde competentes.

A plataforma não se responsabiliza por:
• Decisões médicas tomadas com base nas recomendações dos agentes
• Danos diretos ou indiretos resultantes do uso da plataforma
• Interrupções temporárias do serviço por manutenção ou falhas técnicas
• Ações de terceiros que possam afetar o funcionamento da plataforma`,
    },
  ];

  const additionalTerms = [
    {
      title: '5. Propriedade Intelectual',
      content: 'Todo o conteúdo da plataforma, incluindo software, algoritmos, interfaces, textos, gráficos e logotipos, é propriedade da IntelliCare ou de seus licenciadores e está protegido por leis de direitos autorais e propriedade intelectual.',
    },
    {
      title: '6. Privacidade e Dados',
      content: 'O uso da plataforma está sujeito à nossa Política de Privacidade, que descreve como coletamos, usamos e protegemos suas informações pessoais e dados de saúde em conformidade com a LGPD e outras regulamentações aplicáveis.',
    },
    {
      title: '7. Modificações dos Termos',
      content: 'Reservamo-nos o direito de modificar estes termos a qualquer momento. As alterações entrarão em vigor imediatamente após a publicação na plataforma. O uso continuado da plataforma após as modificações constitui aceitação dos novos termos.',
    },
    {
      title: '8. Rescisão',
      content: 'Podemos suspender ou encerrar seu acesso à plataforma a qualquer momento, sem aviso prévio, por violação destes termos ou por qualquer outro motivo que consideremos apropriado.',
    },
    {
      title: '9. Lei Aplicável',
      content: 'Estes termos são regidos pelas leis da República Federativa do Brasil. Qualquer disputa será resolvida nos tribunais competentes do estado de São Paulo.',
    },
    {
      title: '10. Contato',
      content: 'Para dúvidas sobre estes termos, entre em contato através do e-mail: juridico@intellicare.com.br',
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
            Termos de Uso
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
          <p className="text-neutral-600 leading-relaxed mb-6">
            Bem-vindo à IntelliCare. Estes Termos de Uso estabelecem as regras e diretrizes 
            para o uso da nossa plataforma de agentes inteligentes em saúde. Ao utilizar 
            nossos serviços, você concorda com estes termos. Leia-os atentamente.
          </p>
        </motion.div>

        <div className="space-y-6">
          {sections.map((section, index) => (
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

          {additionalTerms.map((term, index) => (
            <motion.div
              key={term.title}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5, delay: 0.7 + index * 0.1 }}
              className="bg-white rounded-xl shadow-sm border border-neutral-200 p-6"
            >
              <h2 className="text-xl font-bold text-neutral-900 mb-3">
                {term.title}
              </h2>
              <p className="text-neutral-600 leading-relaxed">
                {term.content}
              </p>
            </motion.div>
          ))}
        </div>

        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ duration: 0.6, delay: 1.3 }}
          className="mt-12 text-center"
        >
          <p className="text-sm text-neutral-500">
            Ao utilizar a plataforma IntelliCare, você confirma que leu, entendeu 
            e concorda com estes Termos de Uso.
          </p>
        </motion.div>
      </div>
    </div>
  );
}
