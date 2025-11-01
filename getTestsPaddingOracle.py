import base64
import json
import os
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad


def generate_ciphertext(plaintext, key, iv):
    cipher=AES.new(key, AES.MODE_CBC, iv)
    padded_plaintext=pad(plaintext, 16)
    ciphertext=cipher.encrypt(padded_plaintext)
    return ciphertext, padded_plaintext

key1=bytes.fromhex('0123456789abcdef0123456789abcdef')


iv1=bytes.fromhex('771f4f06ceefe184b270e4db4e7a7c41')
iv2=bytes.fromhex('a1b2c3d4e5f6071829384756a1b2c3d4')
iv3=bytes.fromhex('11223344556677889900aabbccddeeff')


plaintext1=b"Tt long lw"
plaintext2=b"Hello Worrrrrrrrr test test test"
plaintext3=b"Short mmm"

ciphertext1, padded_plaintext1= generate_ciphertext(plaintext1, key1, iv1)
ciphertext2, padded_plaintext2= generate_ciphertext(plaintext2, key1, iv2)
ciphertext3, padded_plaintext3= generate_ciphertext(plaintext3, key1, iv3)

print(f"ciphertext1: {base64.b64encode(ciphertext1).decode('ascii')}")
print(f"ciphertext2: {base64.b64encode(ciphertext2).decode('ascii')}")
print(f"ciphertext3: {base64.b64encode(ciphertext3).decode('ascii')}")

print(f"iv1: {base64.b64encode(iv1).decode('ascii')}")
print(f"iv2: {base64.b64encode(iv2).decode('ascii')}")
print(f"iv3: {base64.b64encode(iv3).decode('ascii')}")




print(f"padded_plaintext1: {base64.b64encode(padded_plaintext1).decode('ascii')}")
print(f"padded_plaintext2: {base64.b64encode(padded_plaintext2).decode('ascii')}")
print(f"padded_plaintext3: {base64.b64encode(padded_plaintext3).decode('ascii')}")

doc = {
  "title": "Action: padding_oracle",
  "description": "Tests for testing the padding_oracle action. As well as some current invalid actions.",
  "testcases": {
    "test1": {
      "action": "padding_oracle",
      "arguments": {
        "hostname": "localhost",
        "port": 18652,
        "key_id": 1324,
        "iv": base64.b64encode(iv1).decode("ascii"),
        "ciphertext": base64.b64encode(ciphertext1).decode("ascii")
      }
    },
    "test2": {
      "action": "padding_oracle",
      "arguments": {
        "hostname": "localhost",
        "port": 18652,
        "key_id": 1234,
        "iv": base64.b64encode(iv2).decode("ascii"),
        "ciphertext": base64.b64encode(ciphertext2).decode("ascii")
      }
    },
    "test3": {
      "action": "padding_oracle",
      "arguments": {
        "hostname": "localhost",
        "port": 18652,
        "key_id": 1111,
        "iv": base64.b64encode(iv3).decode("ascii"),
        "ciphertext": base64.b64encode(ciphertext3).decode("ascii")
      }
    }
  },
  "expectedResults": {
    "test1": { "plaintext": base64.b64encode(padded_plaintext1).decode("ascii") },
    "test2": { "plaintext": base64.b64encode(padded_plaintext2).decode("ascii") },
    "test3": { "plaintext": base64.b64encode(padded_plaintext3).decode("ascii") }
  }
}


out_path = "tests/paddingOracle.json"
os.makedirs(os.path.dirname(out_path), exist_ok=True)
try:
    os.remove(out_path)
except:
    pass

with open(out_path, "w", encoding="utf-8") as f:
    json.dump(doc, f, indent=2)
