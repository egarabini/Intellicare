import { Link } from 'react-router-dom';
import { motion } from 'framer-motion';
import { ArrowRight, Sparkles } from 'lucide-react';
import type { Agent } from '@/types';

interface AgentCardProps {
  agent: Agent;
  index: number;
}

export default function AgentCard({ agent, index }: AgentCardProps) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5, delay: index * 0.1 }}
      className="card group hover:scale-105"
    >
      <div className="flex flex-col h-full">
        <div className="flex items-start justify-between mb-4">
          {agent.imageUrl ? (
            <div className="w-16 h-16 rounded-xl overflow-hidden shadow-lg">
              <img
                src={agent.imageUrl}
                alt={agent.name}
                className="w-full h-full object-cover"
              />
            </div>
          ) : (
            <div className="w-16 h-16 rounded-xl bg-gradient-to-br from-primary-500 to-secondary-500 flex items-center justify-center text-white text-2xl font-bold shadow-lg">
              {agent.icon}
            </div>
          )}
          <span className="px-3 py-1 bg-accent-100 text-accent-700 rounded-full text-sm font-semibold">
            {agent.category}
          </span>
        </div>

        <h3 className="text-2xl font-bold text-neutral-900 mb-2 group-hover:text-primary-600 transition-colors">
          {agent.name}
        </h3>

        <p className="text-neutral-600 mb-4 flex-grow line-clamp-3">
          {agent.description}
        </p>

        <div className="mb-4">
          <div className="flex items-center gap-2 text-sm text-neutral-500 mb-2">
            <Sparkles className="w-4 h-4 text-accent-500" />
            <span className="font-semibold">Principais Funcionalidades:</span>
          </div>
          <ul className="space-y-1">
            {agent.features.slice(0, 3).map((feature, idx) => (
              <li key={idx} className="text-sm text-neutral-600 flex items-start">
                <span className="text-primary-500 mr-2">•</span>
                <span className="line-clamp-1">{feature}</span>
              </li>
            ))}
          </ul>
        </div>

        <Link
          to={`/agentes/${agent.slug}`}
          className="inline-flex items-center gap-2 text-primary-600 font-semibold hover:text-primary-700 transition-colors group/link"
        >
          Saiba mais
          <ArrowRight className="w-4 h-4 group-hover/link:translate-x-1 transition-transform" />
        </Link>
      </div>
    </motion.div>
  );
}
