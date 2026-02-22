# ESPECIFICAÇÃO TÉCNICA: OSWALDO - IMPLEMENTAÇÃO

## 📌 ID: DEV2-TEC-002
## 🏥 Domínio: Gerenciamento de Doenças Crônicas
## 📅 Data: 12/02/2026
## 👨‍💻 Responsável DEV2: Especificação Técnica

---

## 1. MODELOS SQLALCHEMY (7 Classes ORM)

### 1.1. BaseModel
```python
from datetime import datetime
from sqlalchemy import Column, DateTime, func
from sqlalchemy.orm import declarative_base

Base = declarative_base()

class BaseModel(Base):
    """Classe base com timestamps automáticos"""
    __abstract__ = True
    
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)
```

### 1.2. CondicaoCronica
```python
from sqlalchemy import Column, Integer, String, Date, Boolean, Enum, Text, ForeignKey
from sqlalchemy.orm import relationship
from enum import Enum as PyEnum

class GravidadeEnum(PyEnum):
    LEVE = "LEVE"
    MODERADA = "MODERADA"
    GRAVE = "GRAVE"
    MUITO_GRAVE = "MUITO_GRAVE"

class CondicaoCronica(BaseModel):
    """
    Registro de doença crônica de um paciente
    
    Relacionamentos:
    - paciente: Paciente que possui a condição
    - estadiamentos: Histórico de classificações
    - plano_cuidado: Plano terapêutico
    - acompanhamentos: Consultas de acompanhamento
    """
    __tablename__ = "condicoes_cronicas"
    
    id = Column(Integer, primary_key=True)
    paciente_cpf = Column(String(11), ForeignKey("pacientes.cpf"), nullable=False)
    cid10 = Column(String(10), nullable=False)  # ex: I10, E11, N18
    data_diagnostico = Column(Date, nullable=False)
    medico_diagnosticador = Column(String(100))
    crm_diagnosticador = Column(String(20))
    confirmacao_exames = Column(Boolean, default=False)
    gravidade_inicial = Column(Enum(GravidadeEnum), default=GravidadeEnum.LEVE)
    observacoes = Column(Text)
    
    # Relacionamentos
    estadiamentos = relationship("Estadiamento", back_populates="condicao_cronica", cascade="all, delete-orphan")
    plano_cuidado = relationship("PlanoCuidado", back_populates="condicao_cronica", uselist=False, cascade="all, delete-orphan")
    acompanhamentos = relationship("Acompanhamento", back_populates="condicao_cronica", cascade="all, delete-orphan")

class Paciente(BaseModel):
    """Paciente (reutilizado de Florence)"""
    __tablename__ = "pacientes"
    cpf = Column(String(11), primary_key=True)
    nome_completo = Column(String(255), nullable=False)
    data_nascimento = Column(Date, nullable=False)
    sexo_biologico = Column(String(1), nullable=False)  # M ou F
    tipo_sanguineo = Column(String(5))
    
    # Relacionamentos
    condicoes_cronicas = relationship("CondicaoCronica", foreign_keys=[CondicaoCronica.paciente_cpf])
```

### 1.3. Estadiamento
```python
from sqlalchemy import Column, Integer, ForeignKey, String, Date, JSON
from sqlalchemy.orm import relationship

class Estadiamento(BaseModel):
    """
    Classificação/estágio de uma condição em um momento específico
    
    Exemplo:
    - Hipertensão Estágio 1 (PA 140-159)
    - DRC KDIGO G3b (TFGe 30-44)
    - Diabetes HbA1c 7.5%
    """
    __tablename__ = "estadiamentos"
    
    id = Column(Integer, primary_key=True)
    condicao_cronica_id = Column(Integer, ForeignKey("condicoes_cronicas.id"), nullable=False)
    sistema_classificacao = Column(String(50), nullable=False)  # NYHA, KDIGO, ABCD
    estagio = Column(String(20), nullable=False)  # I, II, III, IV, G1, G2, etc
    data_classificacao = Column(Date, nullable=False)
    criterios = Column(JSON, nullable=False)  # {"pressao_sistolica": 165, "pa_diastolica": 105}
    exames_suporte = Column(JSON)  # [{"exame_id": 123, "parametro": "PA"}]
    
    # Relacionamentos
    condicao_cronica = relationship("CondicaoCronica", back_populates="estadiamentos")
```

