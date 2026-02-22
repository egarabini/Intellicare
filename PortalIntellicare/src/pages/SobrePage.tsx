import { motion } from 'framer-motion';
import {
  Lightbulb,
  Target,
  Heart,
  Users,
  Shield,
  Zap,
  Globe,
  Award,
  Clock,
  TrendingUp,
  CheckCircle2,
  ArrowRight,
} from 'lucide-react';
import { Card, CardContent } from '@/components/ui/card';
import { Button } from '@components/ui/button';

const fadeInUp = {
  initial: { opacity: 0, y: 20 },
  animate: { opacity: 1, y: 0 },
  transition: { duration: 0.5 },
};

const staggerContainer = {
  animate: {
    transition: {
      staggerChildren: 0.1,
    },
  },
};

const valores = [
  {
    icon: Heart,
    title: 'Cuidado Centrado no Paciente',
    description:
      'Colocamos o paciente no centro de todas as decisões, garantindo atenção integral e humanizada.',
  },
  {
    icon: Shield,
    title: 'Segurança e Privacidade',
    description:
      'Protegemos os dados dos pacientes com os mais altos padrões de segurança e conformidade com a LGPD.',
  },
  {
    icon: Zap,
    title: 'Inovação Constante',
    description:
      'Utilizamos tecnologia de ponta, incluindo Inteligência Artificial, para transformar a saúde pública.',
  },
  {
    icon: Users,
    title: 'Colaboração',
    description:
      'Promovemos a integração entre profissionais de saúde, gestores e pacientes para um cuidado coordenado.',
  },
];

const diferenciais = [
  {
    icon: Globe,
    title: 'Cobertura Nacional',
    description: 'Presente em todos os estados brasileiros, atendendo milhares de unidades de saúde.',
  },
  {
    icon: Award,
    title: 'Reconhecimento',
    description: 'Premiado como uma das melhores soluções de saúde digital do país.',
  },
  {
    icon: Clock,
    title: 'Disponibilidade 24/7',
    description: 'Sistema sempre disponível para garantir o cuidado contínuo dos pacientes.',
  },
  {
    icon: TrendingUp,
    title: 'Resultados Comprovados',
    description: 'Redução de 30% em internações evitáveis e aumento de 45% na adesão ao tratamento.',
  },
];

const tecnologias = [
  'Inteligência Artificial',
  'Machine Learning',
  'Processamento de Linguagem Natural',
  'Análise Preditiva',
  'Interoperabilidade FHIR',
  'Cloud Computing',
  'Big Data',
  'Mobile First',
];

