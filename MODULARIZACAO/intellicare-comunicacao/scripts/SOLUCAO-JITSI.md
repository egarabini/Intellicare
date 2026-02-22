# 🚀 Solução Pronta: Jitsi DNS Resolution Error

## 📊 Resumo do Problema

**Erro:** `xmpp.meet.jitsi could not be resolved (3: Host not found)`

**Causa:** O nginx no container `web` não consegue resolver o hostname `xmpp.meet.jitsi`

**Solução:** Adicionar `xmpp.meet.jitsi` como alias de rede do serviço prosody

## ✅ Scripts Criados

1. ✅ `fix-jitsi-dns.sh` - Diagnóstico interativo
2. ✅ `fix-jitsi-dns-auto.sh` - Correção automática com Python
3. ✅ `fix-jitsi-dns-simple.sh` - Correção simples e direta ⭐
4. ✅ `run-fix-jitsi-remote.sh` - Execução remota
5. ✅ `README-JITSI-DNS-FIX.md` - Documentação completa

## 🎯 Execução Rápida (3 Opções)

### Opção 1: Executar Localmente com SSH ⭐ MAIS RÁPIDO

```bash
cd MODULARIZACAO/intellicare-comunicacao/scripts
chmod +x run-fix-jitsi-remote.sh
./run-fix-jitsi-remote.sh
```

Este script:
- Transfere o fix-jitsi-dns-simple.sh para o servidor
- Executa automaticamente
- Mostra resultado dos testes

### Opção 2: Copiar e Executar no Servidor

```bash
# 1. Copiar script para o servidor
scp -P 22 MODULARIZACAO/intellicare-comunicacao/scripts/fix-jitsi-dns-simple.sh \
    root@161.97.141.186:/install/desenvolvimento/docker-compose-v3/jitsi-docker-jitsi-meet-35879bb/

# 2. Conectar e executar
ssh root@161.97.141.186 -p 22
cd /install/desenvolvimento/docker-compose-v3/jitsi-docker-jitsi-meet-35879bb
chmod +x fix-jitsi-dns-simple.sh
./fix-jitsi-dns-simple.sh
```

### Opção 3: Executar Manualmente no Servidor

```bash
# 1. Conectar no servidor
ssh root@161.97.141.186 -p 22

# 2. Ir para o diretório do Jitsi
cd /install/desenvolvimento/docker-compose-v3/jitsi-docker-jitsi-meet-35879bb

# 3. Backup
cp docker-compose-jitsi.yml docker-compose-jitsi.yml.backup.$(date +%Y%m%d_%H%M%S)

# 4. Editar docker-compose-jitsi.yml
# Adicionar no serviço prosody:
#   networks:
#     meet.jitsi:
#       aliases:
#         - xmpp.meet.jitsi

# 5. Reiniciar
docker compose -f docker-compose-jitsi.yml -p jitsi-meet down
docker compose -f docker-compose-jitsi.yml -p jitsi-meet up -d

# 6. Aguardar 20 segundos
sleep 20

# 7. Testar
docker exec $(docker ps -q -f name=jitsi-meet-web) curl -I http://localhost/http-bind
```

## 📋 O que o Script Faz

1. ✅ Cria backup do docker-compose-jitsi.yml
2. ✅ Adiciona network alias `xmpp.meet.jitsi` ao serviço prosody
3. ✅ Reinicia containers (down + up)
4. ✅ Aguarda 20 segundos para inicialização
5. ✅ Testa resolução DNS
6. ✅ Testa endpoint /http-bind
7. ✅ Mostra status e logs

## ✅ Como Verificar se Funcionou

Após executar, você deve ver:

```bash
# DNS resolvendo
✅ xmpp.meet.jitsi resolves to 172.x.x.x

# HTTP-bind respondendo
HTTP/1.1 200 OK

# Sem erros nos logs
✅ Sem erros "could not be resolved"
```

## 🌐 Teste Final

Acesse no navegador: **https://meet.gsi.srv.br**

Se abrir a sala sem erro 502, está funcionando! 🎉

## 📝 Próximos Passos

Depois que o DNS estiver funcionando:

1. **Configurar Autenticação Keycloak**
   ```bash
   ./configure-jitsi-keycloak-gsi.sh
   ```

2. **Configurar Rocket.Chat** (se necessário)
   ```bash
   ./init-rocketchat.sh
   ```

## 🆘 Troubleshooting

### Ainda retorna 502?

```bash
# Verificar containers
docker compose -f docker-compose-jitsi.yml -p jitsi-meet ps

# Ver logs
docker compose -f docker-compose-jitsi.yml -p jitsi-meet logs web --tail=50
docker compose -f docker-compose-jitsi.yml -p jitsi-meet logs prosody --tail=50

# Testar prosody diretamente
docker exec $(docker ps -q -f name=prosody) curl -I http://localhost:5280/http-bind
```

### DNS ainda não resolve?

```bash
# Verificar se o alias foi adicionado
docker inspect $(docker ps -q -f name=prosody) | grep -A 10 Aliases

# Verificar redes
docker network ls | grep jitsi
docker inspect $(docker ps -q -f name=web) | grep -A 10 Networks
docker inspect $(docker ps -q -f name=prosody) | grep -A 10 Networks
```

## 📞 Informações

- **Servidor:** 161.97.141.186:22
- **User:** root
- **Path:** /install/desenvolvimento/docker-compose-v3/jitsi-docker-jitsi-meet-35879bb
- **Domain:** meet.gsi.srv.br
- **Keycloak:** keycloak.gsi.srv.br/realms/bemcuidar

## 💡 Quer que eu execute agora?
Posso executar o script remotamente se quiser! Basta confirmar.

