"""
Modelos SQLAlchemy para o módulo Oswaldo.

Tabelas:
1. CondicaoCronica - Diagnóstico de doenças crônicas
2. Estadiamento - Classificação/staging da doença (NYHA, KDIGO, etc)
3. PlanoCuidado - Plano terapêutico personalizado
4. Acompanhamento - Visitas clínicas / Follow-up
5. Alerta - Alertas clínicos para descontrole/piora
"""

from sqlalchemy import Column, Integer, String, Date, DateTime, Float, JSON, Boolean, ForeignKey, Index, Text, func
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

Base = declarative_base()


# ========================================================================
# 1. CONDICAO_CRONICA - Diagnóstico de doença crônica
# ========================================================================
class CondicaoCronica(Base):
    """
    Armazena diagnóstico de doença crônica de um paciente.
    
    Fluxo: PENDENTE_VALIDACAO → CONFIRMADO → (REVISADO | SUSPENSO | ENCERRADO)
    """
    __tablename__ = "condicao_cronica"
    
    # Chave primária
    id = Column(Integer, primary_key=True, index=True)
    
    # Paciente (referência ao hash CPF de Florence)
    paciente_cpf_hash = Column(String(64), nullable=False, index=True)
    
    # Diagnóstico
    cid10 = Column(String(10), nullable=False, index=True)  # I10 (HAS), E11 (DM2), N18 (DRC), etc
    
    # Dados de diagnóstico
    data_diagnostico = Column(Date, nullable=False)
    medico_diagnosticador = Column(String(100), nullable=True)
    confirmacao_exames = Column(Boolean, default=False)
    
    # Status e classificação
    status = Column(String(50), nullable=False, index=True, default="PENDENTE_VALIDACAO")
    # PENDENTE_VALIDACAO | CONFIRMADO | REVISADO | SUSPENSO | ENCERRADO
    
    gravidade_inicial = Column(String(20), nullable=True)  # LEVE, MODERADA, GRAVE
    
    # Auditoria
    criado_em = Column(DateTime, nullable=False, server_default=func.now(), index=True)
    atualizado_em = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())
    
    # Índices compostos
    __table_args__ = (
        Index("idx_paciente_status", "paciente_cpf_hash", "status"),
        Index("idx_cid10_data", "cid10", "data_diagnostico"),
    )
    
    # Relacionamentos
    estadiamentos = relationship("Estadiamento", back_populates="condicao", cascade="all, delete-orphan")
    acompanhamentos = relationship("Acompanhamento", back_populates="condicao", cascade="all, delete-orphan")
    plano_cuidado = relationship("PlanoCuidado", back_populates="condicao", uselist=False, cascade="all, delete-orphan")
    alertas = relationship("Alerta", back_populates="condicao", cascade="all, delete-orphan")


# ========================================================================
# 2. ESTADIAMENTO - Classificação/staging da doença
# ========================================================================
class Estadiamento(Base):
    """
    Armazena histórico de classificação/staging de doença crônica.
    
    Exemplos de sistemas: NYHA (cardiac), KDIGO (renal), SBC (hypertension), ADA (diabetes)
    """
    __tablename__ = "estadiamento"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Referência à condição crônica
    condicao_cronica_id = Column(Integer, ForeignKey("condicao_cronica.id"), nullable=False, index=True)
    
    # Classificação
    sistema_classificacao = Column(String(50), nullable=False)  # NYHA, KDIGO, ABCD, SBC, ADA, etc
    estagio = Column(String(20), nullable=False)  # I, II, III, IV, G1-G5, A1-A3, etc
    
    # Auditoria temporal
    data_classificacao = Column(DateTime, nullable=False, server_default=func.now(), index=True)
    
    # Dados suportadores
    criterios = Column(JSON, nullable=True)  # {"PA_sys": 160, "PA_dia": 100, "resultado": "ESTAGIO_2"}
    exames_suporte = Column(JSON, nullable=True)  # [{"id": 123, "tipo": "PA", "valor": 160}]
    
    # Índices
    __table_args__ = (
        Index("idx_condicao_data", "condicao_cronica_id", "data_classificacao"),
    )
    
    # Relacionamento
    condicao = relationship("CondicaoCronica", back_populates="estadiamentos")


