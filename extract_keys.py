import base64
from py_vapid import Vapid
import cryptography.hazmat.primitives.serialization as serialization

v = Vapid()
v.generate_keys()

# Get raw bytes for public and private
# ECPublicKey uncompressed format is \x04 + X + Y (65 bytes)
try:
    # try latest cryptography usage
    pub_bytes = v.public_key.public_bytes(
        encoding=serialization.Encoding.X962,
        format=serialization.PublicFormat.UncompressedPoint
    )
except Exception:
    pub_bytes = v.public_key.public_numbers().encode_point()

try:
    priv_bytes = v.private_key.private_numbers().private_value.to_bytes(32, byteorder='big')
except Exception:
    priv_bytes = v.private_key.private_numbers().private_value

pub_b64 = base64.urlsafe_b64encode(pub_bytes).decode('utf-8').rstrip('=')
priv_b64 = base64.urlsafe_b64encode(priv_bytes).decode('utf-8').rstrip('=')

with open('vapid_out.txt', 'w') as f:
    f.write(f"VAPID_PUBLIC_KEY={pub_b64}\n")
    f.write(f"VAPID_PRIVATE_KEY={priv_b64}\n")
    f.write("VAPID_SUBJECT=mailto:admin@intellicare.ia.br\n")
