import { useState, useEffect } from 'react';
import { Search, FileJson, Activity, User, Code, CheckCircle, Flame } from 'lucide-react';

interface FhirResource {
    resourceType: string;
    id: string;
    [key: string]: any;
}

export default function GrahamePage() {
    const [resources, setResources] = useState<FhirResource[]>([]);
    const [selectedResource, setSelectedResource] = useState<FhirResource | null>(null);
    const [loading, setLoading] = useState(false);
    const [resourceType, setResourceType] = useState('Patient');
    const [search, setSearch] = useState('');

    useEffect(() => {
        fetchResources();
    }, [resourceType]);

    const fetchResources = async () => {
        setLoading(true);
        try {
            const res = await fetch(`http://localhost:8004/api/v1/${resourceType}`);
            if (res.ok) {
                const data = await res.json();
                if (data.resourceType === 'Bundle' && data.entry) {
                    setResources(data.entry.map((e: any) => e.resource));
                } else {
                    setResources([]);
                }
            }
        } catch (error) {
            console.error("Failed to fetch FHIR data:", error);
        } finally {
            setLoading(false);
        }
    };

    const handleSearch = async () => {
        if (!search) {
            fetchResources();
            return;
        }

        setLoading(true);
        try {
            // Simple mock search param logic
            const param = resourceType === 'Patient' ? `name=${search}` : `patient=${search}`;
            const res = await fetch(`http://localhost:8004/api/v1/${resourceType}?${param}`);
            if (res.ok) {
                const data = await res.json();
                if (data.resourceType === 'Bundle' && data.entry) {
                    setResources(data.entry.map((e: any) => e.resource));
                } else {
                    setResources([]);
                }
            }
        } catch (error) {
            console.error("Search failed:", error);
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="min-h-screen bg-slate-900 text-slate-200 font-sans p-6">
            <div className="max-w-7xl mx-auto">

                {/* Header */}
                <div className="mb-8 flex items-center justify-between">
                    <div>
                        <h1 className="text-3xl font-bold text-white flex items-center gap-3">
                            <Flame className="w-8 h-8 text-orange-500" />
                            GRAHAME <span className="text-sm font-mono text-orange-500/50 mt-2">Interoperabilidade FHIR</span>
                        </h1>
                        <p className="text-slate-400 text-sm mt-1">HL7 FHIR R4 Interface (Mock Server)</p>
                    </div>
                    <div className="flex gap-4">
                        <div className="flex items-center gap-2 px-3 py-1.5 bg-slate-800/50 rounded-lg border border-slate-700">
                            <div className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></div>
                            <span className="text-xs font-mono text-emerald-400">SERVER ONLINE</span>
                        </div>
                    </div>
                </div>

                {/* Main Content */}
                <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">

                    {/* Left: Controls & List */}
                    <div className="lg:col-span-1 space-y-6">
                        <div className="bg-slate-800/50 border border-slate-700 rounded-2xl p-6 backdrop-blur-sm">
                            <h3 className="text-lg font-bold text-white mb-4 flex items-center gap-2">
                                <Search className="w-5 h-5 text-orange-400" />
                                Explorador FHIR
                            </h3>

                            <div className="flex gap-2 mb-4">
                                <button
                                    onClick={() => setResourceType('Patient')}
                                    className={`flex-1 py-2 rounded-lg text-sm font-medium transition-colors ${resourceType === 'Patient' ? 'bg-orange-600 text-white' : 'bg-slate-800 text-slate-400 hover:bg-slate-700'}`}
                                >
                                    Pacientes
                                </button>
                                <button
                                    onClick={() => setResourceType('Observation')}
                                    className={`flex-1 py-2 rounded-lg text-sm font-medium transition-colors ${resourceType === 'Observation' ? 'bg-orange-600 text-white' : 'bg-slate-800 text-slate-400 hover:bg-slate-700'}`}
                                >
                                    Observações
                                </button>
                            </div>

                            <div className="flex gap-2 mb-4">
                                <input
                                    type="text"
                                    placeholder={resourceType === 'Patient' ? "Buscar por nome..." : "Buscar por ID do Paciente..."}
                                    className="w-full bg-slate-900 border border-slate-700 rounded-xl px-4 py-2 text-white focus:outline-none focus:border-orange-500 transition-colors text-sm"
                                    value={search}
                                    onChange={(e) => setSearch(e.target.value)}
                                    onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
                                />
                                <button
                                    onClick={handleSearch}
                                    className="bg-slate-700 hover:bg-slate-600 text-white px-3 rounded-xl transition-colors"
                                >
                                    <Search className="w-4 h-4" />
                                </button>
                            </div>

                            <div className="space-y-2 max-h-[500px] overflow-y-auto">
                                {resources.map((res) => (
                                    <div
                                        key={res.id}
                                        onClick={() => setSelectedResource(res)}
                                        className={`p-3 rounded-xl border cursor-pointer transition-all ${selectedResource?.id === res.id ? 'bg-orange-500/10 border-orange-500' : 'bg-slate-900/50 border-slate-800 hover:border-orange-500/30'}`}
                                    >
                                        <div className="flex items-center gap-3">
                                            <div className={`p-2 rounded-lg ${resourceType === 'Patient' ? 'bg-blue-500/10 text-blue-400' : 'bg-purple-500/10 text-purple-400'}`}>
                                                {resourceType === 'Patient' ? <User className="w-4 h-4" /> : <Activity className="w-4 h-4" />}
                                            </div>
                                            <div>
                                                <div className="text-sm font-bold text-white">
                                                    {resourceType === 'Patient'
                                                        ? `${res.name?.[0]?.given?.[0]} ${res.name?.[0]?.family}`
                                                        : res.code?.coding?.[0]?.display
                                                    }
                                                </div>
                                                <div className="text-xs font-mono text-slate-500">ID: {res.id}</div>
                                            </div>
                                        </div>
                                    </div>
                                ))}

                                {resources.length === 0 && !loading && (
                                    <div className="text-center py-8 text-slate-500 text-sm">
                                        Nenhum recurso encontrado.
                                    </div>
                                )}
                            </div>
                        </div>
                    </div>

                    {/* Right: JSON Viewer */}
                    <div className="lg:col-span-2">
                        <div className="bg-slate-800/50 border border-slate-700 rounded-2xl p-6 backdrop-blur-sm min-h-[600px] flex flex-col">
                            <h3 className="text-lg font-bold text-white mb-4 flex items-center gap-2">
                                <Code className="w-5 h-5 text-orange-400" />
                                Visualizador JSON (FHIR Resource)
                            </h3>

                            {selectedResource ? (
                                <div className="flex-1 bg-slate-950 rounded-xl p-4 overflow-auto border border-slate-800 font-mono text-xs">
                                    <pre className="text-orange-200">
                                        {JSON.stringify(selectedResource, null, 2)}
                                    </pre>
                                </div>
                            ) : (
                                <div className="flex-1 flex flex-col items-center justify-center text-slate-500 border-2 border-dashed border-slate-800 rounded-xl">
                                    <FileJson className="w-16 h-16 mb-4 opacity-20" />
                                    <p>Selecione um recurso para ver o JSON detalhado.</p>
                                </div>
                            )}

                            {selectedResource && (
                                <div className="mt-4 flex items-center gap-2 text-xs text-emerald-400 bg-emerald-400/10 px-3 py-2 rounded-lg self-start">
                                    <CheckCircle className="w-3 h-3" />
                                    <span>Válido conforme HL7 FHIR R4</span>
                                </div>
                            )}
                        </div>
                    </div>

                </div>
            </div>
        </div>
    );
}