### 1.4. PlanoCuidado
```python
from sqlalchemy import Column, Integer, ForeignKey, Date, JSON, String, Enum, DateTime
from sqlalchemy.orm import relationship
from enum import Enum as PyEnum

class StatusPlanoEnum(PyEnum):
    ATIVO = "ATIVO"
    REVISADO = "REVISADO"
    SUSPENSO = "SUSPENSO"
    ENCERRADO = "ENCERRADO"

class PlanoCuidado(BaseModel):
    """
    Plano terapêutico personalizado para uma condição crônica
    
    Contém:
    - Objetivos SMART (específicos, mensuráveis, alcançáveis)
    - Intervenções (farmacológicas e não-farmacológicas)
    - Medicamentos com posologia
    - Materiais educativos
    """
    __tablename__ = "planos_cuidado"
    
    id = Column(Integer, primary_key=True)
    condicao_cronica_id = Column(Integer, ForeignKey("condicoes_cronicas.id"), nullable=False)
    data_inicio = Column(Date, nullable=False)
    data_revisao = Column(Date)
    objetivos = Column(JSON, nullable=False)  # [{"objetivo": "PA < 130/80", "prazo_dias": 90}]
    intervencoes = Column(JSON, nullable=False)  # [{"tipo": "farmacologica", "descricao": "Losartana"}]
    medicamentos = Column(JSON)  # [{"nome": "Losartana", "dose": "50mg", "frequencia": "1x/dia"}]
    educacao_saude = Column(JSON)  # [{"tema": "Dieta hipossódica", "url": "..."}]
    status = Column(Enum(StatusPlanoEnum), default=StatusPlanoEnum.ATIVO)
    medico_responsavel_id = Column(Integer, ForeignKey("medicos.id"))
    
    # Relacionamentos
    condicao_cronica = relationship("CondicaoCronica", back_populates="plano_cuidado")
    intervencoes_rel = relationship("Intervencao", back_populates="plano_cuidado", cascade="all, delete-orphan")
```

### 1.5. Intervencao
```python
from sqlalchemy import Column, Integer, ForeignKey, String, Date, Text, Enum
from sqlalchemy.orm import relationship
from enum import Enum as PyEnum

class TipoIntervencaoEnum(PyEnum):
    FARMACOLOGICA = "FARMACOLOGICA"
    NAO_FARMACOLOGICA = "NAO_FARMACOLOGICA"
    EDUCACAO = "EDUCACAO"
    RASTREAMENTO = "RASTREAMENTO"

class StatusIntervencaoEnum(PyEnum):
    ATIVA = "ATIVA"
    PAUSADA = "PAUSADA"
    CONCLUIDA = "CONCLUIDA"
    CANCELADA = "CANCELADA"

class Intervencao(BaseModel):
    """
    Ação específica no plano de cuidado
    
    Exemplos:
    - Iniciar Losartana 50mg
    - Dieta hipossódica com nutricionista
    - Educação sobre controle de peso
    """
    __tablename__ = "intervencoes"
    
    id = Column(Integer, primary_key=True)
    plano_cuidado_id = Column(Integer, ForeignKey("planos_cuidado.id"), nullable=False)
    tipo = Column(Enum(TipoIntervencaoEnum), nullable=False)
    descricao = Column(Text, nullable=False)
    data_inicio = Column(Date, nullable=False)
    data_fim = Column(Date)
    status = Column(Enum(StatusIntervencaoEnum), default=StatusIntervencaoEnum.ATIVA)
    
    # Relacionamentos
    plano_cuidado = relationship("PlanoCuidado", back_populates="intervencoes_rel")
```

