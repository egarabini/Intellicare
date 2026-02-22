"""
Testes para Validadores Clínicos - Day 5.3

Cobre:
- Validação de coerência fisiológica (PA, hemograma, lipídios)
- Detecção de impossibilidades fisiológicas
- Detecção de inconsistências clínicas
- Validação integrada de paciente

Total: ~29 test cases
"""

import pytest
from src.oswaldo.services.validadores_service import (
    ValidadoresClinicosService,
    ValidacaoResult
)


class TestValidacaoPressaoArterial:
    """Testes de validação de PA - 4 casos"""

    def test_pa_coerente_normal(self):
        """PA normal e coerente deve passar com score máximo"""
        resultado = ValidadoresClinicosService.validar_pressao_arterial(
            pressao_sistolica=120,
            pressao_diastolica=80,
            idade_anos=45
        )
        assert resultado.valido is True
        assert len(resultado.erros) == 0
        assert resultado.score_coerencia >= 90

    def test_pa_sistolica_menor_diastolica(self):
        """PA sistólica < diastólica deve falhar"""
        resultado = ValidadoresClinicosService.validar_pressao_arterial(
            pressao_sistolica=70,
            pressao_diastolica=100,
            idade_anos=45
        )
        assert resultado.valido is False
        assert any("sistólica" in e.lower() for e in resultado.erros)

    def test_pa_fora_faixa_fisiologica(self):
        """PA fora de faixa fisiológica (>300 sistólica) deve falhar"""
        resultado = ValidadoresClinicosService.validar_pressao_arterial(
            pressao_sistolica=350,
            pressao_diastolica=220,
            idade_anos=45
        )
        assert resultado.valido is False
        assert any("faixa fisiológica" in e.lower() for e in resultado.erros)

    def test_pa_aumento_pulso_elevado(self):
        """PA com diferença de pulso muito elevada gera aviso"""
        resultado = ValidadoresClinicosService.validar_pressao_arterial(
            pressao_sistolica=180,
            pressao_diastolica=80,
            idade_anos=45
        )
        assert resultado.valido is True
        assert any("pulso" in a.lower() for a in resultado.avisos)


class TestValidacaoHemograma:
    """Testes de validação de hemograma - 5 casos"""

    def test_hemograma_coerente(self):
        """Hemograma com valores coerentes deve passar"""
        resultado = ValidadoresClinicosService.validar_hemograma(
            wbc_total=7.5,
            leucocitos_seg=60,
            linfocitos=30,
            monocitos=5,
            eosinofilos=4,
            basofilos=1,
            hematocrito=42,
            hemoglobina=14.0
        )
        assert resultado.valido is True
        assert len(resultado.erros) == 0

    def test_hemograma_linfocitos_negativo(self):
        """Linfócitos negativos devem falhar"""
        resultado = ValidadoresClinicosService.validar_hemograma(
            wbc_total=7.5,
            leucocitos_seg=60,
            linfocitos=-5,
            monocitos=5,
            eosinofilos=4,
            basofilos=1
        )
        assert resultado.valido is False
        assert any("negativo" in e.lower() for e in resultado.erros)

    def test_hemograma_linfocitos_acima_100(self):
        """Linfócitos > 100% devem falhar"""
        resultado = ValidadoresClinicosService.validar_hemograma(
            wbc_total=7.5,
            leucocitos_seg=60,
            linfocitos=105,
            monocitos=5,
            eosinofilos=4,
            basofilos=1
        )
        assert resultado.valido is False
        assert any("exceder 100%" in e.lower() for e in resultado.erros)

    def test_hemograma_soma_diferenciais_incorreta(self):
        """Soma de diferenciais != 100% gera aviso"""
        resultado = ValidadoresClinicosService.validar_hemograma(
            wbc_total=7.5,
            leucocitos_seg=60,
            linfocitos=25,
            monocitos=5,
            eosinofilos=4,
            basofilos=1
        )
        assert resultado.valido is True
        assert any("soma" in a.lower() for a in resultado.avisos)

    def test_hemograma_hgb_incoerente_hct(self):
        """Hemoglobina incoerente com hematócrito gera aviso"""
        resultado = ValidadoresClinicosService.validar_hemograma(
            wbc_total=7.5,
            hematocrito=42,
            hemoglobina=24.0  # Esperado ~14
        )
        assert resultado.valido is True
        assert any("inconsistent" in a.lower() for a in resultado.avisos)