export default function SobrePage() {
  return (
    <div className="min-h-screen bg-gray-50">
      <div className="bg-gradient-to-r from-primary-600 to-primary-800 py-16">
        <div className="container mx-auto px-4">
          <motion.div {...fadeInUp}>
            <h1 className="text-4xl md:text-5xl font-bold text-white mb-4">Sobre o INTELLICARE</h1>
            <p className="text-xl text-white/90 max-w-3xl">
              Revolucionando o cuidado em saúde através da tecnologia e da inteligência artificial.
            </p>
          </motion.div>
        </div>
      </div>

      <div className="container mx-auto px-4 py-16">
        <motion.div
          initial="initial"
          whileInView="animate"
          viewport={{ once: true }}
          variants={staggerContainer}
          className="space-y-20"
        >
          <section>
            <motion.div variants={fadeInUp} className="max-w-4xl mx-auto text-center mb-12">
              <h2 className="text-3xl font-bold text-gray-900 mb-6">Nossa História</h2>
              <p className="text-lg text-gray-600 leading-relaxed">
                O INTELLICARE nasceu da consolidação de seis projetos de prova de conceito (POC)
                desenvolvidos ao longo de vários anos de pesquisa e inovação em saúde pública.
                Cada projeto trouxe aprendizados valiosos que foram integrados em uma plataforma
                completa e robusta.
              </p>
              <p className="text-lg text-gray-600 leading-relaxed mt-4">
                Nossa missão é transformar a forma como a saúde é entregue no Brasil, utilizando
                tecnologia de ponta para melhorar o acesso, a qualidade e a eficiência do cuidado.
                Acreditamos que todos merecem acesso a uma saúde de qualidade, e trabalhamos
                incansavelmente para tornar isso realidade.
              </p>
            </motion.div>
          </section>

          <section>
            <motion.div variants={fadeInUp} className="text-center mb-12">
              <h2 className="text-3xl font-bold text-gray-900 mb-4">Nossa Missão, Visão e Valores</h2>
            </motion.div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-8 mb-16">
              <motion.div variants={fadeInUp}>
                <Card className="h-full">
                  <CardContent className="pt-6">
                    <div className="w-12 h-12 bg-primary-100 rounded-lg flex items-center justify-center mb-4">
                      <Target className="h-6 w-6 text-primary-600" />
                    </div>
                    <h3 className="text-xl font-bold text-gray-900 mb-3">Missão</h3>
                    <p className="text-gray-600">
                      Transformar a saúde pública brasileira através da tecnologia, promovendo
                      cuidado centrado no paciente, coordenação efetiva e gestão baseada em dados.
                    </p>
                  </CardContent>
                </Card>
              </motion.div>

              <motion.div variants={fadeInUp}>
                <Card className="h-full">
                  <CardContent className="pt-6">
                    <div className="w-12 h-12 bg-primary-100 rounded-lg flex items-center justify-center mb-4">
                      <Lightbulb className="h-6 w-6 text-primary-600" />
                    </div>
                    <h3 className="text-xl font-bold text-gray-900 mb-3">Visão</h3>
                    <p className="text-gray-600">
                      Ser a plataforma de referência em saúde pública no Brasil, reconhecida pela
                      inovação, qualidade do cuidado e impacto positivo na vida dos brasileiros.
                    </p>
                  </CardContent>
                </Card>
              </motion.div>

              <motion.div variants={fadeInUp}>
                <Card className="h-full">
                  <CardContent className="pt-6">
                    <div className="w-12 h-12 bg-primary-100 rounded-lg flex items-center justify-center mb-4">
                      <Heart className="h-6 w-6 text-primary-600" />
                    </div>
                    <h3 className="text-xl font-bold text-gray-900 mb-3">Propósito</h3>
                    <p className="text-gray-600">
                      Democratizar o acesso à saúde de qualidade, empoderando pacientes,
                      profissionais e gestores com ferramentas inteligentes e dados relevantes.
                    </p>
                  </CardContent>
                </Card>
              </motion.div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
              {valores.map((valor, index) => (
                <motion.div key={index} variants={fadeInUp}>
                  <Card className="h-full">
                    <CardContent className="pt-6">
                      <valor.icon className="h-8 w-8 text-primary-600 mb-4" />
                      <h3 className="text-lg font-bold text-gray-900 mb-2">{valor.title}</h3>
                      <p className="text-gray-600 text-sm">{valor.description}</p>
                    </CardContent>
                  </Card>
                </motion.div>
              ))}
            </div>
          </section>

          <section>
            <motion.div variants={fadeInUp} className="text-center mb-12">
              <h2 className="text-3xl font-bold text-gray-900 mb-4">Nossos Diferenciais</h2>
              <p className="text-lg text-gray-600 max-w-2xl mx-auto">
                O que nos torna únicos no cenário da saúde digital brasileira.
              </p>
            </motion.div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {diferenciais.map((diferencial, index) => (
                <motion.div key={index} variants={fadeInUp}>
                  <Card>
                    <CardContent className="pt-6 flex gap-4">
                      <div className="w-12 h-12 bg-primary-100 rounded-lg flex items-center justify-center flex-shrink-0">
                        <diferencial.icon className="h-6 w-6 text-primary-600" />
                      </div>
                      <div>
                        <h3 className="text-lg font-bold text-gray-900 mb-2">{diferencial.title}</h3>
                        <p className="text-gray-600">{diferencial.description}</p>
                      </div>
                    </CardContent>
                  </Card>
                </motion.div>
              ))}
            </div>
          </section>

          <section>
            <motion.div variants={fadeInUp} className="text-center mb-12">
              <h2 className="text-3xl font-bold text-gray-900 mb-4">Tecnologias Utilizadas</h2>
              <p className="text-lg text-gray-600 max-w-2xl mx-auto">
                Stack tecnológica moderna e robusta para garantir performance e escalabilidade.
              </p>
            </motion.div>

            <motion.div
              variants={fadeInUp}
              className="grid grid-cols-2 md:grid-cols-4 gap-4"
            >
              {tecnologias.map((tech, index) => (
                <div
                  key={index}
                  className="bg-white rounded-lg p-4 shadow-sm border border-gray-200 flex items-center gap-3"
                >
                  <CheckCircle2 className="h-5 w-5 text-primary-600 flex-shrink-0" />
                  <span className="font-medium text-gray-900">{tech}</span>
                </div>
              ))}
            </motion.div>
          </section>

          <section>
            <motion.div variants={fadeInUp} className="text-center mb-12">
              <h2 className="text-3xl font-bold text-gray-900 mb-4">Nossos Agentes de IA</h2>
              <p className="text-lg text-gray-600 max-w-2xl mx-auto">
                Três assistentes virtuais inteligentes que revolucionam o cuidado em saúde.
              </p>
            </motion.div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
              <motion.div variants={fadeInUp}>
                <Card className="h-full border-t-4 border-t-green-500">
                  <CardContent className="pt-6">
                    <h3 className="text-2xl font-bold text-gray-900 mb-2">Geralda</h3>
                    <p className="text-green-600 font-medium mb-4">Apoio ao Paciente</p>
                    <p className="text-gray-600 mb-4">
                      Assistente virtual que apoia pacientes no gerenciamento de sua saúde,
                      oferecendo lembretes de medicamentos, dicas de saúde e suporte emocional.
                    </p>
                    <ul className="space-y-2">
                      <li className="flex items-center gap-2 text-sm text-gray-600">
                        <CheckCircle2 className="h-4 w-4 text-green-500" />
                        Lembretes personalizados
                      </li>
                      <li className="flex items-center gap-2 text-sm text-gray-600">
                        <CheckCircle2 className="h-4 w-4 text-green-500" />
                        Educação em saúde
                      </li>
                      <li className="flex items-center gap-2 text-sm text-gray-600">
                        <CheckCircle2 className="h-4 w-4 text-green-500" />
                        Suporte 24/7
                      </li>
                    </ul>
                  </CardContent>
                </Card>
              </motion.div>

              <motion.div variants={fadeInUp}>
                <Card className="h-full border-t-4 border-t-blue-500">
                  <CardContent className="pt-6">
                    <h3 className="text-2xl font-bold text-gray-900 mb-2">Wanda</h3>
                    <p className="text-blue-600 font-medium mb-4">Apoio à Enfermagem</p>
                    <p className="text-gray-600 mb-4">
                      Assistente para profissionais de enfermagem, auxiliando na coordenação do
                      cuidado, priorização de atendimentos e decisões clínicas.
                    </p>
                    <ul className="space-y-2">
                      <li className="flex items-center gap-2 text-sm text-gray-600">
                        <CheckCircle2 className="h-4 w-4 text-blue-500" />
                        Coordenação do cuidado
                      </li>
                      <li className="flex items-center gap-2 text-sm text-gray-600">
                        <CheckCircle2 className="h-4 w-4 text-blue-500" />
                        Raciocínio clínico
                      </li>
                      <li className="flex items-center gap-2 text-sm text-gray-600">
                        <CheckCircle2 className="h-4 w-4 text-blue-500" />
                        Alertas inteligentes
                      </li>
                    </ul>
                  </CardContent>
                </Card>
              </motion.div>

              <motion.div variants={fadeInUp}>
                <Card className="h-full border-t-4 border-t-orange-500">
                  <CardContent className="pt-6">
                    <h3 className="text-2xl font-bold text-gray-900 mb-2">Donabedian</h3>
                    <p className="text-orange-600 font-medium mb-4">Apoio à Gestão</p>
                    <p className="text-gray-600 mb-4">
                      Assistente para gestores de saúde, fornecendo análises, relatórios e
                      recomendações baseadas em dados para melhorar a qualidade da assistência.
                    </p>
                    <ul className="space-y-2">
                      <li className="flex items-center gap-2 text-sm text-gray-600">
                        <CheckCircle2 className="h-4 w-4 text-orange-500" />
                        Análise de indicadores
                      </li>
                      <li className="flex items-center gap-2 text-sm text-gray-600">
                        <CheckCircle2 className="h-4 w-4 text-orange-500" />
                        Relatórios automáticos
                      </li>
                      <li className="flex items-center gap-2 text-sm text-gray-600">
                        <CheckCircle2 className="h-4 w-4 text-orange-500" />
                        Meta Quádrupla
                      </li>
                    </ul>
                  </CardContent>
                </Card>
              </motion.div>
            </div>
          </section>

          <section className="bg-primary-600 rounded-2xl p-8 md:p-12 text-center">
            <motion.div variants={fadeInUp}>
              <h2 className="text-3xl font-bold text-white mb-4">
                Pronto para transformar a saúde da sua região?
              </h2>
              <p className="text-xl text-white/90 mb-8 max-w-2xl mx-auto">
                Junte-se a centenas de secretarias e unidades de saúde que já estão revolucionando
                o cuidado com o INTELLICARE.
              </p>
              <Button size="lg" variant="secondary" className="group">
                Solicitar Participação
                <ArrowRight className="ml-2 h-4 w-4 group-hover:translate-x-1 transition-transform" />
              </Button>
            </motion.div>
          </section>
        </motion.div>
      </div>
    </div>
  );
}
