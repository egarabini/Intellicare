import { motion } from 'framer-motion';
import { Link } from 'react-router-dom';
import { ArrowRight, Sparkles, Brain, Activity } from 'lucide-react';

const HeroSection = () => {
  const containerVariants = {
    hidden: { opacity: 0 },
    visible: {
      opacity: 1,
      transition: {
        staggerChildren: 0.2,
        delayChildren: 0.3,
      },
    },
  };

  const itemVariants = {
    hidden: { opacity: 0, y: 20 },
    visible: {
      opacity: 1,
      y: 0,
      transition: {
        duration: 0.6,
        ease: [0.25, 0.1, 0.25, 1] as const,
      },
    },
  };

  const floatingVariants = {
    initial: { y: 0 },
    animate: {
      y: [-10, 10, -10],
      transition: {
        duration: 4,
        repeat: Infinity,
        ease: [0.4, 0, 0.2, 1] as const,
      },
    },
  };

  return (
    <section className="relative min-h-screen flex items-center justify-center overflow-hidden bg-gradient-to-br from-primary-900 via-primary-800 to-secondary-900">
      <div className="absolute inset-0 bg-[url('/grid.svg')] opacity-10"></div>
      
      <motion.div
        className="absolute top-20 right-20 w-72 h-72 bg-primary-500 rounded-full blur-3xl opacity-20"
        animate={{
          scale: [1, 1.2, 1],
          opacity: [0.2, 0.3, 0.2],
        }}
        transition={{
          duration: 8,
          repeat: Infinity,
          ease: 'easeInOut',
        }}
      />
      
      <motion.div
        className="absolute bottom-20 left-20 w-96 h-96 bg-secondary-500 rounded-full blur-3xl opacity-20"
        animate={{
          scale: [1, 1.3, 1],
          opacity: [0.2, 0.25, 0.2],
        }}
        transition={{
          duration: 10,
          repeat: Infinity,
          ease: 'easeInOut',
        }}
      />

      <div className="container relative z-10">
        <motion.div
          className="max-w-5xl mx-auto text-center"
          variants={containerVariants}
          initial="hidden"
          animate="visible"
        >
          <motion.div
            className="inline-flex items-center space-x-2 bg-white/10 backdrop-blur-sm px-4 py-2 rounded-full mb-8"
            variants={itemVariants}
          >
            <Sparkles className="w-5 h-5 text-accent-400" />
            <span className="text-white font-medium">
              Inovação em Saúde Pública
            </span>
          </motion.div>

          <motion.h1
            className="text-5xl md:text-7xl font-bold text-white mb-6 leading-tight"
            variants={itemVariants}
          >
            Agentes Inteligentes
            <br />
            <span className="text-gradient bg-gradient-to-r from-accent-300 to-accent-500 bg-clip-text text-transparent">
              Transformando a Saúde
            </span>
          </motion.h1>

          <motion.p
            className="text-xl md:text-2xl text-neutral-200 mb-12 max-w-3xl mx-auto"
            variants={itemVariants}
          >
            Plataforma de agentes inteligentes baseados em IA para otimizar
            processos, melhorar a qualidade assistencial e promover o acesso
            universal à saúde pública no Brasil.
          </motion.p>

          <motion.div
            className="flex flex-col sm:flex-row items-center justify-center space-y-4 sm:space-y-0 sm:space-x-6 mb-16"
            variants={itemVariants}
          >
            <Link
              to="/solicitar-secretaria"
              className="group bg-white text-primary-700 hover:bg-accent-400 hover:text-white px-8 py-4 rounded-lg font-semibold text-lg transition-all duration-300 shadow-xl hover:shadow-2xl flex items-center space-x-2"
            >
              <span>Solicitar Acesso</span>
              <ArrowRight className="w-5 h-5 group-hover:translate-x-1 transition-transform" />
            </Link>
            <Link
              to="/agentes"
              className="bg-white/10 backdrop-blur-sm text-white hover:bg-white/20 px-8 py-4 rounded-lg font-semibold text-lg transition-all duration-300 border-2 border-white/30"
            >
              Conhecer Agentes
            </Link>
          </motion.div>

          <motion.div
            className="grid grid-cols-1 md:grid-cols-3 gap-8 max-w-4xl mx-auto"
            variants={containerVariants}
          >
            <motion.div
              className="bg-white/10 backdrop-blur-sm rounded-2xl p-6 border border-white/20"
              variants={itemVariants}
              whileHover={{ scale: 1.05, y: -5 }}
              transition={{ duration: 0.3 }}
            >
              <motion.div
                variants={floatingVariants}
                initial="initial"
                animate="animate"
              >
                <Brain className="w-12 h-12 text-accent-400 mb-4 mx-auto" />
              </motion.div>
              <h3 className="text-2xl font-bold text-white mb-2">5+</h3>
              <p className="text-neutral-200">Agentes Inteligentes</p>
            </motion.div>

            <motion.div
              className="bg-white/10 backdrop-blur-sm rounded-2xl p-6 border border-white/20"
              variants={itemVariants}
              whileHover={{ scale: 1.05, y: -5 }}
              transition={{ duration: 0.3 }}
            >
              <motion.div
                variants={floatingVariants}
                initial="initial"
                animate="animate"
                transition={{ delay: 0.5 }}
              >
                <Activity className="w-12 h-12 text-accent-400 mb-4 mx-auto" />
              </motion.div>
              <h3 className="text-2xl font-bold text-white mb-2">1000+</h3>
              <p className="text-neutral-200">Unidades de Saúde</p>
            </motion.div>

            <motion.div
              className="bg-white/10 backdrop-blur-sm rounded-2xl p-6 border border-white/20"
              variants={itemVariants}
              whileHover={{ scale: 1.05, y: -5 }}
              transition={{ duration: 0.3 }}
            >
              <motion.div
                variants={floatingVariants}
                initial="initial"
                animate="animate"
                transition={{ delay: 1 }}
              >
                <Sparkles className="w-12 h-12 text-accent-400 mb-4 mx-auto" />
              </motion.div>
              <h3 className="text-2xl font-bold text-white mb-2">40%</h3>
              <p className="text-neutral-200">Redução de Custos</p>
            </motion.div>
          </motion.div>
        </motion.div>
      </div>

      <motion.div
        className="absolute bottom-10 left-1/2 transform -translate-x-1/2"
        animate={{
          y: [0, 10, 0],
        }}
        transition={{
          duration: 2,
          repeat: Infinity,
          ease: 'easeInOut',
        }}
      >
        <div className="w-6 h-10 border-2 border-white/50 rounded-full flex items-start justify-center p-2">
          <motion.div
            className="w-1.5 h-1.5 bg-white rounded-full"
            animate={{
              y: [0, 12, 0],
            }}
            transition={{
              duration: 2,
              repeat: Infinity,
              ease: 'easeInOut',
            }}
          />
        </div>
      </motion.div>
    </section>
  );
};

export default HeroSection;