class TestValidacaoLipidios:
    """Testes de validação de lipídios - 5 casos"""

    def test_lipidios_coerentes(self):
        """Lipídios coerentes e dentro de faixa"""
        resultado = ValidadoresClinicosService.validar_lipidios(
            colesterol_total=200,
            ldl=130,
            hdl=50,
            triglicerideos=100
        )
        assert resultado.valido is True
        assert len(resultado.erros) == 0

    def test_colesterol_total_fora_faixa(self):
        """CT > 1000 deve falhar"""
        resultado = ValidadoresClinicosService.validar_lipidios(
            colesterol_total=1200,
            ldl=700,
            hdl=400,
            triglicerideos=100
        )
        assert resultado.valido is False
        assert any("colesterol total" in e.lower() for e in resultado.erros)

    def test_ldl_maior_colesterol_total(self):
        """LDL + HDL > CT deve gerar aviso (Friedewald)"""
        resultado = ValidadoresClinicosService.validar_lipidios(
            colesterol_total=150,
            ldl=100,
            hdl=60,
            triglicerideos=100
        )
        assert resultado.valido is True
        assert any("friedewald" in a.lower() for a in resultado.avisos)

    def test_hdl_muito_baixo(self):
        """HDL < 30 gera aviso de risco CV"""
        resultado = ValidadoresClinicosService.validar_lipidios(
            colesterol_total=250,
            ldl=150,
            hdl=25,
            triglicerideos=200
        )
        assert resultado.valido is True
        assert any("muito baixo" in a.lower() for a in resultado.avisos)

    def test_triglicerideos_muito_elevados(self):
        """TG > 5000 deve falhar como impossível"""
        resultado = ValidadoresClinicosService.validar_lipidios(
            colesterol_total=500,
            ldl=200,
            hdl=50,
            triglicerideos=6000
        )
        assert resultado.valido is False
        assert any("5000" in e.lower() for e in resultado.erros)


class TestDeteccaoImpossibilidades:
    """Testes de detecção de impossibilidades - 6 casos"""

    def test_frequencia_cardiaca_muito_baixa(self):
        """FC < 20 deve ser impossível"""
        resultado = ValidadoresClinicosService.detectar_impossibilidades({
            "frequencia_cardiaca": 10
        })
        assert resultado.valido is False
        assert any("impossível" in e.lower() for e in resultado.erros)

    def test_frequencia_cardiaca_muito_alta(self):
        """FC > 300 deve ser impossível"""
        resultado = ValidadoresClinicosService.detectar_impossibilidades({
            "frequencia_cardiaca": 350
        })
        assert resultado.valido is False
        assert any("300" in e.lower() for e in resultado.erros)

    def test_temperatura_hipotermia_critica(self):
        """Temp < 35°C deve ser impossível (morte cerebral)"""
        resultado = ValidadoresClinicosService.detectar_impossibilidades({
            "temperatura_c": 32
        })
        assert resultado.valido is False
        assert any("hipotermia" in e.lower() for e in resultado.erros)

    def test_spo2_maior_100(self):
        """SpO2 > 100% deve ser impossível"""
        resultado = ValidadoresClinicosService.detectar_impossibilidades({
            "spo2_perc": 105
        })
        assert resultado.valido is False
        assert any("100" in e.lower() for e in resultado.erros)

    def test_spo2_muito_baixo(self):
        """SpO2 < 50% deve ser possível mas crítico"""
        resultado = ValidadoresClinicosService.detectar_impossibilidades({
            "spo2_perc": 40
        })
        assert resultado.valido is False
        assert any("incompatível" in e.lower() for e in resultado.erros)

    def test_peso_negativo(self):
        """Peso negativo deve falhar"""
        resultado = ValidadoresClinicosService.detectar_impossibilidades({
            "peso_kg": -75
        })
        assert resultado.valido is False
        assert any("não pode ser negativo" in e.lower() for e in resultado.erros)


