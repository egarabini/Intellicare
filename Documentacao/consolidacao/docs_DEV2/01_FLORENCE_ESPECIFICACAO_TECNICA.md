# ESPECIFICAÇÃO TÉCNICA: FLORENCE - ANÁLISE CLÍNICA

## 📌 ID: DEV2-TEC-001
## 🏥 Domínio: Análise Clínica e Laboratorial
## 📅 Data: 12/02/2026
## 👨‍💻 Responsável DEV2: Especificação Técnica
## ⚡ Stack: FastAPI + SQLAlchemy + PostgreSQL + Pydantic

---

## 1. MODELOS SQLALCHEMY (ORM)

### 1.1. Base Model
```python
# src/florence/models/base.py
from sqlalchemy.orm import declarative_base
from sqlalchemy import Column, DateTime, func
from datetime import datetime

Base = declarative_base()

class BaseModel(Base):
    """Classe base para todos os modelos"""
    __abstract__ = True
    
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
```

### 1.2. Modelo: Paciente
```python
# src/florence/models/paciente.py
from sqlalchemy import Column, String, Date, Enum, JSON, DateTime, func
from sqlalchemy.orm import relationship
from datetime import datetime, date
import enum

class SexoBiologico(enum.Enum):
    MASCULINO = "M"
    FEMININO = "F"

class TipoSanguineo(enum.Enum):
    A_POSITIVO = "A+"
    A_NEGATIVO = "A-"
    B_POSITIVO = "B+"
    B_NEGATIVO = "B-"
    AB_POSITIVO = "AB+"
    AB_NEGATIVO = "AB-"
    O_POSITIVO = "O+"
    O_NEGATIVO = "O-"

class Paciente(BaseModel):
    """Paciente - entidade central do domínio"""
    __tablename__ = "pacientes"
    
    cpf = Column(String(11), primary_key=True)
    nome_completo = Column(String(255), nullable=False)
    data_nascimento = Column(Date, nullable=False)
    sexo_biologico = Column(Enum(SexoBiologico), nullable=False)
    tipo_sanguineo = Column(Enum(TipoSanguineo), nullable=True)
    
    alergias = Column(JSON, default=[])  # Lista de alergias
    comorbidades = Column(JSON, default=[])  # Lista de doenças crônicas
    
    # Relacionamentos
    exames = relationship("Exame", back_populates="paciente", cascade="all, delete-orphan")
    alertas = relationship("Alerta", back_populates="paciente", cascade="all, delete-orphan")
    alergias_detalhadas = relationship("Alergia", back_populates="paciente", cascade="all, delete-orphan")
    
    def idade_atual(self) -> int:
        """Calcula idade atual do paciente"""
        today = date.today()
        return today.year - self.data_nascimento.year - (
            (today.month, today.day) < (self.data_nascimento.month, self.data_nascimento.day)
        )
```

### 1.3. Modelo: Tipo Exame
```python
# src/florence/models/tipo_exame.py
from sqlalchemy import Column, Integer, String, Enum
from sqlalchemy.orm import relationship
import enum

class CategoriaExame(enum.Enum):
    LABORATORIAL = "LABORATORIAL"
    IMAGEM = "IMAGEM"
    FUNCIONAL = "FUNCIONAL"

class TipoExame(BaseModel):
    """Classificação de tipos de exames"""
    __tablename__ = "tipo_exames"
    
    id = Column(Integer, primary_key=True)
    codigo = Column(String(20), unique=True, nullable=False)
    nome = Column(String(100), nullable=False)
    categoria = Column(Enum(CategoriaExame), nullable=False)
    dias_validade = Column(Integer, default=365)
    metodo_padrao = Column(String(100))
    
    # Relacionamentos
    exames = relationship("Exame", back_populates="tipo_exame")
    valor_referencias = relationship("ValorReferencia", back_populates="tipo_exame", cascade="all, delete-orphan")
```

