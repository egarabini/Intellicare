# 🎯 TAREFA DEV 1 - CORE ENGINE & FUNDAÇÃO

**Responsável:** Dev 1 (Augment Agent)  
**Prioridade:** 🔴 CRÍTICA - Fundação do Sistema  
**Prazo:** 1 semana  
**Status:** 📋 Aguardando Início

---

## 📋 Objetivo

Criar a **fundação completa** da apresentação interativa:
- Engine principal (Pygame)
- Sistema de slides base
- Narração da Wanda (TTS)
- Navegação básica
- Primeira versão funcional (V1 - Visão Geral)

**Meta:** Apresentação MVP funcionando com Wanda narrando 5 slides.

---

## 🎯 Entregas Esperadas

### 1. Estrutura de Diretórios ✅

```
apresentacao/
├── main.py
├── requirements.txt
├── README.md
├── .env.example
├── core/
│   ├── __init__.py
│   ├── presentation_engine.py
│   ├── slide_manager.py
│   ├── narrator.py
│   ├── interaction_handler.py
│   └── animation_engine.py
├── slides/
│   ├── __init__.py
│   ├── base_slide.py
│   ├── title_slide.py
│   ├── content_slide.py
│   ├── diagram_slide.py
│   └── metrics_slide.py
├── wanda_ai/
│   ├── __init__.py
│   ├── wanda_narrator.py
│   └── prompts/
│       └── narrator_prompts.json
├── utils/
│   ├── __init__.py
│   ├── tts_manager.py
│   ├── audio_player.py
│   └── config.py
├── assets/
│   ├── fonts/
│   ├── images/
│   ├── audio/
│   └── themes/
│       ├── dark.json
│       └── light.json
└── versoes/
    └── v1_visao_geral/
        ├── __init__.py
        ├── slides.py
        └── narration.json
```

---

### 2. Core Engine (core/)

#### 2.1 presentation_engine.py

**Responsabilidades:**
- Inicializar Pygame
- Gerenciar loop principal (60 FPS)
- Coordenar slides, narração e interação
- Renderizar tela

**Funcionalidades:**
```python
class PresentationEngine:
    - __init__(width, height, theme)
    - add_slide(slide)
    - run()
    - next_slide()
    - previous_slide()
    - _render_wanda_avatar()
    - _process_action(action)
```

---

#### 2.2 slide_manager.py

**Responsabilidades:**
- Gerenciar lista de slides
- Controlar índice atual
- Transições entre slides

**Funcionalidades:**
```python
class SlideManager:
    - add_slide(slide)
    - get_current_slide()
    - next()
    - previous()
    - goto(index)
    - get_total_slides()
```

---

#### 2.3 narrator.py

**Responsabilidades:**
- Gerenciar TTS (online/offline)
- Reproduzir narração
- Sincronizar com slides

**Funcionalidades:**
```python
class Narrator:
    - __init__(mode="online", voice="nova")
    - speak(text, wait=True)
    - stop()
    - is_speaking()
    - set_volume(volume)
```

---

#### 2.4 interaction_handler.py

**Responsabilidades:**
- Capturar eventos de teclado/mouse
- Mapear para ações
- Retornar comandos

**Funcionalidades:**
```python
class InteractionHandler:
    - handle_event(event) -> str
    - get_key_bindings() -> dict
```

**Mapeamento:**
- SPACE → "next"
- BACKSPACE → "previous"
- D → "deep_dive"
- P → "ask_wanda"
- R → "repeat"
- M → "mute"
- ESC → "quit"

---

#### 2.5 animation_engine.py

**Responsabilidades:**
- Gerenciar animações
- Transições (fade, slide, zoom)
- Efeitos visuais

**Funcionalidades:**
```python
class AnimationEngine:
    - fade_in(surface, duration)
    - fade_out(surface, duration)
    - slide_in(surface, direction, duration)
    - typewriter_effect(text, speed)
```

---

### 3. Sistema de Slides (slides/)