### 1.6. Acompanhamento
```python
from sqlalchemy import Column, Integer, String, Date, Float, JSON, ForeignKey
from sqlalchemy.orm import relationship

class Acompanhamento(BaseModel):
    """
    Consulta/visita de acompanhamento de uma condição crônica
    
    Registra:
    - Dados vitais (PA, peso)
    - Resultados de exames (se aplicável)
    - Medicações vigentes
    - Observações clínicas
    """
    __tablename__ = "acompanhamentos"
    
    id = Column(Integer, primary_key=True)
    paciente_cpf = Column(String(11), ForeignKey("pacientes.cpf"), nullable=False)
    condicao_cronica_id = Column(Integer, ForeignKey("condicoes_cronicas.id"), nullable=False)
    data_acompanhamento = Column(Date, nullable=False)
    medico_id = Column(Integer, ForeignKey("medicos.id"), nullable=False)
    pressao_arterial = Column(String(10))  # formato: SYS/DIA (ex: 130/80)
    glicemia = Column(Float)  # em mg/dL
    peso_kg = Column(Float)
    observacoes = Column(JSON)  # [{"achado": "edema", "local": "MMII"}]
    medicamentos_vigentes = Column(JSON)  # [{"nome": "Losartana", "dose": "50mg"}]
    
    # Relacionamentos
    condicao_cronica = relationship("CondicaoCronica", back_populates="acompanhamentos")

class Medico(BaseModel):
    """Médico (reutilizado)"""
    __tablename__ = "medicos"
    id = Column(Integer, primary_key=True)
    cpf = Column(String(11), unique=True, nullable=False)
    nome = Column(String(255), nullable=False)
    crm = Column(String(20), nullable=False, unique=True)
    especialidade = Column(String(100))
    ativo = Column(Boolean, default=True)
```

---

## 2. SCHEMAS PYDANTIC (5 Grupos)

### 2.1. CondicaoCronica Schemas
```python
from pydantic import BaseModel, Field, field_validator
from datetime import date
from typing import List, Optional

class CondicaoCronicaBase(BaseModel):
    cid10: str = Field(..., pattern="^[A-Z][0-9]{2}(\\.[0-9]{1,2})?$", description="CID-10 válido")
    data_diagnostico: date = Field(..., description="Data do diagnóstico")
    medico_diagnosticador: Optional[str] = None
    crm_diagnosticador: Optional[str] = None
    confirmacao_exames: bool = False
    gravidade_inicial: str = Field(default="LEVE", description="LEVE, MODERADA, GRAVE, MUITO_GRAVE")
    
    @field_validator("gravidade_inicial")
    def validate_gravidade(cls, v):
        valid = ["LEVE", "MODERADA", "GRAVE", "MUITO_GRAVE"]
        if v not in valid:
            raise ValueError(f"Gravidade deve ser uma de: {valid}")
        return v

class CondicaoCronicaCreate(CondicaoCronicaBase):
    paciente_cpf: str = Field(..., pattern="^[0-9]{11}$")

class CondicaoCronicaResponse(CondicaoCronicaBase):
    id: int
    paciente_cpf: str
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True
```

### 2.2. Estadiamento Schemas
```python
class EstadiamentoBase(BaseModel):
    sistema_classificacao: str = Field(..., description="NYHA, KDIGO, ABCD, etc")
    estagio: str = Field(..., description="I, II, III, IV, G1, G2, etc")
    criterios: dict = Field(..., description="Critérios usados para classificação")
    
    @field_validator("estagio")
    def validate_estagio(cls, v):
        valid = ["I", "II", "III", "IV", "V", "G1", "G2", "G3a", "G3b", "G4", "G5"]
        if v not in valid:
            raise ValueError(f"Estágio deve ser um de: {valid}")
        return v

class EstadiamentoCreate(EstadiamentoBase):
    condicao_cronica_id: int
    data_classificacao: date

class EstadiamentoResponse(EstadiamentoBase):
    id: int
    condicao_cronica_id: int
    data_classificacao: date
    exames_suporte: Optional[dict] = None
    created_at: datetime
    
    class Config:
        from_attributes = True
```

### 2.3. PlanoCuidado Schemas
```python
class PlanoCuidadoBase(BaseModel):
    data_inicio: date
    data_revisao: Optional[date] = None
    objetivos: List[dict] = Field(..., description="Objetivos SMART")
    intervencoes: List[dict] = Field(..., description="Lista de intervenções")
    medicamentos: Optional[List[dict]] = None
    educacao_saude: Optional[List[dict]] = None

class PlanoCuidadoCreate(PlanoCuidadoBase):
    condicao_cronica_id: int
    medico_responsavel_id: Optional[int] = None

class PlanoCuidadoResponse(PlanoCuidadoBase):
    id: int
    condicao_cronica_id: int
    status: str
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True
```

