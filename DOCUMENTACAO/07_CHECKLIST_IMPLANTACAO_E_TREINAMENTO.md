# 7. Checklist de Implantacao e Treinamento

## 7.1 Preparacao por perfil

## Admin

- [ ] Criar/validar tenant.
- [ ] Validar gestor responsavel e e-mail.
- [ ] Revisar painel de servicos, modulos e auditoria.

## Gestor

- [ ] Validar unidades e equipe.
- [ ] Validar agenda e perfis de usuarios.
- [ ] Executar disparo de teste no CarePlanner.

## Clinico

- [ ] Abrir e fechar encontro de teste.
- [ ] Salvar nota Florence em `FREE` e em `SOAP`.
- [ ] Criar prescricao com CID-10 via Oswaldo.
- [ ] Exportar PDF clinico.

## Paciente

- [ ] Login e acesso ao painel.
- [ ] Visualizar jornada recebida.
- [ ] Visualizar historico clinico compartilhado.

## 7.2 Roteiro de treinamento (90 minutos)

- `15 min` - visao geral da plataforma e perfis.
- `20 min` - operacao do Gestor (dashboard, jornada, filtros).
- `25 min` - fluxo Clinico (agenda -> encontro -> Florence -> Oswaldo -> PDF).
- `15 min` - experiencia do Paciente.
- `15 min` - perguntas, erros comuns e plano de contingencia.

## 7.3 Erros comuns e correcao rapida

- Contato em formato invalido (telefone/e-mail): corrigir cadastro e reenviar.
- Jornada sem resposta: revisar canal, template e horario.
- Nota incompleta: reforcar checklist SOAP antes de fechar encontro.
- Divergencia de indicador: confirmar periodo/filtro aplicado na tela.

## 7.4 Indicadores minimos para go-live

- [ ] Acesso e autenticacao funcionando nos 4 perfis.
- [ ] Fluxo completo paciente -> agenda -> atendimento -> historico validado.
- [ ] Pelo menos 1 jornada enviada e respondida em canal alvo.
- [ ] Exportacao PDF operacional (admin e clinico).
- [ ] Equipe treinada nos fluxos principais.
