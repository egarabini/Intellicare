from jinja2 import Environment, PackageLoader
from datetime import datetime

# Configurar o Jinja2 para a pasta templates do pacote intellicare_core
jinja_env = Environment(
    loader=PackageLoader("intellicare_core", "pdf/templates")
)

def render_pdf(template_name: str, context: dict) -> bytes:
    """
    Renderiza um template HTML com Jinja2 e retorna os bytes do PDF gerado pelo WeasyPrint
    """
    try:
        from weasyprint import HTML
    except (ImportError, OSError) as e:
        raise RuntimeError(
            "weasyprint não disponível. Instale as dependências de sistema: "
            "libpango, libcairo, libgdk-pixbuf"
        ) from e
    context.setdefault("generated_at", datetime.now().strftime("%d/%m/%Y %H:%M"))
    template = jinja_env.get_template(template_name)
    html_str = template.render(**context)
    return HTML(string=html_str).write_pdf()
