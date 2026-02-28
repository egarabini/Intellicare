# 📦 Guia de Instalação - Apresentação IntelliCare

## Pré-requisitos

- Python 3.8 ou superior
- pip (gerenciador de pacotes Python)

## Instalação

### 1. Instalar Dependências

```bash
cd apresentacao
pip install -r requirements.txt
```

### 2. Configurar Variáveis de Ambiente (Opcional)

Para usar TTS online (OpenAI):

```bash
# Copiar arquivo de exemplo
cp .env.example .env

# Editar .env e adicionar sua OPENAI_API_KEY
# OPENAI_API_KEY=sk-your-api-key-here
```

### 3. Testar Instalação

```bash
python test_presentation.py
```

Você deve ver:
```
🎉 TODOS OS TESTES PASSARAM!
```

## Executar Apresentação

### Modo Offline (sem OpenAI API)

```bash
python main.py --voz offline
```

### Modo Online (com OpenAI TTS)

```bash
python main.py --voz online
```

**Nota:** Modo online requer `OPENAI_API_KEY` configurada no `.env`

## Controles

Durante a apresentação:

- **ESPAÇO**: Próximo slide
- **BACKSPACE**: Slide anterior
- **R**: Repetir narração
- **M**: Mute/Unmute
- **ESC**: Sair

## Troubleshooting

### Erro: "No module named 'pygame'"

```bash
pip install pygame
```

### Erro: "No module named 'pyttsx3'"

```bash
pip install pyttsx3
```

### Erro: "No module named 'openai'"

```bash
pip install openai
```

### TTS offline não funciona

No Windows, pyttsx3 usa SAPI5. Certifique-se de ter vozes instaladas:
- Painel de Controle → Fala → Vozes

### TTS online não funciona

Verifique:
1. `OPENAI_API_KEY` está configurada no `.env`
2. Chave API é válida
3. Tem créditos na conta OpenAI

## Estrutura de Arquivos

```
apresentacao/
├── main.py                 # Launcher principal
├── test_presentation.py    # Script de testes
├── requirements.txt        # Dependências
├── .env.example           # Exemplo de configuração
├── README.md              # Documentação
├── INSTALL.md             # Este arquivo
├── core/                  # Engine principal
├── slides/                # Biblioteca de slides
├── versoes/               # Versões da apresentação
│   └── v1_visao_geral/   # V1 - 5 slides
├── assets/                # Recursos
│   └── themes/           # Temas (dark.json, light.json)
└── utils/                 # Utilitários
```

## Próximos Passos

Após instalação bem-sucedida:

1. Execute o teste: `python test_presentation.py`
2. Execute a apresentação: `python main.py --voz offline`
3. Explore os controles durante a apresentação
4. Experimente o tema claro: `python main.py --tema light`

## Suporte

Para problemas ou dúvidas, consulte:
- README.md
- Documentação do projeto IntelliCare

