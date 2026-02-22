#!/usr/bin/env python3
"""
Script: Enviador de Convites de Reunião
Autor: DEV1
Data: 21/02/2026
Descrição: Envia convites de reunião por email com agenda anexada
"""

from datetime import datetime, timedelta
from typing import List, Dict, Optional
import json
import os


class EnviadorConvites:
    """Enviador de convites de reunião"""

    def __init__(self, stakeholders_path: str = None):
        """
        Inicializa o enviador de convites

        Args:
            stakeholders_path: Caminho para cadastro de stakeholders
        """
        self.stakeholders_path = stakeholders_path or self._get_default_stakeholders_path()
        self.stakeholders = self._carregar_stakeholders()

    def _get_default_stakeholders_path(self) -> str:
        """Retorna caminho padrão do cadastro de stakeholders"""
        base_path = os.path.dirname(os.path.dirname(__file__))
        return os.path.join(
            base_path,
            "comunicacao",
            "stakeholders",
            "cadastro_stakeholders.json"
        )

    def _carregar_stakeholders(self) -> Dict:
        """Carrega cadastro de stakeholders"""
        if os.path.exists(self.stakeholders_path):
            with open(self.stakeholders_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {"stakeholders": []}

    def criar_convite(
        self,
        titulo: str,
        data: str,
        horario_inicio: str,
        duracao_minutos: int,
        participantes_ids: List[str],
        objetivo: str,
        pauta: List[Dict],
        materiais_previos: Optional[List[str]] = None,
        preparacao: Optional[List[str]] = None,
        link_reuniao: Optional[str] = None
    ) -> Dict:
        """
        Cria convite de reunião

        Args:
            titulo: Título da reunião
            data: Data da reunião (DD/MM/YYYY)
            horario_inicio: Horário de início (HH:MM)
            duracao_minutos: Duração em minutos
            participantes_ids: Lista de IDs de stakeholders
            objetivo: Objetivo principal da reunião
            pauta: Lista de tópicos da pauta
            materiais_previos: Links para materiais prévios
            preparacao: Lista de itens de preparação
            link_reuniao: Link da videochamada

        Returns:
            Dicionário com dados do convite
        """
        # Calcular horário de término
        data_obj = datetime.strptime(f"{data} {horario_inicio}", "%d/%m/%Y %H:%M")
        horario_fim = (data_obj + timedelta(minutes=duracao_minutos)).strftime("%H:%M")

        # Buscar dados dos participantes
        participantes = []
        for pid in participantes_ids:
            stakeholder = next(
                (s for s in self.stakeholders['stakeholders'] if s['id'] == pid),
                None
            )
            if stakeholder:
                participantes.append({
                    "id": stakeholder['id'],
                    "nome": stakeholder['nome'],
                    "email": stakeholder['email'],
                    "cargo": stakeholder['cargo']
                })

        # Montar convite
        convite = {
            "titulo": titulo,
            "data": data,
            "horario_inicio": horario_inicio,
            "horario_fim": horario_fim,
            "duracao_minutos": duracao_minutos,
            "participantes": participantes,
            "objetivo": objetivo,
            "pauta": pauta,
            "materiais_previos": materiais_previos or [],
            "preparacao": preparacao or [],
            "link_reuniao": link_reuniao or "A ser enviado",
            "data_criacao": datetime.now().strftime("%d/%m/%Y %H:%M")
        }

        return convite

    def gerar_email_convite(self, convite: Dict) -> str:
        """
        Gera corpo do email de convite

        Args:
            convite: Dados do convite

        Returns:
            Corpo do email em formato texto
        """
        email = f"""Prezados(as),

Você está convidado(a) para a seguinte reunião:

📅 INFORMAÇÕES DA REUNIÃO
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Título: {convite['titulo']}
Data: {convite['data']}
Horário: {convite['horario_inicio']} - {convite['horario_fim']} ({convite['duracao_minutos']} minutos)
Link: {convite['link_reuniao']}

🎯 OBJETIVO
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

{convite['objetivo']}

👥 PARTICIPANTES
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

"""
        for p in convite['participantes']:
            email += f"• {p['nome']} - {p['cargo']}\n"

        email += f"""
📋 PAUTA
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

"""
        for item in convite['pauta']:
            email += f"{item['horario']} ({item['duracao']} min) - {item['topico']}\n"

        if convite['materiais_previos']:
            email += f"""
📎 MATERIAIS PRÉVIOS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

"""
            for material in convite['materiais_previos']:
                email += f"• {material}\n"

        if convite['preparacao']:
            email += f"""
✅ PREPARAÇÃO NECESSÁRIA
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

"""
            for prep in convite['preparacao']:
                email += f"☐ {prep}\n"

        email += f"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Atenciosamente,
DEV1 - Gestor de Comunicação
Projeto INTELLICARE

Convite gerado em: {convite['data_criacao']}
"""

        return email

    def enviar_convite(self, convite: Dict, simular: bool = True) -> Dict:
        """
        Envia convite por email

        Args:
            convite: Dados do convite
            simular: Se True, apenas simula o envio

        Returns:
            Resultado do envio
        """
        email_corpo = self.gerar_email_convite(convite)

        if simular:
            print("=" * 60)
            print("SIMULAÇÃO DE ENVIO DE CONVITE")
            print("=" * 60)
            print(f"\nPara: {', '.join([p['email'] for p in convite['participantes']])}")
            print(f"Assunto: Convite: {convite['titulo']} - {convite['data']}")
            print("\n" + email_corpo)
            print("=" * 60)

            return {
                "sucesso": True,
                "modo": "simulacao",
                "destinatarios": len(convite['participantes']),
                "data_envio": datetime.now().strftime("%d/%m/%Y %H:%M")
            }
        else:
            # Aqui seria a integração real com serviço de email
            # Por exemplo: Gmail API, SendGrid, etc.
            raise NotImplementedError("Envio real de email não implementado ainda")


# Exemplo de uso
if __name__ == "__main__":
    enviador = EnviadorConvites()

    # Criar convite de exemplo
    convite = enviador.criar_convite(
        titulo="Validação LGPD - Anonimização de Dados",
        data="26/02/2026",
        horario_inicio="10:00",
        duracao_minutos=120,
        participantes_ids=["STK-002"],  # Dra. Maria Santos
        objetivo="Validar implementação de anonimização LGPD no sistema INTELLICARE",
        pauta=[
            {"horario": "10:00", "duracao": "5", "topico": "Abertura e contexto"},
            {"horario": "10:05", "duracao": "30", "topico": "Demonstração de anonimização"},
            {"horario": "10:35", "duracao": "45", "topico": "Testes práticos"},
            {"horario": "11:20", "duracao": "30", "topico": "Discussão e feedback"},
            {"horario": "11:50", "duracao": "10", "topico": "Próximos passos"}
        ],
        materiais_previos=[
            "Documentação LGPD: https://drive.google.com/...",
            "Especificação técnica: https://drive.google.com/..."
        ],
        preparacao=[
            "Ler documentação LGPD",
            "Revisar casos de teste"
        ],
        link_reuniao="https://meet.google.com/xxx-yyyy-zzz"
    )

    # Enviar convite (simulação)
    resultado = enviador.enviar_convite(convite, simular=True)
    print(f"\nResultado: {resultado}")
