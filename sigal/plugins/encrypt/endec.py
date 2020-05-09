#!/usr/bin/env python3
#coding: utf-8

# copyright (c) 2020 Bowen Ding

# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to
# deal in the Software without restriction, including without limitation the
# rights to use, copy, modify, merge, publish, distribute, sublicense, and/or
# sell copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
# FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS
# IN THE SOFTWARE.

import io
import os
from base64 import b64decode
from pathlib import Path
from typing import BinaryIO

from cryptography.exceptions import InvalidTag
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

backend = default_backend()
MAGIC_STRING = "_e_n_c_r_y_p_t_e_d_".encode("utf-8")

def kdf_gen_key(password: str, salt: str, iters: int) -> bytes:
    password = password.encode("utf-8")
    salt = salt.encode("utf-8")
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA1(),
        length=16,
        salt=salt,
        iterations=iters,
        backend=backend
    )
    key = kdf.derive(password)
    return key

def dispatchargs(decorated):
    def wrapper(args):
        if args.key is not None:
            key = b64decode(args.key.encode("utf-8"))
        elif args.password is not None:
            key = kdf_gen_key(args.password, args.kdf_salt, args.kdf_iters)
        else:
            raise ValueError("Neither password nor key is provided")
        tag = args.gcm_tag.encode("utf-8")
        outputBuffer = io.BytesIO()
        with Path(args.infile).open("rb") as in_:
            decorated(key, in_, outputBuffer, tag)
        with Path(args.outfile).open("wb") as out:
            out.write(outputBuffer.getbuffer())

    return wrapper

def encrypt(key: bytes, infile: BinaryIO, outfile: BinaryIO, tag: bytes):
    if len(key) != 128/8:
        raise ValueError("Unsupported key length: %d" % len(key))
    aesgcm = AESGCM(key)
    iv = os.urandom(12)
    plaintext = infile
    ciphertext = outfile
    rawbytes = plaintext.read()
    encrypted = aesgcm.encrypt(iv, rawbytes, tag)
    ciphertext.write(MAGIC_STRING)
    ciphertext.write(iv)
    ciphertext.write(encrypted)

def decrypt(key: bytes, infile: BinaryIO, outfile: BinaryIO, tag: bytes):
    if len(key) != 128/8:
        raise ValueError("Unsupported key length: %d" % len(key))
    aesgcm = AESGCM(key)
    ciphertext = infile
    plaintext = outfile
    magicstring = ciphertext.read(len(MAGIC_STRING))
    if magicstring != MAGIC_STRING:
        raise ValueError("Data is not encrypted")
    iv = ciphertext.read(12)
    rawbytes = ciphertext.read()
    try:
        decrypted = aesgcm.decrypt(iv, rawbytes, tag)
    except InvalidTag:
        raise ValueError("Incorrect tag, iv, or corrupted ciphertext")
    plaintext.write(decrypted)

if __name__ == "__main__":
    import argparse as ap
    parser = ap.ArgumentParser(description="Encrypt or decrypt using AES-128-GCM")
    parser.add_argument("-k", "--key", help="Base64-encoded key")
    parser.add_argument("-p", "--password", help="Password in plaintext")
    parser.add_argument("--kdf-salt", help="PBKDF2 salt", default="saltysaltsweetysweet")
    parser.add_argument("--kdf-iters", type=int, help="PBKDF2 iterations", default=10000)
    parser.add_argument("--gcm-tag", help="AES-GCM tag", default="AuTheNTiCatIoNtAG")
    parser.add_argument("-i", "--infile", help="Input file")
    parser.add_argument("-o", "--outfile", help="Output file")
    subparsers = parser.add_subparsers(title="commands", dest="action")
    parser_enc = subparsers.add_parser("enc", help="Encrypt")
    parser_enc.set_defaults(execute=dispatchargs(encrypt))
    parser_dec = subparsers.add_parser("dec", help="Decrypt")
    parser_dec.set_defaults(execute=dispatchargs(decrypt))

    args = parser.parse_args()
    args.execute(args)
