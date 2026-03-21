# 03_PLANO.md — Plano de Execução (DEM-052)

## 1. Mapeamento de Dependências
- Aproveitar as dependências de ambiente do projeto que já possuem a biblioteca `WeasyPrint` instalada nativamente na sprint `DEM-027`.
- **Decisão Arquitetural:** O serviço de conversão HTML para PDF será executado no próprio backend, orquestrando `jinja2` (para injetar dados de SQL direto na *view*) e `weasyprint.HTML` (para exportar bytes finais) no módulo `careplanner/services.py`.

## 2. Passo a Passo de Execução
1. **`careplanner/repository.py`**: Criar método `get_journey_full(ctx, correlation_id)`:
   - Uma união de três consultas simultâneas a `care_tasks`, `care_events` e `care_conversations` pelo mesmo ID transacional `cid` para serialização de um enorme payload de contexto temporal.
   
2. **`careplanner/templates/journey_report.html`**: Construir arquivo Jinja2 nativo aplicando as tags em cascata (`{% if ... %}`, `{% for event in events %}`) seguindo a paleta cromática exigida no *BRIEFING*: Cores `#1a5276`, `#2874a6` para cabeçalhos e badges dinâmicos baseados no tipo do evento ou no canal (`whatsapp`, `email`, etc).
   
3. **`careplanner/services.py`**: Adicionar o controlador `generate_journey_report()`. Este puxará o mapa de chaves da query do repositório, carregará a render template via `Environment(FileSystemLoader(...))`, fará o `.render(**data)` final e encapsulará na instância final `.write_pdf()` que será devolvida em cache/bytes rápidos à API rotativa.
   
4. **`careplanner/api/routes.py`**: O endpoint RESTful `GET /journeys/{correlation_id}/report.pdf` fará a mediação entregando em cabeçalho `application/pdf` e forçando um download explícito: `Content-Disposition: attachment; filename=jornada_UUID.pdf`.

5. **`GestorUI/pages/CareplannerJourneyDetail.tsx`**: Na visualização do *timeline* em React puro do gestor, adicionar o botão "Exportar PDF" do roteamento `@tabler/icons-react` abrindo um link nova aba `target="_blank"` ao `.pdf`. O download será processado pela requisição logada no servidor.

6. **Testes e Build (`test_careplanner_pdf.py`)**: Validações com mock (simulando ou aproveitando o banco local de testes).
   - Validar assert status code = 200.
   - Validar retorno de array hexadecimal iniciado em `%PDF`.
   - Validar status 404 perante falhas/violação de ID.

## 3. Riscos Observados
- Resolução do caminho do *Jinja2*: Utilizaremos `os.path.join(os.path.dirname(__file__), "templates")` assegurando que a rota absoluta nunca cause desabamentos no container Linux/Docker de build.
