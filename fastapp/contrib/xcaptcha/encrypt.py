import base64

from cryptography.hazmat.primitives import padding
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes

from common.settings import settings


class SymmetricEncryption:
    """
    AES/GCM
    """

    def __init__(self):
        self.key = settings.XCAPTCHA_ENCRYPT_KEY.encode()[-32:]
        self.pkcs7 = padding.PKCS7(algorithms.AES.block_size)
        self.cipher = Cipher(algorithms.AES(self.key), modes.ECB())

    def encrypt_message(self, message):
        data = message.encode()

        padder = self.pkcs7.padder()
        padded_data = padder.update(data) + padder.finalize()

        encryptor = self.cipher.encryptor()
        ciphertext = encryptor.update(padded_data) + encryptor.finalize()

        return base64.b64encode(ciphertext).decode()

    def decrypt_message(self, encrypted_msg):
        data = base64.b64decode(encrypted_msg)

        decryptor = self.cipher.decryptor()
        padded_data = decryptor.update(data) + decryptor.finalize()

        unpadder = self.pkcs7.unpadder()
        unpadded_data = unpadder.update(padded_data) + unpadder.finalize()

        return unpadded_data.decode()


def encrypt_ts_key(key):
    return SymmetricEncryption().encrypt_message(key)


def decrypt_ts_key(key):
    return SymmetricEncryption().decrypt_message(key)


def decode_track_id(track_id):
    decoded_track_id = SymmetricEncryption().decrypt_message(track_id)

    return dict(zip(("key", "value", "group"), decoded_track_id.split(":")))
