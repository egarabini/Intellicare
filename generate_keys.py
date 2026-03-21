from py_vapid import Vapid
v = Vapid()
v.generate_keys()
with open("vapid_keys.txt", "w") as f:
    pub = getattr(v, "public_key_string", lambda: getattr(v, "public_key", b""))
    priv = getattr(v, "private_key_string", lambda: getattr(v, "private_key", b""))
    try:
        if callable(pub): pub = pub()
        if callable(priv): priv = priv()
        if isinstance(pub, bytes): pub = pub.decode('utf-8')
        if isinstance(priv, bytes): priv = priv.decode('utf-8')
    except Exception as e:
        pub = str(v.public_key)
        priv = str(v.private_key)
    f.write(f"VAPID_PUBLIC_KEY={pub}\n")
    f.write(f"VAPID_PRIVATE_KEY={priv}\n")
    f.write("VAPID_SUBJECT=mailto:admin@intellicare.ia.br\n")