### 1.4. Modelo: Exame
```python
# src/florence/models/exame.py
from sqlalchemy import Column, Integer, String, DateTime, JSON, ForeignKey, Enum
from sqlalchemy.orm import relationship
import enum

class StatusExame(enum.Enum):
    PENDENTE = "PENDENTE"
    COLETADO = "COLETADO"
    PROCESSANDO = "PROCESSANDO"
    RESULTADO_PRONTO = "RESULTADO_PRONTO"
    LAUDADO = "LAUDADO"
    CANCELADO = "CANCELADO"

class Exame(BaseModel):
    """Exame clínico realizado"""
    __tablename__ = "exames"
    
    id = Column(Integer, primary_key=True)
    paciente_cpf = Column(String(11), ForeignKey("pacientes.cpf"), nullable=False)
    tipo_exame_id = Column(Integer, ForeignKey("tipo_exames.id"), nullable=False)
    medico_solicitante_id = Column(Integer, ForeignKey("medicos.id"), nullable=False)
    
    data_coleta = Column(DateTime, nullable=False, default=func.now())
    data_resultado = Column(DateTime, nullable=True)
    status = Column(Enum(StatusExame), default=StatusExame.PENDENTE)
    
    laboratorio = Column(String(100), nullable=True)
    numero_rastreio = Column(String(50), unique=True, nullable=True)
    resultado = Column(JSON, nullable=True)
    
    # Relacionamentos
    paciente = relationship("Paciente", back_populates="exames")
    tipo_exame = relationship("TipoExame", back_populates="exames")
    medico_solicitante = relationship("Medico", foreign_keys=[medico_solicitante_id])
    resultado_componentes = relationship("ResultadoComponente", back_populates="exame", cascade="all, delete-orphan")
    laudo = relationship("Laudo", back_populates="exame", uselist=False)
    alertas = relationship("Alerta", back_populates="exame", cascade="all, delete-orphan")
    validacoes = relationship("Validacao", back_populates="exame", cascade="all, delete-orphan")
    
    def marcar_como_laudado(self):
        """Muda status para LAUDADO"""
        self.status = StatusExame.LAUDADO
    
    def validar_prazos(self) -> bool:
        """Valida prazos de resultado"""
        if self.data_resultado and self.data_coleta:
            diff_hours = (self.data_resultado - self.data_coleta).total_seconds() / 3600
            return diff_hours <= 48
        return True
```

### 1.5. Modelo: Resultado Componente
```python
# src/florence/models/resultado_componente.py
from sqlalchemy import Column, Integer, String, Numeric, Enum, ForeignKey
from sqlalchemy.orm import relationship
import enum

class InterpretacaoComponente(enum.Enum):
    NORMAL = "NORMAL"
    BAIXO = "BAIXO"
    ALTO = "ALTO"
    CRITICO_BAIXO = "CRITICO_BAIXO"
    CRITICO_ALTO = "CRITICO_ALTO"

class ResultadoComponente(BaseModel):
    """Componentes de cada exame com resultado"""
    __tablename__ = "resultado_componentes"
    
    id = Column(Integer, primary_key=True)
    exame_id = Column(Integer, ForeignKey("exames.id"), nullable=False)
    
    parametro = Column(String(100), nullable=False)
    valor = Column(Numeric(10, 2), nullable=False)
    unidade = Column(String(20), nullable=True)
    
    valor_ref_min = Column(Numeric(10, 2), nullable=True)
    valor_ref_max = Column(Numeric(10, 2), nullable=True)
    
    interpretacao = Column(Enum(InterpretacaoComponente), nullable=True)
    
    # Relacionamentos
    exame = relationship("Exame", back_populates="resultado_componentes")
    
    def calcular_interpretacao(self):
        """Calcula interpretação baseada nos valores de referência"""
        if not self.valor_ref_min or not self.valor_ref_max:
            return InterpretacaoComponente.NORMAL
        
        if self.valor < self.valor_ref_min:
            # Verificar se é crítico
            delta = self.valor_ref_min - self.valor
            if delta > (self.valor_ref_min * 0.5):
                return InterpretacaoComponente.CRITICO_BAIXO
            return InterpretacaoComponente.BAIXO
        
        elif self.valor > self.valor_ref_max:
            delta = self.valor - self.valor_ref_max
            if delta > (self.valor_ref_max * 0.5):
                return InterpretacaoComponente.CRITICO_ALTO
            return InterpretacaoComponente.ALTO
        
        return InterpretacaoComponente.NORMAL
```

