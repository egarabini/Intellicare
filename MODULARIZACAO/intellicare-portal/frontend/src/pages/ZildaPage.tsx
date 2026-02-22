import { useState, useEffect } from 'react';
import { Map, Search, Building2, MapPin, CheckCircle, AlertTriangle, Database, Activity, BarChart3, Users } from 'lucide-react';

interface Establishment {
    cnes_code: string;
    legal_name: string;
    fantasy_name: string;
    unit_type_description: string;
    city_name: string;
    state_code: string;
    city_code: string;
    active: boolean;
}

interface TerritorialContext {
    name: string;
    state: string;
    region_name: string;
    population: number;
    ibge?: {
        idh: number;
        pib_per_capita: number;
        densidade: number;
    };
    rnds?: {
        vaccination_coverage: number;
        last_update: string;
    };
}

export default function ZildaPage() {
    const [establishments, setEstablishments] = useState<Establishment[]>([]);
    const [context, setContext] = useState<TerritorialContext | null>(null);
    const [loading, setLoading] = useState(false);
    const [search, setSearch] = useState('');

    useEffect(() => {
        fetchEstablishments();
    }, []);

    const fetchEstablishments = async () => {
        setLoading(true);
        try {
            // In a real app we would pass search params.
            // For this mock demo, we filter client-side or assume backend logic.
            // To simulate different contexts, we'll try to guess city from search or default to SP

            const res = await fetch(`http://localhost:8003/api/v1/establishments?limit=20`);
            if (res.ok) {
                let data: Establishment[] = await res.json();

                // Simple client-side search simulation for the demo
                if (search) {
                    const term = search.toUpperCase();
                    data = data.filter(e =>
                        e.fantasy_name?.toUpperCase().includes(term) ||
                        e.legal_name?.toUpperCase().includes(term) ||
                        e.city_name?.toUpperCase().includes(term)
                    );
                }

                setEstablishments(data);

                // Update context based on first result or default
                if (data.length > 0) {
                    fetchContext(data[0].city_code);
                } else {
                    setContext(null);
                }
            }
        } catch (error) {
            console.error("Failed to fetch Zilda data:", error);
        } finally {
            setLoading(false);
        }
    };

    const fetchContext = async (cityCode: string) => {
        try {
            // Parallel fetch for context data
            const [estRes, ibgeRes, rndsRes] = await Promise.all([
                fetch(`http://localhost:8003/api/v1/establishments?city_code=${cityCode}&limit=1`),
                fetch(`http://localhost:8003/api/v1/ibge/context/${cityCode}`),
                fetch(`http://localhost:8003/api/v1/rnds/stats/${cityCode}`)
            ]);

            const estData = await estRes.json();
            const ibgeData = ibgeRes.ok ? await ibgeRes.json() : null;
            const rndsData = rndsRes.ok ? await rndsRes.json() : null;

            if (estData && estData.length > 0) {
                const city = estData[0];
                setContext({
                    name: city.city_name,
                    state: city.state_code === '35' ? 'SP' : city.state_code === '33' ? 'RJ' : city.state_code === '41' ? 'PR' : 'BA', // Simple Mapper for demo
                    region_name: "REGIAO METROPOLITANA", // Mocked as we don't have region endpoint easily exposed in Lite
                    population: ibgeData?.population || 0, // Fallback
                    ibge: ibgeData,
                    rnds: rndsData
                });
            }

        } catch (e) {
            console.error("Error fetching context", e);
        }
    }

    return (
        <div className="min-h-screen bg-slate-900 text-slate-200 font-sans p-6">
            <div className="max-w-7xl mx-auto">

                {/* Header */}
                <div className="mb-8 flex items-center justify-between">
                    <div>
                        <h1 className="text-3xl font-bold text-white flex items-center gap-3">
                            <Map className="w-8 h-8 text-rose-500" />
                            ZILDA <span className="text-sm font-mono text-rose-500/50 mt-2">Saúde Pública & Território</span>
                        </h1>
                        <p className="text-slate-400 text-sm mt-1">Dados Nacionais de Saúde (CNES, IBGE, RNDS)</p>
                    </div>

                </div>

                {/* Main Content */}
                <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">

                    {/* Left: Search & Filters */}
                    <div className="lg:col-span-1 space-y-6">
                        <div className="bg-slate-800/50 border border-slate-700 rounded-2xl p-6 backdrop-blur-sm">
                            <h3 className="text-lg font-bold text-white mb-4 flex items-center gap-2">
                                <Search className="w-5 h-5 text-rose-400" />
                                Consulta Unificada
                            </h3>
                            <div className="space-y-4">
                                <div>
                                    <label className="block text-xs text-slate-400 mb-1">Buscar por Nome, CNES ou Município</label>
                                    <input
                                        type="text"
                                        placeholder="Ex: Rio de Janeiro, Curitiba..."
                                        className="w-full bg-slate-900 border border-slate-700 rounded-xl px-4 py-2 text-white focus:outline-none focus:border-rose-500 transition-colors"
                                        value={search}
                                        onChange={(e) => setSearch(e.target.value)}
                                        onKeyDown={(e) => e.key === 'Enter' && fetchEstablishments()}
                                    />
                                </div>
                                <button
                                    onClick={fetchEstablishments}
                                    className="w-full bg-rose-600 hover:bg-rose-500 text-white font-medium py-2 rounded-xl transition-colors"
                                >
                                    Pesquisar
                                </button>
                            </div>
                        </div>

                        {/* Territorial Context Card */}
                        {context && (
                            <div className="bg-slate-800/50 border border-slate-700 rounded-2xl p-6 backdrop-blur-sm animate-in fade-in slide-in-from-bottom-4 duration-500">
                                <h3 className="text-lg font-bold text-white mb-4 flex items-center gap-2">
                                    <MapPin className="w-5 h-5 text-amber-400" />
                                    Contexto Territorial
                                </h3>
                                <div className="space-y-4">
                                    <div className="p-3 bg-slate-900/50 rounded-lg border border-slate-800">
                                        <div className="text-xs text-slate-500 uppercase">Município Atual</div>
                                        <div className="text-white font-bold text-lg">{context.name} - {context.state}</div>
                                        <div className="flex items-center gap-2 mt-1">
                                            <Building2 className="w-3 h-3 text-slate-500" />
                                            <span className="text-xs text-slate-400">{context.region_name}</span>
                                        </div>
                                    </div>

                                    {context.ibge && (
                                        <div className="p-3 bg-slate-900/50 rounded-lg border border-slate-800">
                                            <div className="flex items-center gap-2 mb-2">
                                                <BarChart3 className="w-4 h-4 text-emerald-400" />
                                                <span className="text-xs font-bold text-emerald-400">DADOS IBGE</span>
                                            </div>
                                            <div className="grid grid-cols-2 gap-2">
                                                <div>
                                                    <div className="text-[10px] text-slate-500 uppercase">IDH</div>
                                                    <div className="text-white font-mono">{context.ibge.idh}</div>
                                                </div>
                                                <div>
                                                    <div className="text-[10px] text-slate-500 uppercase">Densidade</div>
                                                    <div className="text-white font-mono">{context.ibge.densidade.toFixed(1)}/km²</div>
                                                </div>
                                            </div>
                                        </div>
                                    )}

                                    {context.rnds && (
                                        <div className="p-3 bg-slate-900/50 rounded-lg border border-slate-800">
                                            <div className="flex items-center gap-2 mb-2">
                                                <Database className="w-4 h-4 text-blue-400" />
                                                <span className="text-xs font-bold text-blue-400">RNDS (Conectsus)</span>
                                            </div>
                                            <div className="space-y-2">
                                                <div>
                                                    <div className="text-[10px] text-slate-500 uppercase flex justify-between">
                                                        <span>Cobertura Vacinal</span>
                                                        <span>{context.rnds.vaccination_coverage}%</span>
                                                    </div>
                                                    <div className="w-full bg-slate-700 h-1.5 rounded-full mt-1">
                                                        <div
                                                            className="bg-blue-500 h-1.5 rounded-full"
                                                            style={{ width: `${context.rnds.vaccination_coverage}%` }}
                                                        ></div>
                                                    </div>
                                                </div>
                                                <div className="text-[10px] text-slate-500">
                                                    Última atualização: {new Date(context.rnds.last_update).toLocaleDateString()}
                                                </div>
                                            </div>
                                        </div>
                                    )}

                                </div>
                            </div>
                        )}
                    </div>

                    {/* Right: Results List */}
                    <div className="lg:col-span-2">
                        <div className="bg-slate-800/50 border border-slate-700 rounded-2xl p-6 backdrop-blur-sm min-h-[500px]">
                            <h3 className="text-lg font-bold text-white mb-6 flex items-center gap-2">
                                <Building2 className="w-5 h-5 text-rose-400" />
                                Estabelecimentos Encontrados
                            </h3>

                            <div className="space-y-3">
                                {establishments.map((est) => (
                                    <div key={est.cnes_code} className="p-4 bg-slate-900/50 border border-slate-800 rounded-xl hover:border-rose-500/30 transition-colors group">
                                        <div className="flex justify-between items-start">
                                            <div>
                                                <h4 className="text-white font-bold group-hover:text-rose-400 transition-colors">{est.fantasy_name || est.legal_name}</h4>
                                                <div className="flex items-center gap-2 text-sm text-slate-400 mt-1">
                                                    <span className="font-mono text-xs bg-slate-800 px-1.5 py-0.5 rounded text-slate-300">CNES: {est.cnes_code}</span>
                                                    <span>•</span>
                                                    <span>{est.unit_type_description}</span>
                                                </div>
                                                <div className="text-xs text-slate-500 mt-2 flex items-center gap-1">
                                                    <MapPin className="w-3 h-3" />
                                                    {est.city_name} - {est.state_code === '35' ? 'SP' : est.state_code === '33' ? 'RJ' : est.state_code === '41' ? 'PR' : 'BA'}
                                                </div>
                                            </div>
                                            <div className="flex flex-col items-end gap-2">
                                                {est.active ? (
                                                    <span className="flex items-center gap-1 text-xs font-medium text-emerald-400 bg-emerald-400/10 px-2 py-1 rounded-full">
                                                        <CheckCircle className="w-3 h-3" /> Ativo
                                                    </span>
                                                ) : (
                                                    <span className="flex items-center gap-1 text-xs font-medium text-red-400 bg-red-400/10 px-2 py-1 rounded-full">
                                                        <AlertTriangle className="w-3 h-3" /> Inativo
                                                    </span>
                                                )}
                                            </div>
                                        </div>
                                    </div>
                                ))}

                                {establishments.length === 0 && !loading && (
                                    <div className="text-center py-12 text-slate-500">
                                        <Building2 className="w-12 h-12 mx-auto mb-3 opacity-20" />
                                        <p>Nenhum estabelecimento encontrado para "{search}".</p>
                                        <p className="text-sm mt-2">Dica: Tente "Rio", "Curitiba" ou "Salvador"</p>
                                    </div>
                                )}
                            </div>
                        </div>
                    </div>

                </div>
            </div>
        </div>
    );
}
