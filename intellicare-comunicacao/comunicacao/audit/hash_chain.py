"""Gerenciador de hash chain para integridade da trilha de auditoria."""

from __future__ import annotations

import hashlib
import json
from typing import Any, Dict, Optional


class HashChainManager:
    """
    Gerenciador de hash chain para trilha de auditoria.
    
    Implementa uma cadeia de hashes semelhante a blockchain simplificado:
    - Cada entry contém hash do entry anterior
    - Hash do entry atual é calculado com base em todos os dados + previous_hash
    - Qualquer alteração quebra a cadeia
    """
    
    @staticmethod
    def calculate_hash(
        intent_id: Optional[str],
        delivery_id: Optional[str],
        intent_type: str,
        channel: str,
        recipient_hash: Optional[str],
        status: str,
        legal_basis: Optional[str],
        lgpd_override: bool,
        severity: str,
        source_module: Optional[str],
        previous_hash: Optional[str],
        created_at: str,
    ) -> str:
        """
        Calcula hash SHA-256 de um audit entry.
        
        Args:
            Todos os campos relevantes do audit entry
        
        Returns:
            Hash SHA-256 (hex string)
        """
        # Criar payload com todos os dados relevantes
        payload = {
            "intent_id": intent_id,
            "delivery_id": delivery_id,
            "intent_type": intent_type,
            "channel": channel,
            "recipient_hash": recipient_hash,
            "status": status,
            "legal_basis": legal_basis,
            "lgpd_override": lgpd_override,
            "severity": severity,
            "source_module": source_module,
            "previous_hash": previous_hash,
            "created_at": created_at,
        }
        
        # Serializar para JSON (ordenado para consistência)
        payload_json = json.dumps(payload, sort_keys=True, ensure_ascii=False)
        
        # Calcular SHA-256
        return hashlib.sha256(payload_json.encode("utf-8")).hexdigest()
    
    @staticmethod
    def hash_recipient(recipient_id: str, salt: str = "intellicare-lgpd-salt-2026") -> str:
        """
        Cria hash pseudonimizado de recipient_id.
        
        Args:
            recipient_id: ID do destinatário
            salt: Salt para hash (deve ser secreto em produção)
        
        Returns:
            Hash SHA-256 (hex string)
        """
        payload = f"{recipient_id}:{salt}"
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()
    
    @staticmethod
    def verify_chain_integrity(entries: list[Dict[str, Any]]) -> tuple[bool, Optional[str]]:
        """
        Verifica integridade da hash chain.
        
        Args:
            entries: Lista de audit entries ordenados por created_at (ASC)
        
        Returns:
            Tupla (is_valid, error_message)
        """
        if not entries:
            return True, None
        
        previous_hash = None
        
        for i, entry in enumerate(entries):
            # Verificar se previous_hash está correto
            if entry.get("previous_hash") != previous_hash:
                return False, f"Entry {i} (id={entry.get('id')}): previous_hash inválido"
            
            # Recalcular hash do entry
            calculated_hash = HashChainManager.calculate_hash(
                intent_id=entry.get("intent_id"),
                delivery_id=entry.get("delivery_id"),
                intent_type=entry.get("intent_type"),
                channel=entry.get("channel"),
                recipient_hash=entry.get("recipient_hash"),
                status=entry.get("status"),
                legal_basis=entry.get("legal_basis"),
                lgpd_override=entry.get("lgpd_override", False),
                severity=entry.get("severity"),
                source_module=entry.get("source_module"),
                previous_hash=previous_hash,
                created_at=entry.get("created_at"),
            )
            
            # Verificar se hash armazenado está correto
            if entry.get("entry_hash") != calculated_hash:
                return False, f"Entry {i} (id={entry.get('id')}): entry_hash inválido (adulteração detectada)"
            
            # Atualizar previous_hash para próxima iteração
            previous_hash = entry.get("entry_hash")
        
        return True, None
    
    @staticmethod
    def get_chain_fingerprint(entries: list[Dict[str, Any]]) -> str:
        """
        Calcula fingerprint da cadeia completa.
        
        Args:
            entries: Lista de audit entries
        
        Returns:
            Hash SHA-256 da cadeia completa
        """
        if not entries:
            return hashlib.sha256(b"").hexdigest()
        
        # Usar hash do último entry como fingerprint
        last_entry = entries[-1]
        return last_entry.get("entry_hash", "")

