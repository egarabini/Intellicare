# TÉRMINO: DEM-088 Professional Identity

## Overview da Entrega
A identidade profissional em backend foi integrada. Semelhante a infraestrutura implantada na validação Patient Identity Foundation (DEM-084/DEM-086), o ciclo vital da gestão de perfis clínicos via Tenant agora gera mapeamentos rastreáveis UUID que habitam em uma coleção agnóstica de acesso Platform.

## Artefatos Gerados / Atualizados
- `db/tenant_migrations/024_professionals_pessoa_id.sql`: Propagação do atributo identity UUID à tabela de professionals.
- `modules/cuidado/schemas.py`: Payload tracking estendido admitindo `cpf` (Optional) em `ProfessionalCreate` e `ProfessionalUpdate`. Schema de resposta `ProfessionalOut` retransmitindo a FK relacional vinculante.
- `modules/cuidado/service.py`: Pipeline expandido injetando validadores de regex que interagem nativamente com a camada `PessoaFisicaIn` da `find_or_create_by_cpf`. Casuísmos sem nome utilizam consultas ao snapshot de update. Lógicas de limpeza do hashmap executadas pré SQL (restringindo SQL inserts explícitos sob a ausência colunar).
- `modules/cuidado/router.py`: Rotas de endpoint de gestão adaptando `platform_db` connection bounds via dependencies FastAPI.
- `tests/test_professional_identity.py`: Suíte consolidando as cinco lógicas de negócio definidas isolando as verificações assíncronas UUID idempotentes. Validado rodando `docker compose exec pytest` 5/5 PASSED.

## Gotchas & Lições Aprendidas
- A Documentação 02 ditava um payload SQL adapter `(platform_db, cpf=..., nome=..., tenant=...)` para a camada target de Identidade, mas a mesma em `services.py` utilizava schemas nativos de conversão direta fechando a própria sessão `get_platform_session`. Adaptamos a lógica no backend em tempo de execução para respeitar as infraestruturas construídas pela DEM-086 mapeando as transições diretas vía `PessoaFisicaIn`.
- Testes Assíncronos falham no patcher utilizando o diretório local via injeção local de imports do Python; o script rodou importando funções de mock injetando instantes após via target de referência superior (`modules.identity.services.find_or_create_by_cpf`).

## Próximos Passos
Esta é a consolidação final da lógica de Identidade. Próximos patches estão liberados à integração front-end GestorUI + Auth Keycloak do Profissional. A branch pode receber commit merge para main.