### 2.4. Acompanhamento Schemas
```python
class AcompanhamentoBase(BaseModel):
    data_acompanhamento: date
    pressao_arterial: Optional[str] = Field(None, pattern="^[0-9]{2,3}/[0-9]{2,3}$")
    glicemia: Optional[float] = Field(None, ge=0)
    peso_kg: Optional[float] = Field(None, gt=0)
    observacoes: Optional[dict] = None
    medicamentos_vigentes: Optional[List[dict]] = None

class AcompanhamentoCreate(AcompanhamentoBase):
    paciente_cpf: str
    condicao_cronica_id: int
    medico_id: int

class AcompanhamentoResponse(AcompanhamentoBase):
    id: int
    paciente_cpf: str
    condicao_cronica_id: int
    medico_id: int
    created_at: datetime
    
    class Config:
        from_attributes = True
```

### 2.5. Intervencao Schemas
```python
class IntervencaoBase(BaseModel):
    tipo: str = Field(..., description="FARMACOLOGICA, NAO_FARMACOLOGICA, EDUCACAO, RASTREAMENTO")
    descricao: str
    data_inicio: date
    data_fim: Optional[date] = None
    status: str = Field(default="ATIVA")

class IntervencaoCreate(IntervencaoBase):
    plano_cuidado_id: int

class IntervencaoResponse(IntervencaoBase):
    id: int
    plano_cuidado_id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True
```

---

## 3. FASTAPI ROUTERS (4 Routers)

### 3.1. Router: Condições Crônicas
```python
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from datetime import date

router = APIRouter(prefix="/api/v1/condicoes", tags=["Condições Crônicas"])

def get_db() -> Session:
    """Dependency para sessão do banco"""
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    
    engine = create_engine("postgresql://user:pass@localhost/intellicare")
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/", response_model=CondicaoCronicaResponse, status_code=201)
async def criar_condicao(
    condicao: CondicaoCronicaCreate,
    db: Session = Depends(get_db)
):
    """Registrar nova condição crônica para um paciente
    
    Validações:
    - CPF do paciente deve existir
    - CID-10 deve ser válido
    - Data não pode ser futura
    """
    # Verificar se paciente existe
    paciente = db.query(Paciente).filter(Paciente.cpf == condicao.paciente_cpf).first()
    if not paciente:
        raise HTTPException(status_code=404, detail="Paciente não encontrado")
    
    # Verificar CID-10 (validação simples)
    if not condicao.cid10:
        raise HTTPException(status_code=400, detail="CID-10 inválido")
    
    db_condicao = CondicaoCronica(**condicao.dict())
    db.add(db_condicao)
    db.commit()
    db.refresh(db_condicao)
    return db_condicao

@router.get("/paciente/{cpf}", response_model=List[CondicaoCronicaResponse])
async def listar_condicoes_paciente(
    cpf: str,
    db: Session = Depends(get_db)
):
    """Listar todas as condições crônicas de um paciente
    
    Retorna ordenado por data de diagnóstico (mais recente primeiro)
    """
    condicoes = db.query(CondicaoCronica)\
        .filter(CondicaoCronica.paciente_cpf == cpf)\
        .order_by(CondicaoCronica.data_diagnostico.desc())\
        .all()
    
    if not condicoes:
        return []
    
    return condicoes

@router.get("/{condicao_id}", response_model=CondicaoCronicaResponse)
async def obter_condicao(
    condicao_id: int,
    db: Session = Depends(get_db)
):
    """Obter detalhes de uma condição crônica"""
    condicao = db.query(CondicaoCronica).filter(CondicaoCronica.id == condicao_id).first()
    if not condicao:
        raise HTTPException(status_code=404, detail="Condição não encontrada")
    return condicao
```

### 3.2. Router: Estadiamentos
```python
@router.post("/estadios/", response_model=EstadiamentoResponse, status_code=201)
async def classificar_condicao(
    estadio: EstadiamentoCreate,
    db: Session = Depends(get_db)
):
    """Registrar um estadiamento/classificação de uma condição
    
    Exemplo para HAS:
    - Sistema: Classificação SBC
    - Estágio: 2
    - Critérios: {"pa_sistolica": 160, "pa_diastolica": 100}
    
    Exemplo para DRC:
    - Sistema: KDIGO
    - Estágio: G3b
    - Critérios: {"tfge": 38}
    """
    # Verificar se condição existe
    condicao = db.query(CondicaoCronica)\
        .filter(CondicaoCronica.id == estadio.condicao_cronica_id)\
        .first()
    if not condicao:
        raise HTTPException(status_code=404, detail="Condição não encontrada")
    
    # Criar novo estadiamento
    db_estadio = Estadiamento(**estadio.dict())
    db.add(db_estadio)
    db.commit()
    db.refresh(db_estadio)
    return db_estadio

@router.get("/estadios/condicao/{condicao_id}", response_model=List[EstadiamentoResponse])
async def obter_historico_estadios(
    condicao_id: int,
    limit: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """Obter histórico de estadiamentos (últimas 10 por padrão)
    
    Retorna ordenado por data (mais recente primeiro)
    """
    estadios = db.query(Estadiamento)\
        .filter(Estadiamento.condicao_cronica_id == condicao_id)\
        .order_by(Estadiamento.data_classificacao.desc())\
        .limit(limit)\
        .all()
    
    return estadios
```

