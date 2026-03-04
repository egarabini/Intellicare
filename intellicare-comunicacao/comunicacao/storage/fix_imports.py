import os

storage_dir = r"c:\Users\egara\INTELLICARE\intellicare-comunicacao\comunicacao\storage"
for fname in os.listdir(storage_dir):
    if fname.endswith(".py") and fname not in ("tenant_utils.py", "__init__.py", "refactor_storage.py", "fix_syntax.py"):
        filepath = os.path.join(storage_dir, fname)
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()

        issue_str = "from comunicacao.storage.tenant_utils import get_tenant_conn\n"
        if issue_str in content and "from __future__ import annotations" in content:
            # Check if it occurs before future
            if content.index(issue_str) < content.index("from __future__ import annotations"):
                # Remove it
                content = content.replace(issue_str, "")
                # Add it after future
                content = content.replace("from __future__ import annotations\n", "from __future__ import annotations\n" + issue_str)
                with open(filepath, "w", encoding="utf-8") as f:
                    f.write(content)
                print(f"Fixed imports {fname}")