### 1.6. Modelo: Valor Referência
```python
# src/florence/models/valor_referencia.py
from sqlalchemy import Column, Integer, Numeric, String, Date, Boolean, ForeignKey, Enum
from sqlalchemy.orm import relationship
import enum

class SexoReferencia(enum.Enum):
    MASCULINO = "M"
    FEMININO = "F"
    UNISEX = "U"

class ValorReferencia(BaseModel):
    """Valores de referência para comparação com resultados"""
    __tablename__ = "valor_referencias"
    
    id = Column(Integer, primary_key=True)
    tipo_exame_id = Column(Integer, ForeignKey("tipo_exames.id"), nullable=False)
    
    parametro = Column(String(100), nullable=False)
    idade_min = Column(Integer, default=0)
    idade_max = Column(Integer, default=999)
    sexo = Column(Enum(SexoReferencia), default=SexoReferencia.UNISEX)
    
    valor_min = Column(Numeric(10, 2), nullable=True)
    valor_max = Column(Numeric(10, 2), nullable=True)
    unidade = Column(String(20), nullable=True)
    
    ativo = Column(Boolean, default=True)
    data_vigencia_inicio = Column(Date, nullable=False, default=func.current_date())
    data_vigencia_fim = Column(Date, nullable=True)
    
    # Relacionamentos
    tipo_exame = relationship("TipoExame", back_populates="valor_referencias")
```

### 1.7. Modelo: Laudo
```python
# src/florence/models/laudo.py
from sqlalchemy import Column, Integer, String, Text, DateTime, LargeBinary, ForeignKey, Enum
from sqlalchemy.orm import relationship
import enum

class StatusLaudo(enum.Enum):
    RASCUNHO = "RASCUNHO"
    ASSINADO = "ASSINADO"
    CANCELADO = "CANCELADO"

class Laudo(BaseModel):
    """Laudo clínico emitido por médico"""
    __tablename__ = "laudos"
    
    id = Column(Integer, primary_key=True)
    exame_id = Column(Integer, ForeignKey("exames.id"), unique=True, nullable=False)
    
    medico_responsavel_id = Column(Integer, ForeignKey("medicos.id"), nullable=False)
    crm = Column(String(20), nullable=False)
    
    conclusao = Column(Text, nullable=False)
    recomendacoes = Column(JSON, default=[])
    
    data_emissao = Column(DateTime, default=func.now())
    assinatura_digital = Column(LargeBinary, nullable=True)
    
    status = Column(Enum(StatusLaudo), default=StatusLaudo.RASCUNHO)
    
    # Relacionamentos
    exame = relationship("Exame", back_populates="laudo")
    medico_responsavel = relationship("Medico", foreign_keys=[medico_responsavel_id])
```

### 1.8. Modelo: Alerta
```python
# src/florence/models/alerta.py
from sqlalchemy import Column, Integer, String, Text, Numeric, DateTime, Boolean, ForeignKey, Enum
from sqlalchemy.orm import relationship
import enum

class NivelAlerta(enum.Enum):
    AMARELO = "AMARELO"      # Fora da faixa, não crítico
    VERMELHO = "VERMELHO"    # Crítico, ação imediata
    PRETO = "PRETO"          # Incompatível com a vida

class Alerta(BaseModel):
    """Alertas clínicos automáticos"""
    __tablename__ = "alertas"
    
    id = Column(Integer, primary_key=True)
    exame_id = Column(Integer, ForeignKey("exames.id"), nullable=False)
    paciente_cpf = Column(String(11), ForeignKey("pacientes.cpf"), nullable=False)
    
    nivel = Column(Enum(NivelAlerta), nullable=False)
    mensagem = Column(Text, nullable=False)
    parametro_afetado = Column(String(100), nullable=True)
    valor_critico = Column(Numeric(10, 2), nullable=True)
    
    data_alerta = Column(DateTime, default=func.now())
    notificado = Column(Boolean, default=False)
    data_notificacao = Column(DateTime, nullable=True)
    
    # Relacionamentos
    exame = relationship("Exame", back_populates="alertas")
    paciente = relationship("Paciente", back_populates="alertas")
```

### 1.9. Modelo: Médico
```python
# src/florence/models/medico.py
from sqlalchemy import Column, Integer, String, Boolean
from sqlalchemy.orm import relationship

class Medico(BaseModel):
    """Médicos responsáveis por solicitações e laudos"""
    __tablename__ = "medicos"
    
    id = Column(Integer, primary_key=True)
    cpf = Column(String(11), unique=True, nullable=False)
    nome = Column(String(255), nullable=False)
    crm = Column(String(30), unique=True, nullable=False)
    especialidade = Column(String(100), nullable=True)
    ativo = Column(Boolean, default=True)
    
    # Relacionamentos
    laudos = relationship("Laudo", back_populates="medico_responsavel", foreign_keys="Laudo.medico_responsavel_id")
```