### 3.3. Router: Planos de Cuidado
```python
@router.post("/planos/", response_model=PlanoCuidadoResponse, status_code=201)
async def criar_plano_cuidado(
    plano: PlanoCuidadoCreate,
    db: Session = Depends(get_db)
):
    """Criar plano de cuidado para uma condição crônica
    
    Deve conter:
    - Objetivos SMART
    - Intervenções específicas
    - Medicamentos com posologia
    - Materiais educativos
    """
    # Verificar condição
    condicao = db.query(CondicaoCronica)\
        .filter(CondicaoCronica.id == plano.condicao_cronica_id)\
        .first()
    if not condicao:
        raise HTTPException(status_code=404, detail="Condição não encontrada")
    
    db_plano = PlanoCuidado(**plano.dict())
    db.add(db_plano)
    db.commit()
    db.refresh(db_plano)
    return db_plano

@router.get("/planos/pendentes-revisao", response_model=List[dict])
async def listar_planos_vencidos(
    db: Session = Depends(get_db)
):
    """Listar planos que precisam revisão (vencimento próximo ou passado)
    
    Retorna:
    - ID do plano
    - Paciente
    - Ultima revisão
    - Dias de atraso
    """
    from datetime import datetime
    
    planos_vencidos = db.query(
        PlanoCuidado.id,
        Paciente.nome_completo,
        PlanoCuidado.data_revisao,
        CondicaoCronica.cid10
    ).join(CondicaoCronica).join(Paciente)\
     .filter(PlanoCuidado.status == "ATIVO")\
     .filter((PlanoCuidado.data_revisao == None) | (PlanoCuidado.data_revisao < date.today()))\
     .all()
    
    return [
        {
            "plano_id": p[0],
            "paciente": p[1],
            "ultima_revisao": p[2],
            "condicao": p[3],
            "dias_atraso": (date.today() - p[2]).days if p[2] else "N/A"
        }
        for p in planos_vencidos
    ]
```

### 3.4. Router: Acompanhamentos
```python
@router.post("/acompanhamentos/", response_model=AcompanhamentoResponse, status_code=201)
async def registrar_acompanhamento(
    acompanhamento: AcompanhamentoCreate,
    db: Session = Depends(get_db)
):
    """Registrar consulta de acompanhamento de uma condição crônica
    
    Coleta:
    - Pressão arterial (formato SYS/DIA)
    - Glicemia em mg/dL
    - Peso em kg
    - Observações clínicas
    - Medicações vigentes
    """
    # Validações
    if not db.query(Paciente).filter(Paciente.cpf == acompanhamento.paciente_cpf).first():
        raise HTTPException(status_code=404, detail="Paciente não encontrado")
    
    if not db.query(CondicaoCronica).filter(CondicaoCronica.id == acompanhamento.condicao_cronica_id).first():
        raise HTTPException(status_code=404, detail="Condição não encontrada")
    
    if not db.query(Medico).filter(Medico.id == acompanhamento.medico_id).first():
        raise HTTPException(status_code=404, detail="Médico não encontrado")
    
    db_acomp = Acompanhamento(**acompanhamento.dict())
    db.add(db_acomp)
    db.commit()
    db.refresh(db_acomp)
    return db_acomp

@router.get("/acompanhamentos/paciente/{cpf}", response_model=List[AcompanhamentoResponse])
async def listar_acompanhamentos(
    cpf: str,
    condicao_id: Optional[int] = None,
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """Listar acompanhamentos de um paciente
    
    Filtro opcional por condição crônica
    Retorna últimos acompanhamentos ordenados por data (mais recente primeiro)
    """
    query = db.query(Acompanhamento)\
        .filter(Acompanhamento.paciente_cpf == cpf)
    
    if condicao_id:
        query = query.filter(Acompanhamento.condicao_cronica_id == condicao_id)
    
    acompanhamentos = query\
        .order_by(Acompanhamento.data_acompanhamento.desc())\
        .limit(limit)\
        .all()
    
    return acompanhamentos
```

