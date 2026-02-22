#!/usr/bin/env python3
"""
Script: Coletor de Feedback
Autor: DEV1
Data: 21/02/2026
Descrição: Coleta e consolida feedback de reuniões e validações
"""

from datetime import datetime
from typing import List, Dict, Optional
import json
import os


class ColetorFeedback:
    """Coletor e consolidador de feedback"""
    
    def __init__(self, feedback_dir: str = None):
        """
        Inicializa o coletor de feedback
        
        Args:
            feedback_dir: Diretório para armazenar feedbacks
        """
        self.feedback_dir = feedback_dir or self._get_default_feedback_dir()
        os.makedirs(self.feedback_dir, exist_ok=True)
    
    def _get_default_feedback_dir(self) -> str:
        """Retorna diretório padrão de feedbacks"""
        base_path = os.path.dirname(os.path.dirname(__file__))
        return os.path.join(base_path, "comunicacao", "metricas", "feedbacks")
    
    def criar_formulario_feedback(
        self,
        tipo_atividade: str,
        titulo: str,
        data: str,
        facilitador: str = "DEV1"
    ) -> Dict:
        """
        Cria formulário de feedback estruturado
        
        Args:
            tipo_atividade: Tipo (Reunião/Validação/Apresentação)
            titulo: Título da atividade
            data: Data da atividade (DD/MM/YYYY)
            facilitador: Nome do facilitador
        
        Returns:
            Formulário de feedback estruturado
        """
        return {
            "metadata": {
                "tipo_atividade": tipo_atividade,
                "titulo": titulo,
                "data": data,
                "facilitador": facilitador,
                "data_criacao": datetime.now().strftime("%d/%m/%Y %H:%M")
            },
            "respostas": []
        }
    
    def adicionar_resposta(
        self,
        formulario: Dict,
        respondente: str,
        cargo: str,
        avaliacao_geral: int,
        organizacao: str,
        clareza: str,
        objetivos_alcancados: str,
        duracao: str,
        materiais: str,
        pontos_fortes: List[str],
        pontos_melhoria: List[str],
        sugestoes: str,
        comentarios_adicionais: Optional[str] = None,
        perguntas_especificas: Optional[Dict] = None
    ) -> Dict:
        """
        Adiciona resposta ao formulário
        
        Args:
            formulario: Formulário de feedback
            respondente: Nome do respondente
            cargo: Cargo do respondente
            avaliacao_geral: Nota de 1 a 5
            organizacao: Avaliação da organização
            clareza: Avaliação da clareza
            objetivos_alcancados: Avaliação dos objetivos
            duracao: Avaliação da duração
            materiais: Avaliação dos materiais
            pontos_fortes: Lista de pontos fortes
            pontos_melhoria: Lista de pontos de melhoria
            sugestoes: Sugestões
            comentarios_adicionais: Comentários adicionais
            perguntas_especificas: Respostas a perguntas específicas
        
        Returns:
            Formulário atualizado
        """
        resposta = {
            "respondente": respondente,
            "cargo": cargo,
            "data_resposta": datetime.now().strftime("%d/%m/%Y %H:%M"),
            "avaliacao": {
                "geral": avaliacao_geral,
                "organizacao": organizacao,
                "clareza": clareza,
                "objetivos_alcancados": objetivos_alcancados,
                "duracao": duracao,
                "materiais": materiais
            },
            "pontos_fortes": pontos_fortes,
            "pontos_melhoria": pontos_melhoria,
            "sugestoes": sugestoes,
            "comentarios_adicionais": comentarios_adicionais,
            "perguntas_especificas": perguntas_especificas or {}
        }
        
        formulario["respostas"].append(resposta)
        return formulario
    
    def consolidar_feedback(self, formulario: Dict) -> Dict:
        """
        Consolida feedback de múltiplas respostas
        
        Args:
            formulario: Formulário com respostas
        
        Returns:
            Feedback consolidado com estatísticas
        """
        if not formulario["respostas"]:
            return {"erro": "Nenhuma resposta para consolidar"}
        
        total_respostas = len(formulario["respostas"])
        
        # Calcular média de avaliação geral
        notas = [r["avaliacao"]["geral"] for r in formulario["respostas"]]
        media_geral = sum(notas) / len(notas)
        
        # Contar avaliações por categoria
        def contar_avaliacoes(campo: str) -> Dict:
            valores = [r["avaliacao"][campo] for r in formulario["respostas"]]
            return {
                "muito_bom": valores.count("Sim, muito bem organizada") + 
                             valores.count("Sim, muito clara") +
                             valores.count("Sim, completamente") +
                             valores.count("Sim, tempo perfeito") +
                             valores.count("Sim, excelentes"),
                "bom": valores.count("Sim, razoavelmente organizada") +
                       valores.count("Sim, razoavelmente clara") +
                       valores.count("Sim, parcialmente") +
                       valores.count("Sim, mas poderia ser mais curta") +
                       valores.count("Sim, adequados"),
                "regular": valores.count("Não, poderia ser melhor") +
                          valores.count("Não, confusa em alguns pontos") +
                          valores.count("Não, poucos objetivos alcançados") +
                          valores.count("Não, muito longa") +
                          valores.count("Não, insuficientes"),
                "ruim": valores.count("Não, mal organizada") +
                       valores.count("Não, muito confusa") +
                       valores.count("Não, nenhum objetivo alcançado") +
                       valores.count("Não, muito curta") +
                       valores.count("Não, inadequados")
            }
        
        # Consolidar pontos fortes e de melhoria
        todos_pontos_fortes = []
        todos_pontos_melhoria = []
        todas_sugestoes = []
        
        for resposta in formulario["respostas"]:
            todos_pontos_fortes.extend(resposta["pontos_fortes"])
            todos_pontos_melhoria.extend(resposta["pontos_melhoria"])
            if resposta["sugestoes"]:
                todas_sugestoes.append(resposta["sugestoes"])
        
        consolidado = {
            "metadata": formulario["metadata"],
            "estatisticas": {
                "total_respostas": total_respostas,
                "media_geral": round(media_geral, 2),
                "distribuicao_notas": {
                    "5_estrelas": notas.count(5),
                    "4_estrelas": notas.count(4),
                    "3_estrelas": notas.count(3),
                    "2_estrelas": notas.count(2),
                    "1_estrela": notas.count(1)
                }
            },
            "pontos_fortes_consolidados": todos_pontos_fortes,
            "pontos_melhoria_consolidados": todos_pontos_melhoria,
            "sugestoes_consolidadas": todas_sugestoes,
            "data_consolidacao": datetime.now().strftime("%d/%m/%Y %H:%M")
        }
        
        return consolidado
    
    def gerar_relatorio_feedback(self, consolidado: Dict) -> str:
        """
        Gera relatório textual do feedback consolidado
        
        Args:
            consolidado: Feedback consolidado
        
        Returns:
            Relatório em formato Markdown
        """
        meta = consolidado["metadata"]
        stats = consolidado["estatisticas"]
        
        relatorio = f"""# RELATÓRIO DE FEEDBACK

## 📋 Informações da Atividade
- **Tipo**: {meta['tipo_atividade']}
- **Título**: {meta['titulo']}
- **Data**: {meta['data']}
- **Facilitador**: {meta['facilitador']}

## 📊 Estatísticas Gerais
- **Total de respostas**: {stats['total_respostas']}
- **Média geral**: {stats['media_geral']}/5 ⭐

### Distribuição de Notas:
- 5 estrelas: {stats['distribuicao_notas']['5_estrelas']} ({stats['distribuicao_notas']['5_estrelas']/stats['total_respostas']*100:.1f}%)
- 4 estrelas: {stats['distribuicao_notas']['4_estrelas']} ({stats['distribuicao_notas']['4_estrelas']/stats['total_respostas']*100:.1f}%)
- 3 estrelas: {stats['distribuicao_notas']['3_estrelas']} ({stats['distribuicao_notas']['3_estrelas']/stats['total_respostas']*100:.1f}%)
- 2 estrelas: {stats['distribuicao_notas']['2_estrelas']} ({stats['distribuicao_notas']['2_estrelas']/stats['total_respostas']*100:.1f}%)
- 1 estrela: {stats['distribuicao_notas']['1_estrela']} ({stats['distribuicao_notas']['1_estrela']/stats['total_respostas']*100:.1f}%)

## ✅ Pontos Fortes
"""
        for ponto in consolidado["pontos_fortes_consolidados"]:
            relatorio += f"- {ponto}\n"
        
        relatorio += "\n## ⚠️ Pontos de Melhoria\n"
        for ponto in consolidado["pontos_melhoria_consolidados"]:
            relatorio += f"- {ponto}\n"
        
        relatorio += "\n## 💡 Sugestões\n"
        for sugestao in consolidado["sugestoes_consolidadas"]:
            relatorio += f"- {sugestao}\n"
        
        relatorio += f"\n---\n**Relatório gerado em**: {consolidado['data_consolidacao']}\n"
        
        return relatorio
    
    def salvar_feedback(self, formulario: Dict, nome_arquivo: str) -> str:
        """
        Salva feedback em arquivo JSON
        
        Args:
            formulario: Formulário de feedback
            nome_arquivo: Nome do arquivo
        
        Returns:
            Caminho do arquivo salvo
        """
        file_path = os.path.join(self.feedback_dir, f"{nome_arquivo}.json")
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(formulario, f, ensure_ascii=False, indent=2)
        
        return file_path


