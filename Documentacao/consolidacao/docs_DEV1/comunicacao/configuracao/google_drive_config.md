# CONFIGURAÇÃO DO GOOGLE DRIVE

## 📁 Estrutura: INTELLICARE/Comunicacao

**Responsável**: DEV1  
**Data de configuração**: 24/02/2026  
**Versão**: 1.0

---

## 1. ESTRUTURA DE PASTAS

```
INTELLICARE/
└── Comunicacao/
    ├── 01_Reunioes/
    │   ├── 2026-02/
    │   │   ├── Agendas/
    │   │   ├── Atas/
    │   │   └── Gravacoes/
    │   └── Templates/
    │       ├── TEMPLATE_AGENDA_REUNIAO.md
    │       └── TEMPLATE_ATA_REUNIAO.md
    │
    ├── 02_Validacoes/
    │   ├── 2026-02/
    │   │   ├── Planejamento/
    │   │   ├── Resultados/
    │   │   ├── Feedbacks/
    │   │   └── Aprovacoes/
    │   └── Templates/
    │       ├── TEMPLATE_VALIDACAO.md
    │       └── TEMPLATE_FEEDBACK.md
    │
    ├── 03_Apresentacoes/
    │   ├── 2026-02/
    │   │   ├── Slides/
    │   │   ├── Demos/
    │   │   └── Videos/
    │   └── Templates/
    │       └── TEMPLATE_APRESENTACAO.pptx
    │
    ├── 04_Stakeholders/
    │   ├── Cadastros/
    │   ├── Historico/
    │   └── Preferencias/
    │
    ├── 05_Metricas/
    │   ├── Dashboards/
    │   ├── Relatorios_Mensais/
    │   └── Analises/
    │
    └── 06_Documentacao/
        ├── Processos/
        ├── Guias/
        └── FAQs/
```

---

## 2. PERMISSÕES DE ACESSO

### Pasta Raiz (INTELLICARE/Comunicacao):
- **DEV1**: Editor (pode criar, editar, excluir)
- **DEV2**: Visualizador (pode ver e comentar)
- **Gestores**: Visualizador (apenas pastas específicas)

### Subpastas Específicas:

#### 01_Reunioes:
- **DEV1**: Editor
- **DEV2**: Visualizador
- **Participantes**: Visualizador (apenas suas reuniões)

#### 02_Validacoes:
- **DEV1**: Editor
- **DEV2**: Visualizador
- **Especialistas**: Visualizador (apenas suas validações)

#### 03_Apresentacoes:
- **DEV1**: Editor
- **DEV2**: Visualizador
- **Público**: Visualizador (apresentações públicas)

#### 04_Stakeholders:
- **DEV1**: Editor
- **Acesso restrito**: Apenas DEV1 (dados sensíveis - LGPD)

#### 05_Metricas:
- **DEV1**: Editor
- **DEV2**: Visualizador
- **Gestores**: Visualizador

#### 06_Documentacao:
- **DEV1**: Editor
- **DEV2**: Comentador
- **Todos**: Visualizador

---

## 3. CONVENÇÕES DE NOMENCLATURA

### Arquivos de Reunião:
```
YYYY-MM-DD_[TIPO]_[NOME]_[VERSAO].ext

Exemplos:
2026-02-26_AGENDA_Validacao_LGPD_v1.md
2026-02-26_ATA_Validacao_LGPD_v1.md
2026-02-26_GRAVACAO_Validacao_LGPD.mp4
```

### Arquivos de Validação:
```
YYYY-MM-DD_VAL-[NN]_[MODULO]_[TIPO].ext

Exemplos:
2026-02-26_VAL-01_LGPD_Planejamento.md
2026-02-26_VAL-01_LGPD_Resultado.md
2026-02-26_VAL-01_LGPD_Feedback.json
2026-02-26_VAL-01_LGPD_Aprovacao.pdf
```

### Arquivos de Apresentação:
```
YYYY-MM-DD_APRES_[TEMA]_[PUBLICO].ext

Exemplos:
2026-02-28_APRES_Arquitetura_CQRS_Gestores.pptx
2026-02-28_APRES_Demo_Sistema_Tecnicos.mp4
```

---

