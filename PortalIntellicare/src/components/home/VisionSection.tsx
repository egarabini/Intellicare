import { motion } from 'framer-motion';
import { useInView } from 'framer-motion';
import { useRef } from 'react';
import { Target, Eye, Lightbulb, Users } from 'lucide-react';

const VisionSection = () => {
  const ref = useRef(null);
  const isInView = useInView(ref, { once: true, margin: '-100px' });

  const containerVariants = {
    hidden: { opacity: 0 },
    visible: {
      opacity: 1,
      transition: {
        staggerChildren: 0.2,
      },
    },
  };

  const itemVariants = {
    hidden: { opacity: 0, y: 30 },
    visible: {
      opacity: 1,
      y: 0,
      transition: {
        duration: 0.6,
        ease: [0.25, 0.1, 0.25, 1] as const,
      },
    },
  };

  const visionItems = [
    {
      icon: Target,
      title: 'Missão',
      description:
        'Democratizar o acesso a tecnologias de IA na saúde pública, promovendo eficiência operacional e melhoria contínua da qualidade assistencial.',
      color: 'primary',
    },
    {
      icon: Eye,
      title: 'Visão',
      description:
        'Ser a principal plataforma de agentes inteligentes para saúde pública no Brasil, transformando a gestão e o cuidado em saúde através da inovação tecnológica.',
      color: 'secondary',
    },
    {
      icon: Lightbulb,
      title: 'Inovação',
      description:
        'Desenvolver soluções baseadas em IA que resolvam problemas reais da saúde pública, com foco em resultados mensuráveis e impacto social positivo.',
      color: 'accent',
    },
    {
      icon: Users,
      title: 'Valores',
      description:
        'Compromisso com a ética, transparência, inclusão e excelência técnica, sempre priorizando o bem-estar dos pacientes e profissionais de saúde.',
      color: 'success',
    },
  ];

  const colorMap = {
    primary: 'from-primary-500 to-primary-700',
    secondary: 'from-secondary-500 to-secondary-700',
    accent: 'from-accent-500 to-accent-700',
    success: 'from-success-500 to-success-700',
  };

  return (
    <section ref={ref} className="py-24 bg-neutral-50">
      <div className="container">
        <motion.div
          className="text-center mb-16"
          initial={{ opacity: 0, y: 20 }}
          animate={isInView ? { opacity: 1, y: 0 } : {}}
          transition={{ duration: 0.6 }}
        >
          <h2 className="section-title">Nossa Visão</h2>
          <p className="section-subtitle max-w-3xl mx-auto">
            Transformar a saúde pública brasileira através de agentes
            inteligentes que promovem eficiência, qualidade e acesso universal
            aos serviços de saúde.
          </p>
        </motion.div>

        <motion.div
          className="grid grid-cols-1 md:grid-cols-2 gap-8"
          variants={containerVariants}
          initial="hidden"
          animate={isInView ? 'visible' : 'hidden'}
        >
          {visionItems.map((item) => (
            <motion.div
              key={item.title}
              className="card group hover:shadow-2xl"
              variants={itemVariants}
              whileHover={{ y: -8 }}
              transition={{ duration: 0.3 }}
            >
              <div
                className={`w-16 h-16 rounded-xl bg-gradient-to-br ${
                  colorMap[item.color as keyof typeof colorMap]
                } flex items-center justify-center mb-6 group-hover:scale-110 transition-transform duration-300`}
              >
                <item.icon className="w-8 h-8 text-white" />
              </div>
              <h3 className="text-2xl font-bold text-neutral-900 mb-4">
                {item.title}
              </h3>
              <p className="text-neutral-600 leading-relaxed">
                {item.description}
              </p>
            </motion.div>
          ))}
        </motion.div>
      </div>
    </section>
  );
};

export default VisionSection;