### 1.10. Modelo: Alergia
```python
# src/florence/models/alergia.py
from sqlalchemy import Column, Integer, String, Date, ForeignKey, Enum
from sqlalchemy.orm import relationship
import enum

class GravidadeAlergia(enum.Enum):
    LEVE = "LEVE"
    MODERADA = "MODERADA"
    GRAVE = "GRAVE"
    ANAFILAXIA = "ANAFILAXIA"

class Alergia(BaseModel):
    """Alergias medicamentosas do paciente"""
    __tablename__ = "alergias"
    
    id = Column(Integer, primary_key=True)
    paciente_cpf = Column(String(11), ForeignKey("pacientes.cpf"), nullable=False)
    
    medicamento = Column(String(100), nullable=False)
    tipo_reacao = Column(String(100), nullable=False)
    gravidade = Column(Enum(GravidadeAlergia), nullable=False)
    
    data_registro = Column(Date, default=func.current_date())
    
    # Relacionamentos
    paciente = relationship("Paciente", back_populates="alergias_detalhadas")
```

### 1.11. Modelo: Validação
```python
# src/florence/models/validacao.py
from sqlalchemy import Column, Integer, String, Text, Boolean, ForeignKey, Enum
from sqlalchemy.orm import relationship
import enum

class TipoValidacao(enum.Enum):
    CAMPO_OBRIGATORIO = "CAMPO_OBRIGATORIO"
    FAIXA_VALOR = "FAIXA_VALOR"
    COERENCIA_CLINICA = "COERENCIA_CLINICA"
    CONSISTENCIA_DADOS = "CONSISTENCIA_DADOS"
    REGRA_NEGOCIO = "REGRA_NEGOCIO"

class Validacao(BaseModel):
    """Validações executadas nos exames"""
    __tablename__ = "validacoes"
    
    id = Column(Integer, primary_key=True)
    exame_id = Column(Integer, ForeignKey("exames.id"), nullable=False)
    
    tipo_validacao = Column(Enum(TipoValidacao), nullable=False)
    resultado = Column(Boolean, nullable=False)
    detalhes = Column(Text, nullable=True)
    
    # Relacionamentos
    exame = relationship("Exame", back_populates="validacoes")
```

---

## 2. SCHEMAS PYDANTIC (Validação)

### 2.1. Schema: Paciente
```python
# src/florence/schemas/paciente.py
from pydantic import BaseModel, Field, validator
from datetime import date, datetime
from typing import Optional, List

class PacienteBase(BaseModel):
    cpf: str = Field(..., regex="^\d{11}$", description="CPF com 11 dígitos")
    nome_completo: str = Field(..., min_length=1, max_length=255)
    data_nascimento: date = Field(..., description="Data de nascimento")
    sexo_biologico: str = Field(..., regex="^[MF]$")
    tipo_sanguineo: Optional[str] = Field(None, regex="^(A|B|AB|O)[+-]$")
    
    class Config:
        from_attributes = True

class PacienteCreate(PacienteBase):
    alergias: Optional[List[str]] = []
    comorbidades: Optional[List[str]] = []

class PacienteResponse(PacienteBase):
    created_at: datetime
    updated_at: datetime
    
    @validator('data_nascimento')
    def validar_data_nascimento(cls, v):
        if v >= date.today():
            raise ValueError("Data de nascimento não pode ser no futuro")
        return v

class PacienteComExames(PacienteResponse):
    exames: List['ExameResponse'] = []
```

### 2.2. Schema: Exame
```python
# src/florence/schemas/exame.py
from pydantic import BaseModel, Field, validator
from datetime import datetime
from typing import Optional, List

class ExameBase(BaseModel):
    paciente_cpf: str
    tipo_exame_id: int
    medico_solicitante_id: int
    laboratorio: Optional[str] = None
    numero_rastreio: Optional[str] = None

class ExameCreate(ExameBase):
    pass

class ExameResponse(ExameBase):
    id: int
    data_coleta: datetime
    data_resultado: Optional[datetime] = None
    status: str
    resultado: Optional[dict] = None
    created_at: datetime
    
    class Config:
        from_attributes = True

class ExameDetalhado(ExameResponse):
    resultado_componentes: List['ResultadoComponenteResponse'] = []
    alertas: List['AlertaResponse'] = []
```

### 2.3. Schema: Resultado Componente
```python
# src/florence/schemas/resultado_componente.py
from pydantic import BaseModel, Field, validator
from datetime import datetime
from typing import Optional

class ResultadoComponenteBase(BaseModel):
    parametro: str = Field(..., min_length=1)
    valor: float = Field(..., description="Valor obtido no exame")
    unidade: Optional[str] = None
    valor_ref_min: Optional[float] = None
    valor_ref_max: Optional[float] = None

class ResultadoComponenteCreate(ResultadoComponenteBase):
    exame_id: int

class ResultadoComponenteResponse(ResultadoComponenteBase):
    id: int
    exame_id: int
    interpretacao: Optional[str] = None
    created_at: datetime
    
    class Config:
        from_attributes = True
    
    @validator('valor')
    def validar_valor(cls, v):
        if v < -10000 or v > 10000:
            raise ValueError("Valor fora dos limites aceitáveis")
        return v
```

