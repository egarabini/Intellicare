"""
Serviço de Plano de Cuidado - Geração Automática de Planos Terapêuticos

Responsível por:
1. Gerar planos automáticos baseado em diagnósticos
2. Definir objetivos SMART por condição
3. Recomendar medicamentos conforme protocolo
4. Listar intervenções farmacológicas + não-farmacológicas
5. Definir frequência de acompanhamento e reavaliação

Protocolos:
- HAS: SBC 2016/2020
- DRC: KDIGO 2012
- Diabetes: ADA 2024
- Dislipidemia: ATP III, ESC/EAS
- IC: ACC/AHA, ESC
- Asma: GINA 2023
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional
from datetime import datetime, timedelta
from enum import Enum


class NivelSeveridade(str, Enum):
    """Nível de severidade da condição"""
    LEVE = "LEVE"
    MODERADA = "MODERADA"
    SEVERA = "SEVERA"
    CRITICA = "CRITICA"


@dataclass
class Objetivo:
    """Objetivo SMART para plano de cuidado"""
    descricao: str  # Ex: "Reduzir PA sistólica para <140 mmHg"
    metrica: str  # Ex: "PA sistólica"
    valor_alvo: float  # Ex: 140
    unidade: str  # Ex: "mmHg"
    prazo_dias: int  # Ex: 90 (3 meses)
    prioridade: str = "ALTA"  # ALTA, MÉDIA, BAIXA


@dataclass
class Medicamento:
    """Medicamento recomendado"""
    nome: str
    dose_inicial: str
    dose_alvo: str
    unidade: str
    frequencia: str  # Ex: "12/12h", "24/24h"
    classe_farmacologica: str
    protocolo: str  # Ex: "SBC 2020"
    justificativa: str
    efeitos_colaterais: List[str] = field(default_factory=list)
    contra_indicacoes: List[str] = field(default_factory=list)


@dataclass
class Intervencao:
    """Intervenção farmacológica ou não-farmacológica"""
    tipo: str  # "FARMACOLOGICA", "NAO_FARMACOLOGICA"
    categoria: str  # Ex: "Educação", "Exercício", "Dieta"
    descricao: str
    frequencia: str  # Ex: "diariamente", "3x/semana"
    duracao_esperada: str  # Ex: "contínua", "8 semanas"
    responsavel: str  # Ex: "paciente", "enfermeiro", "nutricionista"


@dataclass
class PlanoCuidado:
    """Plano de cuidado completo para một condição crônica"""
    condicao_cronica_id: int
    cid10: str
    diagnostico: str
    nivel_severidade: str
    data_criacao: datetime = field(default_factory=datetime.now)
    
    # Componentes do plano
    objetivos: List[Objetivo] = field(default_factory=list)
    medicamentos: List[Medicamento] = field(default_factory=list)
    intervencoes: List[Intervencao] = field(default_factory=list)
    
    # Monitoramento
    frequencia_acompanhamento_dias: int = 90
    exames_recomendados: List[str] = field(default_factory=list)
    parametros_a_monitorar: List[str] = field(default_factory=list)
    
    # Metadata
    status: str = "ATIVO"  # ATIVO, REVISADO, SUSPENSO, ENCERRADO
    data_proxima_revisao: datetime = field(default_factory=lambda: datetime.now() + timedelta(days=90))
    notas_clinicas: str = ""


class PlanoCuidadoService:
    """Serviço de geração automática de planos de cuidado"""

    # ========================================================================
    # MÉTODOS PRINCIPAIS
    # ========================================================================

    @staticmethod
    def criar_plano_completo(
        condicao_cronica_id: int,
        cid10: str,
        diagnostico: str,
        estagio: str,
        classificacao_nivel: str,
        idade_anos: int,
        comorbidades: List[str] = None
    ) -> PlanoCuidado:
        """
        Cria plano de cuidado completo para uma condição crônica.
        
        Args:
            condicao_cronica_id: ID da condição no banco
            cid10: Código CID-10
            diagnostico: Nome do diagnóstico
            estagio: Estágio da condição (ex: ESTAGIO_1, G3a, CONTROLADO)
            classificacao_nivel: Nível (NORMAL, LEVE, MODERADA, SEVERA, CRITICA)
            idade_anos: Idade do paciente
            comorbidades: Lista de CID10 de comorbidades
            
        Returns:
            PlanoCuidado completo
        """
        comorbidades = comorbidades or []
        
        plano = PlanoCuidado(
            condicao_cronica_id=condicao_cronica_id,
            cid10=cid10,
            diagnostico=diagnostico,
            nivel_severidade=classificacao_nivel
        )
        
        # Selecionar handler apropriado conforme CID10
        if cid10.startswith("I10"):
            PlanoCuidadoService._criar_plano_has(plano, estagio, idade_anos, comorbidades)
        elif cid10.startswith("E11"):
            PlanoCuidadoService._criar_plano_diabetes(plano, estagio, idade_anos, comorbidades)
        elif cid10.startswith("N18"):
            PlanoCuidadoService._criar_plano_drc(plano, estagio, idade_anos, comorbidades)
        elif cid10.startswith("E78"):
            PlanoCuidadoService._criar_plano_dislipidemia(plano, estagio, idade_anos)
        elif cid10.startswith("I50"):
            PlanoCuidadoService._criar_plano_ic(plano, estagio, idade_anos, comorbidades)
        elif cid10.startswith("J45"):
            PlanoCuidadoService._criar_plano_asma(plano, estagio, idade_anos)
        
        # Atualizar data_proxima_revisao baseado na frequencia configurada
        plano.data_proxima_revisao = plano.data_criacao + timedelta(days=plano.frequencia_acompanhamento_dias)
        
        return plano

    # ========================================================================
    # PLANOS ESPECÍFICOS POR CONDIÇÃO
    # ========================================================================

    @staticmethod
    def _criar_plano_has(
        plano: PlanoCuidado,
        estagio: str,
        idade_anos: int,
        comorbidades: List[str]
    ):
        """Plano para Hipertensão Arterial (I10) - SBC 2020"""
        
        if estagio == "NORMAL":
            plano.objetivos.extend([
                Objetivo(
                    descricao="Manter PA <120/80 mmHg",
                    metrica="PA sistólica",
                    valor_alvo=120,
                    unidade="mmHg",
                    prazo_dias=365,
                    prioridade="ALTA"
                ),
                Objetivo(
                    descricao="Manter atividade física regular",
                    metrica="Exercício aeróbico",
                    valor_alvo=150,
                    unidade="min/semana",
                    prazo_dias=180,
                    prioridade="MÉDIA"
                )
            ])
            plano.frequencia_acompanhamento_dias = 365
            
        elif estagio == "ELEVADA":
            plano.objetivos.extend([
                Objetivo(
                    descricao="Reduzir PA para <130/80 mmHg com mudanças estilo vida",
                    metrica="PA sistólica",
                    valor_alvo=130,
                    unidade="mmHg",
                    prazo_dias=90,
                    prioridade="ALTA"
                )
            ])
            plano.intervencoes.extend([
                Intervencao("NAO_FARMACOLOGICA", "Dieta", "Reduzir sódio <2.3g/dia", "contínua", "contínua", "paciente"),
                Intervencao("NAO_FARMACOLOGICA", "Exercício", "150 min/semana atividade aeróbica moderada", "3-5x/semana", "contínua", "paciente"),
                Intervencao("NAO_FARMACOLOGICA", "Educação", "Educação sobre HAS e fatores de risco", "1 sessão", "8 semanas", "enfermeiro")
            ])
            plano.frequencia_acompanhamento_dias = 90
            
        elif estagio in ["ESTAGIO_1", "ESTAGIO_2"]:
            plano.objetivos.extend([
                Objetivo(
                    descricao="Reduzir PA sistólica para <140 mmHg",
                    metrica="PA sistólica",
                    valor_alvo=140,
                    unidade="mmHg",
                    prazo_dias=120,
                    prioridade="ALTA"
                ),
                Objetivo(
                    descricao="Reduzir PA diastólica para <90 mmHg",
                    metrica="PA diastólica",
                    valor_alvo=90,
                    unidade="mmHg",
                    prazo_dias=120,
                    prioridade="ALTA"
                )
            ])
            
            # Selecionar medicação conforme estagio
            if estagio == "ESTAGIO_1":
                plano.medicamentos.append(
                    Medicamento(
                        nome="Losartan",
                        dose_inicial="25mg",
                        dose_alvo="50mg",
                        unidade="mg",
                        frequencia="24/24h",
                        classe_farmacologica="ARA2",
                        protocolo="SBC 2020",
                        justificativa="Primeira linha, proteção renal em DM/DRC",
                        efeitos_colaterais=["Tontura", "Hipotensão"],
                        contra_indicacoes=["Gravidez", "Angioedema prévio"]
                    )
                )
            else:  # ESTAGIO_2
                plano.medicamentos.extend([
                    Medicamento(
                        nome="Losartan",
                        dose_inicial="50mg",
                        dose_alvo="100mg",
                        unidade="mg",
                        frequencia="24/24h",
                        classe_farmacologica="ARA2",
                        protocolo="SBC 2020",
                        justificativa="Primeira linha",
                        efeitos_colaterais=["Tontura"],
                        contra_indicacoes=["Gravidez"]
                    ),
                    Medicamento(
                        nome="Amlodipina",
                        dose_inicial="2.5mg",
                        dose_alvo="5-10mg",
                        unidade="mg",
                        frequencia="24/24h",
                        classe_farmacologica="Bloqueador de canais de cálcio",
                        protocolo="SBC 2020",
                        justificativa="Terapia combinada para ESTAGIO_2",
                        efeitos_colaterais=["Edema periférico", "Cefaleia"],
                        contra_indicacoes=[]
                    )
                ])
            
            plano.intervencoes.extend([
                Intervencao("NAO_FARMACOLOGICA", "Dieta", "DASH: sódio <2.3g/dia", "contínua", "contínua", "nutricionista"),
                Intervencao("NAO_FARMACOLOGICA", "Exercício", "150 min/semana", "3-5x/semana", "contínua", "paciente")
            ])
            plano.frequencia_acompanhamento_dias = 30
            
        elif estagio == "ESTAGIO_3":
            plano.objetivos.append(
                Objetivo(
                    descricao="Reduzir PA para <140 mmHg com múltiplos fármacos",
                    metrica="PA sistólica",
                    valor_alvo=140,
                    unidade="mmHg",
                    prazo_dias=60,
                    prioridade="ALTA"
                )
            )
            plano.medicamentos.extend([
                Medicamento(
                    nome="Losartan",
                    dose_inicial="50mg",
                    dose_alvo="100mg",
                    unidade="mg",
                    frequencia="24/24h",
                    classe_farmacologica="ARA2",
                    protocolo="SBC 2020",
                    justificativa="Primeira linha",
                    efeitos_colaterais=["Tontura"]
                ),
                Medicamento(
                    nome="Amlodipina",
                    dose_inicial="5mg",
                    dose_alvo="10mg",
                    unidade="mg",
                    frequencia="24/24h",
                    classe_farmacologica="BCC",
                    protocolo="SBC 2020",
                    justificativa="Bloqueador de canais"
                ),
                Medicamento(
                    nome="Hidroclorotiazida",
                    dose_inicial="12.5mg",
                    dose_alvo="25mg",
                    unidade="mg",
                    frequencia="24/24h",
                    classe_farmacologica="Diurético tiazídico",
                    protocolo="SBC 2020",
                    justificativa="Terceira droga"
                )
            ])
            plano.frequencia_acompanhamento_dias = 15
        
        # Exames recomendados para HAS
        plano.exames_recomendados = [
            "Eletrocardiograma",
            "Creatinina sérica",
            "Potássio",
            "Glicemia",
            "Lipidograma"
        ]
        plano.parametros_a_monitorar = ["PA sistólica", "PA diastólica", "FC"]

    @staticmethod
    def _criar_plano_diabetes(
        plano: PlanoCuidado,
        estagio: str,
        idade_anos: int,
        comorbidades: List[str]
    ):
        """Plano para Diabetes Mellitus (E11) - ADA 2024"""
        
        if estagio == "BEM_CONTROLADO":
            plano.objetivos.append(
                Objetivo(
                    descricao="Manter HbA1c <7.0%",
                    metrica="HbA1c",
                    valor_alvo=7.0,
                    unidade="%",
                    prazo_dias=180,
                    prioridade="ALTA"
                )
            )
            plano.frequencia_acompanhamento_dias = 180
            
        elif estagio == "MODERADO":
            plano.objetivos.extend([
                Objetivo(
                    descricao="Reduzir HbA1c para <7.5%",
                    metrica="HbA1c",
                    valor_alvo=7.5,
                    unidade="%",
                    prazo_dias=120,
                    prioridade="ALTA"
                ),
                Objetivo(
                    descricao="Reduzir peso em 5% inicial",
                    metrica="Peso corporal",
                    valor_alvo=5,
                    unidade="%",
                    prazo_dias=180,
                    prioridade="MÉDIA"
                )
            ])
            plano.medicamentos.append(
                Medicamento(
                    nome="Metformina",
                    dose_inicial="500mg",
                    dose_alvo="1000mg",
                    unidade="mg",
                    frequencia="12/12h",
                    classe_farmacologica="Biguanida",
                    protocolo="ADA 2024",
                    justificativa="Primeira linha, reduz peso",
                    efeitos_colaterais=["Diarreia", "Desconforto GI"],
                    contra_indicacoes=["TFGe <30"]
                )
            )
            plano.frequencia_acompanhamento_dias = 90
            
        elif estagio == "MAL_CONTROLADO":
            plano.objetivos.append(
                Objetivo(
                    descricao="Reduzir HbA1c para <8.0%",
                    metrica="HbA1c",
                    valor_alvo=8.0,
                    unidade="%",
                    prazo_dias=90,
                    prioridade="ALTA"
                )
            )
            plano.medicamentos.extend([
                Medicamento(
                    nome="Metformina",
                    dose_inicial="1000mg",
                    dose_alvo="2000mg",
                    unidade="mg",
                    frequencia="12/12h",
                    classe_farmacologica="Biguanida",
                    protocolo="ADA 2024",
                    justificativa="Primeira linha",
                    efeitos_colaterais=["Diarreia"],
                    contra_indicacoes=["TFGe <30"]
                ),
                Medicamento(
                    nome="Gliclazida",
                    dose_inicial="40mg",
                    dose_alvo="80mg",
                    unidade="mg",
                    frequencia="24/24h",
                    classe_farmacologica="Sulfoniluréia",
                    protocolo="ADA 2024",
                    justificativa="Segunda linha",
                    efeitos_colaterais=["Hipoglicemia"],
                    contra_indicacoes=["Insuficiência renal severa"]
                )
            ])
            plano.frequencia_acompanhamento_dias = 30
            
        elif estagio == "CRITICO":
            plano.objetivos.append(
                Objetivo(
                    descricao="Reduzir HbA1c para <9% com insulina ou biológicos",
                    metrica="HbA1c",
                    valor_alvo=9.0,
                    unidade="%",
                    prazo_dias=60,
                    prioridade="ALTA"
                )
            )
            plano.medicamentos.extend([
                Medicamento(
                    nome="Insulina Glargina",
                    dose_inicial="10 UI",
                    dose_alvo="0.3-0.5 UI/kg",
                    unidade="UI",
                    frequencia="24/24h",
                    classe_farmacologica="Insulina basal",
                    protocolo="ADA 2024",
                    justificativa="Necessário para HbA1c>9%",
                    efeitos_colaterais=["Hipoglicemia"],
                    contra_indicacoes=[]
                )
            ])
            plano.frequencia_acompanhamento_dias = 14
        
        plano.intervencoes.extend([
            Intervencao("NAO_FARMACOLOGICA", "Educação diabetes", "Programa de educação estruturado", "1-2 sessões", "8 semanas", "educador diabetes"),
            Intervencao("NAO_FARMACOLOGICA", "Dieta", "Contagem de carboidratos, índice glicêmico baixo", "contínua", "contínua", "nutricionista"),
            Intervencao("NAO_FARMACOLOGICA", "Exercício", "150 min/semana atividade moderada", "5x/semana", "contínua", "paciente")
        ])
        
        plano.exames_recomendados = ["HbA1c", "Glicemia de jejum", "Perfil lipídico", "Creatinina", "Microalbuminuria"]
        plano.parametros_a_monitorar = ["Glicemia de jejum", "Glicemia pós-prandial", "HbA1c"]

    @staticmethod
    def _criar_plano_drc(
        plano: PlanoCuidado,
        estagio: str,
        idade_anos: int,
        comorbidades: List[str]
    ):
        """Plano para Doença Renal Crônica (N18) - KDIGO 2012"""
        
        estagio_map = {
            "G1": ("Normal", 90, 180),
            "G2": ("Mildly decreased", 60, 180),
            "G3a": ("Mildly-moderately decreased", 45, 90),
            "G3b": ("Moderately-severely decreased", 30, 60),
            "G4": ("Severely decreased", 15, 30),
            "G5": ("Kidney failure", 1, 14)
        }
        
        desc, _, freq_dias = estagio_map.get(estagio, ("Unknown", 365, 180))
        
        plano.objetivos.append(
            Objetivo(
                descricao=f"Manter TFGe estável em estágio {estagio}",
                metrica="TFGe",
                valor_alvo=30 if estagio == "G4" else 15 if estagio == "G5" else 60,
                unidade="mL/min/1.73m²",
                prazo_dias=180,
                prioridade="ALTA"
            )
        )
        
        # Medicações variam por estágio
        if estagio in ["G3a", "G3b", "G4"]:
            plano.medicamentos.extend([
                Medicamento(
                    nome="Losartan",
                    dose_inicial="25mg",
                    dose_alvo="100mg",
                    unidade="mg",
                    frequencia="24/24h",
                    classe_farmacologica="ARA2",
                    protocolo="KDIGO 2012",
                    justificativa="Proteção renal, reduz proteinúria",
                    efeitos_colaterais=["Hipotensão"],
                    contra_indicacoes=["Gravidez"]
                ),
                Medicamento(
                    nome="Finerenona",
                    dose_inicial="10mg",
                    dose_alvo="20mg",
                    unidade="mg",
                    frequencia="24/24h",
                    classe_farmacologica="Antagonista MRA",
                    protocolo="KDIGO 2021",
                    justificativa="Reduz progressão DRC",
                    efeitos_colaterais=["Hipercalemia"],
                    contra_indicacoes=["K >5.5"]
                )
            ])
        
        if estagio in ["G4", "G5"]:
            plano.medicamentos.append(
                Medicamento(
                    nome="Carbonato de cálcio",
                    dose_inicial="1g",
                    dose_alvo="2-3g",
                    unidade="g",
                    frequencia="TID com refeições",
                    classe_farmacologica="Quelante de fósforo",
                    protocolo="KDIGO 2012",
                    justificativa="Controlar fósforo em DRC avançada",
                    efeitos_colaterais=["Constipação"],
                    contra_indicacoes=[]
                )
            )
        
        plano.frequencia_acompanhamento_dias = freq_dias
        plano.exames_recomendados = ["Creatinina", "TFGe", "Potássio", "Fósforo", "Hemoglobina"]
        plano.parametros_a_monitorar = ["TFGe", "Potássio", "Fósforo", "Proteína urinária"]

    @staticmethod
    def _criar_plano_dislipidemia(
        plano: PlanoCuidado,
        estagio: str,
        idade_anos: int
    ):
        """Plano para Dislipidemia (E78) - ATP III / ESC-EAS 2019"""
        
        if estagio == "OTIMA":
            plano.objetivos.append(
                Objetivo(
                    descricao="Manter LDL <70 mg/dL",
                    metrica="LDL colesterol",
                    valor_alvo=70,
                    unidade="mg/dL",
                    prazo_dias=365,
                    prioridade="MEDIA"
                )
            )
            plano.frequencia_acompanhamento_dias = 365
            
        elif estagio == "DESEJAVEL":
            plano.frecuencia_acompanhamento_dias = 180
            
        elif estagio == "LIMÍTROFE":
            plano.objetivos.append(
                Objetivo(
                    descricao="Reduzir LDL para <100 mg/dL",
                    metrica="LDL colesterol",
                    valor_alvo=100,
                    unidade="mg/dL",
                    prazo_dias=120,
                    prioridade="ALTA"
                )
            )
            plano.medicamentos.append(
                Medicamento(
                    nome="Atorvastatina",
                    dose_inicial="10mg",
                    dose_alvo="20mg",
                    unidade="mg",
                    frequencia="24/24h à noite",
                    classe_farmacologica="Estatina",
                    protocolo="ESC-EAS 2019",
                    justificativa="Reduz LDL, risco CV",
                    efeitos_colaterais=["Miosite"],
                    contra_indicacoes=[]
                )
            )
            plano.frequencia_acompanhamento_dias = 90
            
        elif estagio in ["ELEVADA", "MUITO_ELEVADA"]:
            plano.objetivos.append(
                Objetivo(
                    descricao="Reduzir LDL <70 mg/dL com terapia intensiva",
                    metrica="LDL colesterol",
                    valor_alvo=70,
                    unidade="mg/dL",
                    prazo_dias=90,
                    prioridade="ALTA"
                )
            )
            
            medicamentos = [
                Medicamento(
                    nome="Atorvastatina",
                    dose_inicial="40mg",
                    dose_alvo="80mg",
                    unidade="mg",
                    frequencia="24/24h",
                    classe_farmacologica="Estatina",
                    protocolo="ESC-EAS 2019",
                    justificativa="Redução intensiva LDL",
                    efeitos_colaterais=["Miosite"],
                    contra_indicacoes=[]
                )
            ]
            
            if estagio == "MUITO_ELEVADA":
                medicamentos.extend([
                    Medicamento(
                        nome="Ezetimiba",
                        dose_inicial="10mg",
                        dose_alvo="10mg",
                        unidade="mg",
                        frequencia="24/24h",
                        classe_farmacologica="Inibidor absorção colesterol",
                        protocolo="ESC-EAS 2019",
                        justificativa="Redução adicional LDL",
                        efeitos_colaterais=[],
                        contra_indicacoes=[]
                    ),
                    Medicamento(
                        nome="Evolocumab (PCSK9i)",
                        dose_inicial="140mg",
                        dose_alvo="140mg",
                        unidade="mg",
                        frequencia="14 dias SC",
                        classe_farmacologica="Inibidor PCSK9",
                        protocolo="ESC-EAS 2019",
                        justificativa="Redução agressiva em HF ou alto risco",
                        efeitos_colaterais=[],
                        contra_indicacoes=[]
                    )
                ])
            
            plano.medicamentos.extend(medicamentos)
            plano.frequencia_acompanhamento_dias = 30
        
        plano.intervencoes.extend([
            Intervencao("NAO_FARMACOLOGICA", "Dieta", "Dieta pobre em gordura saturada <7% calorias", "contínua", "contínua", "nutricionista"),
            Intervencao("NAO_FARMACOLOGICA", "Exercício", "150 min/semana", "5x/semana", "contínua", "paciente")
        ])
        
        plano.exames_recomendados = ["Lipidograma completo", "LDL subfrações"]
        plano.parametros_a_monitorar = ["LDL colesterol", "HDL colesterol", "Triglicerídeos"]

    @staticmethod
    def _criar_plano_ic(
        plano: PlanoCuidado,
        estagio: str,
        idade_anos: int,
        comorbidades: List[str]
    ):
        """Plano para Insuficiência Cardíaca (I50) - ACC/AHA 2022"""
        
        if estagio == "ASSINTOMATICA":
            plano.objetivos.append(
                Objetivo(
                    descricao="Monitoramento periódico, sem sintomas",
                    metrica="Classe NYHA",
                    valor_alvo=1,
                    unidade="classe",
                    prazo_dias=180,
                    prioridade="MEDIA"
                )
            )
            plano.frequencia_acompanhamento_dias = 180
            
        elif estagio == "LEVE":
            plano.objetivos.append(
                Objetivo(
                    descricao="Manter NYHA I com IECA",
                    metrica="Classe NYHA",
                    valor_alvo=1,
                    unidade="classe",
                    prazo_dias=120,
                    prioridade="ALTA"
                )
            )
            plano.medicamentos.append(
                Medicamento(
                    nome="Enalapril",
                    dose_inicial="2.5mg",
                    dose_alvo="10mg",
                    unidade="mg",
                    frequencia="12/12h",
                    classe_farmacologica="IECA",
                    protocolo="ACC/AHA 2022",
                    justificativa="Melhora estrutura LV, reduz mortalidade",
                    efeitos_colaterais=["Tosse", "Hipotensão"],
                    contra_indicacoes=["Gravidez"]
                )
            )
            plano.frequencia_acompanhamento_dias = 90
            
        elif estagio == "MODERADA":
            plano.objetivos.append(
                Objetivo(
                    descricao="Reduzir para NYHA II, melhorar FE",
                    metrica="Classe NYHA",
                    valor_alvo=2,
                    unidade="classe",
                    prazo_dias=120,
                    prioridade="ALTA"
                )
            )
            plano.medicamentos.extend([
                Medicamento(
                    nome="Enalapril",
                    dose_inicial="5mg",
                    dose_alvo="10mg",
                    unidade="mg",
                    frequencia="12/12h",
                    classe_farmacologica="IECA",
                    protocolo="ACC/AHA 2022",
                    justificativa="Melhora estrutura LV",
                    efeitos_colaterais=["Tosse"],
                    contra_indicacoes=["Gravidez"]
                ),
                Medicamento(
                    nome="Carvedilol",
                    dose_inicial="3.125mg",
                    dose_alvo="25mg",
                    unidade="mg",
                    frequencia="12/12h",
                    classe_farmacologica="Beta-bloqueador",
                    protocolo="ACC/AHA 2022",
                    justificativa="Melhora mortalidade",
                    efeitos_colaterais=["Fadiga"],
                    contra_indicacoes=[]
                ),
                Medicamento(
                    nome="Furosemida",
                    dose_inicial="20mg",
                    dose_alvo="40mg",
                    unidade="mg",
                    frequencia="conforme necessário",
                    classe_farmacologica="Diurético",
                    protocolo="ACC/AHA 2022",
                    justificativa="Controlar congestão",
                    efeitos_colaterais=["Hipocaliemia"],
                    contra_indicacoes=[]
                )
            ])
            plano.frequencia_acompanhamento_dias = 30
            
        elif estagio == "SEVERA":
            plano.objetivos.append(
                Objetivo(
                    descricao="Reduzir sintomas, possível referência para transplante",
                    metrica="Classe NYHA",
                    valor_alvo=3,
                    unidade="classe",
                    prazo_dias=60,
                    prioridade="CRITICA"
                )
            )
            plano.medicamentos.extend([
                Medicamento(
                    nome="Sacubitril/Valsartan",
                    dose_inicial="49/51mg",
                    dose_alvo="97/103mg",
                    unidade="mg",
                    frequencia="12/12h",
                    classe_farmacologica="ARNI",
                    protocolo="ACC/AHA 2022",
                    justificativa="Melhor que IECA em IC reduzida",
                    efeitos_colaterais=["Hipotensão"],
                    contra_indicacoes=[]
                ),
                Medicamento(
                    nome="Carvedilol",
                    dose_inicial="6.25mg",
                    dose_alvo="25mg",
                    unidade="mg",
                    frequencia="12/12h",
                    classe_farmacologica="Beta-bloqueador",
                    protocolo="ACC/AHA 2022",
                    justificativa="Melhora mortalidade",
                    efeitos_colaterais=["Fadiga"],
                    contra_indicacoes=[]
                ),
                Medicamento(
                    nome="Espironolactona",
                    dose_inicial="12.5mg",
                    dose_alvo="50mg",
                    unidade="mg",
                    frequencia="24/24h",
                    classe_farmacologica="MRA",
                    protocolo="ACC/AHA 2022",
                    justificativa="Reduz mortalidade em IC",
                    efeitos_colaterais=["Hipercalemia"],
                    contra_indicacoes=["K >5.5"]
                ),
                Medicamento(
                    nome="Furosemida",
                    dose_inicial="80mg",
                    dose_alvo="160mg",
                    unidade="mg",
                    frequencia="12/12h",
                    classe_farmacologica="Diurético",
                    protocolo="ACC/AHA 2022",
                    justificativa="Controlar congestão severa",
                    efeitos_colaterais=["Hipocaliemia"],
                    contra_indicacoes=[]
                )
            ])
            plano.frequencia_acompanhamento_dias = 7
        
        plano.intervencoes.extend([
            Intervencao("NAO_FARMACOLOGICA", "Repouso", "Restrição atividades conforme classe NYHA", "conforme sintomas", "contínua", "paciente"),
            Intervencao("NAO_FARMACOLOGICA", "Dieta", "Dieta hipossódica <2g/dia", "contínua", "contínua", "nutricionista"),
            Intervencao("NAO_FARMACOLOGICA", "Monitoramento", "Pesar diariamente, relatar ganho >2kg", "diária", "contínua", "paciente")
        ])
        
        plano.exames_recomendados = ["BNP/NT-proBNP", "Ecocardiograma", "Eletrocardiograma", "Testes função renal"]
        plano.parametros_a_monitorar = ["Classe NYHA", "Peso corporal", "Dispneia", "Edema periférico"]

    @staticmethod
    def _criar_plano_asma(
        plano: PlanoCuidado,
        estagio: str,
        idade_anos: int
    ):
        """Plano para Asma (J45) - GINA 2023"""
        
        if estagio == "CONTROLADO":
            plano.objetivos.append(
                Objetivo(
                    descricao="Manter asma completamente controlada",
                    metrica="Sintomas",
                    valor_alvo=0,
                    unidade="dias/semana",
                    prazo_dias=365,
                    prioridade="MEDIA"
                )
            )
            plano.medicamentos.append(
                Medicamento(
                    nome="Salbutamol",
                    dose_inicial="100mcg",
                    dose_alvo="conforme necessário",
                    unidade="mcg",
                    frequencia="conforme necessário",
                    classe_farmacologica="Beta-2 agonista curta ação",
                    protocolo="GINA 2023",
                    justificativa="Resgate",
                    efeitos_colaterais=["Tremor"],
                    contra_indicacoes=[]
                )
            )
            plano.frequencia_acompanhamento_dias = 180
            
        elif estagio == "PARCIALMENTE_CONTROLADO":
            plano.objetivos.append(
                Objetivo(
                    descricao="Alcançar controle completo",
                    metrica="Sintomas",
                    valor_alvo=0,
                    unidade="dias/semana",
                    prazo_dias=90,
                    prioridade="ALTA"
                )
            )
            plano.medicamentos.extend([
                Medicamento(
                    nome="Budesonida/Formoterol",
                    dose_inicial="80/4.5mcg",
                    dose_alvo="160/4.5mcg",
                    unidade="mcg",
                    frequencia="12/12h",
                    classe_farmacologica="Corticosteroide/LABA",
                    protocolo="GINA 2023",
                    justificativa="Controlador, reduz exacerbações",
                    efeitos_colaterais=["Candidíase orofaríngea"],
                    contra_indicacoes=[]
                ),
                Medicamento(
                    nome="Salbutamol",
                    dose_inicial="100mcg",
                    dose_alvo="100mcg",
                    unidade="mcg",
                    frequencia="conforme necessário",
                    classe_farmacologica="Beta-2 agonista curta ação",
                    protocolo="GINA 2023",
                    justificativa="Resgate",
                    efeitos_colaterais=["Tremor"],
                    contra_indicacoes=[]
                )
            ])
            plano.frequencia_acompanhamento_dias = 60
            
        elif estagio == "NAO_CONTROLADO":
            plano.objetivos.append(
                Objetivo(
                    descricao="Controlar asma, reduzir exacerbações",
                    metrica="Crises/mês",
                    valor_alvo=0,
                    unidade="crises",
                    prazo_dias=60,
                    prioridade="CRITICA"
                )
            )
            plano.medicamentos.extend([
                Medicamento(
                    nome="Fluticasona/Salmeterol",
                    dose_inicial="125/25mcg",
                    dose_alvo="250/25mcg",
                    unidade="mcg",
                    frequencia="12/12h",
                    classe_farmacologica="Corticosteroide/LABA",
                    protocolo="GINA 2023",
                    justificativa="Controlador intensivo",
                    efeitos_colaterais=["Candidíase"],
                    contra_indicacoes=[]
                ),
                Medicamento(
                    nome="Montelucaste",
                    dose_inicial="10mg",
                    dose_alvo="10mg",
                    unidade="mg",
                    frequencia="24/24h",
                    classe_farmacologica="Antagonista leucotrieno",
                    protocolo="GINA 2023",
                    justificativa="Reduz inflamação",
                    efeitos_colaterais=["Disturbios comportamentais"],
                    contra_indicacoes=[]
                ),
                Medicamento(
                    nome="Omalizumab",
                    dose_inicial="150mg",
                    dose_alvo="300mg",
                    unidade="mg",
                    frequencia="2-4 semanas",
                    classe_farmacologica="Biológico anti-IgE",
                    protocolo="GINA 2023",
                    justificativa="Para asma alérgica não controlada",
                    efeitos_colaterais=["Anafilaxi"],
                    contra_indicacoes=["IgE >700"]
                )
            ])
            plano.frequencia_acompanhamento_dias = 14
        
        plano.intervencoes.extend([
            Intervencao("NAO_FARMACOLOGICA", "Educação", "Técnica de inalação, reconhecer sinais alerta", "1-2 sessões", "8 semanas", "nurse educator"),
            Intervencao("NAO_FARMACOLOGICA", "Ambiente", "Evitar desencadeantes alérgicos", "contínua", "contínua", "paciente"),
            Intervencao("NAO_FARMACOLOGICA", "Exercício", "Exercício regular com aquecimento", "3-5x/semana", "contínua", "paciente")
        ])
        
        plano.exames_recomendados = ["Espirometria", "IgE total"]
        plano.parametros_a_monitorar = ["VEF1", "Pico fluxo", "Frequência de crises"]
        
        return plano
