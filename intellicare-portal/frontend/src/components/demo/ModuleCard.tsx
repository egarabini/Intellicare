import { Activity, Radio, Cpu, Database, Eye, MessageSquare, Share2, ShieldCheck, Stethoscope, Flame, FileText, BarChart } from 'lucide-react';
import clsx from 'clsx';
import { useNavigate } from 'react-router-dom';

export type ModuleStatus = 'active' | 'standby' | 'offline' | 'connecting';

export interface ModuleProps {
  id: string;
  name: string;
  description: string;
  status: ModuleStatus;
  latency?: number;
  icon: 'pierre' | 'minerva' | 'oswaldo' | 'florence' | 'comunicacao' | 'nise' | 'zilda' | 'geralda' | 'grahame' | 'wanda' | 'donabedian' | 'hippocrates';
  route?: string;
}
import { motion } from 'framer-motion';

const statusColors = {
  active: 'bg-emerald-500/10 border-emerald-500/50 text-emerald-400',
  standby: 'bg-amber-500/10 border-amber-500/50 text-amber-400',
  offline: 'bg-slate-800/50 border-slate-700 text-slate-500',
  connecting: 'bg-blue-500/10 border-blue-500/50 text-blue-400',
};

const statusDotColors = {
  active: 'bg-emerald-400',
  standby: 'bg-amber-400',
  offline: 'bg-slate-500',
  connecting: 'bg-blue-400',
};

const iconMap = {
  pierre: Cpu,
  minerva: Eye,
  oswaldo: Activity,
  florence: Stethoscope,
  comunicacao: MessageSquare,
  nise: Share2,
  zilda: Database,
  geralda: ShieldCheck,
  grahame: Flame,
  wanda: FileText,
  donabedian: BarChart,
  hippocrates: MessageSquare,
};

export const ModuleCard = ({ name, description, status, latency, icon, route }: ModuleProps) => {
  const Icon = iconMap[icon];
  const navigate = useNavigate();

  const handleClick = () => {
    if (route) {
      navigate(route);
    }
  };

  return (
    <motion.div
      whileHover={{ scale: 1.02, boxShadow: '0 0 20px rgba(0,0,0,0.2)' }}
      whileTap={{ scale: 0.98 }}
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      onClick={handleClick}
      className={clsx(
        'relative overflow-hidden rounded-xl border p-6 transition-all duration-300 cursor-pointer backdrop-blur-md',
        statusColors[status],
        route ? 'hover:border-primary-400/80' : 'cursor-default'
      )}
    >
      {/* Background Pulse Effect for Active Modules */}
      {status === 'active' && (
        <div className="absolute -right-10 -top-10 h-32 w-32 rounded-full bg-current opacity-5 blur-3xl animate-pulse-slow font-bold text-inherit" />
      )}

      <div className="flex items-start justify-between">
        <div className="rounded-lg bg-black/20 p-3">
          <Icon className="h-8 w-8" />
        </div>

        <div className="flex items-center gap-2 rounded-full bg-black/40 px-3 py-1 text-xs font-mono">
          <div className={clsx('h-2 w-2 rounded-full', statusDotColors[status], status === 'active' && 'animate-pulse')} />
          <span className="uppercase tracking-wider">{status}</span>
        </div>
      </div>

      <div className="mt-4">
        <h3 className="text-xl font-bold tracking-tight text-white">{name}</h3>
        <p className="mt-1 text-sm opacity-80">{description}</p>
      </div>

      {/* Footer Metrics */}
      <div className="mt-6 flex items-center justify-between border-t border-white/10 pt-4 text-xs font-mono opacity-60">
        <div className="flex items-center gap-1">
          <Radio className="h-3 w-3" />
          <span>{latency ? `${latency}ms` : '--'}</span>
        </div>
        <div>v1.0.0</div>
      </div>
    </motion.div>
  );
};
