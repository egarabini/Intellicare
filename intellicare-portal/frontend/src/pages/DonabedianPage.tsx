import { BarChart, BadgeCheck, Scale, TrendingUp, Users, Heart, Shield, Activity } from 'lucide-react';

export default function DonabedianPage() {
    return (
        <div className="min-h-screen bg-slate-50 text-slate-800 font-sans">
            <div className="bg-teal-900 text-white py-16">
                <div className="container mx-auto px-4 max-w-4xl">
                    <div className="flex flex-col md:flex-row items-center gap-8">
                        <div className="p-4 bg-white/10 rounded-2xl backdrop-blur-sm border border-white/20">
                            <BarChart className="w-16 h-16 text-teal-300" />
                        </div>
                        <div>
                            <h1 className="text-4xl font-bold mb-2">Avedis Donabedian</h1>
                            <p className="text-teal-200 text-xl">O Pai da Qualidade em Saúde (1919-2000)</p>
                        </div>
                    </div>
                </div>
            </div>

            <div className="container mx-auto px-4 py-12 max-w-4xl">
                <div className="prose prose-lg prose-slate max-w-none">
                    <p className="lead text-xl text-slate-600 mb-8">
                        Considerado o pai da Qualidade no setor da Saúde, o médico libanês <strong>Avedis Donabedian</strong> realizou estudos que tiveram um profundo impacto sobre os sistemas de gestão nas áreas da medicina. Seus princípios ainda hoje são considerados atuais e de grande importância para a excelência hospitalar.
                    </p>

                    <div className="bg-white p-8 rounded-2xl shadow-sm border border-slate-100 mb-12">
                        <h3 className="text-2xl font-bold text-teal-800 mb-4">Os 7 Pilares da Qualidade</h3>
                        <p className="text-slate-600 mb-6">
                            Uma das maiores contribuições de Donabedian está presente nos livros “Explorations in quality assessment and monitoring”, onde descreve os pilares que provocaram grandes mudanças na área da saúde.
                        </p>
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                            {[
                                { title: 'Eficácia', icon: BadgeCheck, desc: 'A capacidade de produzir efeitos positivos. São as condições ideais para o tratamento: melhores estruturas, equipamentos e serviços.' },
                                { title: 'Efetividade', icon: Activity, desc: 'O alcance do objetivo real. Mede o quanto o cuidado real se aproxima do ideal, focando nos resultados das ações.' },
                                { title: 'Eficiência', icon: TrendingUp, desc: 'Melhor tratamento com a menor quantidade de recursos possível, sem afetar a melhora do paciente.' },
                                { title: 'Otimização', icon: Scale, desc: 'Melhor relação custo-benefício. Elevar o tratamento ao estado ótimo, equilibrando cuidados e custos.' },
                                { title: 'Aceitabilidade', icon: Heart, desc: 'Adaptação do cliente ao tratamento. Envolve acessibilidade, relação médico-paciente e comodidade.' },
                                { title: 'Legitimidade', icon: Shield, desc: 'Aceitação da instituição pela sociedade como uma boa prestadora de serviços de saúde.' },
                                { title: 'Equidade', icon: Users, desc: 'Justiça na distribuição dos cuidados. Imparcialidade no atendimento hospitalar para todos.' }
                            ].map((item) => (
                                <div key={item.title} className="flex gap-4 p-4 rounded-xl bg-slate-50 border border-slate-100 hover:border-teal-200 transition-colors">
                                    <div className="mt-1">
                                        <item.icon className="w-6 h-6 text-teal-600" />
                                    </div>
                                    <div>
                                        <h4 className="font-bold text-slate-800">{item.title}</h4>
                                        <p className="text-sm text-slate-600 mt-1">{item.desc}</p>
                                    </div>
                                </div>
                            ))}
                        </div>
                    </div>

                    <div className="bg-teal-50 p-8 rounded-2xl border border-teal-100">
                        <h3 className="text-xl font-bold text-teal-900 mb-4">Por que implementar?</h3>
                        <p className="text-teal-800 mb-4">
                            Mesmo tendo sido propostos há quase 40 anos, os pilares da qualidade de Donabedian ainda são referência na Qualidade hospitalar. Eles encorajam a reflexão sobre práticas do setor, elevam a preocupação com o paciente e melhoram a visibilidade das instituições.
                        </p>
                        <p className="text-sm text-teal-600 font-medium italic mt-4">
                            (Referência: Davidson Ramos)
                        </p>
                    </div>
                </div>
            </div>
        </div>
    );
}