#### 3.1 base_slide.py

**Classe abstrata base:**
```python
class BaseSlide(ABC):
    - __init__(title, narration)
    - render(screen, theme) [abstract]
    - animate(delta_time)
    - add_deep_dive(slide)
    - on_enter()
    - on_exit()
```

---

#### 3.2 title_slide.py

**Slide de título:**
- Título grande centralizado
- Subtítulo
- Animação fade in
- Gradiente de cores

---

#### 3.3 content_slide.py

**Slide de conteúdo:**
- Título
- Lista de itens (bullets)
- Animação item por item
- Ícones opcionais

---

#### 3.4 diagram_slide.py

**Slide com diagrama:**
- Título
- Diagrama ASCII ou imagem
- Animação de construção
- Legendas

---

#### 3.5 metrics_slide.py

**Slide de métricas:**
- Cards com números
- Animação de contagem
- Ícones
- Cores por categoria

---

### 4. Wanda AI (wanda_ai/)

#### 4.1 wanda_narrator.py

**Narração inteligente:**
```python
class WandaNarrator:
    - __init__(voice="nova", mode="online")
    - speak(text, wait=True)
    - _speak_online(text, wait)  # OpenAI TTS
    - _speak_offline(text, wait)  # pyttsx3
    - _configure_offline_voice()
```

**Configuração:**
- OpenAI TTS: model="tts-1-hd", voice="nova"
- pyttsx3: voz feminina em português, rate=150

---

#### 4.2 prompts/narrator_prompts.json

**Prompts para narração:**
```json
{
  "welcome": "Olá! Eu sou a Wanda...",
  "slide_transition": "Agora vamos ver...",
  "conclusion": "Isso conclui nossa apresentação..."
}
```

---

### 5. Utilitários (utils/)

#### 5.1 tts_manager.py

**Gerenciador de TTS:**
- Cache de áudios
- Conversão texto → áudio
- Gerenciamento de arquivos temporários

---

#### 5.2 audio_player.py

**Player de áudio:**
- Reprodução com pygame.mixer
- Controle de volume
- Fila de reprodução

---

#### 5.3 config.py

**Configurações:**
```python
class Config:
    SCREEN_WIDTH = 1920
    SCREEN_HEIGHT = 1080
    FPS = 60
    DEFAULT_THEME = "dark"
    TTS_MODE = "online"  # ou "offline"
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
```

---

### 6. Assets (assets/)

#### 6.1 themes/dark.json

```json
{
  "background": "#0a0e27",
  "primary": "#00d4ff",
  "secondary": "#7b2cbf",
  "accent": "#ff006e",
  "text": "#ffffff",
  "text_secondary": "#a0a0a0",
  "success": "#06ffa5",
  "warning": "#ffbe0b",
  "error": "#ff006e"
}
```

#### 6.2 themes/light.json

```json
{
  "background": "#f8f9fa",
  "primary": "#0066cc",
  "secondary": "#6c757d",
  "accent": "#dc3545",
  "text": "#212529",
  "text_secondary": "#6c757d",
  "success": "#28a745",
  "warning": "#ffc107",
  "error": "#dc3545"
}
```

---

### 7. V1 - Visão Geral (versoes/v1_visao_geral/)

#### 7.1 slides.py

**5 Slides:**

1. **Título**
   - "IntelliCare"
   - "Sistema de Saúde Inteligente com IA"

2. **O Problema**
   - Dados isolados em silos
   - Sem integração Hospital ↔ Governo
   - Processos manuais e lentos
   - Falta de visão 360° do paciente

3. **A Solução - Wanda**
   - Diagrama da arquitetura
   - Wanda como orquestrador
   - Integração multi-domínio

4. **Capacidades**
   - 13 ferramentas integradas
   - 5 sistemas conectados
   - 2.6s tempo médio de resposta
   - 100% taxa de sucesso

5. **Demonstração**
   - Query multi-domínio
   - Logs da Wanda raciocinando
   - Resultado integrado