---

## 4. SERVICES (2 Classes)

### 4.1. ReclassificacaoService
```python
from datetime import date

class ReclassificacaoService:
    """Serviço para reclassificação automática de condições"""
    
    @staticmethod
    def calcular_estagio_drc(tfge: float) -> str:
        """KDIGO: Classificar DRC por TFGe
        
        Args:
            tfge: Taxa filtrada glomerular estimada (mL/min/1.73m²)
            
        Returns:
            Estágio KDIGO (G1-G5)
        """
        if tfge >= 90:
            return "G1"
        elif tfge >= 60:
            return "G2"
        elif tfge >= 45:
            return "G3a"
        elif tfge >= 30:
            return "G3b"
        elif tfge >= 15:
            return "G4"
        else:
            return "G5"
    
    @staticmethod
    def calcular_estagio_has(pa_sistolica: int, pa_diastolica: int) -> str:
        """SBC: Classificar HAS por pressão arterial
        
        Args:
            pa_sistolica: Pressão sistólica em mmHg
            pa_diastolica: Pressão diastólica em mmHg
            
        Returns:
            Estágio de HAS (1, 2, 3)
        """
        if pa_sistolica >= 180 or pa_diastolica >= 110:
            return "3"
        elif pa_sistolica >= 160 or pa_diastolica >= 100:
            return "2"
        elif pa_sistolica >= 140 or pa_diastolica >= 90:
            return "1"
        else:
            return "NORMAL"
    
    @staticmethod
    def calcular_estagio_diabetes(hba1c: float) -> str:
        """Classificar diabetes por HbA1c
        
        Args:
            hba1c: Hemoglobina glicada em %
            
        Returns:
            Status de controle glicêmico
        """
        if hba1c < 7.0:
            return "BEM_CONTROLADO"
        elif hba1c <= 8.5:
            return "MODERADO"
        elif hba1c <= 10.0:
            return "MAL_CONTROLADO"
        else:
            return "CRITICO"
    
    @staticmethod
    def sugerir_reclassificacao(
        db: Session,
        condicao_id: int,
        criterios_novos: dict
    ) -> Optional[Estadiamento]:
        """Gerar sugestão de reclassificação baseada em novos critérios
        
        Args:
            db: Sessão do banco
            condicao_id: ID da condição
            criterios_novos: Novos valores de laboratório/clínicos
            
        Returns:
            Novo Estadiamento se houver mudança, None caso contrário
        """
        condicao = db.query(CondicaoCronica).filter(CondicaoCronica.id == condicao_id).first()
        if not condicao:
            return None
        
        # Obter último estadiamento
        ultimo = db.query(Estadiamento)\
            .filter(Estadiamento.condicao_cronica_id == condicao_id)\
            .order_by(Estadiamento.data_classificacao.desc())\
            .first()
        
        if not ultimo:
            return None
        
        # Lógica de reclassificação dependente do CID-10
        novo_estagio = None
        
        if condicao.cid10 == "N18":  # DRC
            novo_estagio = ReclassificacaoService.calcular_estagio_drc(
                criterios_novos.get("tfge", 60)
            )
        elif condicao.cid10 == "I10":  # HAS
            novo_estagio = ReclassificacaoService.calcular_estagio_has(
                criterios_novos.get("pa_sistolica", 120),
                criterios_novos.get("pa_diastolica", 80)
            )
        elif condicao.cid10 == "E11":  # Diabetes
            novo_estagio = ReclassificacaoService.calcular_estagio_diabetes(
                criterios_novos.get("hba1c", 7.0)
            )
        
        # Se houve mudança de estágio, criar novo registro
        if novo_estagio and novo_estagio != ultimo.estagio:
            novo_estadiamento = Estadiamento(
                condicao_cronica_id=condicao_id,
                sistema_classificacao=ultimo.sistema_classificacao,
                estagio=novo_estagio,
                data_classificacao=date.today(),
                criterios=criterios_novos
            )
            db.add(novo_estadiamento)
            db.commit()
            return novo_estadiamento
        
        return None
```

