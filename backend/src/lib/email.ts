import nodemailer from 'nodemailer';

const transporter = nodemailer.createTransport({
  host: process.env.SMTP_HOST,
  port: parseInt(process.env.SMTP_PORT || '587'),
  secure: process.env.SMTP_SECURE === 'true',
  auth: {
    user: process.env.SMTP_USER,
    pass: process.env.SMTP_PASS,
  },
});

export interface EmailData {
  to: string;
  subject: string;
  html: string;
  text?: string;
}

export async function sendEmail(data: EmailData): Promise<void> {
  await transporter.sendMail({
    from: process.env.SMTP_FROM || 'IntelliCare <noreply@intellicare.com.br>',
    to: data.to,
    subject: data.subject,
    html: data.html,
    text: data.text,
  });
}

export function generateToken(): string {
  return Math.floor(10000 + Math.random() * 90000).toString();
}

export function getVerificationEmailTemplate(token: string, protocol: string): string {
  return `
    <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
      <h2 style="color: #2563eb;">IntelliCare - Validação de Email</h2>
      <p>Olá,</p>
      <p>Recebemos sua solicitação no IntelliCare. Para confirmar seu email e prosseguir, utilize o código abaixo:</p>
      <div style="background: #f3f4f6; padding: 20px; text-align: center; margin: 20px 0; border-radius: 8px;">
        <span style="font-size: 32px; font-weight: bold; letter-spacing: 8px; color: #1f2937;">${token}</span>
      </div>
      <p style="color: #6b7280; font-size: 14px;">Este código expira em 30 minutos.</p>
      <p style="color: #6b7280; font-size: 14px;">Protocolo: <strong>${protocol}</strong></p>
      <hr style="border: none; border-top: 1px solid #e5e7eb; margin: 20px 0;">
      <p style="color: #9ca3af; font-size: 12px;">
        Se você não solicitou isso, ignore este email.<br>
        IntelliCare - Portal de Agentes Inteligentes em Saúde
      </p>
    </div>
  `;
}

export function getStatusUpdateEmailTemplate(protocol: string, status: string, message: string): string {
  const statusColors: Record<string, string> = {
    'PENDING': '#f59e0b',
    'EMAIL_VERIFIED': '#3b82f6',
    'IN_ANALYSIS': '#8b5cf6',
    'APPROVED': '#10b981',
    'REJECTED': '#ef4444',
    'COMPLETED': '#059669',
  };

  return `
    <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
      <h2 style="color: #2563eb;">IntelliCare - Atualização de Status</h2>
      <p>Olá,</p>
      <p>Sua solicitação teve uma atualização de status:</p>
      <div style="background: #f3f4f6; padding: 20px; margin: 20px 0; border-radius: 8px;">
        <p><strong>Protocolo:</strong> ${protocol}</p>
        <p><strong>Novo Status:</strong> <span style="color: ${statusColors[status] || '#6b7280'}; font-weight: bold;">${status}</span></p>
        <p><strong>Mensagem:</strong> ${message}</p>
      </div>
      <p>Você pode acompanhar o andamento acessando:</p>
      <a href="${process.env.FRONTEND_URL}/acompanhamento/${protocol}" 
         style="background: #2563eb; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px; display: inline-block;">
        Acompanhar Solicitação
      </a>
      <hr style="border: none; border-top: 1px solid #e5e7eb; margin: 20px 0;">
      <p style="color: #9ca3af; font-size: 12px;">
        IntelliCare - Portal de Agentes Inteligentes em Saúde
      </p>
    </div>
  `;
}
