import os
import base64
from cryptography.fernet import Fernet, InvalidToken # <-- CORRECCIÓN AQUÍ
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.backends import default_backend

# Este es el "cerebro" de la criptografía, siguiendo la lógica de respuesta.txt

def derive_key(password: str, salt: bytes) -> bytes:
    """
    Deriva una llave de 32 bytes (para Fernet) a partir de una contraseña y un salt.
    """
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=480000, # Iteraciones altas para mayor seguridad
        backend=default_backend()
    )
    # Codificamos la contraseña a bytes antes de derivar
    return base64.urlsafe_b64encode(kdf.derive(password.encode()))

def generate_vault_key(password: str) -> bytes:
    """
    Genera una nueva 'llave_fernet' y la cifra con una llave derivada de la contraseña.
    
    Retorna:
        bytes: El contenido completo del archivo 'vault.key' (salt + llave_cifrada).
    """
    # 1. Generar la llave real (Fernet)
    llave_fernet = Fernet.generate_key()

    # 2. Generar un salt nuevo
    salt = os.urandom(16)

    # 3. Derivar la "llave de encapsulación" desde la contraseña
    llave_para_cifrar = derive_key(password, salt)

    # 4. Cifrar la 'llave_fernet'
    f = Fernet(llave_para_cifrar)
    llave_fernet_cifrada = f.encrypt(llave_fernet)

    # 5. Retornar el contenido combinado (salt + llave_cifrada)
    # Guardamos el salt al inicio para saber cómo descifrarlo después
    return salt + llave_fernet_cifrada

def unlock_vault_key(password: str, vault_key_content: bytes) -> Fernet:
    """
    Intenta desbloquear el contenido de 'vault.key' usando la contraseña.
    
    Retorna:
        Fernet: Un objeto Fernet inicializado con la 'llave_fernet' descifrada.
    
    Lanza:
        ValueError: Si la contraseña es incorrecta (InvalidToken).
    """
    try:
        # 1. Extraer el salt y la llave cifrada
        salt = vault_key_content[:16]
        llave_fernet_cifrada = vault_key_content[16:]

        # 2. Derivar la llave de descifrado
        llave_para_descifrar = derive_key(password, salt)

        # 3. Intentar descifrar
        f = Fernet(llave_para_descifrar)
        llave_fernet = f.decrypt(llave_fernet_cifrada)

        # 4. ¡Éxito! Retornar un nuevo objeto Fernet con la llave real
        return Fernet(llave_fernet)

    except InvalidToken:
        # Esto ocurre si la contraseña es incorrecta y el descifrado falla
        raise ValueError("Contraseña incorrecta")
    except Exception as e:
        # Otro error (ej. archivo corrupto)
        raise ValueError(f"Error al descifrar la llave: {e}")