### 2.4. Schema: Alerta
```python
# src/florence/schemas/alerta.py
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional

class AlertaBase(BaseModel):
    nivel: str = Field(..., regex="^(AMARELO|VERMELHO|PRETO)$")
    mensagem: str = Field(..., min_length=1)
    parametro_afetado: Optional[str] = None
    valor_critico: Optional[float] = None

class AlertaCreate(AlertaBase):
    exame_id: int
    paciente_cpf: str

class AlertaResponse(AlertaBase):
    id: int
    exame_id: int
    paciente_cpf: str
    data_alerta: datetime
    notificado: bool
    data_notificacao: Optional[datetime] = None
    
    class Config:
        from_attributes = True
```

### 2.5. Schema: Laudo
```python
# src/florence/schemas/laudo.py
from pydantic import BaseModel, Field, validator
from datetime import datetime
from typing import Optional, List

class LaudoBase(BaseModel):
    conclusao: str = Field(..., min_length=1)
    recomendacoes: Optional[List[str]] = []

class LaudoCreate(LaudoBase):
    exame_id: int
    medico_responsavel_id: int
    crm: str

class LaudoResponse(LaudoBase):
    id: int
    exame_id: int
    medico_responsavel_id: int
    crm: str
    data_emissao: datetime
    status: str
    
    class Config:
        from_attributes = True
```

---

## 3. ENDPOINTS REST API

### 3.1. Base
```python
# src/florence/api/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="Florence - Módulo de Análise Clínica",
    description="API para gerenciamento de exames e análises clínicas",
    version="1.0.0"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
from .routes import clinical, exames, laudos, alertas
app.include_router(clinical.router, prefix="/api/v1", tags=["Clinical"])
app.include_router(exames.router, prefix="/api/v1", tags=["Exames"])
app.include_router(laudos.router, prefix="/api/v1", tags=["Laudos"])
app.include_router(alertas.router, prefix="/api/v1", tags=["Alertas"])
```

### 3.2. Rotas: Exames
```python
# src/florence/api/routes/exames.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import desc
from datetime import datetime, timedelta
from typing import List

router = APIRouter(prefix="/exames", tags=["Exames"])

# Dependency
def get_db():
    from ..database import SessionLocal
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/", response_model=ExameResponse, status_code=status.HTTP_201_CREATED)
async def criar_exame(
    exame: ExameCreate,
    db: Session = Depends(get_db)
):
    """
    Cria novo exame clínico
    
    **Validações**:
    - Paciente deve existir
    - Tipo de exame deve ser válido
    - Médico solicitante deve ser ativo
    """
    from ..models import Exame, Paciente, TipoExame, Medico
    
    # Verificar paciente
    paciente = db.query(Paciente).filter(Paciente.cpf == exame.paciente_cpf).first()
    if not paciente:
        raise HTTPException(status_code=404, detail="Paciente não encontrado")
    
    # Verificar tipo exame
    tipo_exame = db.query(TipoExame).filter(TipoExame.id == exame.tipo_exame_id).first()
    if not tipo_exame:
        raise HTTPException(status_code=404, detail="Tipo de exame inválido")
    
    # Verificar médico solicitante
    medico = db.query(Medico).filter(Medico.id == exame.medico_solicitante_id).first()
    if not medico or not medico.ativo:
        raise HTTPException(status_code=404, detail="Médico não encontrado ou inativo")
    
    # Criar exame
    db_exame = Exame(**exame.dict())
    db.add(db_exame)
    db.commit()
    db.refresh(db_exame)
    
    return db_exame

@router.get("/{exame_id}", response_model=ExameDetalhado)
async def obter_exame(
    exame_id: int,
    db: Session = Depends(get_db)
):
    """Obtém detalhes completos de um exame"""
    from ..models import Exame
    
    exame = db.query(Exame).filter(Exame.id == exame_id).first()
    if not exame:
        raise HTTPException(status_code=404, detail="Exame não encontrado")
    
    return exame

@router.get("/paciente/{cpf}", response_model=List[ExameResponse])
async def listar_exames_paciente(
    cpf: str,
    limite: int = 10,
    db: Session = Depends(get_db)
):
    """
    Lista últimos exames do paciente
    
    **Parâmetros**:
    - `cpf`: CPF do paciente
    - `limite`: Número máximo de exames a retornar (default: 10)
    """
    from ..models import Exame
    
    exames = db.query(Exame)\
        .filter(Exame.paciente_cpf == cpf)\
        .order_by(desc(Exame.data_coleta))\
        .limit(limite)\
        .all()
    
    if not exames:
        raise HTTPException(status_code=404, detail="Nenhum exame encontrado")
    
    return exames

@router.put("/{exame_id}/resultado")
async def carregar_resultado(
    exame_id: int,
    resultado: dict,
    db: Session = Depends(get_db)
):
    """
    Carrega resultado de um exame
    
    **Exemplo de resultado**:
    ```json
    {
        "componentes": [
            {
                "parametro": "hemoglobina",
                "valor": 14.5,
                "unidade": "g/dL"
            }
        ]
    }
    ```
    """
    from ..models import Exame, ResultadoComponente, StatusExame
    
    exame = db.query(Exame).filter(Exame.id == exame_id).first()
    if not exame:
        raise HTTPException(status_code=404, detail="Exame não encontrado")
    
    # Atualizar resultado
    exame.resultado = resultado
    exame.status = StatusExame.RESULTADO_PRONTO
    exame.data_resultado = datetime.now()
    
    # Processar componentes
    for comp in resultado.get("componentes", []):
        componente = ResultadoComponente(
            exame_id=exame_id,
            parametro=comp["parametro"],
            valor=comp["valor"],
            unidade=comp.get("unidade")
        )
        db.add(componente)
    
    db.commit()
    db.refresh(exame)
    
    return {"mensagem": "Resultado carregado com sucesso", "exame_id": exame_id}
```

