# CONFIGURAÇÃO DE TEMPLATES DE EMAIL

## 📧 Gmail: INTELLICARE - Comunicação

**Responsável**: DEV1  
**Data de configuração**: 24/02/2026  
**Versão**: 1.0

---

## 1. CONFIGURAÇÃO DO GMAIL

### Criar Templates (Respostas Prontas):
1. Acessar Gmail (https://mail.google.com)
2. Clicar em ⚙️ Configurações → Ver todas as configurações
3. Aba "Avançado"
4. Ativar "Modelos" (Templates)
5. Salvar alterações

---

## 2. TEMPLATES DE EMAIL

### Template 1: Convite de Reunião

**Nome**: `CONVITE_REUNIAO`

```
Assunto: Convite: [TIPO] - [TÍTULO] - [DATA]

Prezado(a) [NOME],

Gostaria de convidá-lo(a) para participar de uma [TIPO DE REUNIÃO] sobre [TEMA].

📅 DATA E HORÁRIO
Data: [DD/MM/YYYY]
Horário: [HH:MM] - [HH:MM] ([DURAÇÃO] minutos)
Local: Google Meet (link abaixo)

🎯 OBJETIVO
[Descrição do objetivo da reunião]

📋 AGENDA
[HH:MM] - [Tópico 1]
[HH:MM] - [Tópico 2]
[HH:MM] - [Tópico 3]

📎 MATERIAIS PRÉVIOS
[Links para documentação]

✅ PREPARAÇÃO NECESSÁRIA
- [Item 1]
- [Item 2]

🔗 LINK DA REUNIÃO
[Link do Google Meet]

Por favor, confirme sua participação respondendo este email.

Atenciosamente,
DEV1
Projeto INTELLICARE
```

---

### Template 2: Distribuição de Ata

**Nome**: `DISTRIBUICAO_ATA`

```
Assunto: Ata: [TIPO] - [TÍTULO] - [DATA]

Prezados(as),

Segue a ata da reunião realizada em [DATA].

📊 RESUMO EXECUTIVO
[Resumo em 2-3 linhas]

✅ PRINCIPAIS DECISÕES
1. [Decisão 1]
2. [Decisão 2]
3. [Decisão 3]

📌 ACTION ITEMS
[RESPONSÁVEL] - [TAREFA] - Prazo: [DATA]
[RESPONSÁVEL] - [TAREFA] - Prazo: [DATA]

📎 DOCUMENTOS
- Ata completa: [Link]
- Materiais apresentados: [Link]
- Gravação (se aplicável): [Link]

🔜 PRÓXIMOS PASSOS
[Descrição dos próximos passos]

Para dúvidas ou comentários, por favor responda este email.

Atenciosamente,
DEV1
Projeto INTELLICARE
```

---

### Template 3: Convite de Validação

**Nome**: `CONVITE_VALIDACAO`

```
Assunto: Convite para Validação: [MÓDULO] - [FUNCIONALIDADE]

Prezado(a) [NOME],

Como especialista em [ÁREA], gostaríamos de contar com sua participação na validação de [FUNCIONALIDADE] do módulo [MÓDULO] do projeto INTELLICARE.

📅 DATA E HORÁRIO
Data: [DD/MM/YYYY]
Horário: [HH:MM] - [HH:MM] (2 horas)
Local: Google Meet (link abaixo)

🎯 OBJETIVO DA VALIDAÇÃO
Validar se [FUNCIONALIDADE] atende aos requisitos de [ÁREA/NORMA].

📋 AGENDA
10:00 - Abertura e contexto (5 min)
10:05 - Demonstração do sistema (30 min)
10:35 - Testes práticos (45 min)
11:20 - Discussão e feedback (30 min)
11:50 - Próximos passos (10 min)

📎 DOCUMENTAÇÃO PRÉVIA
Por favor, revise antes da reunião:
- Especificação funcional: [Link]
- Especificação técnica: [Link]
- Casos de teste: [Link]

✅ PREPARAÇÃO
- Ler documentação prévia (30 min)
- Preparar perguntas e cenários de teste
- Ter em mãos checklist de conformidade (se aplicável)

🔗 LINK DA REUNIÃO
[Link do Google Meet]

📝 FORMULÁRIO DE FEEDBACK
Após a validação, solicitamos o preenchimento do formulário:
[Link do formulário]

Sua expertise é fundamental para garantir a qualidade do sistema!

Atenciosamente,
DEV1
Projeto INTELLICARE
```

---

### Template 4: Solicitação de Feedback

**Nome**: `SOLICITACAO_FEEDBACK`

```
Assunto: Feedback: [ATIVIDADE] - [DATA]

Prezado(a) [NOME],

Agradecemos sua participação em [ATIVIDADE] realizada em [DATA].

Para melhorarmos continuamente nossos processos, gostaríamos de receber seu feedback.

📝 FORMULÁRIO DE FEEDBACK
Por favor, preencha o formulário (5 minutos):
[Link do formulário]

🎯 TÓPICOS AVALIADOS
- Organização e clareza
- Qualidade dos materiais
- Alcance dos objetivos
- Sugestões de melhoria

⏰ PRAZO
Solicitamos o preenchimento até [DATA] para consolidarmos os resultados.

Seu feedback é muito importante para nós!

Atenciosamente,
DEV1
Projeto INTELLICARE
```

---

### Template 5: Relatório Mensal

**Nome**: `RELATORIO_MENSAL`

```
Assunto: Relatório Mensal de Comunicação - [MÊS/ANO]

Prezados(as),

Segue o relatório mensal de atividades de comunicação do projeto INTELLICARE.

📊 RESUMO DO MÊS
Período: [MÊS/ANO]

📈 MÉTRICAS PRINCIPAIS
- Reuniões realizadas: [N]
- Validações concluídas: [N]
- Taxa de participação: [X]%
- Satisfação média: [X]/5
- Action items completados: [X]%

✅ DESTAQUES
1. [Destaque 1]
2. [Destaque 2]
3. [Destaque 3]

📌 VALIDAÇÕES REALIZADAS
- [Módulo] - [Funcionalidade] - Status: [Aprovado/Reprovado]
- [Módulo] - [Funcionalidade] - Status: [Aprovado/Reprovado]

🔜 PRÓXIMAS ATIVIDADES
- [Data] - [Atividade]
- [Data] - [Atividade]

📎 DOCUMENTOS
- Dashboard completo: [Link]
- Relatório detalhado: [Link]
- Atas do mês: [Link]

Para mais informações, consulte a documentação ou entre em contato.

Atenciosamente,
DEV1
Projeto INTELLICARE
```

---

## 3. ASSINATURAS DE EMAIL

### Assinatura Padrão DEV1:

```
---
DEV1
Gerente de Comunicação e Documentação
Projeto INTELLICARE

📧 dev1@intellicare.com
📅 Agendar reunião: [Link Calendly]
📁 Documentação: [Link Google Drive]
```

---

## 4. INTEGRAÇÃO COM SCRIPTS

### Envio Automático via Python:

```python
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

def enviar_email(
    destinatarios: list,
    assunto: str,
    corpo_html: str,
    anexos: list = None
):
    """
    Envia email via Gmail SMTP
    
    Nota: Requer senha de aplicativo do Gmail
    """
    # Configuração SMTP
    smtp_server = "smtp.gmail.com"
    smtp_port = 587
    sender_email = "dev1@intellicare.com"
    sender_password = "senha_aplicativo"  # Usar variável de ambiente
    
    # Criar mensagem
    msg = MIMEMultipart('alternative')
    msg['Subject'] = assunto
    msg['From'] = sender_email
    msg['To'] = ', '.join(destinatarios)
    
    # Corpo HTML
    html_part = MIMEText(corpo_html, 'html')
    msg.attach(html_part)
    
    # Anexos (se houver)
    if anexos:
        for arquivo in anexos:
            # Adicionar anexo
            pass
    
    # Enviar
    with smtplib.SMTP(smtp_server, smtp_port) as server:
        server.starttls()
        server.login(sender_email, sender_password)
        server.send_message(msg)
    
    return True
```

---

## 5. BOAS PRÁTICAS

### Ao Enviar Email:
- ✅ Usar assunto claro e descritivo
- ✅ Incluir data no assunto (para reuniões)
- ✅ Usar formatação para facilitar leitura
- ✅ Incluir todos os links necessários
- ✅ Revisar antes de enviar
- ✅ Usar CC com moderação
- ✅ Responder em até 4 horas (meta)

### Ao Responder:
- ✅ Responder em até 24 horas
- ✅ Ser claro e objetivo
- ✅ Incluir contexto se necessário
- ✅ Usar "Responder a todos" quando apropriado

### Ao Usar Templates:
- ✅ Personalizar campos [VARIÁVEIS]
- ✅ Revisar todo o conteúdo
- ✅ Adaptar tom ao público
- ✅ Verificar links antes de enviar

---

**Configurado por**: DEV1  
**Data**: 24/02/2026  
**Status**: ✅ Templates criados e configurados

