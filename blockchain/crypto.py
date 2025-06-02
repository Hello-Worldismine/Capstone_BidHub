# app/crypto_utils.py
import os
import binascii
from dotenv import load_dotenv
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend

load_dotenv(dotenv_path=".env")

def get_or_generate_aes_key(env_path=".env"):
    key = os.getenv("AES_KEY")
    if key is None:
        new_key = binascii.hexlify(os.urandom(32)).decode()
        with open(env_path, "a") as f:
            f.write(f"\nAES_KEY={new_key}\n")
        return new_key
    return key

aes_key_hex = get_or_generate_aes_key()
aes_key = binascii.unhexlify(aes_key_hex)

def serialize_bid_data(trade_num, amount, security, bidder_address, bid_time):
    return (
        trade_num.to_bytes(8, 'big') +
        amount.to_bytes(10, 'big') +
        security.to_bytes(10, 'big') +
        bytes.fromhex(bidder_address[2:]) +
        bid_time.to_bytes(4, 'big')
    )

def encrypt_bid_data(trade_num, amount, security, bidder_address, bid_time):
    plain_data = serialize_bid_data(trade_num, amount, security, bidder_address, bid_time)
    iv = os.urandom(16)
    padded_data = plain_data + b'\x00' * (16 - (len(plain_data) % 16))
    cipher = Cipher(algorithms.AES(aes_key), modes.CBC(iv), backend=default_backend())
    encryptor = cipher.encryptor()
    ciphertext = encryptor.update(padded_data) + encryptor.finalize()
    full_data = iv + ciphertext
    chunks = [int.from_bytes(full_data[i:i+32], 'big') for i in range(0, len(full_data), 32)]
    while len(chunks) < 3:
        chunks.append(0)
    return chunks[:3]

def decrypt_aes(p1: int, p2: int, p3: int) -> bytes:
    """
    p1, p2, p3: 각각 uint256로 표현된 암호화 데이터 조각들
    """
    # 각 p값을 32바이트 big-endian으로 변환하여 연결
    iv_and_ciphertext = (
        p1.to_bytes(32, 'big') +
        p2.to_bytes(32, 'big') +
        p3.to_bytes(32, 'big')
    )

    # IV와 ciphertext 분리
    iv = iv_and_ciphertext[:16]
    ciphertext = iv_and_ciphertext[16:]

    # AES 복호화
    cipher = Cipher(algorithms.AES(aes_key), modes.CBC(iv), backend=default_backend())
    decryptor = cipher.decryptor()
    decrypted_padded = decryptor.update(ciphertext) + decryptor.finalize()

    return decrypted_padded[:52]  # 52바이트만 추출

def deserialize_decrypted_data(decrypted_data: bytes):
    trade_num = int.from_bytes(decrypted_data[0:8], 'big')
    amount = int.from_bytes(decrypted_data[8:18], 'big')
    security = int.from_bytes(decrypted_data[18:28], 'big')
    bidder = '0x' + decrypted_data[28:48].hex()
    bid_time = int.from_bytes(decrypted_data[48:52], 'big')
    return {
        'trade_num': trade_num,
        'amount': amount,
        'security': security,
        'bidder': bidder,
        'bid_time': bid_time,
    }