### 3.3. Rotas: Alertas
```python
# src/florence/api/routes/alertas.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import and_

router = APIRouter(prefix="/alertas", tags=["Alertas"])

@router.get("/pendentes")
async def listar_alertas_pendentes(db: Session = Depends(get_db)):
    """Lista alertas não notificados, ordenado por nível crítico"""
    from ..models import Alerta, NivelAlerta
    
    alertas = db.query(Alerta)\
        .filter(Alerta.notificado == False)\
        .order_by(
            # Priorizar PRETO > VERMELHO > AMARELO
            Alerta.nivel == NivelAlerta.PRETO,
            Alerta.nivel == NivelAlerta.VERMELHO,
            Alerta.data_alerta.desc()
        )\
        .all()
    
    return alertas

@router.post("/{alerta_id}/notificar")
async def marcar_notificado(
    alerta_id: int,
    db: Session = Depends(get_db)
):
    """Marca alerta como notificado"""
    from ..models import Alerta
    from datetime import datetime
    
    alerta = db.query(Alerta).filter(Alerta.id == alerta_id).first()
    if not alerta:
        raise HTTPException(status_code=404, detail="Alerta não encontrado")
    
    alerta.notificado = True
    alerta.data_notificacao = datetime.now()
    db.commit()
    
    return {"mensagem": "Alerta marcado como notificado"}
```

### 3.4. Rotas: Laudos
```python
# src/florence/api/routes/laudos.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

router = APIRouter(prefix="/laudos", tags=["Laudos"])

@router.post("/", response_model=LaudoResponse, status_code=status.HTTP_201_CREATED)
async def criar_laudo(
    laudo: LaudoCreate,
    db: Session = Depends(get_db)
):
    """
    Cria novo laudo para um exame
    
    **Regras**:
    - Exame deve ter resultado pronto
    - Médico deve ser ativo
    """
    from ..models import Laudo, Exame, Medico, StatusExame
    
    # Verificar exame
    exame = db.query(Exame).filter(Exame.id == laudo.exame_id).first()
    if not exame:
        raise HTTPException(status_code=404, detail="Exame não encontrado")
    
    if exame.status != StatusExame.RESULTADO_PRONTO:
        raise HTTPException(
            status_code=400,
            detail=f"Exame deve ter resultado pronto para laudar. Status atual: {exame.status}"
        )
    
    # Verificar médico
    medico = db.query(Medico).filter(Medico.id == laudo.medico_responsavel_id).first()
    if not medico or not medico.ativo:
        raise HTTPException(status_code=404, detail="Médico não encontrado ou inativo")
    
    # Criar laudo
    db_laudo = Laudo(**laudo.dict())
    db.add(db_laudo)
    
    # Marcar exame como laudado
    exame.marcar_como_laudado()
    
    db.commit()
    db.refresh(db_laudo)
    
    return db_laudo

@router.get("/{laudo_id}", response_model=LaudoResponse)
async def obter_laudo(
    laudo_id: int,
    db: Session = Depends(get_db)
):
    """Obtém laudo específico"""
    from ..models import Laudo
    
    laudo = db.query(Laudo).filter(Laudo.id == laudo_id).first()
    if not laudo:
        raise HTTPException(status_code=404, detail="Laudo não encontrado")
    
    return laudo
```

