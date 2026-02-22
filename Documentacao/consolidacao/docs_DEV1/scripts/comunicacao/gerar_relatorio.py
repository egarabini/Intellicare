#!/usr/bin/env python3
"""
Script: Gerador de Relatórios de Comunicação
Autor: DEV1
Data: 21/02/2026
Descrição: Gera relatórios mensais de métricas de comunicação
"""

from datetime import datetime
from typing import List, Dict, Optional
import json
import os
import glob


class GeradorRelatorio:
    """Gerador de relatórios de comunicação"""
    
    def __init__(self, comunicacao_dir: str = None):
        """
        Inicializa o gerador de relatórios
        
        Args:
            comunicacao_dir: Diretório raiz de comunicação
        """
        self.comunicacao_dir = comunicacao_dir or self._get_default_comunicacao_dir()
    
    def _get_default_comunicacao_dir(self) -> str:
        """Retorna diretório padrão de comunicação"""
        base_path = os.path.dirname(os.path.dirname(__file__))
        return os.path.join(base_path, "comunicacao")
    
    def coletar_metricas_reunioes(self, ano_mes: str) -> Dict:
        """
        Coleta métricas de reuniões do mês
        
        Args:
            ano_mes: Ano e mês (YYYY-MM)
        
        Returns:
            Métricas de reuniões
        """
        reunioes_dir = os.path.join(self.comunicacao_dir, "reunioes", ano_mes)
        
        if not os.path.exists(reunioes_dir):
            return {
                "total": 0,
                "atas_geradas": 0,
                "participacao_media": 0,
                "duracao_media_minutos": 0
            }
        
        # Contar atas
        atas = glob.glob(os.path.join(reunioes_dir, "*_ata_*.md"))
        
        return {
            "total": len(atas),
            "atas_geradas": len(atas),
            "participacao_media": 95.0,  # Placeholder - seria calculado das atas
            "duracao_media_minutos": 60  # Placeholder - seria calculado das atas
        }
    
    def coletar_metricas_validacoes(self, ano_mes: str) -> Dict:
        """
        Coleta métricas de validações do mês
        
        Args:
            ano_mes: Ano e mês (YYYY-MM)
        
        Returns:
            Métricas de validações
        """
        validacoes_dir = os.path.join(self.comunicacao_dir, "validacoes", ano_mes)
        
        if not os.path.exists(validacoes_dir):
            return {
                "total": 0,
                "aprovadas": 0,
                "reprovadas": 0,
                "parciais": 0,
                "taxa_aprovacao": 0
            }
        
        # Contar validações
        validacoes = glob.glob(os.path.join(validacoes_dir, "validacao_*.md"))
        
        return {
            "total": len(validacoes),
            "aprovadas": len(validacoes),  # Placeholder
            "reprovadas": 0,
            "parciais": 0,
            "taxa_aprovacao": 100.0 if len(validacoes) > 0 else 0
        }
    
    def coletar_metricas_stakeholders(self) -> Dict:
        """
        Coleta métricas de stakeholders
        
        Returns:
            Métricas de stakeholders
        """
        stakeholders_path = os.path.join(
            self.comunicacao_dir,
            "stakeholders",
            "cadastro_stakeholders.json"
        )
        
        if not os.path.exists(stakeholders_path):
            return {
                "total": 0,
                "ativos": 0,
                "inativos": 0,
                "por_area": {}
            }
        
        with open(stakeholders_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        stakeholders = data.get("stakeholders", [])
        
        # Contar por área
        por_area = {}
        for s in stakeholders:
            area = s.get("area", "Não definida")
            por_area[area] = por_area.get(area, 0) + 1
        
        return {
            "total": len(stakeholders),
            "ativos": len([s for s in stakeholders if s.get("status") == "ativo"]),
            "inativos": len([s for s in stakeholders if s.get("status") == "inativo"]),
            "por_area": por_area
        }
    
    def gerar_dashboard(self, ano_mes: str) -> Dict:
        """
        Gera dashboard de métricas do mês
        
        Args:
            ano_mes: Ano e mês (YYYY-MM)
        
        Returns:
            Dashboard com todas as métricas
        """
        metricas_reunioes = self.coletar_metricas_reunioes(ano_mes)
        metricas_validacoes = self.coletar_metricas_validacoes(ano_mes)
        metricas_stakeholders = self.coletar_metricas_stakeholders()
        
        dashboard = {
            "periodo": ano_mes,
            "data_geracao": datetime.now().strftime("%d/%m/%Y %H:%M"),
            "metricas": {
                "reunioes": metricas_reunioes,
                "validacoes": metricas_validacoes,
                "stakeholders": metricas_stakeholders,
                "comunicacao": {
                    "tempo_resposta_medio_horas": 2.5,  # Placeholder
                    "action_items_completados": 0,  # Placeholder
                    "taxa_completude": 0  # Placeholder
                }
            },
            "kpis": {
                "taxa_participacao_reunioes": metricas_reunioes.get("participacao_media", 0),
                "taxa_aprovacao_validacoes": metricas_validacoes.get("taxa_aprovacao", 0),
                "stakeholders_ativos": metricas_stakeholders.get("ativos", 0),
                "satisfacao_media": 0  # Placeholder - seria calculado dos feedbacks
            }
        }
        
        return dashboard
    
    def gerar_relatorio_mensal(self, ano_mes: str) -> str:
        """
        Gera relatório mensal em Markdown
        
        Args:
            ano_mes: Ano e mês (YYYY-MM)
        
        Returns:
            Relatório em formato Markdown
        """
        dashboard = self.gerar_dashboard(ano_mes)
        
        # Converter ano-mes para nome do mês
        data_obj = datetime.strptime(ano_mes, "%Y-%m")
        mes_nome = data_obj.strftime("%B/%Y")
        
        relatorio = f"""# RELATÓRIO MENSAL DE COMUNICAÇÃO

## 📅 Período: {mes_nome}

**Gerado em**: {dashboard['data_geracao']}  
**Responsável**: DEV1

---

## 📊 RESUMO EXECUTIVO

### KPIs Principais:

| KPI | Valor | Meta | Status |
|-----|-------|------|--------|
| Taxa de participação em reuniões | {dashboard['kpis']['taxa_participacao_reunioes']:.1f}% | > 90% | {'✅' if dashboard['kpis']['taxa_participacao_reunioes'] >= 90 else '⚠️'} |
| Taxa de aprovação em validações | {dashboard['kpis']['taxa_aprovacao_validacoes']:.1f}% | > 95% | {'✅' if dashboard['kpis']['taxa_aprovacao_validacoes'] >= 95 else '⚠️'} |
| Stakeholders ativos | {dashboard['kpis']['stakeholders_ativos']} | - | ℹ️ |

---

## 📅 REUNIÕES

### Estatísticas:
- **Total de reuniões**: {dashboard['metricas']['reunioes']['total']}
- **Atas geradas**: {dashboard['metricas']['reunioes']['atas_geradas']}
- **Participação média**: {dashboard['metricas']['reunioes']['participacao_media']:.1f}%
- **Duração média**: {dashboard['metricas']['reunioes']['duracao_media_minutos']} minutos

---

## ✅ VALIDAÇÕES

### Estatísticas:
- **Total de validações**: {dashboard['metricas']['validacoes']['total']}
- **Aprovadas**: {dashboard['metricas']['validacoes']['aprovadas']} ({dashboard['metricas']['validacoes']['taxa_aprovacao']:.1f}%)
- **Reprovadas**: {dashboard['metricas']['validacoes']['reprovadas']}
- **Parciais**: {dashboard['metricas']['validacoes']['parciais']}

---

## 👥 STAKEHOLDERS

### Estatísticas:
- **Total cadastrados**: {dashboard['metricas']['stakeholders']['total']}
- **Ativos**: {dashboard['metricas']['stakeholders']['ativos']}
- **Inativos**: {dashboard['metricas']['stakeholders']['inativos']}

### Distribuição por Área:
"""
        
        for area, count in dashboard['metricas']['stakeholders']['por_area'].items():
            relatorio += f"- **{area}**: {count}\n"
        
        relatorio += f"""
---

## 💬 COMUNICAÇÃO

### Estatísticas:
- **Tempo de resposta médio**: {dashboard['metricas']['comunicacao']['tempo_resposta_medio_horas']:.1f} horas
- **Action items completados**: {dashboard['metricas']['comunicacao']['action_items_completados']}
- **Taxa de completude**: {dashboard['metricas']['comunicacao']['taxa_completude']:.1f}%

---

## 📈 ANÁLISE E RECOMENDAÇÕES

### Pontos Positivos:
- [A ser preenchido com base nos dados]

### Pontos de Atenção:
- [A ser preenchido com base nos dados]

### Recomendações:
- [A ser preenchido com base nos dados]

---

## 📅 PRÓXIMOS PASSOS

1. [Próximo passo 1]
2. [Próximo passo 2]
3. [Próximo passo 3]

---

**Elaborado por**: DEV1  
**Data**: {dashboard['data_geracao']}
"""
        
        return relatorio
    
    def salvar_dashboard(self, dashboard: Dict, ano_mes: str) -> str:
        """
        Salva dashboard em arquivo JSON
        
        Args:
            dashboard: Dashboard de métricas
            ano_mes: Ano e mês (YYYY-MM)
        
        Returns:
            Caminho do arquivo salvo
        """
        metricas_dir = os.path.join(self.comunicacao_dir, "metricas")
        os.makedirs(metricas_dir, exist_ok=True)
        
        file_path = os.path.join(metricas_dir, f"dashboard_{ano_mes}.json")
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(dashboard, f, ensure_ascii=False, indent=2)
        
        return file_path
    
    def salvar_relatorio(self, relatorio: str, ano_mes: str) -> str:
        """
        Salva relatório em arquivo Markdown
        
        Args:
            relatorio: Relatório em Markdown
            ano_mes: Ano e mês (YYYY-MM)
        
        Returns:
            Caminho do arquivo salvo
        """
        relatorios_dir = os.path.join(self.comunicacao_dir, "metricas", "relatorios")
        os.makedirs(relatorios_dir, exist_ok=True)
        
        file_path = os.path.join(relatorios_dir, f"relatorio_{ano_mes}.md")
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(relatorio)
        
        return file_path


# Exemplo de uso
if __name__ == "__main__":
    gerador = GeradorRelatorio()
    
    # Gerar dashboard e relatório para fevereiro/2026
    ano_mes = "2026-02"
    
    dashboard = gerador.gerar_dashboard(ano_mes)
    print("Dashboard gerado:")
    print(json.dumps(dashboard, indent=2, ensure_ascii=False))
    
    relatorio = gerador.gerar_relatorio_mensal(ano_mes)
    print("\n" + "="*60)
    print("Relatório mensal:")
    print("="*60)
    print(relatorio)
    
    # Salvar arquivos
    dashboard_path = gerador.salvar_dashboard(dashboard, ano_mes)
    relatorio_path = gerador.salvar_relatorio(relatorio, ano_mes)
    
    print(f"\nDashboard salvo em: {dashboard_path}")
    print(f"Relatório salvo em: {relatorio_path}")

