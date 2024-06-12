# encryption decryption
from cryptography.fernet import Fernet
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import base64
from flask import current_app

# Encrypting and Decrypting the cookie
# Error handling req for invalid alue of cookie
def generate_fernet_key_from_value(value):
    # Convert the value to bytes
    value_bytes = value.encode()

    # Derive a key using PBKDF2HMAC
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=current_app.config['SECRET_KEY'].encode(),  # Use a random and unique salt for better security
        iterations=1000,  # Adjust the number of iterations based on your security requirements
        backend=default_backend()
    )
    key = base64.urlsafe_b64encode(kdf.derive(value_bytes))
    return key


def encrypt_fernet(data, key):
    try:
        fernet_key = generate_fernet_key_from_value(key)
        fernet = Fernet(fernet_key)
        ciphertext = fernet.encrypt(data.encode())
        return ciphertext
    except Exception as e:
        print("Encryption error : ",e)
        return None


def decrypt_fernet(ciphertext, key):
    try:
        fernet_key = generate_fernet_key_from_value(key)
        fernet = Fernet(fernet_key)
        plaintext = fernet.decrypt(ciphertext).decode()
        return plaintext
    except Exception as e:
        print("Decryption error : ",e)
        return None
