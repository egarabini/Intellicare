# 10. Modelo de Legendas e Anonimizacao

Use este arquivo como modelo pronto para cada print do manual.

## 10.1 Template de legenda (copiar e preencher)

```text
Titulo da tela:
Objetivo da tela:
Perfil:
Quando usar:
Passos:
1)
2)
3)
Resultado esperado:
Erros comuns:
```

## 10.2 Exemplo preenchido (Gestor - Nova Jornada)

```text
Titulo da tela: Nova Jornada CarePlanner
Objetivo da tela: Disparar comunicacao de cuidado para um paciente por canal especifico.
Perfil: Gestor
Quando usar: Follow-up de adesao, monitoramento ou check-in.
Passos:
1) Informar referencia do paciente.
2) Escolher tipo de jornada e canal.
3) Informar telefone (WhatsApp/SMS) ou e-mail.
4) Selecionar template e confirmar em "Iniciar Jornada".
Resultado esperado: Jornada criada com execution_id e status inicial no painel.
Erros comuns: Contato em formato invalido; canal sem credencial ativa; template incompativel com canal.
```

## 10.3 Checklist de anonimização antes de publicar imagens

- [ ] Nome completo de paciente removido ou mascarado.
- [ ] CPF, CNS, telefone, e-mail pessoal mascarados.
- [ ] ID interno/UUID sensivel mascarado quando nao for didatico.
- [ ] Dados clinicos sensiveis substituidos por dados ficticios.
- [ ] Nenhum token, segredo, URL privada ou host interno visivel.
- [ ] Horarios e datas reais sensiveis, quando necessario, substituidos.

## 10.4 Padrao de mascara recomendado

- Nome: `Paciente Exemplo A`
- E-mail: `paciente.exemplo@demo.local`
- Telefone: `+55 11 99999-0000`
- Documento: `***.***.***-**`
- UUID: `xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx`

## 10.5 Classificacao das imagens para distribuicao

- `INTERNO` - pode conter dados operacionais nao sensiveis.
- `TREINAMENTO` - dados totalmente ficticios, apto para uso amplo.
- `PUBLICO` - apto para apresentacao externa (sem dados reais, sem infraestrutura interna).

## 10.6 Modelo de aprovacao final (por lote de prints)

```text
Lote:
Responsavel captura:
Responsavel revisao:
Data:
Status: Aprovado / Ajustar
Pendencias:
- 
- 
```
