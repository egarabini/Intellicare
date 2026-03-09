# 🔑 Chave SSH para GitHub - IntelliCare

## ✅ Chaves Criadas com Sucesso!

Foram criadas 2 chaves SSH:

1. **RSA 4096 bits** (começa com `ssh-rsa`) - **USE ESTA!**
2. **ED25519** (mais moderna, mas GitHub pode não aceitar em alguns casos)

---

## 📋 CHAVE PÚBLICA RSA (Copie esta!)

```
ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAACAQCxFMbSGk0IUFu2idcWTPtuwtNVx9AGXcUTFXvligFXuCDCAjb7fYGp6RxxV8F/gkSPpP8NKybbksHQ0qdLhRvwtVWBFyRBtt0RBNl6vqThQSLvkLEPlX0zWl33pEQUPDZSg8UPYBwg4JkIhdPqo4YnzLXADIUVOPP/j9Ti7vwBy0BJZJAcr4RIewNnvC5HTX/GzAps6KhJ+5ViiK9Giell+qFe9mxFTF81aDZdfK9KWAVwEOnGAtNFw4lRPeTBI2WaKJH0dsUR0hf8StIteXJSYgDOXCyZRIM6PKOQ2wbTjGuGNEIdHXoa4I1M7RN96gJsVSLDd/AUEHsw3fyFm8PUpfv69TOJCyGO6Dh8FGtN4IT7OpajyHYd25ir8xdFxkPMKN2wGtKY9/h8A+ouEq16dBMbh2fWUWqKVD/7eT9CBnyx7HGp6utrEcmaLCeYBlLem5+i9k5mmzKL9sp/trE41RSka29VTE/rWA7lowEUfbOvpAfxqYDSOQ3j9kyzdlV7QNIOa4IxTumaKQUdFcYgXHCkp9KG/Ml3A0HaBhzFRqW7mqKnyaAE0vRrKT8RSlaNaE2M4RubSBG9kIEkuXFRmvwjsyz623256GojHYf7znT706orXq7XeZqsteznsgmDTrSEoJgZ4+vSQWdc6VXMW3yo30Nr/5N7la4XR7NnBQ== egarabini@intellicare
```

---

## 🚀 Como Adicionar no GitHub (Passo a Passo)

### **Passo 1: Copiar a Chave**

Copie TODO o texto acima (começando com `ssh-rsa` até `egarabini@intellicare`)

### **Passo 2: Ir para GitHub**

1. Acesse: https://github.com/settings/keys
2. Ou vá em: **Settings** → **SSH and GPG keys**

### **Passo 3: Adicionar Nova Chave**

1. Clique em **"New SSH key"** (botão verde)
2. Preencha:
   - **Title:** `IntelliCare - Windows Desktop`
   - **Key type:** `Authentication Key`
   - **Key:** Cole a chave pública RSA (copiada no Passo 1)
3. Clique em **"Add SSH key"**
4. Confirme com sua senha do GitHub se solicitado

---

## ✅ Testar a Conexão SSH

Após adicionar a chave no GitHub, teste a conexão:

```powershell
ssh -T git@github.com
```

**Resposta esperada:**
```
Hi egarabini! You've successfully authenticated, but GitHub does not provide shell access.
```

---

## 🔧 Configurar Git para Usar SSH

### **Passo 1: Remover o remote HTTPS atual**

```powershell
cd C:\User\egara\INTELLICARE
git remote remove origin
```

### **Passo 2: Adicionar remote SSH**

```powershell
git remote add origin git@github.com:egarabini/intellicare.git
```

### **Passo 3: Fazer Push**

```powershell
git push -u origin main:master
```

---

## 📁 Localização das Chaves

### **Chaves Privadas** (NÃO COMPARTILHE!)
- RSA: `C:\Users\egara\.ssh\id_rsa_intellicare`
- ED25519: `C:\Users\egara\.ssh\id_ed25519_intellicare`

### **Chaves Públicas** (pode compartilhar)
- RSA: `C:\Users\egara\.ssh\id_rsa_intellicare.pub`
- ED25519: `C:\Users\egara\.ssh\id_ed25519_intellicare.pub`

---

## 🔐 Configurar SSH Agent (Opcional)

Para não precisar digitar a senha toda vez:

```powershell
# Iniciar SSH Agent
Start-Service ssh-agent

# Adicionar chave
ssh-add C:\Users\egara\.ssh\id_rsa_intellicare
```

---

## ⚠️ Importante

- ✅ **Chave Pública:** Pode ser compartilhada (adicione no GitHub)
- ❌ **Chave Privada:** NUNCA compartilhe ou envie para ninguém!
- 🔒 **Backup:** Faça backup das chaves privadas em local seguro

---

## 🆘 Problemas Comuns

### **Erro: "Permission denied (publickey)"**

1. Verifique se a chave foi adicionada no GitHub
2. Teste a conexão: `ssh -T git@github.com`
3. Verifique se o SSH Agent está rodando

### **Erro: "Could not open a connection to your authentication agent"**

```powershell
Start-Service ssh-agent
ssh-add C:\Users\egara\.ssh\id_rsa_intellicare
```

---

## 📞 Próximos Passos

Após adicionar a chave no GitHub:

1. ✅ Testar conexão SSH
2. ✅ Configurar remote SSH
3. ✅ Fazer push do código
4. ✅ Continuar configuração do servidor

---

**Boa sorte! 🚀**

