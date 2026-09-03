import json
import base64
import urllib.request
import ssl

ctx = ssl._create_unverified_context()
RPC_URL = 'https://1rpc.io/eth'
MAIN_CONTRACT = '0x387C41B0B2F1128dE44dB1Bcf8baad085f26392C'

def get_token_metadata(token_id):
    payload = json.dumps({
        'jsonrpc': '2.0',
        'id': 1,
        'method': 'eth_call',
        'params': [{'to': MAIN_CONTRACT, 'data': '0xc87b56dd' + hex(token_id)[2:].zfill(64)}, 'latest']
    }).encode('utf-8')
    
    req = urllib.request.Request(RPC_URL, headers={'Content-Type': 'application/json', 'User-Agent': 'Mozilla/5.0'}, data=payload)
    with urllib.request.urlopen(req, context=ctx, timeout=10) as resp:
        data = json.loads(resp.read().decode('utf-8'))
        result = data.get('result')
        if not result or result == '0x':
            return None
        raw_bytes = bytes.fromhex(result[2:])
        offset = int.from_bytes(raw_bytes[:32], 'big')
        str_len = int.from_bytes(raw_bytes[offset:offset+32], 'big')
        uri = raw_bytes[offset+32:offset+32+str_len].decode('utf-8', errors='ignore')
        
        # Parse data:application/json;base64,...
        if uri.startswith('data:application/json;base64,'):
            b64_json = uri.split('data:application/json;base64,')[1]
            meta_json = json.loads(base64.b64decode(b64_json).decode('utf-8'))
            return meta_json
    return None

meta = get_token_metadata(1)
print("Token 1 Name:", meta.get('name'))
print("Token 1 Attributes:", meta.get('attributes'))
print("Token 1 Image URI prefix:", meta.get('image', '')[:60])
