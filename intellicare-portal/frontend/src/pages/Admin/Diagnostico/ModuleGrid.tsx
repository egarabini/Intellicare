import React from 'react';
import ModuleCard from './ModuleCard';
import { ModuleProbe } from './index';

interface ModuleGridProps {
    modules: ModuleProbe[];
    loading: boolean;
    onTestFuncional: (moduleName: string) => void;
}

const ModuleGrid: React.FC<ModuleGridProps> = ({ modules, loading, onTestFuncional }) => {

    if (loading && modules.length === 0) {
        return (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
                {[1, 2, 3, 4, 5, 6, 7, 8].map(idx => (
                    <div key={`skeleton-${idx}`} className="bg-white border border-gray-100 rounded-xl p-5 h-64 shadow-sm animate-pulse flex flex-col">
                        <div className="flex justify-between items-start mb-4">
                            <div className="h-6 bg-gray-200 rounded w-1/2"></div>
                            <div className="h-6 bg-gray-200 rounded-full w-20"></div>
                        </div>
                        <div className="h-4 bg-gray-100 rounded w-full mb-2"></div>
                        <div className="h-4 bg-gray-100 rounded w-3/4 mb-6"></div>

                        <div className="mt-auto space-y-3">
                            <div className="flex justify-between">
                                <div className="h-3 bg-gray-100 rounded w-1/3"></div>
                                <div className="h-3 bg-gray-200 rounded w-1/4"></div>
                            </div>
                            <div className="flex justify-between">
                                <div className="h-3 bg-gray-100 rounded w-1/3"></div>
                                <div className="h-3 bg-gray-200 rounded w-1/4"></div>
                            </div>
                        </div>
                    </div>
                ))}
            </div>
        );
    }

    if (modules.length === 0 && !loading) {
        return (
            <div className="flex flex-col items-center justify-center py-16 text-center">
                <div className="bg-gray-50 text-gray-400 p-4 rounded-full mb-4">
                    <svg className="w-12 h-12" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 002-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" /></svg>
                </div>
                <h3 className="text-lg font-medium text-gray-900 mb-1">Nenhum Módulo Encontrado</h3>
                <p className="text-gray-500">O registry do proxy não retornou nenhum microserviço.</p>
            </div>
        );
    }

    return (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
            {modules.map((moduleItem) => (
                <ModuleCard
                    key={moduleItem.name}
                    moduleItem={moduleItem}
                    loading={loading}
                    onTestFuncional={() => onTestFuncional(moduleItem.name)}
                />
            ))}
        </div>
    );
};

export default ModuleGrid;
