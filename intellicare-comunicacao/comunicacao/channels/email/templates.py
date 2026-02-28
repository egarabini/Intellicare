from jinja2 import Environment, FileSystemLoader, select_autoescape, DictLoader
import os
from typing import Dict, Any

# Default templates to ensure the system works even without files
DEFAULT_TEMPLATES = {
    "alert_notification": """
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
            .container { max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid #ddd; border-radius: 5px; }
            .header { background-color: #f8f9fa; padding: 10px; text-align: center; border-bottom: 1px solid #ddd; }
            .alert-box { background-color: #ffebee; border: 1px solid #ef9a9a; color: #c62828; padding: 15px; margin: 20px 0; border-radius: 4px; }
            .footer { margin-top: 20px; font-size: 12px; color: #777; text-align: center; }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h2>IntelliCare Alert System</h2>
            </div>
            
            <p>Hello {{ recipient_name }},</p>
            
            <p>An alert has been triggered for your attention:</p>
            
            <div class="alert-box">
                <strong>Severity:</strong> {{ severity|upper }}<br>
                <strong>Message:</strong> {{ message }}
            </div>
            
            <p>Please log in to the portal to review the details.</p>
            
            <p>Best regards,<br>The IntelliCare Team</p>
            
            <div class="footer">
                <p>This is an automated message. Please do not reply.</p>
            </div>
        </div>
    </body>
    </html>
    """,
    "welcome_email": """
    <!DOCTYPE html>
    <html>
    <body>
        <h2>Welcome to IntelliCare!</h2>
        <p>Hello {{ recipient_name }},</p>
        <p>We are glad to have you on board.</p>
    </body>
    </html>
    """
}

class EmailTemplateEngine:
    def __init__(self, templates_dir: str = None):
        self.loader = DictLoader(DEFAULT_TEMPLATES)
        
        # If directory exists, use it as primary loader
        if templates_dir and os.path.exists(templates_dir):
            self.file_loader = FileSystemLoader(templates_dir)
            # Chain loaders? For simplicity, we'll implement a fallback manually or just use DictLoader for now if fs fails
            # In a robust system we'd use ChoiceLoader([FileSystemLoader(path), DictLoader(defaults)])
            from jinja2 import ChoiceLoader
            self.loader = ChoiceLoader([self.file_loader, self.loader])
            
        self.env = Environment(
            loader=self.loader,
            autoescape=select_autoescape(['html', 'xml'])
        )
    
    def render(self, template_name: str, context: Dict[str, Any]) -> str:
        """Renders a template with the given context."""
        try:
            template = self.env.get_template(template_name)
            return template.render(**context)
        except Exception as e:
            # Fallback to simple text if template fails
            return f"Error rendering template {template_name}: {str(e)}"
