from py_vapid import Vapid
v = Vapid()
v.generate_keys()
with open("vapid_out.txt", "w") as f:
    f.write(str(dir(v)))