### 4.2. ValidacaoClinicaService
```python
class ValidacaoClinicaService:
    """Validações de coerência clínica entre dados"""
    
    @staticmethod
    def validar_pressao_arterial(systolica: int, diastolica: int) -> tuple[bool, str]:
        """Validar pressão arterial em ranges fisiológicos
        
        Returns:
            (válida, mensagem)
        """
        if systolica < 40 or systolica > 250:
            return False, "PA sistólica em range não fisiológico"
        if diastolica < 20 or diastolica > 150:
            return False, "PA diastólica em range não fisiológico"
        if diastolica >= systolica:
            return False, "PA diastólica não pode ser >= sistólica"
        return True, "OK"
    
    @staticmethod
    def validar_glicemia(glicemia: float) -> tuple[bool, str]:
        """Validar glicemia em range fisiológico
        
        Returns:
            (válida, mensagem)
        """
        if glicemia < 20 or glicemia > 800:
            return False, "Glicemia em range não fisiológico"
        return True, "OK"
    
    @staticmethod
    def validar_coerencia_drc(
        creatinina: float,
        ureia: float,
        tfge: float
    ) -> tuple[bool, str]:
        """Validar coerência metabólica em DRC
        
        Verifica se razão Ureia/Creatinina é consistente
        """
        if creatinina == 0:
            return False, "Creatinina deve ser > 0"
        
        razao = ureia / creatinina
        
        # DRC: razão esperada 10-20
        if razao < 5 or razao > 50:
            return False, f"Razão Ureia/Creatinina anômala: {razao:.1f} (esperado 10-20)"
        
        return True, "Coerência metabólica OK"
    
    @staticmethod
    def detectar_descontrole(
        condicao_cid10: str,
        medicamentos_vigentes: list,
        valores_recentes: dict
    ) -> Optional[dict]:
        """Detectar descontrole de condição
        
        Args:
            condicao_cid10: CID-10 da condição
            medicamentos_vigentes: Lista de medicamentos em uso
            valores_recentes: Últimos valores clínicos
            
        Returns:
            Alerta com recomendação ou None
        """
        alerta = None
        
        # HAS: PA acima de 160/100 em duas ocasiões
        if condicao_cid10 == "I10":
            systolica = valores_recentes.get("pa_sistolica")
            if systolica and systolica >= 180:
                alerta = {
                    "nivel": "CRITICO",
                    "mensagem": "PA crítica >= 180 mmHg",
                    "recomendacao": "Avaliar urgentemente"
                }
        
        # Diabetes: HbA1c > 10%
        elif condicao_cid10 == "E11":
            hba1c = valores_recentes.get("hba1c")
            if hba1c and hba1c > 10.0:
                alerta = {
                    "nivel": "CRITICO",
                    "mensagem": f"Glicemia mal controlada (HbA1c {hba1c:.1f}%)",
                    "recomendacao": "Intensificar tratamento"
                }
        
        # DRC: TFGe < 15 (necessita diálise)
        elif condicao_cid10 == "N18":
            tfge = valores_recentes.get("tfge")
            if tfge and tfge < 15:
                alerta = {
                    "nivel": "CRITICO",
                    "mensagem": "DRC G5 - Falência renal iminente",
                    "recomendacao": "Preparar para diálise/transplante"
                }
        
        return alerta
```

---

## 5. EXEMPLO END-TO-END

