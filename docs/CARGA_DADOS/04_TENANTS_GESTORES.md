# Tenants, Gestores e Profissionais

## Tenants (Keycloak)

| tenant_id | Descrição | Organizações |
|-----------|-----------|--------------|
| `secretaria-brasilia` | SES-DF | org-ses-df, org-ubs-asa-sul |
| `secretaria-montesclaros` | SMS Montes Claros | org-sms-montesclaros, org-ubs-mc-centro |
| `hospital-brasilia` | Hospitais DF | org-hran, org-hbdf |
| `hospital-montesclaros` | Santa Casa MC | org-santacasa-mc |

## Gestores (TENANT_GESTOR)

| Username | Tenant | Nome |
|----------|--------|------|
| gestor.sesdf@saude.df.gov.br | secretaria-brasilia | Roberto Almeida |
| gestor.sms@montesclaros.mg.gov.br | secretaria-montesclaros | Carla Mendes |
| gestor.hran@saude.df.gov.br | hospital-brasilia | Dr. Paulo Henrique Costa |
| gestor.santacasa@santacasa-mc.org.br | hospital-montesclaros | Dra. Mariana Souza |

## Unidades (Location) por tenant

| Tenant | Unidades |
|--------|----------|
| secretaria-brasilia | Sede SES-DF, UBS Asa Sul |
| secretaria-montesclaros | Sede SMS, UBS Centro MC |
| hospital-brasilia | HRAN, HBDF |
| hospital-montesclaros | Santa Casa MC |

## Profissionais por unidade

| Profissional | Org | Location | Tenant | Role |
|--------------|-----|----------|--------|------|
| Dr. Carlos Eduardo Silva | org-hran | loc-hran | hospital-brasilia | MEDICO |
| Dra. Ana Paula Santos | org-hran | loc-hran | hospital-brasilia | MEDICO |
| Dr. Roberto Mendes | org-hbdf | loc-hbdf | hospital-brasilia | MEDICO |
| Dra. Fernanda Oliveira | org-hbdf | loc-hbdf | hospital-brasilia | MEDICO |
| Enf. Maria do Carmo | org-ubs-asa-sul | loc-ubs-asa-sul | secretaria-brasilia | ENFERMEIRO |
| Dr. João Pedro Costa | org-santacasa-mc | loc-santacasa-mc | hospital-montesclaros | MEDICO |
| Dra. Luciana Ferreira | org-santacasa-mc | loc-santacasa-mc | hospital-montesclaros | MEDICO |
| Enf. Paulo Henrique | org-ubs-mc-centro | loc-ubs-mc-centro | secretaria-montesclaros | ENFERMEIRO |
| Dr. André Luiz Souza | org-hran | loc-hran | hospital-brasilia | MEDICO |
| Dra. Beatriz Lima | org-santacasa-mc | loc-santacasa-mc | hospital-montesclaros | MEDICO |
