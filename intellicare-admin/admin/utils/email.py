import logging

logger = logging.getLogger(__name__)

async def send_welcome_email(tenant_nome: str, gestor_email: str):
    logger.info(f"Mocking email envio para {gestor_email} do tenant {tenant_nome}")
    # Simulação de envio de email. 
    # Em produção, usaria aiosmtplib e um provedor como SendGrid/AWS SES.

async def send_credentials_email(tenant_nome: str, gestor_email: str, password: str):
    logger.info(f"Mocking email de credenciais para {gestor_email}")
    pass
