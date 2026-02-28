# 🚀 EXECUTE AGORA - Configuração do Servidor

## ⚡ Método Mais Rápido (3 comandos)

### 1️⃣ Conecte ao servidor

```bash
ssh root@167.86.97.142
```

**Senha:** `Soeuso419863`

---

### 2️⃣ Baixe e execute o script

Cole estes comandos no terminal SSH:

```bash
curl -fsSL https://raw.githubusercontent.com/eduardo/intellicare/main/scripts/setup_servidor_direto.sh -o setup.sh
chmod +x setup.sh
./setup.sh
```

---

### 3️⃣ Aguarde a conclusão

O script executará automaticamente:
- ✅ Fase A: Preparação (~5-10 min)
- ✅ Fase B: Clone (~2-3 min)
- ✅ Fase C: Infraestrutura (~2 min)

**Tempo total:** ~10-15 minutos

---

## 📊 O que o script faz:

### Fase A - Preparação
- Atualiza sistema (apt update/upgrade)
- Instala ferramentas (curl, wget, git, vim, htop, ufw)
- Instala Docker
- Instala Docker Compose
- Configura firewall (portas 22, 80, 443, 3001, 8001-8006, 3000, 9090)

### Fase B - Clone
- Cria `/opt/intellicare`
- Clona repositório GitHub
- Copia `.env.homologacao` → `.env`

### Fase C - Infraestrutura
- Sobe PostgreSQL (container)
- Sobe Redis (container)
- Cria 6 schemas no banco

---

## ✅ Validação

Ao final, você verá:

```
✅ CONFIGURAÇÃO CONCLUÍDA COM SUCESSO!

Fases executadas:
  ✅ Fase A - Preparação do Servidor
  ✅ Fase B - Clone e Configuração
  ✅ Fase C - Infraestrutura

Serviços rodando:
NAME       STATUS
postgres   Up (healthy)
redis      Up (healthy)
```

---

## 🐛 Se der erro

### Erro: "curl: command not found"

```bash
apt update && apt install -y curl
```

Depois execute o passo 2 novamente.

---

### Erro: "Permission denied"

Certifique-se de estar logado como `root`:

```bash
whoami
# Deve retornar: root
```

---

### Erro ao clonar repositório

Verifique se o repositório é público:

```bash
git clone https://github.com/eduardo/intellicare.git
```

---

## 📝 Após a conclusão

1. ✅ Containers rodando (postgres, redis)
2. ✅ Schemas criados no banco
3. ✅ Firewall configurado
4. ⏳ Pronto para Fase D (Deploy completo)

---

## 🎯 Alternativa: Executar manualmente

Se preferir executar passo a passo, veja:

`docs/SERVIDORES/HOMOLOGACAO/implementacao/Inicializacao/Fase1_Preparacao_Sistema/20260222-1215_GUIA_EXECUCAO_REMOTA.md`

---

## 📞 Suporte

Se encontrar problemas, copie a saída do script e me envie para análise.

---

**Boa sorte! 🚀**

