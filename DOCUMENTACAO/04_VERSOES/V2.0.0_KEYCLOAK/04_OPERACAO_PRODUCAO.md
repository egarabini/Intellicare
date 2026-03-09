# 04 — Operação de Produção: Keycloak IntelliCare

> **Versão:** 2.0.0 | **Data:** 2026-03-06 | **Status:** ✅ Ativo
> **Rastreabilidade:** V2.0.0-KEYCLOAK Phase 5 | **Público-alvo:** Sysadmins, DevOps

---

## 🔒 T5.7 - Habilitar MFA Obrigatório para Superadmins (`PLATFORM_ADMIN`)

O Keycloak V2.0.0-KEYCLOAK exige que todos os usuários associados a perfis com altos privilégios (`PLATFORM_ADMIN` ou `PLATFORM_BILLING`) reforcem a conta com Autenticação de Dois Fatores (OTP via Google Authenticator).

### Passos via Painel Administrativo do Keycloak:
1. Acesse o **Admin Console** do Keycloak (`https://auth.intellicare.ia.br/admin`).
2. Vá ao Realm: **bemcuidar**.
3. No painel à esquerda, selecione **Authentication** > guia **Required Actions**.
4. Certifique-se de que a ação **Configure OTP** esteja habilitada (`Enabled`).
5. Acesse **Realm Roles**. Selecione a role `PLATFORM_ADMIN`.
6. (Workaround de Design do Keycloak): Uma Role diretamente não impõe MFA. Contudo, você deve criar um **Authentication Flow** customizado baseado no "Browser Flow":
   - Em **Authentication** > **Flows**, copie o "Browser" para "Browser-IntelliCare".
   - Altere a condição de OTP para `Conditional`.
   - Clique na engrenagem da Configuração Condicional e coloque a condição `Condition - User Role` apontando para `PLATFORM_ADMIN`.
   - Marque o fluxo Browser-IntelliCare como "Bind" para ser o fluxo global do portal.

*(Scripts de automação K-Admin-CLI podem setar o "Configure OTP" automaticamente a cada registro).*

---

## 🔑 T5.8 - Rotação de `client_secrets`

Os módulos do IntelliCare R4 (Grahame, Wanda, Florence, etc.) autenticam via `client_credentials`. É boa prática realizar a rotação dessas senhas semestralmente.

### Procedimento de Rotação Zero-Downtime:
1. Acesse o **Admin Console** > Realm **bemcuidar** > **Clients**.
2. Selecione o Client desejado (ex: `intellicare-grahame`).
3. Vá na aba **Credentials**.
4. Clique em **Regenerate Secret**. *Importante: Ao fazer isso, as instâncias ativas do Grahame de imediato perdem acesso a novas requisições até serem reiniciadas com o novo segredo.*
5. Atualize o arquivo **`keycloak_client_secrets.json`** no repositório `intellicare-auth` (ou nas variáveis/Vault de CI/CD de Produção).
6. Realize um rolling update ou reinicie os containers afetados para recarregarem via biblioteca `configure_auth()`.

## 💾 T5.3 - Backups Diários

O script `scripts/backup_keycloak.sh` cobre 100% da garantia do SSO:
- Faz Dump binário (`pg_dump`) das chaves de criptografia RSA guardadas no Postgres 15.
- Executa o Build Export standalone (`kc.sh export`) capturando Realms e Clients em JSON puro para portabilidade imediata (Disaster Recovery).
- O CRON ideal diário: `0 2 * * * /opt/intellicare/scripts/backup_keycloak.sh`.
