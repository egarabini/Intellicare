import re

def validate_cnpj_digits(cnpj: str) -> bool:
    """Valida os dígitos verificadores de um CNPJ."""
    cnpj = re.sub(r'[^0-9]', '', cnpj)
    
    if len(cnpj) != 14:
        return False
        
    if cnpj == cnpj[0] * 14:
        return False

    def calculate_digit(cnpj, multipliers):
        soma = 0
        for i, digit in enumerate(cnpj):
            soma += int(digit) * multipliers[i]
        resto = soma % 11
        return 0 if resto < 2 else 11 - resto

    multipliers_1 = [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
    digit_1 = calculate_digit(cnpj[:12], multipliers_1)
    if int(cnpj[12]) != digit_1:
         return False

    multipliers_2 = [6, 5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
    digit_2 = calculate_digit(cnpj[:13], multipliers_2)
    if int(cnpj[13]) != digit_2:
        return False

    return True

def format_cnpj(cnpj: str) -> str:
    if not cnpj:
        return ""
    cnpj = re.sub(r'[^0-9]', '', cnpj)
    if len(cnpj) != 14:
        return cnpj
    return f"{cnpj[:2]}.{cnpj[2:5]}.{cnpj[5:8]}/{cnpj[8:12]}-{cnpj[12:]}"
