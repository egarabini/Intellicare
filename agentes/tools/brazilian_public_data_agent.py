"""
============================================================================
HERMES - Brazilian Public Data Agent
============================================================================
Agente Especialista em Dados Públicos Brasileiros Oficiais.
Integra: Banco Central (PTAX), ViaCEP, BrasilAPI.

Author: HERMES Team
Version: 3.5.1
============================================================================
"""

import requests
import logging
import json
from typing import Dict, Any
from core.base_tool import BaseTool

logger = logging.getLogger(__name__)


class BrazilianPublicDataAgent(BaseTool):
    """
    Agente Especialista em Dados Públicos Brasileiros Oficiais.
    Integra: Banco Central (PTAX), ViaCEP, BrasilAPI.
    """
    
    NAME = "br_data_agent"
    DESCRIPTION = (
        "Consulta dados oficiais brasileiros em tempo real via APIs governamentais. "
        "SEMPRE use esta ferramenta para: "
        "1) Cotações atuais (Dólar, Euro) "
        "2) Taxas econômicas (CDI, Selic, IPCA) "
        "3) Consulta CEP (endereço completo) "
        "4) Consulta CNPJ (dados da empresa) "
        "5) Lista de Bancos brasileiros "
        "6) Feriados nacionais "
        "7) Marcas FIPE (veículos) "
        "8) Informações IBGE de Estados (nome, ID, região) "
        "9) Informações IBGE de Cidades (ID, microrregião, mesorregião) "
        "10) Busca CNAE (classificação de atividades econômicas). "
        "Fontes oficiais: Banco Central, ViaCEP, ReceitaWS, BrasilAPI, IBGE. "
        "NÃO use conhecimento interno - SEMPRE consulte as APIs para dados atualizados."
    )

    def __init__(self):
        super().__init__(self.NAME, self.DESCRIPTION)

    def get_definition(self) -> Dict[str, Any]:
        """Definição Multi-Função para o Maestro"""
        return {
            "name": self.NAME,
            "description": self.DESCRIPTION,
            "input_schema": {
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "enum": [
                            "get_dolar_price", "get_euro_price", "get_cep_info",
                            "get_banks_list", "get_cdi_rate", "get_selic_rate",
                            "get_ipca_rate", "get_cnpj_info", "get_holidays",
                            "get_fipe_brands", "get_ibge_uf_info", "get_ibge_city_info",
                            "search_cnae"
                        ],
                        "description": (
                            "Ação a executar. Use: "
                            "get_ibge_uf_info para estados (ex: RJ, São Paulo), "
                            "get_ibge_city_info para cidades (ex: Vitória, Rio de Janeiro), "
                            "search_cnae para atividades econômicas (ex: informática, 6200)."
                        )
                    },
                    "params": {
                        "type": "object",
                        "description": (
                            "Parâmetros da ação. Exemplos: "
                            "{'cep': '01001000'}, "
                            "{'cnpj': '00000000000191'}, "
                            "{'uf_code': 'RJ'}, "
                            "{'city_name': 'Vitória'}, "
                            "{'query_term': 'informática'}, "
                            "{'year': '2026'}, "
                            "{'vehicle_type': 'carros'}."
                        )
                    }
                },
                "required": ["action"]
            }
        }

    def run(self, input_text: str) -> str:
        """
        O Maestro enviará um JSON string como input_text: 
        '{"action": "get_dolar_price", "params": {}}'
        """
        try:
            data = json.loads(input_text)
            action = data.get("action")
            params = data.get("params", {})

            if action == "get_dolar_price":
                return self._get_dolar_bacen()

            elif action == "get_euro_price":
                return self._get_euro_bacen()

            elif action == "get_cep_info":
                return self._get_cep_viacep(params.get("cep"))

            elif action == "get_banks_list":
                return self._get_banks_brasilapi()

            elif action == "get_cdi_rate":
                return self._get_cdi_bacen()

            elif action == "get_selic_rate":
                return self._get_selic_bacen()

            elif action == "get_ipca_rate":
                return self._get_ipca_bacen()

            elif action == "get_cnpj_info":
                return self._get_cnpj_receitaws(params.get("cnpj"))

            elif action == "get_holidays":
                return self._get_holidays_brasilapi(params.get("year"))

            elif action == "get_fipe_brands":
                return self._get_fipe_brands_brasilapi(params.get("vehicle_type", "carros"))

            elif action == "get_ibge_uf_info":
                return self._get_ibge_uf_info(params.get("uf_code"))

            elif action == "get_ibge_city_info":
                return self._get_ibge_city_info(params.get("city_name"))

            elif action == "search_cnae":
                return self._search_cnae(params.get("query_term"))

            else:
                return "Ação não reconhecida. Ações disponíveis: get_dolar_price, get_euro_price, get_cep_info, get_banks_list, get_cdi_rate, get_selic_rate, get_ipca_rate, get_cnpj_info, get_holidays, get_fipe_brands, get_ibge_uf_info, get_ibge_city_info, search_cnae."
                
        except json.JSONDecodeError:
            logger.error("Erro de formato JSON na entrada do agente")
            return "Erro de formato JSON na entrada do agente."
        except Exception as e:
            logger.error(f"Erro ao processar dados públicos: {str(e)}")
            return f"Erro ao processar dados públicos: {str(e)}"

    # --- MÉTODOS PRIVADOS DE INTEGRAÇÃO ---

    def _get_dolar_bacen(self) -> str:
        """Cotação Dólar Comercial (Venda) - Código 10813"""
        url = "https://api.bcb.gov.br/dados/serie/bcdata.sgs.10813/dados/ultimos/1?formato=json"
        try:
            r = requests.get(url, timeout=5)
            r.raise_for_status()
            data = r.json()[0]
            valor = float(data["valor"].replace(",", "."))
            return f"🇺🇸 **Dólar Comercial (Venda)**\nData: {data['data']}\nValor: R$ {valor:.4f}\nFonte: Banco Central do Brasil"
        except Exception as e:
            logger.error(f"Erro ao consultar Bacen: {e}")
            return f"Erro ao consultar cotação do dólar no Banco Central: {str(e)}"

    def _get_cep_viacep(self, cep: str) -> str:
        """Consulta ViaCEP"""
        if not cep:
            return "Por favor, forneça um CEP numérico (ex: 01001000 ou 01001-000)."
        
        # Limpa o CEP (remove traços e espaços)
        cep = "".join(filter(str.isdigit, str(cep)))
        
        if len(cep) != 8:
            return "CEP inválido. Deve conter 8 dígitos."
        
        try:
            url = f"https://viacep.com.br/ws/{cep}/json/"
            r = requests.get(url, timeout=3)
            r.raise_for_status()
            
            data = r.json()
            if "erro" in data:
                return f"CEP {cep} não encontrado na base ViaCEP."
            
            return (
                f"📍 **Endereço Completo:**\n"
                f"Logradouro: {data.get('logradouro', 'N/A')}\n"
                f"Complemento: {data.get('complemento', 'N/A')}\n"
                f"Bairro: {data.get('bairro', 'N/A')}\n"
                f"Cidade: {data.get('localidade', 'N/A')} - {data.get('uf', 'N/A')}\n"
                f"CEP: {data.get('cep', 'N/A')}\n"
                f"Fonte: ViaCEP"
            )
        except Exception as e:
            logger.error(f"Erro ao consultar ViaCEP: {e}")
            return f"Erro ao consultar CEP: {str(e)}"

    def _get_banks_brasilapi(self) -> str:
        """Lista de Bancos (Top 10)"""
        try:
            url = "https://brasilapi.com.br/api/banks/v1"
            r = requests.get(url, timeout=5)
            r.raise_for_status()
            
            # Pega apenas os 10 primeiros para não lotar o contexto
            banks = r.json()[:10]
            
            list_str = "\n".join([f"- {b.get('name', 'N/A')} (Código: {b.get('code', 'N/A')})" for b in banks])
            return f"🏦 **Bancos Brasileiros (Top 10):**\n{list_str}\nFonte: BrasilAPI"
        except Exception as e:
            logger.error(f"Erro ao consultar BrasilAPI: {e}")
            return f"Erro ao consultar lista de bancos: {str(e)}"
            
    def _get_cdi_bacen(self) -> str:
        """Taxa CDI Diária - Código 12"""
        url = "https://api.bcb.gov.br/dados/serie/bcdata.sgs.12/dados/ultimos/1?formato=json"
        try:
            r = requests.get(url, timeout=5)
            r.raise_for_status()
            data = r.json()[0]
            valor = float(data["valor"].replace(",", "."))
            return f"📉 **Taxa CDI Diária:** {valor:.2f}%\nData: {data['data']}\nFonte: Banco Central do Brasil"
        except Exception as e:
            logger.error(f"Erro ao consultar CDI no Bacen: {e}")
            return f"Erro ao consultar taxa CDI: {str(e)}"

    def _get_euro_bacen(self) -> str:
        """Cotação Euro Comercial (Venda) - Código 21619"""
        url = "https://api.bcb.gov.br/dados/serie/bcdata.sgs.21619/dados/ultimos/1?formato=json"
        try:
            r = requests.get(url, timeout=5)
            r.raise_for_status()
            data = r.json()[0]
            valor = float(data["valor"])
            return f"🇪🇺 **Euro Comercial (Venda)**\nValor: R$ {valor:.4f}\nData: {data['data']}\nFonte: Banco Central do Brasil"
        except Exception as e:
            logger.error(f"Erro ao consultar Euro no Bacen: {e}")
            return f"Erro ao consultar cotação do Euro: {str(e)}"

    def _get_selic_bacen(self) -> str:
        """Taxa Selic Meta Anual - Série 432"""
        url = "https://api.bcb.gov.br/dados/serie/bcdata.sgs.432/dados/ultimos/1?formato=json"
        try:
            r = requests.get(url, timeout=5)
            r.raise_for_status()
            data = r.json()[0]

            # A Selic meta vem como valor simples (ex: 10.75)
            valor = float(data["valor"])

            return f"📉 **Taxa Selic Meta Anual**\nMeta Atual: {valor:.2f}% ao ano\nData: {data['data']}\nFonte: Banco Central do Brasil (COPOM)"
        except Exception as e:
            logger.error(f"Erro ao consultar Selic no Bacen: {e}")
            return f"Erro ao consultar Selic: {str(e)}"

    def _get_ipca_bacen(self) -> str:
        """IPCA (Inflação) - Código 433"""
        url = "https://api.bcb.gov.br/dados/serie/bcdata.sgs.433/dados/ultimos/1?formato=json"
        try:
            r = requests.get(url, timeout=5)
            r.raise_for_status()
            data = r.json()[0]
            valor = float(data["valor"].replace(",", "."))
            return f"📈 **IPCA (Inflação):** {valor:.2f}%\nData: {data['data']}\nFonte: Banco Central do Brasil (IBGE)"
        except Exception as e:
            logger.error(f"Erro ao consultar IPCA no Bacen: {e}")
            return f"Erro ao consultar IPCA: {str(e)}"

    def _get_cnpj_receitaws(self, cnpj: str) -> str:
        """Consulta CNPJ via ReceitaWS com fallback para BrasilAPI"""
        if not cnpj:
            return "Por favor, forneça um CNPJ (apenas números, 14 dígitos)."

        # Limpa o CNPJ (remove pontos, traços e barras)
        cnpj = "".join(filter(str.isdigit, str(cnpj)))

        if len(cnpj) != 14:
            return "CNPJ inválido. Deve conter 14 dígitos."

        # Tenta ReceitaWS primeiro (mais completo)
        try:
            url = f"https://www.receitaws.com.br/v1/cnpj/{cnpj}"
            r = requests.get(url, timeout=10)
            r.raise_for_status()

            data = r.json()

            if data.get("status") == "ERROR":
                # Se ReceitaWS falhar, tenta BrasilAPI
                logger.warning(f"ReceitaWS falhou, tentando BrasilAPI: {data.get('message')}")
                return self._get_cnpj_brasilapi_fallback(cnpj)

            return (
                f"🏢 **Dados da Empresa:**\n"
                f"Razão Social: {data.get('nome', 'N/A')}\n"
                f"Nome Fantasia: {data.get('fantasia', 'N/A')}\n"
                f"CNPJ: {data.get('cnpj', 'N/A')}\n"
                f"Situação: {data.get('situacao', 'N/A')}\n"
                f"Abertura: {data.get('abertura', 'N/A')}\n"
                f"Atividade Principal: {data.get('atividade_principal', [{}])[0].get('text', 'N/A') if data.get('atividade_principal') else 'N/A'}\n"
                f"Endereço: {data.get('logradouro', 'N/A')}, {data.get('numero', 'N/A')} - {data.get('bairro', 'N/A')}\n"
                f"Cidade: {data.get('municipio', 'N/A')} - {data.get('uf', 'N/A')}\n"
                f"CEP: {data.get('cep', 'N/A')}\n"
                f"Telefone: {data.get('telefone', 'N/A')}\n"
                f"Email: {data.get('email', 'N/A')}\n"
                f"Fonte: ReceitaWS (Receita Federal)"
            )
        except Exception as e:
            logger.error(f"Erro ao consultar ReceitaWS, tentando BrasilAPI: {e}")
            # Fallback para BrasilAPI
            return self._get_cnpj_brasilapi_fallback(cnpj)

    def _get_cnpj_brasilapi_fallback(self, cnpj: str) -> str:
        """Fallback: Consulta CNPJ via BrasilAPI"""
        try:
            url = f"https://brasilapi.com.br/api/cnpj/v1/{cnpj}"
            r = requests.get(url, timeout=10)
            r.raise_for_status()

            data = r.json()

            return (
                f"🏢 **Dados da Empresa:**\n"
                f"Razão Social: {data.get('razao_social', 'N/A')}\n"
                f"Nome Fantasia: {data.get('nome_fantasia', 'N/A')}\n"
                f"CNPJ: {data.get('cnpj', 'N/A')}\n"
                f"Situação: {data.get('descricao_situacao_cadastral', 'N/A')}\n"
                f"Data Situação: {data.get('data_situacao_cadastral', 'N/A')}\n"
                f"Abertura: {data.get('data_inicio_atividade', 'N/A')}\n"
                f"Atividade Principal: {data.get('cnae_fiscal_descricao', 'N/A')}\n"
                f"Endereço: {data.get('logradouro', 'N/A')}, {data.get('numero', 'N/A')} - {data.get('bairro', 'N/A')}\n"
                f"Cidade: {data.get('municipio', 'N/A')} - {data.get('uf', 'N/A')}\n"
                f"CEP: {data.get('cep', 'N/A')}\n"
                f"Capital Social: R$ {data.get('capital_social', 'N/A')}\n"
                f"Fonte: BrasilAPI (Receita Federal)"
            )
        except Exception as e:
            logger.error(f"Erro ao consultar CNPJ via BrasilAPI: {e}")
            return f"Erro ao consultar CNPJ (ambas as fontes falharam): ReceitaWS e BrasilAPI indisponíveis."

    def _get_holidays_brasilapi(self, year: str) -> str:
        """Feriados Nacionais via BrasilAPI"""
        import datetime

        if not year:
            year = str(datetime.datetime.now().year)

        try:
            url = f"https://brasilapi.com.br/api/feriados/v1/{year}"
            r = requests.get(url, timeout=5)
            r.raise_for_status()

            holidays = r.json()

            # Formata a lista de feriados
            list_str = "\n".join([
                f"- {h.get('date', 'N/A')}: {h.get('name', 'N/A')} ({h.get('type', 'N/A')})"
                for h in holidays[:15]  # Limita a 15 para não lotar
            ])

            return f"📅 **Feriados Nacionais de {year}:**\n{list_str}\nFonte: BrasilAPI"
        except Exception as e:
            logger.error(f"Erro ao consultar feriados: {e}")
            return f"Erro ao consultar feriados: {str(e)}"

    def _get_fipe_brands_brasilapi(self, vehicle_type: str) -> str:
        """Marcas de Veículos (Tabela FIPE) via BrasilAPI"""
        # vehicle_type pode ser: carros, motos, caminhoes
        if vehicle_type not in ["carros", "motos", "caminhoes"]:
            vehicle_type = "carros"

        try:
            url = f"https://brasilapi.com.br/api/fipe/marcas/v1/{vehicle_type}"
            r = requests.get(url, timeout=5)
            r.raise_for_status()

            brands = r.json()[:15]  # Top 15 marcas

            list_str = "\n".join([f"- {b.get('nome', 'N/A')}" for b in brands])

            tipo_veiculo = {"carros": "Carros", "motos": "Motos", "caminhoes": "Caminhões"}.get(vehicle_type, "Carros")

            return f"🚗 **Marcas de {tipo_veiculo} (Tabela FIPE - Top 15):**\n{list_str}\nFonte: BrasilAPI (FIPE)"
        except Exception as e:
            logger.error(f"Erro ao consultar FIPE: {e}")
            return f"Erro ao consultar Tabela FIPE: {str(e)}"

    # --- MÉTODOS IBGE (Localidades & Economia) ---

    def _get_ibge_uf_info(self, uf_code: str) -> str:
        """Busca detalhes de um Estado brasileiro (UF) pelo nome ou sigla"""
        if not uf_code:
            return "Por favor, forneça a sigla ou nome do estado (ex: 'SP', 'São Paulo')."

        url_base = "https://servicodados.ibge.gov.br/api/v1/localidades/estados/"

        try:
            # Lista todos os estados para encontrar o ID se necessário
            r_all = requests.get(url_base, timeout=5)
            r_all.raise_for_status()
            estados = r_all.json()

            target_uf = None

            # Tenta encontrar por sigla (ex: "SP") ou ID numérico
            uf_code_clean = str(uf_code).strip().upper()

            for est in estados:
                if est['sigla'] == uf_code_clean or str(est['id']) == uf_code_clean:
                    target_uf = est
                    break
                # Busca por nome (contém)
                if uf_code_clean in est['nome'].upper():
                    target_uf = est
                    break

            if target_uf:
                regiao = target_uf.get('regiao', {}).get('nome', 'N/A')
                sigla_regiao = target_uf.get('regiao', {}).get('sigla', 'N/A')
                return (
                    f"🏛️ **Estado: {target_uf['nome']} ({target_uf['sigla']})**\n"
                    f"🆔 IBGE ID: {target_uf['id']}\n"
                    f"🌎 Região: {regiao} ({sigla_regiao})\n"
                    f"Fonte: IBGE (Instituto Brasileiro de Geografia e Estatística)"
                )
            else:
                return f"Estado '{uf_code}' não encontrado no IBGE."

        except Exception as e:
            logger.error(f"Erro ao consultar IBGE UF: {e}")
            return f"Erro ao consultar IBGE: {str(e)}"

    def _get_ibge_city_info(self, city_name: str) -> str:
        """Busca informações básicas e ID IBGE de uma cidade/município"""
        if not city_name:
            return "Por favor, forneça o nome da cidade (ex: 'São Paulo', 'Vitória')."

        try:
            # Endpoint de busca de municípios
            url = f"https://servicodados.ibge.gov.br/api/v1/localidades/municipios?nome={city_name}"
            r = requests.get(url, timeout=5)
            r.raise_for_status()
            data = r.json()

            if not data:
                return f"Cidade '{city_name}' não encontrada no IBGE."

            # Se houver múltiplos resultados, mostra os primeiros 3
            if len(data) > 1:
                results = data[:3]
                list_str = "\n".join([
                    f"- {c['nome']} - {c['microrregiao']['mesorregiao']['UF']['sigla']} (ID: {c['id']})"
                    for c in results
                ])
                return (
                    f"🏙️ **Múltiplas cidades encontradas para '{city_name}':**\n{list_str}\n"
                    f"Fonte: IBGE"
                )

            # Pega o primeiro resultado
            city = data[0]
            nome = city['nome']
            uf_sigla = city['microrregiao']['mesorregiao']['UF']['sigla']
            uf_nome = city['microrregiao']['mesorregiao']['UF']['nome']
            ibge_id = city['id']
            microrregiao = city['microrregiao']['nome']
            mesorregiao = city['microrregiao']['mesorregiao']['nome']

            return (
                f"🏙️ **Município: {nome} - {uf_sigla}**\n"
                f"🆔 IBGE ID: {ibge_id}\n"
                f"🗺️ Estado: {uf_nome}\n"
                f"📍 Microrregião: {microrregiao}\n"
                f"📍 Mesorregião: {mesorregiao}\n"
                f"Fonte: IBGE (Instituto Brasileiro de Geografia e Estatística)"
            )
        except Exception as e:
            logger.error(f"Erro ao buscar cidade no IBGE: {e}")
            return f"Erro ao buscar cidade: {str(e)}"

    def _search_cnae(self, query_term: str) -> str:
        """Busca atividades econômicas na Classificação Nacional de Atividades Econômicas (CNAE)"""
        if not query_term:
            return "Por favor, forneça um termo de busca (ex: 'informática', 'restaurante', '6200')."

        try:
            # NOTA: A API do IBGE não possui busca textual funcional
            # Solução: Buscar todas as subclasses e filtrar localmente
            url = "https://servicodados.ibge.gov.br/api/v2/cnae/subclasses"
            r = requests.get(url, timeout=10)
            r.raise_for_status()
            data = r.json()

            if not data:
                return "Erro: API CNAE não retornou dados."

            # Filtrar resultados que contenham o termo de busca (case-insensitive)
            query_lower = query_term.lower()
            matches = []

            for item in data:
                codigo = item.get('id', '')
                descricao = item.get('descricao', '')

                # Buscar no código ou na descrição
                if query_lower in codigo.lower() or query_lower in descricao.lower():
                    matches.append({
                        'codigo': codigo,
                        'descricao': descricao
                    })

                # Limitar a 10 resultados para não sobrecarregar
                if len(matches) >= 10:
                    break

            if not matches:
                return f"Nenhuma atividade CNAE encontrada para '{query_term}'."

            # Formatar resultados (top 5)
            results = matches[:5]
            output_lines = [f"🔎 **Resultados CNAE para '{query_term}':**\n"]

            for item in results:
                codigo = item['codigo']
                descricao = item['descricao']
                output_lines.append(f"• **{codigo}**: {descricao}")

            output_lines.append(f"\n✅ Encontrados {len(matches)} resultados (mostrando top 5)")
            output_lines.append("Fonte: IBGE (Classificação Nacional de Atividades Econômicas)")
            return "\n".join(output_lines)

        except Exception as e:
            logger.error(f"Erro ao consultar CNAE: {e}")
            return f"Erro ao consultar CNAE: {str(e)}"