---

## 4. SERVIÇOS (Business Logic)

### 4.1. Serviço: Interpretação de Resultados
```python
# src/florence/services/interpretacao_service.py
from sqlalchemy.orm import Session
from datetime import date
from typing import Dict

class InterpretacaoService:
    """Serviço para interpretação de resultados clínicos"""
    
    @staticmethod
    def obter_valor_referencia(
        db: Session,
        tipo_exame_id: int,
        parametro: str,
        paciente_idade: int,
        paciente_sexo: str
    ) -> Dict:
        """Busca valor de referência apropriado para o paciente"""
        from ..models import ValorReferencia, SexoReferencia
        
        # Tentar encontrar valor específico para idade/sexo
        vr = db.query(ValorReferencia)\
            .filter(
                ValorReferencia.tipo_exame_id == tipo_exame_id,
                ValorReferencia.parametro == parametro,
                ValorReferencia.idade_min <= paciente_idade,
                ValorReferencia.idade_max >= paciente_idade,
                ValorReferencia.sexo.in_([paciente_sexo, 'U']),
                ValorReferencia.ativo == True
            )\
            .first()
        
        if vr:
            return {
                "valor_min": vr.valor_min,
                "valor_max": vr.valor_max,
                "unidade": vr.unidade
            }
        
        return {"valor_min": None, "valor_max": None, "unidade": None}
    
    @staticmethod
    def gerar_alertas(
        db: Session,
        exame_id: int,
        resultado_componentes: list
    ) -> list:
        """Gera alertas automáticos baseado nos resultados"""
        from ..models import Alerta, NivelAlerta, ResultadoComponente
        
        alertas = []
        
        for componente in resultado_componentes:
            rc = db.query(ResultadoComponente)\
                .filter(ResultadoComponente.id == componente.id)\
                .first()
            
            if not rc:
                continue
            
            # Determinar nível de alerta
            if rc.interpretacao == "CRITICO_ALTO" or rc.interpretacao == "CRITICO_BAIXO":
                nivel = NivelAlerta.VERMELHO
                mensagem = f"{rc.parametro}: valor crítico (valor={rc.valor})"
            elif rc.interpretacao in ["ALTO", "BAIXO"]:
                nivel = NivelAlerta.AMARELO
                mensagem = f"{rc.parametro}: valor anormal (valor={rc.valor})"
            else:
                continue
            
            alerta = Alerta(
                exame_id=exame_id,
                nivel=nivel,
                mensagem=mensagem,
                parametro_afetado=rc.parametro,
                valor_critico=float(rc.valor)
            )
            alertas.append(alerta)
        
        return alertas
```

### 4.2. Serviço: Validação Clínica
```python
# src/florence/services/validacao_service.py
from sqlalchemy.orm import Session
from typing import List, Tuple

class ValidacaoClinicaService:
    """Validações clínicas específicas do domínio"""
    
    @staticmethod
    def validar_hemograma(valores: dict, sexo: str) -> List[Tuple[str, bool]]:
        """Valida coerência de hemograma"""
        validacoes = []
        
        # Hemoglobina vs Hematócrito: correlação esperada
        hgb = valores.get("hemoglobina")
        hct = valores.get("hematocrito")
        
        if hgb and hct:
            # Fórmula: Hematócrito ≈ Hemoglobina x 3
            esperado_hct = hgb * 3
            if abs(hct - esperado_hct) > esperado_hct * 0.1:
                validacoes.append(("correlacao_hgb_hct", False))
            else:
                validacoes.append(("correlacao_hgb_hct", True))
        
        # Leucócitos vs Diferenciais: soma deve ser ~100%
        leuc = valores.get("leucocitos")
        neut = valores.get("neutrofilos_perc")
        linf = valores.get("linfocitos_perc")
        mono = valores.get("monocitos_perc")
        
        if all([neut, linf, mono]):
            soma = neut + linf + mono
            if abs(soma - 100) > 5:
                validacoes.append(("soma_diferenciais", False))
            else:
                validacoes.append(("soma_diferenciais", True))
        
        return validacoes
    
    @staticmethod
    def validar_coerencia_metabolica(valores: dict) -> List[Tuple[str, bool]]:
        """Valida coerência entre parâmetros metabólicos"""
        validacoes = []
        
        creatinina = valores.get("creatinina")
        ureia = valores.get("ureia")
        
        # Se ambos elevados, pode indicar insuficiência renal
        if creatinina and ureia:
            if creatinina > 1.2 and ureia > 45:
                # Calcular razão ureia/creatinina (esperado: 10-20)
                if ureia and creatinina:
                    razao = ureia / creatinina
                    if razao < 8 or razao > 25:
                        validacoes.append(("insuficiencia_renal_suspeita", False))
                    else:
                        validacoes.append(("insuficiencia_renal_suspeita", True))
        
        return validacoes
```

