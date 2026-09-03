import json
import urllib.request
import ssl
import hashlib

# keccak256 using Crypto / pysha3 / Crypto.Hash.keccak if available, or sha3
def keccak256(text):
    try:
        from Crypto.Hash import keccak
        k = keccak.new(digest_bits=256)
        k.update(text.encode('utf-8'))
        return k.hexdigest()
    except Exception:
        pass
    try:
        import sha3
        k = sha3.keccak_256()
        k.update(text.encode('utf-8'))
        return k.hexdigest()
    except Exception:
        pass
    # We can also compute keccak via web3 or standard python
    try:
        import eth_utils
        return eth_utils.keccak(text=text).hex()
    except Exception:
        pass
    return None

print("traitsOf(uint256) selector:", keccak256("traitsOf(uint256)"))
print("traitChunks(uint256) selector:", keccak256("traitChunks(uint256)"))
print("tokenURI(uint256) selector:", keccak256("tokenURI(uint256)"))
