#!/usr/bin/env python3
"""
Script: Gerador de Ata de Reunião
Autor: DEV1
Data: 21/02/2026
Descrição: Gera ata de reunião a partir de template e dados estruturados
"""

from datetime import datetime
from typing import List, Dict, Optional
import json
import os


class GeradorAta:
    """Gerador de atas de reunião padronizadas"""
    
    def __init__(self, template_path: str = None):
        """
        Inicializa o gerador de ata
        
        Args:
            template_path: Caminho para o template de ata
        """
        self.template_path = template_path or self._get_default_template_path()
        
    def _get_default_template_path(self) -> str:
        """Retorna caminho padrão do template"""
        base_path = os.path.dirname(os.path.dirname(__file__))
        return os.path.join(
            base_path,
            "comunicacao",
            "reunioes",
            "templates",
            "TEMPLATE_ATA_REUNIAO.md"
        )
    
    def gerar_ata(
        self,
        data: str,
        horario_inicio: str,
        horario_fim: str,
        facilitador: str,
        participantes_presentes: List[Dict[str, str]],
        participantes_ausentes: List[Dict[str, str]],
        resumo_executivo: str,
        objetivos: List[Dict[str, bool]],
        topicos: List[Dict],
        action_items: List[Dict],
        proximos_passos: List[str],
        proxima_reuniao: Optional[Dict] = None,
        anexos: Optional[List[str]] = None,
        observacoes: Optional[str] = None
    ) -> str:
        """
        Gera ata de reunião formatada
        
        Args:
            data: Data da reunião (DD/MM/YYYY)
            horario_inicio: Horário de início (HH:MM)
            horario_fim: Horário de término (HH:MM)
            facilitador: Nome do facilitador
            participantes_presentes: Lista de participantes presentes
            participantes_ausentes: Lista de participantes ausentes
            resumo_executivo: Resumo executivo da reunião
            objetivos: Lista de objetivos e status
            topicos: Lista de tópicos discutidos
            action_items: Lista de action items
            proximos_passos: Lista de próximos passos
            proxima_reuniao: Dados da próxima reunião (opcional)
            anexos: Lista de links para anexos (opcional)
            observacoes: Observações adicionais (opcional)
        
        Returns:
            Ata formatada em Markdown
        """
        # Calcular duração
        h_inicio = datetime.strptime(horario_inicio, "%H:%M")
        h_fim = datetime.strptime(horario_fim, "%H:%M")
        duracao = int((h_fim - h_inicio).total_seconds() / 60)
        
        # Montar ata
        ata = f"""# ATA DE REUNIÃO

## 📋 Informações
- **Data**: {data}
- **Horário**: {horario_inicio} - {horario_fim}
- **Duração real**: {duracao} minutos
- **Facilitador**: {facilitador}
- **Participantes presentes**: 
"""
        
        # Adicionar participantes presentes
        for p in participantes_presentes:
            ata += f"  - ✅ {p['nome']} - {p['cargo']}\n"
        
        # Adicionar participantes ausentes
        if participantes_ausentes:
            ata += "- **Ausentes**: \n"
            for p in participantes_ausentes:
                motivo = p.get('motivo', 'Não informado')
                ata += f"  - ❌ {p['nome']} - {motivo}\n"
        
        # Resumo executivo
        ata += f"\n## 📊 Resumo Executivo\n{resumo_executivo}\n"
        
        # Objetivos alcançados
        ata += "\n## 🎯 Objetivos Alcançados\n"
        for obj in objetivos:
            status = "[x]" if obj['alcancado'] else "[ ]"
            descricao = obj['descricao']
            observacao = f" - {obj['observacao']}" if 'observacao' in obj else ""
            ata += f"- {status} {descricao}{observacao}\n"
        
        # Discussões principais
        ata += "\n## 💬 Discussões Principais\n\n"
        for topico in topicos:
            ata += f"### Tópico: {topico['nome']}\n"
            ata += "**Discussão**:\n"
            for ponto in topico['discussao']:
                ata += f"- {ponto}\n"
            
            if 'decisoes' in topico and topico['decisoes']:
                ata += "\n**Decisões**:\n"
                for decisao in topico['decisoes']:
                    ata += f"- ✅ {decisao}\n"
            
            if 'pendencias' in topico and topico['pendencias']:
                ata += "\n**Pendências**:\n"
                for pendencia in topico['pendencias']:
                    ata += f"- ⏳ {pendencia}\n"
            
            ata += "\n---\n\n"
        
        # Action items
        ata += "## ✅ Action Items\n\n"
        ata += "| ID | Ação | Responsável | Prazo | Prioridade | Status |\n"
        ata += "|----|------|-------------|-------|------------|--------|\n"
        for ai in action_items:
            prioridade_emoji = {
                'alta': '🔴 Alta',
                'media': '🟡 Média',
                'baixa': '🟢 Baixa'
            }.get(ai.get('prioridade', 'media'), '🟡 Média')
            
            ata += f"| {ai['id']} | {ai['acao']} | {ai['responsavel']} | "
            ata += f"{ai['prazo']} | {prioridade_emoji} | ⏳ Pendente |\n"
        
        # Próximos passos
        ata += "\n## 📅 Próximos Passos\n"
        for i, passo in enumerate(proximos_passos, 1):
            ata += f"{i}. {passo}\n"
        
        # Próxima reunião
        if proxima_reuniao:
            ata += "\n## 📌 Próxima Reunião\n"
            ata += f"- **Data**: {proxima_reuniao['data']}\n"
            ata += f"- **Horário**: {proxima_reuniao['horario']}\n"
            ata += f"- **Objetivo**: {proxima_reuniao['objetivo']}\n"
        
        # Anexos
        if anexos:
            ata += "\n## 📎 Anexos\n"
            for anexo in anexos:
                ata += f"- {anexo}\n"
        
        # Observações
        if observacoes:
            ata += f"\n## 📝 Observações Adicionais\n{observacoes}\n"
        
        # Rodapé
        data_elaboracao = datetime.now().strftime("%d/%m/%Y")
        ata += f"\n---\n\n**Elaborado por**: {facilitador}  \n"
        ata += f"**Data de elaboração**: {data_elaboracao}  \n"
        
        return ata
    
    def salvar_ata(self, ata: str, data: str, nome_reuniao: str) -> str:
        """
        Salva ata em arquivo
        
        Args:
            ata: Conteúdo da ata
            data: Data da reunião (DD/MM/YYYY)
            nome_reuniao: Nome da reunião
        
        Returns:
            Caminho do arquivo salvo
        """
        # Converter data para formato de arquivo
        data_obj = datetime.strptime(data, "%d/%m/%Y")
        ano_mes = data_obj.strftime("%Y-%m")
        dia = data_obj.strftime("%d")
        
        # Criar diretório se não existir
        base_path = os.path.dirname(os.path.dirname(__file__))
        dir_path = os.path.join(base_path, "comunicacao", "reunioes", ano_mes)
        os.makedirs(dir_path, exist_ok=True)
        
        # Nome do arquivo
        nome_arquivo = f"{dia}_ata_{nome_reuniao.lower().replace(' ', '_')}.md"
        file_path = os.path.join(dir_path, nome_arquivo)
        
        # Salvar arquivo
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(ata)
        
        return file_path


