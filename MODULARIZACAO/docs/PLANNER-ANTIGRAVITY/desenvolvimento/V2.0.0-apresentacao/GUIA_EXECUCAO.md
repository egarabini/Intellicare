# Guia de Execução — V2.0.0 Apresentação para Palestra

**Objetivo:** Executar a apresentação interativa para palestra.

---

## Pré-requisitos

- Python 3.11+
- Dependências: `pip install -r intellicare-apresentacao/apresentacao/requirements.txt`
- Pygame instalado (incluído no requirements)

---

## Comando

```bash
cd intellicare-apresentacao/apresentacao
python main.py --versao v2_0_0_palestra --tema dark --voz offline
```

### Parâmetros

| Parâmetro | Valores | Default | Descrição |
|-----------|---------|---------|-----------|
| `--versao` | v2_0_0_palestra | v1_visao_geral | Versão da apresentação |
| `--tema` | dark, light | dark | Tema visual |
| `--voz` | online, offline | offline | TTS: online=OpenAI, offline=pyttsx3 |
| `--width` | número | 1920 | Largura da janela |
| `--height` | número | 1080 | Altura da janela |

---

## Controles Durante a Apresentação

| Tecla | Ação |
|-------|------|
| **Espaço** ou **Clique** | Próximo slide |
| **Backspace** | Slide anterior |
| **D** | **Deep Dive** — abre overlay com detalhamento |
| **R** | Repetir narração |
| **M** | Mute (silenciar TTS) |
| **ESC** | Sair |

---

## Estrutura da Apresentação

1. **Título** — IntelliCare: Uma Visão Além do Tempo
2. **O que temos hoje** — 7 agentes, LEGO, demo
3. **Multi-Tenancy** — 2 camadas, isolamento
4. **Novos Módulos** — admin, gestor
5. **Roadmap Paralelo** — T1 a T5
6. **Demo Investidores** — Pierre, Minerva, Portal
7. **TenantContext** — F0, fundação
8. **Stack e Arquitetura** — diagrama
9. **Mercado e Oportunidade** — SaaS
10. **Fechamento** — próximos passos

Em cada slide: pressione **D** para ver o detalhamento completo.

---

## Troubleshooting

- **Janela não abre:** Verifique se Pygame está instalado e se há display disponível (X11/Wayland no Linux)
- **Narração não funciona (offline):** pyttsx3 pode precisar de pacotes de voz no sistema
- **Narração online:** Requer chave API OpenAI configurada para TTS
