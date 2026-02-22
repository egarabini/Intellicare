import os
import json
import glob

def fix_json_unicode(path):
    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=True, indent=2)
    print(f"Corrigido: {path}")

if __name__ == "__main__":
    base = os.path.join(os.path.dirname(__file__), '..', 'comunicacao', 'dashboards')
    for file in glob.glob(os.path.join(base, '*.json')):
        try:
            fix_json_unicode(file)
        except Exception as e:
            print(f"Erro ao processar {file}: {e}")