---

## 5. CONFIGURAÇÃO ALEMBIC (Migrations)

### 5.1. Arquivo: env.py
```python
# alembic/env.py
from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool
from alembic import context
from sqlalchemy import MetaData

# Import todos os modelos
from src.florence.models import (
    Paciente, Exame, Laudo, ResultadoComponente,
    ValorReferencia, Alerta, Medico, Alergia, Validacao,
    TipoExame, Base
)

config = context.config
fileConfig(config.config_file_name)
target_metadata = Base.metadata

def run_migrations_online():
    """Run migrations in 'online' mode"""
    connectable = engine_from_config(
        config.get_section(config.config_ini_section),
        prefix='sqlalchemy.',
        poolclass=pool.NullPool,
    )
    
    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata
        )
        
        with context.begin_transaction():
            context.run_migrations()

run_migrations_online()
```

### 5.2. Geração de Migrations
```bash
# Criar revision inicial
alembic revision --autogenerate -m "Initial Florence schema"

# Aplicar migrations
alembic upgrade head
```

---

## 6. EXEMPLO DE USO COMPLETO

```python
# exemplo_uso.py
from sqlalchemy.orm import Session
from src.florence.models import (
    Paciente, Exame, ResultadoComponente, Laudo, Alerta
)
from src.florence.services import InterpretacaoService
from datetime import datetime

# 1. Criar paciente
paciente = Paciente(
    cpf="12345678901",
    nome_completo="João Silva",
    data_nascimento=date(1962, 5, 15),
    sexo_biologico="M",
    tipo_sanguineo="O+"
)
db.add(paciente)
db.commit()

# 2. Solicitar exame
exame = Exame(
    paciente_cpf="12345678901",
    tipo_exame_id=1,  # Hemograma
    medico_solicitante_id=1,
    data_coleta=datetime.now()
)
db.add(exame)
db.commit()

# 3. Carregar resultado
resultado = ResultadoComponente(
    exame_id=exame.id,
    parametro="hemoglobina",
    valor=8.5,  # BAIXO (anemia)
    unidade="g/dL"
)
db.add(resultado)

# 4. Calcular interpretação
resultado.interpretacao = resultado.calcular_interpretacao()
db.commit()

# 5. Gerar alertas automáticos
alertas = InterpretacaoService.gerar_alertas(db, exame.id, [resultado])
for alerta in alertas:
    db.add(alerta)
db.commit()

# 6. Emitir laudo
laudo = Laudo(
    exame_id=exame.id,
    medico_responsavel_id=1,
    crm="SP123456",
    conclusao="Anemia moderada. Recomenda-se investigação de causa.",
    recomendacoes=["Avaliação de ferro", "Retorno em 2 semanas"]
)
db.add(laudo)
exame.marcar_como_laudado()
db.commit()

print("✅ Exame processado com sucesso!")
print(f"Alertas gerados: {len(alertas)}")
print(f"Paciente: {paciente.nome_completo}")
```

---

## 📋 Checklist de Implementação

- [ ] Todos os modelos SQLAlchemy criados
- [ ] Todos os schemas Pydantic definidos
- [ ] Endpoints REST implementados
- [ ] Serviços de negócio criados
- [ ] Migrations Alembic geradas
- [ ] Dados iniciais carregados
- [ ] Testes unitários (>90% cobertura)
- [ ] Documentação de API (Swagger)
- [ ] Validações clínicas testadas
- [ ] Alertas automáticos funcionando
- [ ] Performance verificada
- [ ] Segurança validada

---

**STATUS**: ✅ **ESPECIFICAÇÃO TÉCNICA COMPLETA**

*Pronto para implementação na Fase 2.5.1*