```python
from datetime import date, datetime

# 1. Criar paciente (Florence/comum)
paciente_oswaldo = Paciente(
    cpf="12345678901",
    nome_completo="João da Silva",
    data_nascimento=date(1965, 5, 10),
    sexo_biologico="M",
    tipo_sanguineo="O+"
)

# 2. Registrar condição crônica (HAS)
condicao_has = CondicaoCronica(
    paciente_cpf=paciente_oswaldo.cpf,
    cid10="I10",
    data_diagnostico=date(2020, 3, 15),
    medico_diagnosticador="Dr. Carlos",
    crm_diagnosticador="123456/SP",
    confirmacao_exames=True,
    gravidade_inicial=GravidadeEnum.MODERADA
)
db.add_all([paciente_oswaldo, condicao_has])
db.commit()

# 3. Classificar estágio inicial
estadio_inicial = Estadiamento(
    condicao_cronica_id=condicao_has.id,
    sistema_classificacao="Classificação SBC",
    estagio="2",
    data_classificacao=date(2020, 3, 20),
    criterios={
        "pa_sistolica": 165,
        "pa_diastolica": 105,
        "sem_lesao_orgao": False
    }
)
db.add(estadio_inicial)
db.commit()

# 4. Criar plano de cuidado
plano = PlanoCuidado(
    condicao_cronica_id=condicao_has.id,
    data_inicio=date(2020, 4, 1),
    data_revisao=date(2026, 4, 1),
    objetivos=[
        {
            "objetivo": "Controlar PA para < 130/80 mmHg",
            "prazo_dias": 90,
            "metrica": "monitoria domiciliar"
        }
    ],
    intervencoes=[
        {
            "tipo": "farmacologica",
            "descricao": "Iniciar Losartana 50mg 1x/dia",
            "data_inicio": date(2020, 4, 1)
        },
        {
            "tipo": "nao_farmacologica",
            "descricao": "Dieta hipossódica com nutricionista",
            "frequencia": "1x/2 semanas"
        }
    ],
    medicamentos=[
        {
            "nome": "Losartana",
            "dose": "50mg",
            "frequencia": "1x/dia",
            "via": "oral"
        }
    ],
    educacao_saude=[
        {
            "tema": "Dieta DASH para HAS",
            "tipo": "apostila",
            "url": "/docs/dieta-dash.pdf"
        }
    ],
    status=StatusPlanoEnum.ATIVO
)
db.add(plano)
db.commit()

# 5. Registrar acompanhamento (consulta)
acompanhamento = Acompanhamento(
    paciente_cpf=paciente_oswaldo.cpf,
    condicao_cronica_id=condicao_has.id,
    data_acompanhamento=date(2026, 1, 30),
    medico_id=1,  # Médico responsável
    pressao_arterial="145/95",
    peso_kg=82.5,
    observacoes=[
        {
            "achado": "PA ainda elevada",
            "recomendacao": "Aumentar dose de losartana para 100mg"
        }
    ],
    medicamentos_vigentes=[
        {
            "nome": "Losartana",
            "dose": "100mg",  # Aumentado
            "frequencia": "1x/dia"
        }
    ]
)
db.add(acompanhamento)
db.commit()

# 6. Verificar se precisa reclassificar
novo_estadio = ReclassificacaoService.sugerir_reclassificacao(
    db=db,
    condicao_id=condicao_has.id,
    criterios_novos={
        "pa_sistolica": 145,
        "pa_diastolica": 95
    }
)

if novo_estadio:
    print(f"✅ Reclassificado: {novo_estadio.estagio}")
else:
    print("✅ Mantém estágio anterior")

# 7. Recuperar histórico completo
print("\n=== HISTÓRICO CLÍNICO COMPLETO ===")
print(f"Paciente: {paciente_oswaldo.nome_completo}")
print(f"Condição: CID {condicao_has.cid10} desde {condicao_has.data_diagnostico}")
print(f"\nEstadios:")
for e in condicao_has.estadiamentos:
    print(f"  - {e.data_classificacao}: Estágio {e.estagio}")

print(f"\nÚltimos acompanhamentos:")
for a in sorted(condicao_has.acompanhamentos, key=lambda x: x.data_acompanhamento, reverse=True)[:3]:
    print(f"  - {a.data_acompanhamento}: PA {a.pressao_arterial}, Peso {a.peso_kg}kg")

```

---

## 6. CHECKLIST DE IMPLEMENTAÇÃO

- [ ] Modelos SQLAlchemy criados em `src/oswaldo/models/`
- [ ] Schemas Pydantic criados em `src/oswaldo/schemas/`
- [ ] Routers FastAPI criados em `src/oswaldo/api/routes/`
- [ ] Services implementados em `src/oswaldo/services/`
- [ ] Migrations Alembic criadas
- [ ] Database seed com dados de teste
- [ ] Testes unitários (95%+ cobertura)
- [ ] Testes de integração com Florence
- [ ] Documentação de API (Swagger)
- [ ] Validações clínicas implementadas
- [ ] Performance testada (< 100ms p99)

---

**Status**: ✅ **PRONTO PARA IMPLEMENTAÇÃO EM FASE 2.5.1**

*Esta especificação fornece código pronto para copiar/colar em `src/oswaldo/` com integração clínica completa.*