# Exemplo de uso
if __name__ == "__main__":
    gerador = GeradorAta()
    
    # Dados de exemplo
    ata = gerador.gerar_ata(
        data="26/02/2026",
        horario_inicio="10:00",
        horario_fim="12:00",
        facilitador="DEV1",
        participantes_presentes=[
            {"nome": "Dra. Maria Santos", "cargo": "Especialista LGPD"},
            {"nome": "DEV2", "cargo": "Desenvolvedor"}
        ],
        participantes_ausentes=[],
        resumo_executivo="Validação da implementação de anonimização LGPD no sistema INTELLICARE.",
        objetivos=[
            {"descricao": "Validar anonimização de dados", "alcancado": True},
            {"descricao": "Aprovar conformidade LGPD", "alcancado": True}
        ],
        topicos=[
            {
                "nome": "Demonstração de Anonimização",
                "discussao": [
                    "Apresentação do processo de hash SHA-256",
                    "Demonstração de categorização de dados"
                ],
                "decisoes": [
                    "Processo aprovado pela especialista LGPD"
                ],
                "pendencias": []
            }
        ],
        action_items=[
            {
                "id": "AI-001",
                "acao": "Documentar processo de anonimização",
                "responsavel": "DEV1",
                "prazo": "28/02",
                "prioridade": "alta"
            }
        ],
        proximos_passos=[
            "Implementar em produção",
            "Monitorar conformidade"
        ]
    )
    
    print(ata)

