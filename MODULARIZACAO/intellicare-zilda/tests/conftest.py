"""Fixtures compartilhadas para testes do Zilda."""

import pytest

from zilda.engine.cache import SimpleCache
from zilda.engine.cnes_client import CnesClient
from zilda.engine.territorial import TerritorialEngine


CNES_BASE_URL = "https://apidadosabertos.saude.gov.br"

# --- Dados fake para testes ---

FAKE_UNIT_TYPES = [
    {"codigo_tipo_unidade": 1, "descricao_tipo_unidade": "POSTO DE SAUDE"},
    {"codigo_tipo_unidade": 5, "descricao_tipo_unidade": "HOSPITAL GERAL"},
    {"codigo_tipo_unidade": 36, "descricao_tipo_unidade": "CLINICA ESPECIALIZADA"},
]

FAKE_ESTABLISHMENT = {
    "codigo_cnes": "2077485",
    "cnpj": "12345678000199",
    "nome_razao_social": "Hospital Municipal de Exemplo",
    "nome_fantasia": "Hospital Exemplo",
    "codigo_tipo_unidade": 5,
    "descricao_tipo_unidade": "HOSPITAL GERAL",
    "codigo_uf": "35",
    "codigo_municipio": "3550308",
    "nome_municipio": "SAO PAULO",
    "endereco_estabelecimento": "Rua Exemplo 123",
    "bairro_estabelecimento": "Centro",
    "numero_telefone_estabelecimento": "1133334444",
    "latitude_estabelecimento_decimo_grau": "-23.5505",
    "longitude_estabelecimento_decimo_grau": "-46.6333",
    "estabelecimento_possui_centro_cirurgico": 1,
    "estabelecimento_possui_centro_obstetrico": 1,
    "estabelecimento_possui_centro_neonatal": 0,
    "codigo_motivo_desabilitacao": None,
}

FAKE_ESTABLISHMENT_2 = {
    "codigo_cnes": "3033112",
    "cnpj": None,
    "nome_razao_social": "UBS Vila Nova",
    "nome_fantasia": "UBS Vila Nova",
    "codigo_tipo_unidade": 1,
    "descricao_tipo_unidade": "POSTO DE SAUDE",
    "codigo_uf": "35",
    "codigo_municipio": "3550308",
    "nome_municipio": "SAO PAULO",
    "endereco_estabelecimento": "Av. Saude 456",
    "bairro_estabelecimento": "Vila Nova",
    "numero_telefone_estabelecimento": None,
    "latitude_estabelecimento_decimo_grau": None,
    "longitude_estabelecimento_decimo_grau": None,
    "estabelecimento_possui_centro_cirurgico": 0,
    "estabelecimento_possui_centro_obstetrico": 0,
    "estabelecimento_possui_centro_neonatal": 0,
    "codigo_motivo_desabilitacao": None,
}

FAKE_REGION = {
    "codigo_municipio": "3550308",
    "nome_municipio": "SAO PAULO",
    "codigo_uf": "35",
    "nome_uf": "SAO PAULO",
    "codigo_regiao_saude": "35001",
    "nome_regiao_saude": "Grande Sao Paulo",
    "codigo_macrorregiao_saude": "35000",
    "nome_macrorregiao_saude": "Macro Sao Paulo",
    "populacao_ibge_2022": 12325232,
}

FAKE_REGION_2 = {
    "codigo_municipio": "3509502",
    "nome_municipio": "CAMPINAS",
    "codigo_uf": "35",
    "nome_uf": "SAO PAULO",
    "codigo_regiao_saude": "35002",
    "nome_regiao_saude": "Campinas",
    "codigo_macrorregiao_saude": "35000",
    "nome_macrorregiao_saude": "Macro Sao Paulo",
    "populacao_ibge_2022": 1213792,
}


@pytest.fixture
def cache() -> SimpleCache:
    return SimpleCache()


@pytest.fixture
def cnes_client() -> CnesClient:
    return CnesClient(base_url=CNES_BASE_URL, timeout=5)