class TestDeteccaoInconsistencias:
    """Testes de detecção de inconsistências clínicas - 5 casos"""

    def test_has_normal_com_multiplos_anti_hipertensivos(self):
        """HAS NORMAL mas em 3+ anti-HTA gera aviso"""
        resultado = ValidadoresClinicosService.detectar_inconsistencias_clinicas(
            classificacoes={"HAS": "NORMAL"},
            medicamentos_ativos=[
                "Losartan 50mg",
                "Enalapril 10mg",
                "Nifedipina 30mg"
            ],
            laboratorio={"pa_sistolica": 120}
        )
        assert resultado.valido is True
        assert any("anti-hipertensivos" in a.lower() for a in resultado.avisos)

    def test_creatinina_elevada_com_gfr_normal(self):
        """Creatinina > 3 mas GFR G1/G2 gera aviso"""
        resultado = ValidadoresClinicosService.detectar_inconsistencias_clinicas(
            classificacoes={"DRC": "G1"},
            medicamentos_ativos=[],
            laboratorio={"creatinina": 3.5}
        )
        assert resultado.valido is True
        assert any("creatinina" in a.lower() for a in resultado.avisos)

    def test_hdl_baixo_sem_estatina(self):
        """HDL < 30 com dislipidemia e sem estatina gera sugestão"""
        resultado = ValidadoresClinicosService.detectar_inconsistencias_clinicas(
            classificacoes={"LIPIDIO": "MUITO_ELEVADA"},
            medicamentos_ativos=["Losartan 50mg"],
            laboratorio={"hdl": 25}
        )
        assert resultado.valido is True
        assert any("estatina" in s.lower() for s in resultado.sugestoes)

    def test_diabetes_critica_sem_insulina(self):
        """HbA1c > 9 (CRITICA) sem insulina gera sugestão"""
        resultado = ValidadoresClinicosService.detectar_inconsistencias_clinicas(
            classificacoes={"DIABETES": "CRITICO"},
            medicamentos_ativos=["Metformina 1000mg"],
            laboratorio={"hba1c": 9.5}
        )
        assert resultado.valido is True
        assert any("insulina" in s.lower() for s in resultado.sugestoes)

    def test_ic_severa_sem_ieca(self):
        """IC SEVERA sem IECA/ARA2 gera sugestão"""
        resultado = ValidadoresClinicosService.detectar_inconsistencias_clinicas(
            classificacoes={"IC": "SEVERA"},
            medicamentos_ativos=["Furosemida 40mg", "Digoxina 0.5mg"],
            laboratorio={}
        )
        assert resultado.valido is True
        assert any("ieca" in s.lower() or "ara" in s.lower() for s in resultado.sugestoes)


class TestValidacaoIntegrada:
    """Testes de validação integrada de paciente - 4 casos"""

    def test_paciente_saudavel_sem_problemas(self):
        """Paciente saudável com todos os parâmetros normais"""
        resultado = ValidadoresClinicosService.validar_paciente_completo(
            dados_vitais={
                "pressao_sistolica": 120,
                "pressao_diastolica": 80,
                "frequencia_cardiaca": 72,
                "temperatura_c": 36.8,
                "spo2_perc": 98
            },
            laboratorio={
                "colesterol_total": 180,
                "ldl": 110,
                "hdl": 50,
                "triglicerideos": 100,
                "glicemia": 95,
                "creatinina": 0.9,
                "wbc_total": 7.0,
                "hemoglobina": 14.0,
                "hematocrito": 42
            },
            classificacoes={"HAS": "NORMAL", "DRC": "G1", "DIABETES": "CONTROLADO"},
            medicamentos_ativos=[],
            idade_anos=45
        )
        assert resultado.valido is True
        assert len(resultado.erros) == 0
        assert resultado.score_coerencia >= 90

    def test_paciente_hipertenso_com_inconsistencias(self):
        """Paciente com HAS mal controlada e inconsistências"""
        resultado = ValidadoresClinicosService.validar_paciente_completo(
            dados_vitais={
                "pressao_sistolica": 160,
                "pressao_diastolica": 100,
                "frequencia_cardiaca": 85,
                "temperatura_c": 36.5,
                "spo2_perc": 96
            },
            laboratorio={
                "colesterol_total": 200,
                "ldl": 130,
                "hdl": 25,  # < 30 para triggerar inconsistência
                "triglicerideos": 150,
                "glicemia": 110,
                "creatinina": 1.2
            },
            classificacoes={"HAS": "ESTAGIO_2", "DRC": "G2", "LIPIDIO": "ELEVADA"},
            medicamentos_ativos=["Losartan 50mg"],  # Sem estatina
            idade_anos=60
        )
        assert resultado.valido is True
        # HDL muito baixo com dislipidemia deve gerar sugestão
        assert len(resultado.sugestoes) >= 1

    def test_paciente_com_impossibilidades(self):
        """Paciente com valores impossíveis deve falhar validação"""
        resultado = ValidadoresClinicosService.validar_paciente_completo(
            dados_vitais={
                "pressao_sistolica": 250,
                "pressao_diastolica": 160,
                "frequencia_cardiaca": 15,  # Impossível
                "temperatura_c": 32,  # Impossível
                "spo2_perc": 105  # Impossível
            },
            laboratorio={
                "glicemia": 500,
                "creatinina": 5.0
            },
            classificacoes={"DRC": "G5"},
            medicamentos_ativos=[],
            idade_anos=70
        )
        assert resultado.valido is False
        assert len(resultado.erros) >= 3  # Múltiplas impossibilidades

    def test_paciente_idoso_com_anomalias_esperadas(self):
        """Paciente idoso com alguns parâmetros esperados de idade"""
        resultado = ValidadoresClinicosService.validar_paciente_completo(
            dados_vitais={
                "pressao_sistolica": 145,
                "pressao_diastolica": 75,  # SPA isolada
                "frequencia_cardiaca": 68,
                "temperatura_c": 36.5,
                "spo2_perc": 96
            },
            laboratorio={
                "colesterol_total": 220,
                "ldl": 140,
                "hdl": 45,
                "triglicerideos": 180,
                "creatinina": 1.3,
                "hemoglobina": 12.5,
                "hematocrito": 38
            },
            classificacoes={"HAS": "ESTAGIO_2", "DRC": "G2"},
            medicamentos_ativos=["Losartan 50mg"],
            idade_anos=78
        )
        assert resultado.valido is True
        assert resultado.score_coerencia >= 70


