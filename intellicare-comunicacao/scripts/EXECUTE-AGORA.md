# ⚡ EXECUTE AGORA - Correção Jitsi DNS

## 🎯 O QUE FAZER

Copie e cole os comandos abaixo **diretamente no servidor**.

---

## 📋 PASSO 1: Conectar no Servidor

Abra seu terminal SSH e conecte:

```bash
ssh root@161.97.141.186 -p 22
```

Senha: `Crazy57LB`

---

## 📋 PASSO 2: Ir para o Diretório do Jitsi

```bash
cd /install/desenvolvimento/docker-compose-v3/jitsi-docker-jitsi-meet-35879bb
```

---

## 📋 PASSO 3: Criar o Script de Correção

Cole este comando completo (copia tudo de uma vez):

```bash
cat > fix-jitsi-dns.sh << 'EOF'
#!/bin/bash

set -e

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}╔═══════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║        CORREÇÃO JITSI DNS RESOLUTION ERROR            ║${NC}"
echo -e "${BLUE}╚═══════════════════════════════════════════════════════╝${NC}"
echo ""

echo -e "${YELLOW}1. Backup...${NC}"
cp docker-compose-jitsi.yml docker-compose-jitsi.yml.backup.$(date +%Y%m%d_%H%M%S)
echo -e "${GREEN}✅ Backup criado${NC}"
echo ""

echo -e "${YELLOW}2. Verificando se já tem alias...${NC}"
if grep -q "xmpp.meet.jitsi" docker-compose-jitsi.yml; then
    echo -e "${GREEN}✅ Alias já existe!${NC}"
    NEEDS_FIX=false
else
    echo -e "${YELLOW}⚠️  Alias não encontrado - adicionando...${NC}"
    NEEDS_FIX=true
fi
echo ""

if [ "$NEEDS_FIX" = true ]; then
    echo -e "${YELLOW}3. Adicionando alias...${NC}"
    
    awk '
    /^  prosody:/ {
        print $0
        in_prosody = 1
        next
    }
    
    in_prosody && /^    [a-z_]/ {
        if (!added) {
            print "    networks:"
            print "      meet.jitsi:"
            print "        aliases:"
            print "          - xmpp.meet.jitsi"
            added = 1
        }
        in_prosody = 0
    }
    
    in_prosody && /^  [a-z]/ {
        if (!added) {
            print "    networks:"
            print "      meet.jitsi:"
            print "        aliases:"
            print "          - xmpp.meet.jitsi"
            added = 1
        }
        in_prosody = 0
    }
    
    { print $0 }
    ' docker-compose-jitsi.yml > docker-compose-jitsi.yml.tmp
    
    mv docker-compose-jitsi.yml.tmp docker-compose-jitsi.yml
    echo -e "${GREEN}✅ Alias adicionado${NC}"
fi
echo ""

echo -e "${YELLOW}4. Reiniciando containers...${NC}"
docker compose -f docker-compose-jitsi.yml -p jitsi-meet down
docker compose -f docker-compose-jitsi.yml -p jitsi-meet up -d

echo "   Aguardando 20 segundos..."
sleep 20
echo ""

echo -e "${YELLOW}5. Status:${NC}"
docker compose -f docker-compose-jitsi.yml -p jitsi-meet ps
echo ""

echo -e "${YELLOW}6. Testando DNS...${NC}"
WEB=$(docker ps -q -f name=jitsi-meet-web)

if [ -n "$WEB" ]; then
    echo "   DNS resolution:"
    docker exec $WEB getent hosts xmpp.meet.jitsi 2>/dev/null && echo -e "${GREEN}   ✅ DNS OK!${NC}" || echo -e "${RED}   ❌ DNS falhou${NC}"
    
    echo ""
    echo "   HTTP-bind endpoint:"
    docker exec $WEB curl -I http://localhost/http-bind 2>&1 | head -1
    
    echo ""
    echo "   Verificando erros nos logs:"
    docker logs $WEB --tail 10 2>&1 | grep -i "could not be resolved" || echo -e "${GREEN}   ✅ Sem erros DNS!${NC}"
fi

echo ""
echo -e "${BLUE}╔═══════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║                  CONCLUÍDO!                           ║${NC}"
echo -e "${BLUE}╚═══════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${YELLOW}🌐 Teste: https://meet.gsi.srv.br${NC}"
EOF
```

---

## 📋 PASSO 4: Executar o Script

```bash
chmod +x fix-jitsi-dns.sh
./fix-jitsi-dns.sh
```

---

## ✅ O QUE ESPERAR

Você verá:

1. ✅ Backup criado
2. ✅ Alias adicionado (se necessário)
3. ✅ Containers reiniciando
4. ✅ Status dos containers
5. ✅ Teste DNS: deve mostrar IP do prosody
6. ✅ Teste HTTP-bind: deve retornar `HTTP/1.1 200 OK`
7. ✅ Sem erros "could not be resolved" nos logs

---

## 🌐 TESTE FINAL

Abra no navegador: **https://meet.gsi.srv.br**

Crie uma sala (exemplo: https://meet.gsi.srv.br/teste)

Se entrar na sala sem erro 502 = **FUNCIONOU!** 🎉

---

## 📝 PRÓXIMO PASSO

Depois que funcionar, vamos configurar o Keycloak.

---

## 🆘 SE DER ERRO

Cole a saída completa do script aqui para eu analisar.

---

## 💡 RESUMO DO PROBLEMA

**Erro atual:** `xmpp.meet.jitsi could not be resolved (3: Host not found)`

**O que faz:** Adiciona `xmpp.meet.jitsi` como alias do container prosody na rede Docker

**Por que funciona:** O nginx conseguirá resolver o hostname e se conectar ao prosody

---

**Pronto! Execute agora e me avise o resultado! 🚀**
