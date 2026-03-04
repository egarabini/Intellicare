import { motion } from 'framer-motion';
import { demoModules } from '../mocks/demoData';
import { ModuleCard } from '../components/demo/ModuleCard';
import { useTenantContext } from '../contexts/TenantContext';

const container = {
    hidden: { opacity: 0 },
    show: {
        opacity: 1,
        transition: {
            staggerChildren: 0.1
        }
    }
};

const item = {
    hidden: { opacity: 0, y: 20 },
    show: { opacity: 1, y: 0 }
};

const DemoDashboard = () => {
    const { tenantInfo } = useTenantContext();
    const activeModules = tenantInfo ? demoModules.filter(m => tenantInfo.activeModules.includes(m.id)) : demoModules;

    return (
        <div className="min-h-screen bg-slate-900 bg-[radial-gradient(ellipse_at_top,_var(--tw-gradient-stops))] from-slate-800 via-slate-900 to-slate-950 p-8 text-white">
            <div className="max-w-7xl mx-auto">
                <header className="mb-12 flex items-center justify-between">
                    <div>
                        <h1 className="text-4xl font-bold tracking-tight text-white/90">
                            <span className="text-emerald-400">Intelli</span>Care Platform
                        </h1>
                        <p className="mt-2 text-lg text-slate-400">
                            Monitoramento em Tempo Real do Ecossistema de Saúde
                        </p>
                    </div>
                    <div className="flex gap-4">
                        <div className="rounded-full bg-emerald-500/10 px-4 py-2 text-sm font-mono text-emerald-400 border border-emerald-500/20 animate-pulse">
                            SYSTEM STATUS: ONLINE
                        </div>
                    </div>
                </header>

                <motion.div
                    variants={container}
                    initial="hidden"
                    animate="show"
                    className="grid grid-cols-1 gap-6 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4"
                >
                    {activeModules.map((module) => (
                        <motion.div key={module.id} variants={item}>
                            <ModuleCard {...module} />
                        </motion.div>
                    ))}
                </motion.div>

                <footer className="mt-20 border-t border-white/5 pt-8 text-center text-sm text-slate-500">
                    <p>© 2026 IntelliCare Health Systems. Modular Architecture v5.0.</p>
                </footer>
            </div>
        </div>
    );
};

export default DemoDashboard;
