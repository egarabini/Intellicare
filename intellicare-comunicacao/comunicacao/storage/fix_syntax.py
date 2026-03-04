import os

storage_dir = r"c:\Users\egara\INTELLICARE\intellicare-comunicacao\comunicacao\storage"
for fname in os.listdir(storage_dir):
    if fname.endswith(".py"):
        filepath = os.path.join(storage_dir, fname)
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()
            
        new_content = content.replace(r"(", "(").replace(r")", ")").replace(r"|", "|").replace(r"[", "[").replace(r"]", "]").replace(r",", ",")
        
        if new_content != content:
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(new_content)
            print(f"Fixed {fname}")