---

#### 7.2 narration.json

```json
{
  "slide_1": "Olá! Eu sou a Wanda, e vou apresentar o IntelliCare...",
  "slide_2": "Hoje, os sistemas de saúde enfrentam grandes desafios...",
  "slide_3": "A Wanda é um orquestrador inteligente...",
  "slide_4": "A Wanda integra 13 ferramentas diferentes...",
  "slide_5": "Agora vou mostrar o raciocínio multi-domínio em ação..."
}
```

---

### 8. Arquivos Principais

#### 8.1 main.py

```python
#!/usr/bin/env python3
"""
IntelliCare - Apresentação Interativa com Wanda
"""

import argparse
from core.presentation_engine import PresentationEngine
from versoes.v1_visao_geral.slides import create_v1_slides

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--versao", default="v1_visao_geral")
    parser.add_argument("--tema", default="dark")
    parser.add_argument("--voz", default="online")
    args = parser.parse_args()
    
    engine = PresentationEngine(theme=args.tema, tts_mode=args.voz)
    
    # Carrega slides da versão
    if args.versao == "v1_visao_geral":
        slides = create_v1_slides()
        for slide in slides:
            engine.add_slide(slide)
    
    engine.run()

if __name__ == "__main__":
    main()
```

---

#### 8.2 requirements.txt

```txt
# Core
pygame>=2.5.0
python-dotenv>=1.0.0

# IA e TTS
openai>=1.0.0
pyttsx3>=2.90

# Utilitários
pillow>=10.0.0
```

---

#### 8.3 .env.example

```bash
# OpenAI Configuration
OPENAI_API_KEY=sk-your-api-key-here

# Presentation Settings
TTS_MODE=online  # online ou offline
DEFAULT_THEME=dark  # dark ou light
SCREEN_WIDTH=1920
SCREEN_HEIGHT=1080
```

---

#### 8.4 README.md

```markdown
# IntelliCare - Apresentação Interativa com Wanda

Apresentação Python interativa com IA narradora.

## Instalação

```bash
pip install -r requirements.txt
cp .env.example .env
# Edite .env com sua OPENAI_API_KEY
```

## Uso

```bash
# V1 - Visão Geral (online TTS)
python main.py --versao v1_visao_geral --voz online

# V1 - Visão Geral (offline TTS)
python main.py --versao v1_visao_geral --voz offline

# Tema claro
python main.py --tema light
```

## Controles

- **ESPAÇO**: Próximo slide
- **BACKSPACE**: Slide anterior
- **R**: Repetir narração
- **M**: Mute/Unmute
- **ESC**: Sair
```

---

## ✅ Checklist de Implementação

### Fase 1: Setup Inicial (Dia 1)
- [ ] Criar estrutura de diretórios
- [ ] Criar requirements.txt
- [ ] Criar .env.example
- [ ] Criar README.md
- [ ] Testar instalação de dependências

### Fase 2: Core Engine (Dias 2-3)
- [ ] Implementar PresentationEngine
- [ ] Implementar SlideManager
- [ ] Implementar InteractionHandler
- [ ] Implementar AnimationEngine
- [ ] Testar loop principal

### Fase 3: Sistema de Slides (Dia 4)
- [ ] Implementar BaseSlide
- [ ] Implementar TitleSlide
- [ ] Implementar ContentSlide
- [ ] Implementar DiagramSlide
- [ ] Implementar MetricsSlide

### Fase 4: Narração (Dia 5)
- [ ] Implementar Narrator
- [ ] Implementar WandaNarrator
- [ ] Configurar OpenAI TTS
- [ ] Configurar pyttsx3 (fallback)
- [ ] Testar narração online/offline

### Fase 5: V1 - Visão Geral (Dia 6)
- [ ] Criar 5 slides da V1
- [ ] Escrever narrações
- [ ] Testar apresentação completa
- [ ] Ajustar timings

