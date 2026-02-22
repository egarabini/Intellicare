"""Carregador de templates seed no banco de dados."""

from __future__ import annotations

import logging

from comunicacao.templates.seed_templates import get_seed_templates
from comunicacao.templates.store import TemplateStore

logger = logging.getLogger(__name__)


def load_seed_templates(store: TemplateStore, force: bool = False) -> dict[str, str]:
    """Carrega os templates seed no store.
    
    Args:
        store: Store de templates (PostgreSQL ou in-memory)
        force: Se True, sobrescreve templates existentes
        
    Returns:
        Dict com status de cada template: {"template_id": "created|updated|skipped"}
    """
    templates = get_seed_templates()
    results: dict[str, str] = {}
    
    for template in templates:
        try:
            existing = store.get(template.id)
            
            if existing is None:
                # Template não existe, criar
                store.create(template)
                results[template.id] = "created"
                logger.info(f"Template seed criado: {template.id}")
                
            elif force:
                # Template existe mas force=True, atualizar
                store.update(template)
                results[template.id] = "updated"
                logger.info(f"Template seed atualizado: {template.id}")
                
            else:
                # Template existe e force=False, pular
                results[template.id] = "skipped"
                logger.debug(f"Template seed já existe: {template.id}")
                
        except Exception as exc:
            logger.error(f"Erro ao carregar template seed {template.id}: {exc}")
            results[template.id] = f"error: {exc}"
    
    return results


def ensure_seed_templates(store: TemplateStore) -> None:
    """Garante que os templates seed existem no store.
    
    Carrega apenas templates que não existem (não sobrescreve).
    
    Args:
        store: Store de templates
    """
    results = load_seed_templates(store, force=False)
    
    created_count = sum(1 for status in results.values() if status == "created")
    skipped_count = sum(1 for status in results.values() if status == "skipped")
    error_count = sum(1 for status in results.values() if status.startswith("error"))
    
    logger.info(
        f"Templates seed: {created_count} criados, {skipped_count} já existiam, {error_count} erros"
    )

