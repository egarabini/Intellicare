# 01 - Setup de Certificados SSL para Keycloak

## 📋 Visão Geral

Este guia cobre a criação de certificados SSL para o Keycloak em todos os ambientes.

## 🔐 Tipos de Certificados

| Ambiente | Tipo de Certificado | Validade | Auto-renovação |
|----------|-------------------|----------|----------------|
| Desenvolvimento | Self-signed | 365 dias | ❌ Manual |
| Staging | Let's Encrypt (Staging) | 90 dias | ✅ Automática |
| Produção | Let's Encrypt (Produção) | 90 dias | ✅ Automática |

## 📁 Estrutura de Diretórios

```bash
keycloak/
└── certs/
    ├── server.keystore        # Keystore Java (JKS)
    ├── server.key             # Chave privada (opcional)
    ├── server.crt             # Certificado (opcional)
    └── generate-keystore.sh   # Script de geração
```

## 🚀 Passo a Passo

### Passo 1: Criar Diretório de Certificados

```bash
# Criar diretório
mkdir -p keycloak/certs
cd keycloak/certs
```

### Passo 2: Gerar Self-Signed Certificate (Desenvolvimento)

```bash
# Criar script de geração
cat > generate-keystore.sh << 'EOF'
#!/bin/bash
set -e

# Configurações
KEYSTORE_FILE="server.keystore"
KEYSTORE_PASSWORD="changeme"  # ⚠️ MUDAR EM PRODUÇÃO
KEY_ALIAS="keycloak"
VALIDITY=365  # dias
DN="CN=localhost,OU=IntelliCare,O=HealthTech,L=City,ST=State,C=BR"

echo "🔐 Gerando keystore auto-assinado..."
echo "   Arquivo: $KEYSTORE_FILE"
echo "   Validade: $VALIDITY dias"
echo "   Senha: $KEYSTORE_PASSWORD"

# Gerar keystore
keytool -genkeypair \
  -alias $KEY_ALIAS \
  -keyalg RSA \
  -keysize 2048 \
  -validity $VALIDITY \
  -keystore $KEYSTORE_FILE \
  -storepass $KEYSTORE_PASSWORD \
  -keypass $KEYSTORE_PASSWORD \
  -dname "$DN"

echo "✅ Keystore gerado com sucesso!"
echo ""
echo "📋 Informações do certificado:"
keytool -list -v -keystore $KEYSTORE_FILE -storepass $KEYSTORE_PASSWORD

EOF

# Dar permissão de execução
chmod +x generate-keystore.sh

# Executar
./generate-keystore.sh
```

### Passo 3: Verificar Keystore

```bash
# Listar conteúdo do keystore
keytool -list -v -keystore server.keystore -storepass changeme

# Saída esperada:
# Alias name: keycloak
# Creation date: Mar 1, 2026
# Entry type: PrivateKeyEntry
# Certificate chain length: 1
# Certificate[1]:
#   Owner: CN=localhost, OU=IntelliCare, O=HealthTech, ...
#   Issuer: CN=localhost, OU=IntelliCare, O=HealthTech, ...
#   Valid from: ...
```

### Passo 4: Ajustar Permissões

```bash
# Permissões seguras
chmod 600 server.keystore
chmod 700 keycloak/certs

# Verificar
ls -la keycloak/certs/
```

## 🌐 Ambientes

### Desenvolvimento (localhost)

```bash
# Usar certificado self-signed
cd keycloak/certs
./generate-keystore.sh

# Configurar .env.keycloak
cat > ../../.env.keycloak << 'EOF'
KEYCLOAK_DB_PASSWORD=dev_password_change_me
KEYCLOAK_HOSTNAME=localhost
KEYCLOAK_ADMIN=admin
KEYCLOAK_ADMIN_PASSWORD=admin_change_me
KEYCLOAK_HTTP_PORT=8080
KEYCLOAK_HTTPS_PORT=8443
EOF
```

### Staging (auth.intellicare.ia.br)

```bash
# Opção 1: Let's Encrypt via Traefik (RECOMENDADO)
# O Traefik gerencia certificados automaticamente
# Não precisa de certificados manualmente

# Opção 2: Certificado próprio (se necessário)
# Adquirir certificado de CA
# Converter para JKS
openssl pkcs12 -export -in fullchain.pem -inkey privkey.pem -out cert.p12 -name keycloak
keytool -importkeystore -deststorepass changeme -destkeypass changeme -destkeystore server.keystore -srckeystore cert.p12 -srcstoretype PKCS12 -srcstorepass changeme -alias keycloak

# Configurar .env.staging
cat > ../../.env.staging << 'EOF'
# Keycloak Staging
KEYCLOAK_DB_PASSWORD=${KEYCLOAK_DB_PASSWORD}
KEYCLOAK_HOSTNAME=auth.intellicare.ia.br
KEYCLOAK_ADMIN=admin
KEYCLOAK_ADMIN_PASSWORD=${KEYCLOAK_ADMIN_PASSWORD}
KEYCLOAK_HTTP_PORT=8080
KEYCLOAK_HTTPS_PORT=8443
EOF
```

### Produção (auth.saudeconectada.com.br)

```bash
# ⚠️ USAR APENAS CERTIFICADOS DE CA CONFIÁVEIS
# Let's Encrypt via Traefik é RECOMENDADO

# Certificado deve ter:
# - CN=auth.saudeconectada.com.br
# - SAN=auth.saudeconectada.com.br, *.saudeconectada.com.br
# - Emitido por CA confiável (Let's Encrypt, Comodo, DigiCert, etc)

# Configurar .env.production
cat > ../../.env.production << 'EOF'
# Keycloak Production
KEYCLOAK_DB_PASSWORD=${KEYCLOAK_DB_PASSWORD}  # From Vault
KEYCLOAK_HOSTNAME=auth.saudeconectada.com.br
KEYCLOAK_ADMIN=admin
KEYCLOAK_ADMIN_PASSWORD=${KEYCLOAK_ADMIN_PASSWORD}  # From Vault
KEYCLOAK_HTTP_PORT=8080
KEYCLOAK_HTTPS_PORT=8443
EOF
```

## 🔧 Troubleshooting

### Erro: "keystore password was incorrect"

```bash
# Verificar senha do keystore
keytool -list -keystore server.keystore
# Digitar a senha

# Se esqueceu a senha, regenerar
rm server.keystore
./generate-keystore.sh
```

### Erro: "Certificate expired"

```bash
# Verificar data de expiração
keytool -list -v -keystore server.keystore | grep "Valid from"

# Regenerar com validade maior
# Editar generate-keystore.sh: VALIDITY=3650 (10 anos)
./generate-keystore.sh
```

### Erro: "Hostname verification failed"

```bash
# Para desenvolvimento, adicionar exceção no browser
# Ou usar CN correto no certificado

# Para staging/produção, usar hostname correto:
# - auth.intellicare.ia.br
# - auth.saudeconectada.com.br
```

## ✅ Checklist

- [ ] Diretório `keycloak/certs` criado
- [ ] Script `generate-keystore.sh` criado
- [ ] Keystore `server.keystore` gerado
- [ ] Permissões corretas (600 para keystore)
- [ ] Senha documentada em local seguro
- [ ] `.env.keycloak` configurado
- [ ] Certificado verificado com `keytool -list`

## 📝 Próximo Passo

Após criar os certificados, prossiga para: **[02_START_KEYCLOAK.md](./02_START_KEYCLOAK.md)**

---

**Última Atualização**: 2026-03-01
**Responsável**: IntelliCare Team
