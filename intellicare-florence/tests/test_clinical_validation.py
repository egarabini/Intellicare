"""
Tests for Clinical Algorithm Validation

Testa validadores clínicos para coerência de exames
"""

import pytest
from florence.services.clinical_validation import ClinicaAlgorithmValidator


class TestHemogramaValidation:
    """Testes de validação do hemograma"""
    
    def test_hemograma_valido(self):
        """Hemograma com valores normais passa validação"""
        
        valido, msg = ClinicaAlgorithmValidator.validar_hemograma(
            hemoglobina=14.5,
            hematocrito=43.0,
            plaquetas=250.0,
            leucócitos=7.0,
            diferenciais={
                "neutrófilos": 60,
                "linfócitos": 30,
                "monócitos": 7,
                "eosinófilos": 2,
                "basófilos": 1,
            },
            sexo="M"
        )
        
        assert valido is True
        assert "✅" in msg
    
    def test_hemograma_incoerencia_hb_ht(self):
        """Hemograma com incoerência Hb/Ht é rejeitado"""
        
        valido, msg = ClinicaAlgorithmValidator.validar_hemograma(
            hemoglobina=14.5,
            hematocrito=20.0,  # Deveria ser ~43.5 (14.5 × 3)
            plaquetas=250.0,
            leucócitos=7.0,
            diferenciais={
                "neutrófilos": 60,
                "linfócitos": 30,
                "monócitos": 7,
                "eosinófilos": 2,
                "basófilos": 1,
            },
            sexo="M"
        )
        
        assert valido is False
        assert "Proporção Hb/Ht" in msg
    
    def test_hemograma_diferencial_invalido(self):
        """Diferencial leucocitário que não soma 100% é rejeitado"""
        
        valido, msg = ClinicaAlgorithmValidator.validar_hemograma(
            hemoglobina=14.5,
            hematocrito=43.0,
            plaquetas=250.0,
            leucócitos=7.0,
            diferenciais={
                "neutrófilos": 60,
                "linfócitos": 30,
                "monócitos": 5,  # Falta 5%
            },
            sexo="M"
        )
        
        assert valido is False
        assert "soma" in msg.lower()


class TestLipidogramaValidation:
    """Testes de validação do lipidograma"""
    
    def test_lipidograma_valido(self):
        """Lipidograma válido passa validação"""
        
        # Valores que atendem Friedewald: LDL = 200 - 50 - (100/5) = 130
        valido, msg = ClinicaAlgorithmValidator.validar_lipidograma(
            colesterol_total=200,
            triglicérides=100,
            hdl=50,
            ldl=130
        )
        
        assert valido is True
    
    def test_lipidograma_friedewald_incoerencia(self):
        """LDL incoerente com Friedewald é rejeitado"""
        
        # LDL deveria ser ~130, mas passamos 150
        valido, msg = ClinicaAlgorithmValidator.validar_lipidograma(
            colesterol_total=200,
            triglicérides=100,
            hdl=50,
            ldl=150  # Incorreto: não corresponde a Friedewald
        )
        
        assert valido is False
        assert "Friedewald" in msg


class TestHepatogramaValidation:
    """Testes de validação do hepatograma"""
    
    def test_hepatograma_valido(self):
        """Hepatograma com valores normais passa"""
        
        valido, msg = ClinicaAlgorithmValidator.validar_hepatograma(
            ast=25.0,
            alt=20.0,
            bilirrubina_total=0.8,
            bilirrubina_direta=0.2,
            fosfatase_alcalina=70.0
        )
        
        assert valido is True
    
    def test_hepatograma_bilirrubina_incoerencia(self):
        """Bilirrubina direta > total é rejeitada"""
        
        valido, msg = ClinicaAlgorithmValidator.validar_hepatograma(
            ast=25.0,
            alt=20.0,
            bilirrubina_total=0.8,
            bilirrubina_direta=1.0,  # > total (incoerente)
            fosfatase_alcalina=70.0
        )
        
        assert valido is False
        assert "direta" in msg.lower()


class TestFuncaoRenalValidation:
    """Testes de validação de função renal"""
    
    def test_funcao_renal_valida(self):
        """Função renal normal passa validação"""
        
        valido, msg = ClinicaAlgorithmValidator.validar_funcao_renal(
            creatinina=1.0,
            ureia=15.0,
            idade=50
        )
        
        assert valido is True
    
    def test_funcao_renal_insuficiencia_pre_renal(self):
        """Razão ureia/creatinina > 20 sugere pré-renal"""
        
        valido, msg = ClinicaAlgorithmValidator.validar_funcao_renal(
            creatinina=0.8,
            ureia=20.0,  # Razão = 25 (> 20)
            idade=50
        )
        
        assert valido is False
        assert "pré-renal" in msg.lower()


class TestGlicemiaValidation:
    """Testes de validação de glicemia"""
    
    def test_glicemia_jejum_normal(self):
        """Glicemia em jejum normal passa"""
        
        valido, msg = ClinicaAlgorithmValidator.validar_glicemia(
            glicemia=85.0,
            tipo_amostra="jejum",
            paciente_diabetico=False
        )
        
        assert valido is True
    
    def test_glicemia_jejum_impaired(self):
        """Glicemia em jejum alterada é alertada"""
        
        valido, msg = ClinicaAlgorithmValidator.validar_glicemia(
            glicemia=110.0,
            tipo_amostra="jejum",
            paciente_diabetico=False
        )
        
        assert valido is False
        assert "diabete" in msg.lower()
    
    def test_glicemia_critica(self):
        """Glicemia crítica (>200 aleatória) é rejeitada"""
        
        valido, msg = ClinicaAlgorithmValidator.validar_glicemia(
            glicemia=350.0,
            tipo_amostra="aleatorio",
            paciente_diabetico=False
        )
        
        assert valido is False
        assert "crítica" in msg.lower() or "200" in msg


