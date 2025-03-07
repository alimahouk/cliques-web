import hashlib


def sha256_str(string):
        return hashlib.sha256(string.encode("utf-8")).hexdigest()


def sha256_bytes(bytes):
        return hashlib.sha256(bytes).hexdigest()