class TestEdgeCases:
    """Testes de casos extremos e edge cases - 3 casos"""

    def test_parametros_vazio(self):
        """Validação com parâmetros vazios ou nulos"""
        resultado = ValidadoresClinicosService.detectar_impossibilidades({})
        assert resultado.valido is True
        assert len(resultado.erros) == 0

    def test_valores_limites_fisiologicos(self):
        """Valores nos limites extremos da faixa fisiológica"""
        resultado = ValidadoresClinicosService.validar_pressao_arterial(
            pressao_sistolica=50,  # Limite inferior
            pressao_diastolica=30,  # Limite inferior
            idade_anos=90
        )
        assert resultado.valido is True or len(resultado.erros) <= 1

    def test_multiplos_erros_acumulados(self):
        """Validação com múltiplos erros simultaneamente"""
        resultado = ValidadoresClinicosService.validar_paciente_completo(
            dados_vitais={
                "pressao_sistolica": 70,
                "pressao_diastolica": 120,  # Invertida
                "frequencia_cardiaca": 350,  # Impossível
                "temperatura_c": 28,  # Impossível
                "spo2_perc": 110  # Impossível
            },
            laboratorio={
                "peso_kg": -80,  # Negativo
                "wbc_total": -5,  # Negativo
                "linfocitos": 200  # >100%
            },
            classificacoes={},
            medicamentos_ativos=[],
            idade_anos=45
        )
        assert resultado.valido is False
        assert len(resultado.erros) >= 5  # Múltiplos erros críticos


# ========================================================================
# TESTES DE INTEGRAÇÃO
# ========================================================================

class TestIntegracaoComClassificadorService:
    """Testes de integração com ClassificadorService - 2 casos"""

    def test_fluxo_exame_classificacao_validacao(self):
        """E2E: Exame → Classificação → Validação"""
        # Simular exame com parâmetros
        parametros_laboratorio = {
            "pressao_sistolica": 160,
            "pressao_diastolica": 100,
            "glicemia_jejum": 150,
            "creatinina": 1.5,
            "colesterol_total": 250,
            "ldl": 160,
            "hdl": 35,
            "triglicerideos": 200
        }

        # Validar se parâmetros estão coerentes ANTES da classificação
        resultado = ValidadoresClinicosService.validar_pressao_arterial(
            parametros_laboratorio["pressao_sistolica"],
            parametros_laboratorio["pressao_diastolica"]
        )
        assert resultado.valido is True

    def test_validacao_pre_diagnostico(self):
        """Validação antes de interpretar diagnóstico"""
        # Dados com impossibilidades
        dados_problema = {
            "frequencia_cardiaca": 25,  # Baixa mas não impossível
            "temperatura_c": 36.5,
            "spo2_perc": 95,
            "glicemia": 450,
            "hba1c": 12
        }

        resultado = ValidadoresClinicosService.detectar_impossibilidades(dados_problema)
        assert resultado.valido is True  # FC=25 é baixo mas pode ocorrer em atletas


# ========================================================================
# MÉTRICAS E COBERTURA
# ========================================================================

if __name__ == "__main__":
    # Executar: python -m pytest tests/test_day5_validadores.py -v --tb=short
    # Esperado: 29/29 passing
    print("Teste de Validadores Clínicos - Day 5.3")
    print("Suites:")
    print("  1. TestValidacaoPressaoArterial (4 testes)")
    print("  2. TestValidacaoHemograma (5 testes)")
    print("  3. TestValidacaoLipidios (5 testes)")
    print("  4. TestDeteccaoImpossibilidades (6 testes)")
    print("  5. TestDeteccaoInconsistencias (5 testes)")
    print("  6. TestValidacaoIntegrada (4 testes)")
    print("  7. TestEdgeCases (3 testes)")
    print("  8. TestIntegracaoComClassificadorService (2 testes)")
    print("-" * 60)
    print("TOTAL: 29 testes")