class TestExameCompleto:
    """Testes de validação de exame completo"""
    
    def test_exame_completo_valido(self):
        """Exame completo com todos os valores válidos"""
        
        exame_data = {
            # Hemograma
            "hemoglobina": 14.5,
            "hematocrito": 43.0,
            "plaquetas": 250.0,
            "leucócitos": 7.0,
            "diferenciais": {
                "neutrófilos": 60,
                "linfócitos": 30,
                "monócitos": 7,
                "eosinófilos": 2,
                "basófilos": 1,
            },
            # Lipidograma
            "colesterol_total": 200,
            "triglicérides": 100,
            "hdl": 50,
            "ldl": 130,
            # Hepatograma
            "ast": 25.0,
            "alt": 20.0,
            "bilirrubina_total": 0.8,
            "bilirrubina_direta": 0.2,
            "fosfatase_alcalina": 70.0,
            # Função renal
            "creatinina": 1.0,
            "ureia": 15.0,
            # Glicemia
            "glicemia": 85.0,
            "tipo_amostra": "jejum",
            "idade": 50,
        }
        
        valido, resultado = ClinicaAlgorithmValidator.validar_exame_completo(
            exame_data,
            sexo="M"
        )
        
        assert valido is True
        assert resultado["válido"] is True
        assert len(resultado["erros"]) == 0
    
    def test_exame_com_multiplos_erros(self):
        """Exame com múltiplos erros é detectado"""
        
        exame_data = {
            "hemoglobina": 14.5,
            "hematocrito": 20.0,  # Incoerente com Hb
            "plaquetas": 250.0,
            "leucócitos": 7.0,
            "diferenciais": {
                "neutrófilos": 60,
                "linfócitos": 30,
            },  # Soma <100%
            "colesterol_total": 200,
            "triglicérides": 100,
            "hdl": 50,
            "ldl": 150,  # Incoerente com Friedewald
            "creatinina": 1.0,
            "ureia": 30.0,  # Razão > 20
        }
        
        valido, resultado = ClinicaAlgorithmValidator.validar_exame_completo(
            exame_data,
            sexo="M"
        )
        
        assert valido is False
        assert len(resultado["erros"]) >= 3


# ============================================================================
# Demo/Manual Tests
# ============================================================================

def demo_validacao_clinica():
    """Demonstração de validação clínica"""
    print("\n" + "="*70)
    print("DEMONSTRAÇÃO: VALIDAÇÃO CLÍNICA DE EXAMES")
    print("="*70)
    
    # Exemplo 1: Hemograma incoerente
    print("\n📋 TESTE 1: Hemograma com incoerência Hb/Ht")
    valido, msg = ClinicaAlgorithmValidator.validar_hemograma(
        hemoglobina=14.5,
        hematocrito=20.0,  # Deveria ser 43.5
        plaquetas=250.0,
        leucócitos=7.0,
        diferenciais={
            "neutrófilos": 60,
            "linfócitos": 30,
            "monócitos": 7,
            "eosinófilos": 2,
            "basófilos": 1,
        },
    )
    print(f"   Válido: {valido}")
    print(f"   Mensagem: {msg}")
    
    # Exemplo 2: Lipidograma incoerente com Friedewald
    print("\n📋 TESTE 2: Lipidograma com incoerência de Friedewald")
    valido, msg = ClinicaAlgorithmValidator.validar_lipidograma(
        colesterol_total=200,
        triglicérides=100,
        hdl=50,
        ldl=150,  # Deveria ser 130
    )
    print(f"   Válido: {valido}")
    print(f"   Mensagem: {msg}")
    
    # Exemplo 3: Função renal com suspeita de pré-renal
    print("\n📋 TESTE 3: Função renal com razão ureia/creatinina > 20")
    valido, msg = ClinicaAlgorithmValidator.validar_funcao_renal(
        creatinina=0.8,
        ureia=20.0,  # Razão = 25
    )
    print(f"   Válido: {valido}")
    print(f"   Mensagem: {msg}")
    
    # Exemplo 4: Exame completo válido
    print("\n📋 TESTE 4: Exame Completo Válido")
    exame_valido = {
        "hemoglobina": 14.5,
        "hematocrito": 43.5,
        "plaquetas": 250.0,
        "leucócitos": 7.0,
        "diferenciais": {"neutrófilos": 60, "linfócitos": 30, "monócitos": 7, 
                        "eosinófilos": 2, "basófilos": 1},
        "colesterol_total": 200,
        "triglicérides": 100,
        "hdl": 50,
        "ldl": 130,
        "ast": 25.0,
        "alt": 20.0,
        "bilirrubina_total": 0.8,
        "bilirrubina_direta": 0.2,
        "glicemia": 85.0,
    }
    
    valido, resultado = ClinicaAlgorithmValidator.validar_exame_completo(
        exame_valido,
        sexo="M"
    )
    
    print(f"   Válido: {resultado['válido']}")
    print(f"   Validações: {len(resultado['validações'])}")
    for teste, resultado_teste in resultado['validações'].items():
        print(f"      • {teste}: {resultado_teste}")
    
    print("\n" + "="*70 + "\n")


if __name__ == "__main__":
    demo_validacao_clinica()
