"""Schemas JSON das tools MCP."""

from __future__ import annotations


TOOLS: list[dict] = [
    {
        "name": "extract_document",
        "description": "Extrai texto e estrutura de documentos medicos.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "file_content_base64": {"type": "string"},
                "file_type": {"type": "string", "enum": ["pdf", "jpeg", "png", "tiff", "txt"]},
                "document_type": {
                    "type": "string",
                    "enum": ["lab_report", "discharge_summary", "prescription", "regulatory", "generic"],
                },
                "patient_id": {"type": "string"},
                "language": {"type": "string"},
            },
            "required": ["file_content_base64", "file_type"],
        },
    },
    {
        "name": "ocr_image",
        "description": "OCR especializado para imagens medicas.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "image_base64": {"type": "string"},
                "image_type": {"type": "string", "enum": ["jpeg", "png", "tiff", "dicom_text"]},
                "enhance_quality": {"type": "boolean"},
                "language": {"type": "string"},
            },
            "required": ["image_base64", "image_type"],
        },
    },
    {
        "name": "parse_lab_result",
        "description": "Converte documento em lab_results compativel com Florence.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "document_text": {"type": "string"},
                "file_content_base64": {"type": "string"},
                "file_type": {"type": "string", "enum": ["pdf", "jpeg", "png", "txt"]},
            },
            "required": [],
        },
    },
    {
        "name": "parse_discharge_summary",
        "description": "Extrai dados estruturados de sumario de alta.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "file_content_base64": {"type": "string"},
                "file_type": {"type": "string", "enum": ["pdf", "jpeg", "png", "txt"]},
                "patient_id": {"type": "string"},
            },
            "required": ["file_content_base64", "file_type"],
        },
    },
    {
        "name": "search_documents",
        "description": "Busca semantica em documentos indexados.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": {"type": "string"},
                "patient_id": {"type": "string"},
                "document_type": {"type": "string"},
                "top_k": {"type": "integer"},
                "date_from": {"type": "string"},
                "date_to": {"type": "string"},
            },
            "required": ["query", "patient_id"],
        },
    },
    {
        "name": "index_document",
        "description": "Indexa documento para busca futura.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "document_text": {"type": "string"},
                "document_type": {"type": "string"},
                "patient_id": {"type": "string"},
                "metadata": {"type": "object"},
            },
            "required": ["document_text", "document_type"],
        },
    },
]