# Exemplo de uso
if __name__ == "__main__":
    coletor = ColetorFeedback()
    
    # Criar formulário
    formulario = coletor.criar_formulario_feedback(
        tipo_atividade="Validação",
        titulo="Validação LGPD - Anonimização",
        data="26/02/2026"
    )
    
    # Adicionar resposta de exemplo
    formulario = coletor.adicionar_resposta(
        formulario=formulario,
        respondente="Dra. Maria Santos",
        cargo="Especialista LGPD",
        avaliacao_geral=5,
        organizacao="Sim, muito bem organizada",
        clareza="Sim, muito clara",
        objetivos_alcancados="Sim, completamente",
        duracao="Sim, tempo perfeito",
        materiais="Sim, excelentes",
        pontos_fortes=[
            "Demonstração clara do processo de anonimização",
            "Documentação completa e bem estruturada",
            "Conformidade total com LGPD"
        ],
        pontos_melhoria=[
            "Poderia incluir mais casos de teste edge cases"
        ],
        sugestoes="Excelente trabalho! Recomendo implementação em produção."
    )
    
    # Consolidar feedback
    consolidado = coletor.consolidar_feedback(formulario)
    
    # Gerar relatório
    relatorio = coletor.gerar_relatorio_feedback(consolidado)
    print(relatorio)