### Fase 6: Polimento (Dia 7)
- [ ] Criar temas (dark/light)
- [ ] Adicionar avatar da Wanda
- [ ] Ajustar animações
- [ ] Testar todos os controles
- [ ] Documentar código

---

## 🎯 Critérios de Sucesso

### Funcional
- ✅ Apresentação inicia sem erros
- ✅ Wanda narra todos os 5 slides
- ✅ Navegação funciona (ESPAÇO, BACKSPACE)
- ✅ TTS online e offline funcionam
- ✅ Animações suaves (60 FPS)

### Qualidade
- ✅ Código modular e bem organizado
- ✅ Classes com responsabilidades claras
- ✅ Documentação inline (docstrings)
- ✅ Sem warnings ou erros

### Visual
- ✅ Tema dark implementado
- ✅ Transições suaves
- ✅ Texto legível
- ✅ Avatar da Wanda visível

---

## 📊 Métricas de Entrega

| Métrica | Meta |
|---------|------|
| **Arquivos Python** | ~15 arquivos |
| **Linhas de código** | ~1,500 linhas |
| **Classes** | ~10 classes |
| **Slides V1** | 5 slides |
| **Temas** | 2 (dark/light) |
| **Modos TTS** | 2 (online/offline) |

---

## 🚨 Pontos de Atenção

### Crítico
- ⚠️ **OpenAI API Key**: Necessária para TTS online
- ⚠️ **Pygame**: Testar em Windows (pode precisar ajustes)
- ⚠️ **pyttsx3**: Voz em português pode não estar disponível em todos os sistemas

### Importante
- 💡 **Performance**: Manter 60 FPS constante
- 💡 **Cache de áudio**: Evitar gerar mesmo áudio múltiplas vezes
- 💡 **Tratamento de erros**: Fallback para offline se API falhar

---

## 🔗 Dependências da Tarefa Dev 2

**Dev 2 depende de:**
- ✅ Estrutura de diretórios criada
- ✅ BaseSlide implementado
- ✅ PresentationEngine funcionando
- ✅ Sistema de temas (JSON)

**Dev 2 NÃO depende de:**
- ❌ V1 completa
- ❌ Narração funcionando
- ❌ Animações polidas

**Ponto de integração:** Após Fase 3 (Sistema de Slides), Dev 2 pode começar.

---

## 📝 Notas de Implementação

### OpenAI TTS
```python
from openai import OpenAI
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

response = client.audio.speech.create(
    model="tts-1-hd",
    voice="nova",  # Voz feminina natural
    input="Olá! Eu sou a Wanda."
)
response.stream_to_file("wanda_voice.mp3")
```

### pyttsx3 (Offline)
```python
import pyttsx3
engine = pyttsx3.init()
engine.setProperty('rate', 150)
engine.setProperty('volume', 0.9)
engine.say("Olá! Eu sou a Wanda.")
engine.runAndWait()
```

### Pygame Loop
```python
clock = pygame.time.Clock()
while running:
    for event in pygame.event.get():
        # Handle events

    # Update
    # Render

    pygame.display.flip()
    clock.tick(60)  # 60 FPS
```

---

## 🎉 Entrega Final

**Ao final desta tarefa, teremos:**

✅ **Apresentação MVP funcionando**
- 5 slides da V1 (Visão Geral)
- Wanda narrando com voz natural
- Navegação básica (próximo/anterior)
- Tema dark implementado
- TTS online e offline

✅ **Fundação sólida para Dev 2**
- Arquitetura modular
- Sistema de slides extensível
- Engine de apresentação robusto
- Documentação completa

✅ **Pronto para demonstração**
- Apresentação pode ser mostrada a stakeholders
- Conceito validado
- Base para expansão (V2, V3)

---

**Responsável:** Dev 1 (Augment Agent)
**Prazo:** 7 dias
**Início:** Aguardando aprovação
**Status:** 📋 Pronto para começar

---

**Próximo passo:** Aguardando sinal verde para iniciar implementação! 🚀