# ========================================================================
# 3. PLANO_CUIDADO - Plano terapêutico personalizado
# ========================================================================
class PlanoCuidado(Base):
    """
    Armazena plano de cuidado personalizado para uma condição crônica.
    
    Contém: objetivos SMART, intervenções, medicamentos, educação em saúde.
    """
    __tablename__ = "plano_cuidado"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Referência única à condição
    condicao_cronica_id = Column(Integer, ForeignKey("condicao_cronica.id"), nullable=False, unique=True, index=True)
    
    # Validade do plano
    data_inicio = Column(Date, nullable=False)
    data_revisao = Column(Date, nullable=True)  # Próxima revisão programada
    
    # Status
    status = Column(String(50), nullable=False, default="ATIVO")
    # ATIVO | REVISADO | SUSPENSO | ENCERRADO
    
    # Conteúdo do plano
    objetivos = Column(JSON, nullable=False)  
    # [{"objetivo": "Reduzir PA < 140/90", "prazo": "3 meses", "indicador": "PA_media"}]
    
    intervencoes = Column(JSON, nullable=False)
    # [{"tipo": "medicamento", "descricao": "Losartan 50mg"}, {"tipo": "exercicio", "freq": "3x/semana"}]
    
    medicamentos = Column(JSON, nullable=False)
    # [{"nome": "Losartan", "dose": 50, "unidade": "mg", "frequencia": "1x/dia"}]
    
    educacao_saude = Column(JSON, nullable=True)
    # [{"tema": "Redução de sal na dieta", "data_inicio": "2026-02-12"}]
    
    # Auditoria
    criado_em = Column(DateTime, nullable=False, server_default=func.now())
    atualizado_em = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())
    
    # Relacionamento
    condicao = relationship("CondicaoCronica", back_populates="plano_cuidado")


# ========================================================================
# 4. ACOMPANHAMENTO - Visitas clínicas / Follow-up
# ========================================================================
class Acompanhamento(Base):
    """
    Armazena registro de acompanhamento clínico (visita/consulta).
    
    Captura: vitais, observações clínicas, adesão ao plano, próximos passos.
    """
    __tablename__ = "acompanhamento"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Referências
    paciente_cpf_hash = Column(String(64), nullable=False, index=True)
    condicao_cronica_id = Column(Integer, ForeignKey("condicao_cronica.id"), nullable=False, index=True)
    
    # Consulta
    data_acompanhamento = Column(DateTime, nullable=False, index=True)
    medico_id = Column(String(50), nullable=False)
    local_consulta = Column(String(100), nullable=True)
    
    # Vitais e biométricos
    pressao_arterial = Column(String(20), nullable=True)  # "160/100"
    peso_kg = Column(Float, nullable=True)
    glicemia = Column(Float, nullable=True)
    temperatura = Column(Float, nullable=True)
    
    # Clínico
    adesao_medicamentos = Column(String(20), nullable=True)  # BOA, REGULAR, RUIM
    observacoes = Column(Text, nullable=True)
    medicamentos_vigentes = Column(JSON, nullable=True)  # Medicamentos atuais do paciente
    proxima_consulta = Column(Date, nullable=True)
    
    # Auditoria
    criado_em = Column(DateTime, nullable=False, server_default=func.now())
    atualizado_em = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())
    
    # Índices
    __table_args__ = (
        Index("idx_paciente_data", "paciente_cpf_hash", "data_acompanhamento"),
        Index("idx_condicao_data_acomp", "condicao_cronica_id", "data_acompanhamento"),
    )
    
    # Relacionamento
    condicao = relationship("CondicaoCronica", back_populates="acompanhamentos")


# ========================================================================
# 5. ALERTA - Alertas clínicos
# ========================================================================
class Alerta(Base):
    """
    Armazena alertas clínicos para descontrole, piora ou eventos adversos.
    
    Tipos: DESCONTROLE, PIORA_PROGRESSIVA, ALERGICO, OUTRO
    Severidade: BAIXA, MEDIA, ALTA, CRITICA
    """
    __tablename__ = "alerta"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Referências
    paciente_cpf_hash = Column(String(64), nullable=False, index=True)
    condicao_cronica_id = Column(Integer, ForeignKey("condicao_cronica.id"), nullable=False, index=True)
    
    # Tipo e severidade
    tipo_alerta = Column(String(50), nullable=False, index=True)
    # DESCONTROLE | PIORA_PROGRESSIVA | ALERGICO | OUTRO
    
    severidade = Column(String(20), nullable=False, index=True)
    # BAIXA | MEDIA | ALTA | CRITICA
    
    # Conteúdo
    descricao = Column(String(256), nullable=False)
    dados_alerta = Column(JSON, nullable=True)  # {"parametro": "glicemia", "valor": 450, "limite": 200}
    
    # Status
    status = Column(String(20), nullable=False, index=True, default="NOVO")
    # NOVO | ATRIBUIDO | RESOLVIDO | IGNORADO
    
    # Auditoria
    data_criacao = Column(DateTime, nullable=False, server_default=func.now(), index=True)
    data_resolvido = Column(DateTime, nullable=True)
    medico_atribuido = Column(String(50), nullable=True)
    
    # Índices
    __table_args__ = (
        Index("idx_paciente_severidade", "paciente_cpf_hash", "severidade"),
        Index("idx_status_data", "status", "data_criacao"),
    )
    
    # Relacionamento
    condicao = relationship("CondicaoCronica", back_populates="alertas")
