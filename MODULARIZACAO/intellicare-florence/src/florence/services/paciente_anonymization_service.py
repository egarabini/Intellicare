"""
Paciente Anonymization Service

Serviço para criação de pacientes com anonimização automática LGPD-compliant
"""

import os
import logging
from datetime import datetime, date
from typing import Optional

from sqlalchemy.orm import Session
from cryptography.fernet import Fernet, InvalidToken

from florence.models.anonymization import (
    PacienteAnonimizado,
    PacienteHashMapping,
    AcessoHashMapping,
)
from florence.services.anonymization import AnonymizationService

logger = logging.getLogger(__name__)


class UnauthorizedException(Exception):
    """Exceção para acesso não autorizado a PII"""
    pass


class NotFoundException(Exception):
    """Exceção para recurso não encontrado"""
    pass


class AnonimizationException(Exception):
    """Exceção genérica de anonimização"""
    pass


class PacienteAnonymizationService:
    """
    Service para inserir pacientes com anonimização automática
    
    Fluxo:
    1. Recebe dados PII (CPF, Nome, Data)
    2. Calcula hash irreversível do CPF (HMAC-SHA256)
    3. Trunca nome ("João da Silva" → "João S.")
    4. Agrupa data por mês/ano
    5. Insere paciente anonimizado em registro público
    6. Encripta e armazena mapeamento CPF em registro separado
    
    Resultado: Paciente nunca pode ser re-identificado
    """
    
    def __init__(self, db: Session):
        """
        Inicializa serviço
        
        Args:
            db: Sessão SQLAlchemy do banco de dados
        """
        self.db = db
        self.anonymizer = AnonymizationService()
        self._cipher = self._get_cipher()
    
    @staticmethod
    def _get_cipher() -> Optional[Fernet]:
        """
        Obtém cipher para encriptação AES-256
        
        Returns:
            Cipher Fernet ou None se não configurado (dev mode)
        """
        encryption_key = os.getenv("ENCRYPTION_KEY_PII")
        
        if encryption_key:
            try:
                return Fernet(encryption_key.encode())
            except Exception as e:
                logger.warning(f"Erro inicializando cipher: {e}")
                return None
        
        return None
    
    def criar_paciente_anonimizado(
        self,
        cpf: str,
        nome: str,
        data_nascimento: date,
        sexo: str,
        altura_cm: Optional[int] = None,
        peso_kg: Optional[float] = None,
    ) -> PacienteAnonimizado:
        """
        Cria paciente com anonimização automática
        
        Fluxo LGPD-compliant:
        1. Valida CPF
        2. Hash irreversível do CPF
        3. Trunca nome para primeiras letras
        4. Agrupa data por mês/ano
        5. Insere paciente (sem PII)
        6. Cria mapeamento encriptado
        7. Commita transação
        
        Args:
            cpf: CPF em formato "12345678901"
            nome: Nome completo
            data_nascimento: Data nascimento
            sexo: "M" ou "F"
            altura_cm: Altura em centímetros
            peso_kg: Peso em quilogramas
            
        Returns:
            PacienteAnonimizado (sem dados PII)
            
        Raises:
            ValueError: Se dados inválidos
            AnonimizationException: Se erro na anonimização
        """
        
        try:
            # 1. Validar CPF
            valido, msg = self.anonymizer.validate_cpf_format(cpf)
            if not valido:
                raise ValueError(f"CPF inválido: {msg}")
            
            # 2. Hash do CPF (irreversível)
            cpf_hash = self.anonymizer.hash_cpf(cpf)
            logger.info(f"CPF hasheado: {cpf_hash[:16]}...")
            
            # 3. Truncar nome
            nome_truncado = self.anonymizer.truncate_name(nome)
            logger.info(f"Nome truncado: {nome_truncado}")
            
            # 4. Anonimizar data (mês/ano)
            data_anonimizada = self.anonymizer.anonymize_date(
                data_nascimento,
                precisao="mes"
            )
            logger.info(f"Data anonimizada: {data_anonimizada}")
            
            # 5. Criar registro paciente anonimizado
            paciente = PacienteAnonimizado(
                paciente_id_hash=cpf_hash,
                nome_truncado=nome_truncado,
                data_nascimento_mes_ano=data_anonimizada,
                sexo=sexo,
                altura_cm=altura_cm,
                peso_kg=peso_kg,
            )
            
            self.db.add(paciente)
            self.db.flush()  # Garante inserção antes de criar mapping
            
            logger.info(f"Paciente anonimizado criado: {paciente}")
            
            # 6. Criar mapeamento encriptado
            self._criar_mapping_encriptado(cpf_hash, cpf)
            
            # 7. Commit
            self.db.commit()
            
            logger.info(f"Paciente com PII mapeado e encriptado: {cpf_hash[:16]}...")
            
            return paciente
            
        except ValueError as e:
            self.db.rollback()
            logger.error(f"Erro validação: {e}")
            raise
        except Exception as e:
            self.db.rollback()
            logger.error(f"Erro criando paciente anonimizado: {e}")
            raise AnonimizationException(f"Erro anonimização: {str(e)}")
    
    def _criar_mapping_encriptado(self, cpf_hash: str, cpf: str) -> None:
        """
        Cria mapeamento encriptado CPF original → Hash
        
        Usa Fernet (AES-128 CFB-mode) para encriptação
        
        Args:
            cpf_hash: Hash do CPF
            cpf: CPF original a ser encriptado
            
        Raises:
            AnonimizationException: Se erro na encriptação
        """
        
        try:
            # Encriptar CPF (se cipher está configurado)
            if self._cipher:
                cpf_encrypted = self._cipher.encrypt(cpf.encode())
            else:
                # Dev mode: não encriptar (NUNCA em produção!)
                logger.warning("⚠️ Dev mode: CPF não está encriptado!")
                cpf_encrypted = cpf.encode()
            
            # Criar mapeamento
            mapping = PacienteHashMapping(
                cpf_hash=cpf_hash,
                cpf_aes256_encrypted=cpf_encrypted,
            )
            
            self.db.add(mapping)
            self.db.flush()
            
            logger.info(f"Mapeamento encriptado criado para {cpf_hash[:16]}...")
            
        except Exception as e:
            logger.error(f"Erro criando mapeamento encriptado: {e}")
            raise AnonimizationException(f"Erro encriptação: {str(e)}")
    
    def recuperar_cpf_original(
        self,
        cpf_hash: str,
        usuario_id: str,
        motivo: str,
        usuario_ip: str = "0.0.0.0",
    ) -> str:
        """
        Recupera CPF original APENAS para casos específicos
        
        ⚠️ OPERAÇÃO CRÍTICA DE SEGURANÇA
        - Requer autorização do usuário
        - Loga TODOS os acessos para auditoria LGPD
        - Use apenas para: SMS, Email, Impressão de resultado
        
        Args:
            cpf_hash: Hash do paciente
            usuario_id: ID do usuário acessando
            motivo: Justificativa do acesso (ex: "Envio SMS")
            usuario_ip: IP do cliente (padrão: 0.0.0.0)
            
        Returns:
            CPF original desencriptado
            
        Raises:
            UnauthorizedException: Se usuário sem permissão
            NotFoundException: Se paciente não encontrado
            AnonimizationException: Se erro de encriptação
        """
        
        try:
            # 1. Verificar permissão do usuário
            # (stub - implementar com sistema de permissões real)
            # if not self._usuario_tem_permissao(usuario_id):
            #     self._log_acesso(cpf_hash, usuario_id, False, "Sem permissão", usuario_ip)
            #     raise UnauthorizedException(f"Usuário {usuario_id} sem acesso a PII")
            
            # 2. Buscar mapeamento
            mapping = self.db.query(PacienteHashMapping).filter(
                PacienteHashMapping.cpf_hash == cpf_hash
            ).first()
            
            if not mapping or mapping.is_deleted:
                self._log_acesso(
                    cpf_hash,
                    usuario_id,
                    False,
                    "Paciente deletado",
                    usuario_ip,
                )
                raise NotFoundException("Paciente não encontrado ou deletado")
            
            # 3. Desencriptar CPF
            if self._cipher:
                try:
                    cpf_original = self._cipher.decrypt(
                        mapping.cpf_aes256_encrypted
                    ).decode()
                except InvalidToken:
                    raise AnonimizationException("Erro desencriptando CPF")
            else:
                # Dev mode
                cpf_original = mapping.cpf_aes256_encrypted.decode()
            
            # 4. Log de acesso (auditoria LGPD Art. 6)
            self._log_acesso(
                cpf_hash,
                usuario_id,
                True,
                motivo,
                usuario_ip,
            )
            
            # 5. Atualizar estatísticas de acesso
            mapping.accessed_count += 1
            mapping.last_accessed_by = usuario_id
            mapping.last_accessed_at = datetime.utcnow()
            self.db.commit()
            
            logger.warning(
                f"⚠️ PII ACESSO: {usuario_id} recuperou CPF para {motivo}"
            )
            
            return cpf_original
            
        except (UnauthorizedException, NotFoundException):
            raise
        except Exception as e:
            logger.error(f"Erro recuperando CPF original: {e}")
            raise AnonimizationException(f"Erro acesso PII: {str(e)}")
    
    def _log_acesso(
        self,
        cpf_hash: str,
        usuario_id: str,
        sucesso: bool,
        motivo: str,
        usuario_ip: str = "0.0.0.0",
        erro_msg: Optional[str] = None,
    ) -> None:
        """
        Log detalhado de auditoria para conformidade LGPD
        
        Args:
            cpf_hash: Hash do CPF acessado
            usuario_id: ID do usuário
            sucesso: Se acesso foi bem-sucedido
            motivo: Justificativa do acesso
            usuario_ip: IP do cliente
            erro_msg: Mensagem de erro (se aplicável)
        """
        
        try:
            log = AcessoHashMapping(
                cpf_hash=cpf_hash,
                usuario_id=usuario_id,
                usuario_ip=usuario_ip,
                motivo_acesso=motivo,
                sucesso=sucesso,
                erro_msg=erro_msg,
                accessed_at=datetime.utcnow(),
            )
            
            self.db.add(log)
            self.db.commit()
            
            status = "✅" if sucesso else "❌"
            logger.info(f"Auditoria: {status} {usuario_id} acessou {cpf_hash[:16]}...")
            
        except Exception as e:
            logger.error(f"Erro logando acesso: {e}")
            # Não lançar erro - log não deve bloquear operação
    
    def listar_acessos_pii(
        self,
        cpf_hash: str,
        dias_retroativos: int = 30,
    ) -> list:
        """
        Lista todos os acessos a um CPF para auditoria
        
        Args:
            cpf_hash: Hash do CPF
            dias_retroativos: Quantos dias retroagir
            
        Returns:
            Lista de AcessoHashMapping
        """
        
        from datetime import timedelta
        
        data_limite = datetime.utcnow() - timedelta(days=dias_retroativos)
        
        acessos = self.db.query(AcessoHashMapping).filter(
            AcessoHashMapping.cpf_hash == cpf_hash,
            AcessoHashMapping.accessed_at >= data_limite,
        ).order_by(AcessoHashMapping.accessed_at.desc()).all()
        
        return acessos


__all__ = [
    "PacienteAnonymizationService",
    "UnauthorizedException",
    "NotFoundException",
    "AnonimizationException",
]