## 4. TEMPLATES DISPONÍVEIS

### Templates de Reunião:
1. **TEMPLATE_AGENDA_REUNIAO.md**
   - Formato: Markdown
   - Uso: Criar agendas padronizadas
   - Localização: `01_Reunioes/Templates/`

2. **TEMPLATE_ATA_REUNIAO.md**
   - Formato: Markdown
   - Uso: Documentar reuniões
   - Localização: `01_Reunioes/Templates/`

### Templates de Validação:
1. **TEMPLATE_VALIDACAO.md**
   - Formato: Markdown
   - Uso: Planejar e documentar validações
   - Localização: `02_Validacoes/Templates/`

2. **TEMPLATE_FEEDBACK.md**
   - Formato: Markdown
   - Uso: Coletar feedback estruturado
   - Localização: `02_Validacoes/Templates/`

### Templates de Apresentação:
1. **TEMPLATE_APRESENTACAO.pptx**
   - Formato: PowerPoint
   - Uso: Criar apresentações padronizadas
   - Localização: `03_Apresentacoes/Templates/`

---

## 5. INTEGRAÇÃO COM SCRIPTS

### Upload Automático de Ata:

```python
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

def upload_ata_para_drive(
    file_path: str,
    data: str,
    nome_reuniao: str
):
    """
    Faz upload de ata para Google Drive
    
    Nota: Requer autenticação OAuth2
    """
    service = build('drive', 'v3', credentials=creds)
    
    # Determinar pasta de destino
    ano_mes = data[:7]  # YYYY-MM
    folder_id = get_or_create_folder(f'2026-02')
    
    # Metadados do arquivo
    file_metadata = {
        'name': f'{data}_ATA_{nome_reuniao}_v1.md',
        'parents': [folder_id]
    }
    
    # Upload
    media = MediaFileUpload(file_path, mimetype='text/markdown')
    file = service.files().create(
        body=file_metadata,
        media_body=media,
        fields='id, webViewLink'
    ).execute()
    
    return file.get('webViewLink')
```

---

## 6. BACKUP E VERSIONAMENTO

### Política de Backup:
- **Frequência**: Diária (automática pelo Google Drive)
- **Retenção**: 30 dias de histórico de versões
- **Backup local**: Semanal (via Git para documentos Markdown)

### Versionamento:
- **Documentos importantes**: Manter versões (v1, v2, v3...)
- **Atas finais**: Versão única (após aprovação)
- **Templates**: Versionamento no nome do arquivo

---

## 7. ORGANIZAÇÃO MENSAL

### Início do Mês:
1. Criar pasta `YYYY-MM` em cada categoria
2. Copiar templates para novas pastas
3. Arquivar mês anterior (mover para "Arquivo/")

### Fim do Mês:
1. Gerar relatório mensal
2. Consolidar métricas
3. Revisar e arquivar documentos
4. Preparar estrutura para próximo mês

---

## 8. LINKS RÁPIDOS

### Pastas Principais:
- **Reuniões**: [Link para pasta]
- **Validações**: [Link para pasta]
- **Apresentações**: [Link para pasta]
- **Métricas**: [Link para pasta]
- **Documentação**: [Link para pasta]

### Templates:
- **Templates de Reunião**: [Link para pasta]
- **Templates de Validação**: [Link para pasta]
- **Templates de Apresentação**: [Link para pasta]

---

## 9. BOAS PRÁTICAS

### Ao Criar Arquivo:
- ✅ Usar nomenclatura padronizada
- ✅ Salvar na pasta correta
- ✅ Adicionar descrição no arquivo
- ✅ Configurar permissões adequadas
- ✅ Adicionar tags/labels se disponível

### Ao Compartilhar:
- ✅ Verificar permissões antes de compartilhar
- ✅ Usar links com permissões específicas
- ✅ Notificar destinatários
- ✅ Definir data de expiração se aplicável

### Ao Arquivar:
- ✅ Mover para pasta "Arquivo/"
- ✅ Manter estrutura organizada
- ✅ Documentar motivo do arquivamento
- ✅ Manter por pelo menos 1 ano

---

**Configurado por**: DEV1  
**Data**: 24/02/2026  
**Status**: ✅ Estrutura criada e configurada

