# 📋 Fase 3: Sessão de Teste - Em Andamento

**Data:** 2026-02-08  
**Horário Início:** Agora  
**Testador:** Você (Stakeholder Principal)  
**Versão:** V1 - Visão Geral

---

## 🎯 Objetivo da Sessão

Validar a apresentação interativa Wanda e coletar feedback para melhorias.

---

## 🎮 Apresentação em Execução

**Comando executado:**
```bash
python main.py --versao v1_visao_geral --voz offline --width 1280 --height 720
```

**Configuração:**
- Resolução: 1280x720
- TTS: Offline (pyttsx3)
- Tema: Dark (padrão)
- Versão: V1 - Visão Geral (5 slides)

---

## 🎬 Roteiro de Teste

### Slide 1: Título - IntelliCare
**O que observar:**
- [ ] Animação de fade in suave
- [ ] Título legível e impactante
- [ ] Subtítulo aparece após título
- [ ] Narração clara (se TTS funcionando)

**Tempo estimado:** 30 segundos

---

### Slide 2: O Desafio da Saúde no Brasil
**O que observar:**
- [ ] Lista de 4 itens aparece
- [ ] Ícones ❌ visíveis
- [ ] Texto legível
- [ ] Mensagem clara sobre os problemas

**Teste especial:**
- [ ] Pressionar `D` para Deep Dive
- [ ] Conteúdo de arquitetura aparece
- [ ] Informações técnicas detalhadas
- [ ] Voltar ao slide principal

**Tempo estimado:** 1-2 minutos

---

### Slide 3: Wanda - Orquestrador Inteligente
**O que observar:**
- [ ] Diagrama ASCII art aparece
- [ ] Estrutura de arquitetura clara
- [ ] Conexões entre componentes visíveis
- [ ] Narração explica o diagrama

**Tempo estimado:** 1 minuto

---

### Slide 4: O que a Wanda Sabe Fazer
**O que observar:**
- [ ] Tabela de métricas aparece
- [ ] 4 métricas com ícones
- [ ] Números destacados
- [ ] Layout organizado

**Métricas esperadas:**
- 🔧 Ferramentas Integradas: 13
- 🔗 Sistemas Conectados: 5
- ⚡ Tempo Médio: 2.6s
- ✅ Taxa de Sucesso: 100%

**Tempo estimado:** 1 minuto

---

### Slide 5: Demonstração - Raciocínio Multi-Domínio
**O que observar:**
- [ ] Exemplo de query aparece
- [ ] Passos do raciocínio visíveis
- [ ] Resultado integrado mostrado
- [ ] Demonstração clara do valor

**Tempo estimado:** 1-2 minutos

---

## 🎮 Controles para Testar

Durante a apresentação, teste:

| Controle | Ação | Status |
|----------|------|--------|
| `ESPAÇO` | Próximo slide | [ ] Testado |
| `BACKSPACE` | Slide anterior | [ ] Testado |
| `D` | Deep Dive (Slide 2) | [ ] Testado |
| `R` | Repetir narração | [ ] Testado |
| `M` | Mute/Unmute | [ ] Testado |
| `ESC` | Sair | [ ] Testado |

---

## 📝 Notas Durante a Apresentação

### Impressões Gerais
```
[Escreva suas impressões aqui enquanto assiste]




```

### Pontos Positivos
```
1. 
2. 
3. 
```

### Pontos a Melhorar
```
1. 
2. 
3. 
```

### Bugs/Problemas Encontrados
```
1. 
2. 
3. 
```

---

## 📊 Avaliação Rápida

**Escala: 1 (Ruim) a 5 (Excelente)**

| Aspecto | Nota | Comentário |
|---------|------|------------|
| Qualidade Visual | /5 | |
| Clareza do Conteúdo | /5 | |
| Navegação | /5 | |
| Animações | /5 | |
| Narração (se testada) | /5 | |
| **GERAL** | /5 | |

---

## 💡 Sugestões de Melhorias

### Imediatas (Críticas)
```
1. 
2. 
3. 
```

### Importantes (Próxima Fase)
```
1. 
2. 
3. 
```

### Desejáveis (Futuro)
```
1. 
2. 
3. 
```

---

## ✅ Checklist Final

Após completar a apresentação:

- [ ] Todos os 5 slides visualizados
- [ ] Navegação testada (frente e trás)
- [ ] Deep dive testado (Slide 2)
- [ ] Controles funcionando
- [ ] Feedback documentado acima
- [ ] Nota geral atribuída

---

## 🎯 Próximos Passos

Após esta sessão:

1. [ ] Consolidar feedback
2. [ ] Priorizar melhorias
3. [ ] Decidir próxima fase (Fase 4 ou 5)
4. [ ] Atualizar roadmap

---

## 📞 Comandos Úteis

**Se precisar reiniciar:**
```bash
# Fechar apresentação atual (ESC)
# Executar novamente:
python main.py --versao v1_visao_geral --voz offline
```

**Testar com TTS online (melhor qualidade):**
```bash
# Requer OPENAI_API_KEY no .env
python main.py --versao v1_visao_geral --voz online
```

**Testar tema claro:**
```bash
python main.py --tema light
```

---

**Status:** 🎬 Apresentação em execução  
**Aguardando:** Seu feedback após visualização completa

