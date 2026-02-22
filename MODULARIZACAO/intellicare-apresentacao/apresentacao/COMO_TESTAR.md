# 🧪 Como Testar a Apresentação Interativa Wanda

**Guia rápido para testar todas as funcionalidades implementadas.**

---

## 🚀 Início Rápido

### 1. Instalação
```bash
cd apresentacao
pip install -r requirements.txt
```

### 2. Testes Automatizados (Recomendado)
```bash
# Teste Fase 1 (Protótipo Terminal)
python test_terminal_auto.py

# Teste Fase 2 (MVP Pygame)
python test_pygame_mvp.py
```

**Resultado esperado:** Todos os testes devem passar ✅

---

## 🎭 Modos de Teste

### Modo 1: Testes Automatizados (Sem Interação)

#### Fase 1 - Terminal
```bash
python test_terminal_auto.py
```

**O que testa:**
- ✅ Criação de 5 slides
- ✅ Atributos dos slides
- ✅ Deep dive
- ✅ Narrações
- ✅ Simulação de renderização

**Tempo:** ~5 segundos

---

#### Fase 2 - Pygame
```bash
python test_pygame_mvp.py
```

**O que testa:**
- ✅ Inicialização do Pygame
- ✅ Criação do PresentationEngine
- ✅ Carregamento de slides
- ✅ Renderização de slides
- ✅ Navegação
- ✅ Carregamento de temas

**Tempo:** ~10 segundos

---

### Modo 2: Protótipo Terminal (Interativo)

```bash
python test_terminal_prototype.py
```

**Controles:**
- `ENTER` - Próximo slide
- `B` - Voltar
- `D` - Deep Dive (no Slide 2)
- `R` - Repetir narração
- `Q` - Sair

**O que testar:**
1. Navegação sequencial (ENTER)
2. Voltar (B)
3. Deep dive no Slide 2 (D)
4. Repetir narração (R)
5. Sair (Q)

**Tempo:** ~5 minutos

---

### Modo 3: Apresentação Pygame Completa (Interativo)

#### Opção A: TTS Offline (Padrão)
```bash
python main.py --versao v1_visao_geral --voz offline
```

#### Opção B: TTS Online (Melhor Qualidade)
```bash
# Requer OPENAI_API_KEY no .env
python main.py --versao v1_visao_geral --voz online
```

#### Opção C: Tema Claro
```bash
python main.py --tema light
```

#### Opção D: Resolução Customizada
```bash
python main.py --width 1280 --height 720
```

**Controles:**
- `ESPAÇO` - Próximo slide
- `BACKSPACE` - Slide anterior
- `R` - Repetir narração
- `M` - Mute/Unmute
- `ESC` - Sair

**O que testar:**
1. ✅ Animações de fade in (Slide 1)
2. ✅ Lista de itens (Slide 2)
3. ✅ Diagrama ASCII (Slide 3)
4. ✅ Tabela de métricas (Slide 4)
5. ✅ Demonstração (Slide 5)
6. ✅ Navegação completa
7. ✅ Narração (se TTS configurado)

**Tempo:** ~10 minutos

---

## 📋 Checklist de Validação

### ✅ Testes Automatizados
- [ ] `test_terminal_auto.py` - 5/5 testes passaram
- [ ] `test_pygame_mvp.py` - 6/6 testes passaram

### ✅ Protótipo Terminal
- [ ] Navegação funciona (ENTER, B)
- [ ] Deep dive funciona (D no Slide 2)
- [ ] Repetir narração funciona (R)
- [ ] Sair funciona (Q)
- [ ] Todos os 5 slides aparecem corretamente

### ✅ Apresentação Pygame
- [ ] Janela abre corretamente
- [ ] Slide 1 (Título) renderiza com fade in
- [ ] Slide 2 (Conteúdo) mostra lista de itens
- [ ] Slide 3 (Diagrama) mostra arquitetura
- [ ] Slide 4 (Métricas) mostra tabela
- [ ] Slide 5 (Demo) mostra exemplo
- [ ] Navegação ESPAÇO funciona
- [ ] Navegação BACKSPACE funciona
- [ ] ESC fecha a apresentação
- [ ] Tema dark carrega corretamente
- [ ] Tema light carrega corretamente (se testado)

### ✅ TTS (Se Configurado)
- [ ] Narração toca automaticamente
- [ ] Voz é clara e compreensível
- [ ] Sincronização com slides está correta
- [ ] Mute (M) funciona
- [ ] Repetir (R) funciona

---

## 🐛 Troubleshooting

### Problema: "ModuleNotFoundError: No module named 'rich'"
**Solução:**
```bash
pip install rich
```

### Problema: "ModuleNotFoundError: No module named 'pygame'"
**Solução:**
```bash
pip install pygame
```

### Problema: TTS não funciona (offline)
**Solução:**
```bash
pip install pyttsx3
```

### Problema: TTS não funciona (online)
**Solução:**
1. Criar arquivo `.env` na pasta `apresentacao/`
2. Adicionar: `OPENAI_API_KEY=sk-your-key-here`

### Problema: Janela Pygame não abre
**Solução:**
- Verificar se há outro processo Pygame rodando
- Tentar resolução menor: `python main.py --width 800 --height 600`

### Problema: Testes falham
**Solução:**
1. Verificar se todas as dependências estão instaladas
2. Executar: `pip install -r requirements.txt`
3. Verificar se está na pasta `apresentacao/`

---

## 📊 Resultados Esperados

### Testes Automatizados
```
============================================================
🧪 TESTES DO PROTÓTIPO TERMINAL - FASE 1
============================================================
✅ PASSOU: Criação de Slides
✅ PASSOU: Atributos dos Slides
✅ PASSOU: Deep Dive
✅ PASSOU: Narrações
✅ PASSOU: Simulação de Renderização

Resultado: 5/5 testes passaram
🎉 TODOS OS TESTES PASSARAM!
```

```
============================================================
🧪 TESTES DO MVP PYGAME - FASE 2
============================================================
✅ PASSOU: Inicialização do Pygame
✅ PASSOU: Criação do PresentationEngine
✅ PASSOU: Carregamento de Slides
✅ PASSOU: Renderização de Slides
✅ PASSOU: Navegação
✅ PASSOU: Carregamento de Temas

Resultado: 6/6 testes passaram
🎉 TODOS OS TESTES PASSARAM!
```

---

## 🎯 Próximos Passos

Após validar todos os testes:

1. ✅ Executar apresentação completa
2. ✅ Testar com stakeholders (ver `FASE3_GUIA_TESTE_STAKEHOLDERS.md`)
3. ✅ Coletar feedback
4. ✅ Implementar melhorias

---

## 📞 Suporte

Se encontrar problemas:

1. Verificar `RESUMO_PROGRESSO_FASES.md` para contexto
2. Consultar `FASE1_CONCLUIDA.md` e `FASE2_CONCLUIDA.md`
3. Revisar logs de erro
4. Verificar versões das dependências

---

**Criado por:** Augment Agent  
**Data:** 2026-02-08  
**Última Atualização:** 2026-02-08

