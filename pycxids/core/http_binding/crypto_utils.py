# Copyright (c) 2023 - for information on the respective copyright owner
# see the NOTICE file and/or the repository
# https://github.com/boschresearch/py-cx-ids
#
# SPDX-License-Identifier: Apache-2.0

import os
from typing import Union
import base64
import secrets
import math
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey, Ed25519PublicKey
from cryptography.hazmat.primitives.serialization import Encoding, PublicFormat, PrivateFormat
from cryptography.hazmat.primitives import _serialization
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from jwcrypto.jwk import JWKSet, JWK
from jwcrypto.jwt import JWT, JWE
from jwcrypto.jws import JWS
from jwcrypto.common import json_encode
# jwt lib does not support encyrption
from time import time

def pem_to_jwk(data_pem: bytes):
    """
    data_pem: public or private key in PEM format, use PKCS8 for private keys!
    """
    pub_key_jwk = JWK()
    pub_key_jwk.import_from_pem(data=data_pem)
    return pub_key_jwk

def pub_key_to_jwk(pub_key: Union[rsa.RSAPublicKey, Ed25519PublicKey]) -> JWK:
    """
    Creates a JWK json form a given public key
    """
    pub_key_jwk = JWK()
    pub_key_jwk.import_from_pyca(key=pub_key)
    return pub_key_jwk.export_public(as_dict=True)

def private_key_to_jwk(key: Union[rsa.RSAPrivateKey, Ed25519PrivateKey]) -> JWK:
    """
    Attention, PRIVATE keys here!
    Used for singing in jwt lib
    """
    key_jwk = JWK()
    key_jwk.import_from_pyca(key=key)
    return key_jwk

def pub_key_to_jwk_thumbprint(pub_key: Union[rsa.RSAPublicKey, Ed25519PublicKey]) -> JWK:
    """
    Create a hash of the jwk. Uses sha256.
    """
    pub_key_jwk = JWK()
    pub_key_jwk.import_from_pyca(key=pub_key)
    thumbprint = pub_key_jwk.thumbprint()
    return thumbprint

def encrypt(payload: bytes, public_key_pem: bytes):
    """
    Sign the payload asymentrically with the given payload

    Hint: In case you want to sign and encrypt, sign the message first!
    https://datatracker.ietf.org/doc/html/rfc7519#section-11.2
    """
    pub_key_jwk = pem_to_jwk(data_pem=public_key_pem)

    protected_header = {
        "alg": "RSA-OAEP-256",
        "enc": "A256CBC-HS512",
        "typ": "JWE",
        "kid":  pub_key_jwk.thumbprint(),
    }
    jwetoken = JWE(payload, recipient=pub_key_jwk, protected=protected_header)
    enc = jwetoken.serialize(compact=True) # jwt is always compact!
    return enc

def decrypt(payload: bytes, private_key_pem: bytes):
    jwetoken = JWE()
    jwetoken.deserialize(payload)
    key = pem_to_jwk(data_pem=private_key_pem)
    jwetoken.decrypt(key=key)
    decrypted_msg = jwetoken.payload
    return decrypted_msg

def sign(payload: bytes, private_key_pem: bytes):
    """
    Sign the playload with the given private key

    Details: https://jwcrypto.readthedocs.io/en/latest/jws.html#examples

    Hint: you might want to use 'encrypt' afterwards

    payload: utf-8 encoded
    """
    private_key_jwk = pem_to_jwk(data_pem=private_key_pem)
    jwstoken = JWS(payload=payload)
    # TODO: check 'protected' param!
    jwstoken.add_signature(key=private_key_jwk, alg=None, protected=json_encode({"alg": "RS256"}), header=json_encode({"kid": private_key_jwk.thumbprint()}))
    signed_token = jwstoken.serialize(compact=True) # jwt is always compact!
    return signed_token

def verify(payload: bytes, public_key_pem: bytes):
    """
    Will decode() payload before verifies
    """
    public_key_jwk = pem_to_jwk(data_pem=public_key_pem)
    jwstoken = JWS()
    jwstoken.deserialize(payload.decode())
    jwstoken.verify(public_key_jwk)
    payload = jwstoken.payload
    return payload

def generate_rsa_key() -> rsa.RSAPrivateKey:
    """
    Use cryptography default params from:
    https://cryptography.io/en/latest/hazmat/primitives/asymmetric/rsa/#cryptography.hazmat.primitives.asymmetric.rsa.generate_private_key
    """
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    return key

def key_to_public_pem(key: rsa.RSAPrivateKey) -> bytes:
    pub_key = key.public_key().public_bytes(
        encoding=Encoding.PEM,
        format=PublicFormat.SubjectPublicKeyInfo,
    )
    return pub_key


def key_to_private_pkcs8(key: rsa.RSAPrivateKey) -> bytes:
    """
    Use PKCS8 format
    """
    private_key = key.private_bytes(
        encoding=Encoding.PEM,
            format=PrivateFormat.PKCS8,
            encryption_algorithm=_serialization.NoEncryption(),
    )
    return private_key

def generate_rsa_keys_to_file(public_key_fn: str, private_key_fn: str):
    """
    Generate new RSA key pari and write to file.
    private key file is PKCS8 format
    both in PEM
    """
    key = generate_rsa_key()
    private_key = key_to_private_pkcs8(key=key)
    public_key = key_to_public_pem(key=key)
    with open(public_key_fn, "wb") as f:
        f.write(public_key)
    with open(private_key_fn, "wb") as f:
        f.write(private_key)


def generate_seed(len: int = 32) -> str:
    """
    """
    bytes_len = math.floor(len/2)
    return secrets.token_hex(bytes_len)

def generate_ed25519_key(seed: str = ''):
    """
    Generate a private key from given seed.
    Same seed generates same private keys reproducible.
    seed: 32 characters
    """
    if not seed:
        seed = generate_seed()
    assert len(seed) == 32, "Seed must be 32 characters"
    private_key = Ed25519PrivateKey.from_private_bytes(seed.encode())
    return private_key

def key_to_public_raw(key: Ed25519PrivateKey) -> bytes:
    """
    Private key to public key
    key: ed25519 private key
    return: RAW bytes
    """
    public_key = key.public_key()
    pk_raw = public_key.public_bytes(encoding=Encoding.Raw, format=PublicFormat.Raw)
    return pk_raw

def decrypt(b64_cipher: str, b64_key: str):
    """
    This is meant to decrypt AES GCM messages.
    This is mainly for EDR content sent from an EDC Provider to the Consumer.
    The content of the 'authCode's 'dad' is encrypted.
    https://github.com/paullatzelsperger/tractusx-edc/blob/2e0b98c9a24816a56f7c98c02024b87088bd15ff/edc-extensions/data-encryption/src/main/java/org/eclipse/tractusx/edc/data/encryption/aes/AesEncryptor.java

    The cipher looks like:
    <16_bytes_iv><encyrpted_message><16_bytes_tag>

    The 'tag' is authenticated, but not encrypted.
    The 'tag' is not really used in EDC EDR content.
    """
    key = base64.b64decode(b64_key)
    decoded = base64.b64decode(b64_cipher)
    iv = decoded[:16]
    cipher_text = decoded[16:-16]
    tag = decoded[-16:]
    decryptor = Cipher(
        algorithm=algorithms.AES(key=key),
        mode=modes.GCM(iv)
        ).decryptor()
    # tag needs to be provided either in creating the decryptor,
    # or with the finalize call
    # the content of it is not relevant for us.
    raw = decryptor.update(cipher_text) + decryptor.finalize_with_tag(tag=tag)
    text = raw.decode()
    return text
