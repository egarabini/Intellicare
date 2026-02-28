"""Excalidraw Diagram Storage Service.

Salva diagramas Excalidraw como FHIR Media + DocumentReference.
"""

import base64
import hashlib
import json
from datetime import datetime
from typing import Optional, Dict, Any, List
from uuid import uuid4

from sqlalchemy.orm import Session

from grahame.models import FHIRResource
from grahame.services.fhir_storage import FHIRStorageService


class ExcalidrawDiagramStorage:
    """Serviço para armazenar diagramas Excalidraw no FHIR."""

    def __init__(self, db: Session, tenant_id: str):
        """Inicializa o serviço.
        
        Args:
            db: Sessão do banco de dados
            tenant_id: ID do tenant
        """
        self.db = db
        self.tenant_id = tenant_id
        self.storage = FHIRStorageService(db, tenant_id)

    def save_diagram(
        self,
        diagram_data: Dict[str, Any],
        patient_id: str,
        title: str,
        description: Optional[str] = None,
        category: str = "clinical-diagram",
        author_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Salva um diagrama Excalidraw como FHIR Media + DocumentReference.
        
        Args:
            diagram_data: Dados do diagrama Excalidraw (JSON)
            patient_id: ID do paciente (FHIR Patient)
            title: Título do diagrama
            description: Descrição opcional
            category: Categoria do diagrama
            author_id: ID do autor (FHIR Practitioner)
        
        Returns:
            Dict com IDs do Media e DocumentReference criados
        """
        # 1. Criar FHIR Media com o diagrama JSON
        media_id = self._create_media(diagram_data, patient_id, title)

        # 2. Criar FHIR DocumentReference apontando para o Media
        doc_ref_id = self._create_document_reference(
            media_id=media_id,
            patient_id=patient_id,
            title=title,
            description=description,
            category=category,
            author_id=author_id,
        )

        return {
            "media_id": media_id,
            "document_reference_id": doc_ref_id,
            "diagram_url": f"/fhir/Media/{media_id}",
        }

    def _create_media(
        self,
        diagram_data: Dict[str, Any],
        patient_id: str,
        title: str,
    ) -> str:
        """Cria um FHIR Media resource com o diagrama.
        
        Args:
            diagram_data: Dados do diagrama Excalidraw
            patient_id: ID do paciente
            title: Título do diagrama
        
        Returns:
            ID do Media criado
        """
        # Serializar diagrama para JSON
        diagram_json = json.dumps(diagram_data, ensure_ascii=False)
        diagram_bytes = diagram_json.encode("utf-8")
        diagram_base64 = base64.b64encode(diagram_bytes).decode("ascii")

        # Calcular hash para integridade
        diagram_hash = hashlib.sha256(diagram_bytes).hexdigest()

        # Criar FHIR Media
        media = {
            "resourceType": "Media",
            "status": "completed",
            "type": {
                "coding": [
                    {
                        "system": "http://terminology.hl7.org/CodeSystem/media-type",
                        "code": "diagram",
                        "display": "Diagram",
                    }
                ],
                "text": "Excalidraw Diagram",
            },
            "subject": {"reference": f"Patient/{patient_id}"},
            "createdDateTime": datetime.utcnow().isoformat() + "Z",
            "content": {
                "contentType": "application/vnd.excalidraw+json",
                "data": diagram_base64,
                "title": title,
                "creation": datetime.utcnow().isoformat() + "Z",
                "hash": diagram_hash,
            },
            "note": [
                {
                    "text": f"Excalidraw diagram with {len(diagram_data.get('elements', []))} elements"
                }
            ],
        }

        # Salvar no FHIR Storage
        created_media = self.storage.create_resource("Media", media)
        return created_media["id"]

    def _create_document_reference(
        self,
        media_id: str,
        patient_id: str,
        title: str,
        description: Optional[str],
        category: str,
        author_id: Optional[str],
    ) -> str:
        """Cria um FHIR DocumentReference apontando para o Media.
        
        Args:
            media_id: ID do Media
            patient_id: ID do paciente
            title: Título do documento
            description: Descrição opcional
            category: Categoria do documento
            author_id: ID do autor
        
        Returns:
            ID do DocumentReference criado
        """
        doc_ref = {
            "resourceType": "DocumentReference",
            "status": "current",
            "type": {
                "coding": [
                    {
                        "system": "http://loinc.org",
                        "code": "11488-4",
                        "display": "Consult note",
                    }
                ],
                "text": "Clinical Diagram",
            },
            "category": [
                {
                    "coding": [
                        {
                            "system": "http://intellicare.com/fhir/CodeSystem/document-category",
                            "code": category,
                            "display": category.replace("-", " ").title(),
                        }
                    ]
                }
            ],
            "subject": {"reference": f"Patient/{patient_id}"},
            "date": datetime.utcnow().isoformat() + "Z",
            "description": description or title,
            "content": [
                {
                    "attachment": {
                        "contentType": "application/vnd.excalidraw+json",
                        "url": f"/fhir/Media/{media_id}",
                        "title": title,
                        "creation": datetime.utcnow().isoformat() + "Z",
                    }
                }
            ],
        }

        # Adicionar autor se fornecido
        if author_id:
            doc_ref["author"] = [{"reference": f"Practitioner/{author_id}"}]

        # Salvar no FHIR Storage
        created_doc_ref = self.storage.create_resource("DocumentReference", doc_ref)
        return created_doc_ref["id"]

    def get_diagram(self, media_id: str) -> Optional[Dict[str, Any]]:
        """Recupera um diagrama Excalidraw.

        Args:
            media_id: ID do Media

        Returns:
            Dados do diagrama Excalidraw ou None se não encontrado
        """
        # Buscar Media
        media = self.storage.read_resource("Media", media_id)
        if not media:
            return None

        # Decodificar diagrama
        diagram_base64 = media.get("content", {}).get("data", "")
        if not diagram_base64:
            return None

        diagram_bytes = base64.b64decode(diagram_base64)
        diagram_json = diagram_bytes.decode("utf-8")
        diagram_data = json.loads(diagram_json)

        return {
            "id": media_id,
            "data": diagram_data,
            "title": media.get("content", {}).get("title", "Untitled"),
            "created": media.get("createdDateTime"),
            "patient_id": media.get("subject", {}).get("reference", "").replace("Patient/", ""),
        }

    def list_patient_diagrams(
        self,
        patient_id: str,
        category: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Lista todos os diagramas de um paciente.

        Args:
            patient_id: ID do paciente
            category: Filtrar por categoria (opcional)

        Returns:
            Lista de diagramas
        """
        # Buscar DocumentReferences do paciente
        search_params = {
            "subject": f"Patient/{patient_id}",
            "type": "11488-4",  # Consult note (clinical diagram)
        }

        if category:
            search_params["category"] = category

        doc_refs = self.storage.search_resources("DocumentReference", search_params)

        diagrams = []
        for doc_ref in doc_refs:
            # Extrair Media ID do content
            content = doc_ref.get("content", [])
            if not content:
                continue

            media_url = content[0].get("attachment", {}).get("url", "")
            if not media_url.startswith("/fhir/Media/"):
                continue

            media_id = media_url.replace("/fhir/Media/", "")

            diagrams.append({
                "id": media_id,
                "document_reference_id": doc_ref["id"],
                "title": content[0].get("attachment", {}).get("title", "Untitled"),
                "description": doc_ref.get("description", ""),
                "category": doc_ref.get("category", [{}])[0].get("coding", [{}])[0].get("code", ""),
                "created": doc_ref.get("date"),
                "author": doc_ref.get("author", [{}])[0].get("reference", ""),
            })

        return diagrams

    def update_diagram(
        self,
        media_id: str,
        diagram_data: Dict[str, Any],
        title: Optional[str] = None,
    ) -> bool:
        """Atualiza um diagrama existente (cria nova versão).

        Args:
            media_id: ID do Media original
            diagram_data: Novos dados do diagrama
            title: Novo título (opcional)

        Returns:
            True se atualizado com sucesso
        """
        # Buscar Media original
        original_media = self.storage.read_resource("Media", media_id)
        if not original_media:
            return False

        # Criar nova versão do Media
        diagram_json = json.dumps(diagram_data, ensure_ascii=False)
        diagram_bytes = diagram_json.encode("utf-8")
        diagram_base64 = base64.b64encode(diagram_bytes).decode("ascii")
        diagram_hash = hashlib.sha256(diagram_bytes).hexdigest()

        # Atualizar content
        original_media["content"]["data"] = diagram_base64
        original_media["content"]["hash"] = diagram_hash
        if title:
            original_media["content"]["title"] = title

        # Atualizar no FHIR Storage (cria nova versão)
        self.storage.update_resource("Media", media_id, original_media)
        return True

    def delete_diagram(self, media_id: str) -> bool:
        """Deleta um diagrama (soft delete).

        Args:
            media_id: ID do Media

        Returns:
            True se deletado com sucesso
        """
        return self.storage.delete_resource("Media", media_id)

