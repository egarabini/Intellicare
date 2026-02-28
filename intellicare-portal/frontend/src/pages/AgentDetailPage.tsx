import { useParams, Link, Navigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import {
  ArrowLeft,
  ArrowUpRight,
  CheckCircle2,
  Target,
  Zap,
  Database,
  TrendingUp,
} from 'lucide-react';
import { AGENTS } from '@/types';

export default function AgentDetailPage() {
  const { slug } = useParams<{ slug: string }>();
  const agent = AGENTS.find((a) => a.slug === slug);

  if (!agent) {
    return <Navigate to="/agentes" replace />;
  }

  return (
    <div className="min-h-screen bg-gradient-to-b from-neutral-50 to-white py-16">
      <div className="container">
        <motion.div
          initial={{ opacity: 0, x: -20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ duration: 0.5 }}
          className="mb-8"
        >
          <Link
            to="/agentes"
            className="inline-flex items-center gap-2 text-primary-600 hover:text-primary-700 font-semibold transition-colors group"
          >
            <ArrowLeft className="w-5 h-5 group-hover:-translate-x-1 transition-transform" />
            Voltar para Agentes
          </Link>
        </motion.div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6 }}
            className="lg:col-span-2"
          >
            <div className="card">
              <div className="flex items-start gap-6 mb-6">
                {agent.imageUrl ? (
                  <div className="w-20 h-20 rounded-2xl overflow-hidden shadow-xl flex-shrink-0">
                    <img
                      src={agent.imageUrl}
                      alt={agent.name}
                      className="w-full h-full object-cover"
                    />
                  </div>
                ) : (
                  <div className="w-20 h-20 rounded-2xl bg-gradient-to-br from-primary-500 to-secondary-500 flex items-center justify-center text-white text-3xl font-bold shadow-xl flex-shrink-0">
                    {agent.icon}
                  </div>
                )}
                <div className="flex-grow">
                  <span className="inline-block px-3 py-1 bg-accent-100 text-accent-700 rounded-full text-sm font-semibold mb-3">
                    {agent.category}
                  </span>
                  <h1 className="text-4xl font-bold text-neutral-900 mb-2">
                    {agent.name}
                  </h1>
                  <p className="text-xl text-neutral-600 mb-4">{agent.description}</p>
                  {agent.externalLink && (
                    <a
                      href={agent.externalLink}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="inline-flex items-center gap-2 text-primary-600 hover:text-primary-700 font-semibold transition-colors group"
                    >
                      {agent.externalLinkLabel || 'Ver mais informações'}
                      <ArrowUpRight className="w-4 h-4 group-hover:translate-x-0.5 group-hover:-translate-y-0.5 transition-transform" />
                    </a>
                  )}
                </div>
              </div>

              <div className="border-t border-neutral-200 pt-6 mb-6">
                <div className="flex items-center gap-2 mb-4">
                  <Target className="w-6 h-6 text-primary-600" />
                  <h2 className="text-2xl font-bold text-neutral-900">
                    Funcionalidades Principais
                  </h2>
                </div>
                <ul className="space-y-3">
                  {agent.features.map((feature, index) => (
                    <motion.li
                      key={index}
                      initial={{ opacity: 0, x: -20 }}
                      animate={{ opacity: 1, x: 0 }}
                      transition={{ duration: 0.5, delay: index * 0.1 }}
                      className="flex items-start gap-3"
                    >
                      <CheckCircle2 className="w-6 h-6 text-secondary-500 flex-shrink-0 mt-0.5" />
                      <span className="text-neutral-700">{feature}</span>
                    </motion.li>
                  ))}
                </ul>
              </div>

              <div className="border-t border-neutral-200 pt-6">
                <div className="flex items-center gap-2 mb-4">
                  <Zap className="w-6 h-6 text-accent-600" />
                  <h2 className="text-2xl font-bold text-neutral-900">
                    Casos de Uso
                  </h2>
                </div>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {agent.useCases.map((useCase, index) => (
                    <motion.div
                      key={index}
                      initial={{ opacity: 0, scale: 0.95 }}
                      animate={{ opacity: 1, scale: 1 }}
                      transition={{ duration: 0.5, delay: index * 0.1 }}
                      className="bg-gradient-to-br from-neutral-50 to-white p-4 rounded-lg border border-neutral-200"
                    >
                      <h3 className="font-bold text-neutral-900 mb-2">
                        {useCase.title}
                      </h3>
                      <p className="text-sm text-neutral-600">
                        {useCase.description}
                      </p>
                    </motion.div>
                  ))}
                </div>
              </div>
            </div>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.2 }}
            className="space-y-6"
          >
            <div className="card bg-gradient-to-br from-primary-50 to-secondary-50">
              <div className="flex items-center gap-2 mb-4">
                <Database className="w-6 h-6 text-primary-600" />
                <h3 className="text-xl font-bold text-neutral-900">
                  Fontes de Dados
                </h3>
              </div>
              <ul className="space-y-2">
                {agent.dataSources.map((source, index) => (
                  <li
                    key={index}
                    className="flex items-center gap-2 text-neutral-700"
                  >
                    <span className="w-2 h-2 bg-primary-500 rounded-full"></span>
                    {source}
                  </li>
                ))}
              </ul>
            </div>

            <div className="card bg-gradient-to-br from-accent-50 to-secondary-50">
              <div className="flex items-center gap-2 mb-4">
                <TrendingUp className="w-6 h-6 text-accent-600" />
                <h3 className="text-xl font-bold text-neutral-900">
                  Benefícios Esperados
                </h3>
              </div>
              <ul className="space-y-2">
                {agent.benefits.map((benefit, index) => (
                  <li
                    key={index}
                    className="flex items-start gap-2 text-neutral-700"
                  >
                    <CheckCircle2 className="w-5 h-5 text-secondary-500 flex-shrink-0 mt-0.5" />
                    <span className="text-sm">{benefit}</span>
                  </li>
                ))}
              </ul>
            </div>

            <div className="card bg-gradient-to-br from-primary-600 to-secondary-600 text-white">
              <h3 className="text-xl font-bold mb-3">Interessado?</h3>
              <p className="text-primary-50 mb-4">
                Entre em contato para saber mais sobre como este agente pode
                transformar a gestão de saúde na sua região.
              </p>
              <Link
                to="/contato"
                className="inline-block w-full text-center bg-white text-primary-600 font-semibold py-3 px-6 rounded-lg hover:bg-neutral-100 transition-colors"
              >
                Fale Conosco
              </Link>
            </div>
          </motion.div>
        </div>
      </div>
    </div>
  );
}
