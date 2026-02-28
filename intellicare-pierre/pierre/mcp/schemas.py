"""JSON Schemas para as 6 MCP Tools."""

WEB_SEARCH_SCHEMA = {
    "type": "object",
    "properties": {
        "query": {"type": "string", "description": "Termos de busca"},
        "max_results": {"type": "integer", "default": 5, "minimum": 1, "maximum": 10},
        "search_depth": {
            "type": "string",
            "enum": ["basic", "advanced"],
            "default": "advanced",
        },
        "include_domains": {
            "type": "array",
            "items": {"type": "string"},
            "description": "Dominios prioritarios (ex: pubmed.ncbi.nlm.nih.gov)",
        },
        "exclude_domains": {
            "type": "array",
            "items": {"type": "string"},
            "description": "Dominios a excluir (ex: wikipedia.org)",
        },
        "time_range": {
            "type": "string",
            "enum": ["1d", "1w", "1m", "1y"],
            "description": "Filtro de data dos resultados",
        },
    },
    "required": ["query"],
}

SEARCH_MEDICAL_LITERATURE_SCHEMA = {
    "type": "object",
    "properties": {
        "query": {"type": "string", "description": "Termos de busca medica"},
        "database": {
            "type": "string",
            "enum": ["pubmed", "bireme", "scielo", "all"],
            "default": "pubmed",
        },
        "max_results": {"type": "integer", "default": 5, "minimum": 1, "maximum": 20},
        "study_type": {
            "type": "string",
            "enum": ["rct", "systematic_review", "meta_analysis", "guideline", "any"],
            "default": "any",
        },
        "date_from": {"type": "string", "description": "Ano minimo (ex: 2020)"},
        "language": {
            "type": "string",
            "enum": ["any", "pt", "en", "es"],
            "default": "any",
        },
    },
    "required": ["query"],
}

CHECK_REGULATORY_SCHEMA = {
    "type": "object",
    "properties": {
        "query": {"type": "string", "description": "Nome do medicamento ou procedimento"},
        "authority": {
            "type": "string",
            "enum": ["anvisa", "ans", "cfm", "cofen", "all"],
            "default": "all",
        },
        "document_type": {
            "type": "string",
            "enum": ["bula", "resolucao", "nota_tecnica", "lista_cobertura", "any"],
            "default": "any",
        },
    },
    "required": ["query"],
}

ANALYZE_TEXT_SCHEMA = {
    "type": "object",
    "properties": {
        "text": {"type": "string", "description": "Texto a analisar"},
        "instruction": {"type": "string", "description": "O que extrair ou analisar"},
        "output_format": {
            "type": "string",
            "enum": ["bullet_points", "paragraph", "structured_json", "table"],
            "default": "bullet_points",
        },
        "max_tokens": {"type": "integer", "default": 500, "minimum": 50, "maximum": 2000},
        "language": {"type": "string", "default": "pt-BR"},
    },
    "required": ["text", "instruction"],
}

SUMMARIZE_DOCUMENT_SCHEMA = {
    "type": "object",
    "properties": {
        "text": {"type": "string", "description": "Texto do documento (alternativa a URL)"},
        "url": {"type": "string", "description": "URL publica do documento (alternativa a texto)"},
        "summary_type": {
            "type": "string",
            "enum": ["executive", "clinical_action", "methodology", "full_abstract"],
            "default": "clinical_action",
        },
        "max_sentences": {"type": "integer", "default": 5, "minimum": 1, "maximum": 20},
        "target_audience": {
            "type": "string",
            "enum": ["medico", "gestor", "paciente", "tecnico"],
            "default": "medico",
        },
        "language": {"type": "string", "default": "pt-BR"},
    },
    "required": [],
}

TRANSLATE_TO_PORTUGUESE_SCHEMA = {
    "type": "object",
    "properties": {
        "text": {"type": "string", "description": "Texto a traduzir"},
        "source_language": {
            "type": "string",
            "enum": ["en", "es", "fr", "auto"],
            "default": "auto",
        },
        "context": {
            "type": "string",
            "enum": ["medical_guideline", "research_article", "patient_information", "regulatory"],
            "default": "medical_guideline",
        },
        "preserve_medical_terms": {"type": "boolean", "default": True},
    },
    "required": ["text"],
}
