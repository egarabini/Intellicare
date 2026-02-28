# 🎭 IntelliCare - Apresentação Interativa com Wanda

Apresentação Python interativa com IA narradora (Wanda) apresentando o projeto IntelliCare.

**Status:** ✅ Fases 1 e 2 concluídas | 📋 Fase 3 preparada

---

## 🚀 Início Rápido

### Instalação
```bash
cd apresentacao
python -m venv .venv
# Windows PowerShell
.venv\Scripts\Activate.ps1
# Linux/macOS
# source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### Testes Automatizados (Recomendado)
```bash
# Validar tudo está funcionando
python test_terminal_auto.py  # Fase 1: 5/5 testes
python test_pygame_mvp.py     # Fase 2: 6/6 testes
```

### Apresentação Completa
```bash
# TTS offline (padrão)
python main.py --versao v1_visao_geral --voz offline

# TTS online (melhor qualidade - requer API key)
python main.py --versao v1_visao_geral --voz online

# V2 - Galeria de Agentes
python main.py --versao v2_agentes --voz offline

# V2 usando fotos "reais" dos agentes
python main.py --versao v2_agentes --agente-imagem real --voz offline

# V2 com transicao real -> cartoon no mesmo slide
python main.py --versao v2_agentes --agente-imagem dual --voz offline
```

---

## 🎮 Controles

| Tecla | Ação |
|-------|------|
| **ESPAÇO** | Próximo slide |
| **BACKSPACE** | Slide anterior |
| **D** | Deep dive |
| **P** | Perguntar para Wanda |
| **R** | Repetir narração |
| **M** | Mute/Unmute |
| **ESC** | Sair |

---

## 📊 Status das Fases

| Fase | Status | Testes | Tempo |
|------|--------|--------|-------|
| **1. Protótipo Terminal** | ✅ Completa | 5/5 ✅ | 1h |
| **2. MVP Pygame** | ✅ Completa | 6/6 ✅ | 30min |
| **3. Teste Stakeholders** | 📋 Preparada | - | 1 dia |
| **4. TTS Inteligente** | ⏸️ Aguardando | - | 3 dias |
| **5. Visualizações 3D** | ⏸️ Aguardando | - | 1 semana |
| **6. Interatividade** | ⏸️ Aguardando | - | 3 dias |
| **7. Polimento** | ⏸️ Aguardando | - | 2 dias |

---

## 📂 Estrutura

```
apresentacao/
├── main.py                              # Launcher principal
├── test_terminal_auto.py                # Testes Fase 1
├── test_pygame_mvp.py                   # Testes Fase 2
├── test_terminal_prototype.py           # Protótipo interativo
│
├── core/                                # Engine principal
│   ├── presentation_engine.py           # Engine Pygame
│   ├── slide_manager.py                 # Gerenciador de slides
│   ├── narrator.py                      # Narrador
│   ├── interaction_handler.py           # Controles
│   └── animation_engine.py              # Animações
│
├── slides/                              # Biblioteca de slides
│   ├── base_slide.py                    # Classe base
│   ├── title_slide.py                   # Slide de título
│   ├── content_slide.py                 # Slide de conteúdo
│   ├── diagram_slide.py                 # Slide de diagrama
│   └── metrics_slide.py                 # Slide de métricas
│
├── versoes/                             # Versões da apresentação
│   └── v1_visao_geral/                  # V1 - 5 slides
│       └── slides.py
│
├── assets/                              # Recursos
│   └── themes/
│       ├── dark.json                    # Tema escuro
│       └── light.json                   # Tema claro
│
└── docs/                                # Documentação
    ├── FASE1_CONCLUIDA.md               # Fase 1: Resultados
    ├── FASE2_CONCLUIDA.md               # Fase 2: Resultados
    ├── FASE3_GUIA_TESTE_STAKEHOLDERS.md # Fase 3: Guia
    ├── RESUMO_PROGRESSO_FASES.md        # Resumo geral
    └── COMO_TESTAR.md                   # Guia de testes
```

---

## 🎯 Versões Disponíveis

### V1 - Visão Geral (5 slides)
1. **Título** - IntelliCare
2. **O Problema** - Desafios da saúde no Brasil (com deep dive)
3. **A Solução** - Wanda Orchestrator
4. **Capacidades** - Métricas e números
5. **Demonstração** - Raciocínio multi-domínio

### V2 - Galeria de Agentes (10 slides)
1. **Abertura** - Wanda como apresentadora
2. **Públicos da apresentação** - Diversidade de stakeholders
3. **Orquestração** - Papel da Wanda no ecossistema
4. **WANDA** - Identidade e representação
5. **FLORENCE** - Identidade e representação
6. **OSWALDO** - Identidade e representação
7. **ZILDA** - Identidade e representação
8. **GERALDA** - Identidade e representação
9. **DONABEDIAN** - Identidade e representação
10. **Encerramento** - Síntese do ecossistema

---

## 🛠️ Tecnologias

- **Pygame** - Engine gráfico principal
- **Rich** - Prototipagem terminal
- **OpenAI TTS** - Voz da Wanda (online)
- **pyttsx3** - TTS offline (fallback)

---

## 📖 Documentação

- **[COMO_TESTAR.md](COMO_TESTAR.md)** - Guia completo de testes
- **[RESUMO_PROGRESSO_FASES.md](RESUMO_PROGRESSO_FASES.md)** - Status geral
- **[FASE3_GUIA_TESTE_STAKEHOLDERS.md](FASE3_GUIA_TESTE_STAKEHOLDERS.md)** - Próximos passos

---

## 🧪 Testes

### Executar Todos os Testes
```bash
python test_terminal_auto.py && python test_pygame_mvp.py
```

**Resultado esperado:** 11/11 testes passando ✅

---

## 📝 Licença

Projeto IntelliCare - 2026
