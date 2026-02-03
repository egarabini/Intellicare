import { motion, useInView, useMotionValue, useSpring } from 'framer-motion';
import { useRef, useEffect } from 'react';
import { TrendingUp, Users, Building2, Award } from 'lucide-react';

interface CounterProps {
  value: number;
  duration?: number;
  suffix?: string;
  prefix?: string;
}

const Counter = ({ value, suffix = '', prefix = '' }: CounterProps) => {
  const ref = useRef<HTMLSpanElement>(null);
  const motionValue = useMotionValue(0);
  const springValue = useSpring(motionValue, {
    damping: 60,
    stiffness: 100,
  });
  const isInView = useInView(ref, { once: true, margin: '-100px' });

  useEffect(() => {
    if (isInView) {
      motionValue.set(value);
    }
  }, [motionValue, isInView, value]);

  useEffect(() => {
    springValue.on('change', (latest) => {
      if (ref.current) {
        ref.current.textContent = `${prefix}${Math.floor(latest).toLocaleString('pt-BR')}${suffix}`;
      }
    });
  }, [springValue, prefix, suffix]);

  return <span ref={ref}>{prefix}0{suffix}</span>;
};

const ImpactNumbers = () => {
  const ref = useRef(null);
  const isInView = useInView(ref, { once: true, margin: '-100px' });

  const stats = [
    {
      icon: Users,
      value: 2500000,
      suffix: '+',
      label: 'Pacientes Atendidos',
      description: 'Através dos agentes inteligentes',
      color: 'primary',
    },
    {
      icon: Building2,
      value: 1200,
      suffix: '+',
      label: 'Unidades de Saúde',
      description: 'Utilizando a plataforma',
      color: 'secondary',
    },
    {
      icon: TrendingUp,
      value: 40,
      suffix: '%',
      label: 'Redução de Custos',
      description: 'Em processos operacionais',
      color: 'success',
    },
    {
      icon: Award,
      value: 95,
      suffix: '%',
      label: 'Satisfação',
      description: 'Dos profissionais de saúde',
      color: 'accent',
    },
  ];

  const colorMap = {
    primary: {
      bg: 'bg-primary-50',
      icon: 'text-primary-600',
      gradient: 'from-primary-500 to-primary-700',
    },
    secondary: {
      bg: 'bg-secondary-50',
      icon: 'text-secondary-600',
      gradient: 'from-secondary-500 to-secondary-700',
    },
    success: {
      bg: 'bg-success-50',
      icon: 'text-success-600',
      gradient: 'from-success-500 to-success-700',
    },
    accent: {
      bg: 'bg-accent-50',
      icon: 'text-accent-600',
      gradient: 'from-accent-500 to-accent-700',
    },
  };

  return (
    <section ref={ref} className="py-24 bg-white">
      <div className="container">
        <motion.div
          className="text-center mb-16"
          initial={{ opacity: 0, y: 20 }}
          animate={isInView ? { opacity: 1, y: 0 } : {}}
          transition={{ duration: 0.6 }}
        >
          <h2 className="section-title">Impacto Real</h2>
          <p className="section-subtitle max-w-3xl mx-auto">
            Números que demonstram o impacto positivo dos agentes inteligentes
            na saúde pública brasileira.
          </p>
        </motion.div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-8">
          {stats.map((stat, index) => {
            const colors = colorMap[stat.color as keyof typeof colorMap];
            return (
              <motion.div
                key={stat.label}
                className="relative group"
                initial={{ opacity: 0, y: 30 }}
                animate={isInView ? { opacity: 1, y: 0 } : {}}
                transition={{ duration: 0.6, delay: index * 0.1 }}
              >
                <div className="card text-center h-full">
                  <div
                    className={`w-16 h-16 ${colors.bg} rounded-xl flex items-center justify-center mx-auto mb-6 group-hover:scale-110 transition-transform duration-300`}
                  >
                    <stat.icon className={`w-8 h-8 ${colors.icon}`} />
                  </div>
                  <div className="text-5xl font-bold text-neutral-900 mb-2">
                    <Counter
                      value={stat.value}
                      suffix={stat.suffix}
                      duration={2.5}
                    />
                  </div>
                  <h3 className="text-xl font-semibold text-neutral-800 mb-2">
                    {stat.label}
                  </h3>
                  <p className="text-neutral-600 text-sm">
                    {stat.description}
                  </p>
                </div>
                <motion.div
                  className={`absolute inset-0 bg-gradient-to-br ${colors.gradient} rounded-xl opacity-0 group-hover:opacity-5 transition-opacity duration-300 -z-10`}
                  initial={false}
                />
              </motion.div>
            );
          })}
        </div>

        <motion.div
          className="mt-16 text-center"
          initial={{ opacity: 0 }}
          animate={isInView ? { opacity: 1 } : {}}
          transition={{ duration: 0.6, delay: 0.8 }}
        >
          <p className="text-neutral-600 text-lg">
            Dados atualizados em tempo real através de nossa plataforma de
            monitoramento
          </p>
        </motion.div>
      </div>
    </section>
  );
};

export default ImpactNumbers;
