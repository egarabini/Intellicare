import docx
doc = docx.Document(r'C:\Users\egara\INTELLICARE\docs\IMPLEMENTACAO_MODULAR\CORE_ACCESS_POLICIES\20260305-1200_W2B_ACCESS_POLICIES_ESPECIFICACAO_COMPLETA.docx')

with open(r'C:\Users\egara\INTELLICARE\docs_w2b_spec.txt', 'w', encoding='utf-8') as f:
    for p in doc.paragraphs:
        f.write(p.text + '\n')
