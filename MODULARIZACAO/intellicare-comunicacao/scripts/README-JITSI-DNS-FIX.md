# Correção: Jitsi DNS Resolution Error

## 🔍 Problema Identificado

O erro nos logs:
```
xmpp.meet.jitsi could not be resolved (3: Host not found)
```

**Causa:** O container `web` (nginx) não consegue resolver o hostname `xmpp.meet.jitsi` na rede Docker.

O nginx está configurado para:
```nginx
proxy_pass http://xmpp.meet.jitsi:5280/http-bind
```

Mas esse hostname não existe como alias na rede Docker!

## ✅ Solução

Adicionar `xmpp.meet.jitsi` como **network alias** do serviço `prosody` no docker-compose.

## 📜 Scripts Disponíveis

### 1. `fix-jitsi-dns-simple.sh` ⭐ RECOMENDADO

Script simples e direto que:
- Faz backup automático
- Adiciona o alias necessário
- Reinicia os containers
- Testa a conectividade

**Uso:**
```bash
cd /install/desenvolvimento/docker-compose-v3/jitsi-docker-jitsi-meet-35879bb
bash fix-jitsi-dns-simple.sh
```

### 2. `fix-jitsi-dns-auto.sh`

Script mais completo com Python para edição YAML segura.

**Uso:**
```bash
cd /install/desenvolvimento/docker-compose-v3/jitsi-docker-jitsi-meet-35879bb
bash fix-jitsi-dns-auto.sh
```

### 3. `fix-jitsi-dns.sh`

Script interativo de diagnóstico e correção.

**Uso:**
```bash
cd /install/desenvolvimento/docker-compose-v3/jitsi-docker-jitsi-meet-35879bb
bash fix-jitsi-dns.sh
```

## 🚀 Execução Rápida

Conecte no servidor e execute:

```bash
# Conectar no servidor
ssh root@161.97.141.186

# Navegar até o diretório do Jitsi
cd /install/desenvolvimento/docker-compose-v3/jitsi-docker-jitsi-meet-35879bb

# Baixar o script (se necessário)
# ou copiar do workspace local

# Executar
chmod +x fix-jitsi-dns-simple.sh
./fix-jitsi-dns-simple.sh
```

## 🔧 Correção Manual (Alternativa)

Se preferir editar manualmente o `docker-compose-jitsi.yml`:

1. Localize o serviço `prosody`:
```yaml
  prosody:
    image: jitsi/prosody:stable-8960
    # ... outras configs
```

2. Adicione a seção `networks` com aliases:
```yaml
  prosody:
    image: jitsi/prosody:stable-8960
    # ... outras configs
    networks:
      meet.jitsi:
        aliases:
          - xmpp.meet.jitsi
```

3. Reinicie os containers:
```bash
docker compose -f docker-compose-jitsi.yml -p jitsi-meet down
docker compose -f docker-compose-jitsi.yml -p jitsi-meet up -d
```

## ✅ Verificação

Após a correção, teste:

```bash
# 1. Verificar se o alias foi criado
docker ps -q -f name=jitsi-meet-web | xargs -I {} docker exec {} getent hosts xmpp.meet.jitsi

# 2. Testar http-bind
docker ps -q -f name=jitsi-meet-web | xargs -I {} docker exec {} curl -I http://localhost/http-bind

# 3. Verificar logs
docker compose -f docker-compose-jitsi.yml -p jitsi-meet logs web --tail=20
```

Se tudo estiver OK, você verá:
- ✅ DNS resolvendo o IP do prosody
- ✅ HTTP 200 OK no /http-bind
- ✅ Sem erros "could not be resolved" nos logs

## 📋 Próximos Passos

Após corrigir o DNS:

1. **Testar** acesso: https://meet.gsi.srv.br
2. **Configurar** autenticação Keycloak: `configure-jitsi-keycloak-gsi.sh`
3. **Configurar** Rocket.Chat (se necessário)

## 🆘 Troubleshooting

### O alias não funciona?

Verifique se os containers estão na mesma rede:

```bash
# Ver redes do web
docker inspect $(docker ps -q -f name=jitsi-meet-web) | grep -A 5 Networks

# Ver redes do prosody
docker inspect $(docker ps -q -f name=jitsi-meet-prosody) | grep -A 5 Networks
```

### Ainda retorna 502?

Verifique se o prosody está rodando:

```bash
# Status
docker ps | grep prosody

# Logs
docker logs $(docker ps -q -f name=jitsi-meet-prosody)

# Teste direto na porta 5280
docker exec $(docker ps -q -f name=jitsi-meet-prosody) curl -I http://localhost:5280/http-bind
```

## 📞 Informações do Servidor

- **IP:** 161.97.141.186:22
- **User:** root
- **Jitsi Path:** /install/desenvolvimento/docker-compose-v3/jitsi-docker-jitsi-meet-35879bb
- **Domain:** meet.gsi.srv.br
- **Keycloak:** keycloak.gsi.srv.br
- **Realm:** bemcuidar
