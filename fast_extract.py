import urllib.request
import json
import ssl
import time
from concurrent.futures import ThreadPoolExecutor

RPC_ENDPOINTS = [
    'https://eth-mainnet.public.blastapi.io',
    'https://rpc.mevblocker.io',
    'https://mainnet.gateway.tenderly.co',
    'https://ethereum.publicnode.com'
]

ctx = ssl._create_unverified_context()

def rpc_call(to, data, rpc_idx=0):
    payload = json.dumps({
        'jsonrpc': '2.0',
        'id': 1,
        'method': 'eth_call',
        'params': [{'to': to, 'data': data}, 'latest']
    }).encode('utf-8')
    for attempt in range(len(RPC_ENDPOINTS)):
        ep = RPC_ENDPOINTS[(rpc_idx + attempt) % len(RPC_ENDPOINTS)]
        try:
            req = urllib.request.Request(
                ep,
                headers={
                    'Content-Type': 'application/json',
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                },
                data=payload
            )
            with urllib.request.urlopen(req, context=ctx, timeout=5) as resp:
                res = json.loads(resp.read().decode('utf-8'))
                if 'result' in res:
                    return res['result']
        except Exception:
            continue
    return None

def get_code(addr, rpc_idx=0):
    payload = json.dumps({
        'jsonrpc': '2.0',
        'id': 1,
        'method': 'eth_getCode',
        'params': [addr, 'latest']
    }).encode('utf-8')
    for attempt in range(len(RPC_ENDPOINTS)):
        ep = RPC_ENDPOINTS[(rpc_idx + attempt) % len(RPC_ENDPOINTS)]
        try:
            req = urllib.request.Request(
                ep,
                headers={
                    'Content-Type': 'application/json',
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                },
                data=payload
            )
            with urllib.request.urlopen(req, context=ctx, timeout=5) as resp:
                res = json.loads(resp.read().decode('utf-8'))
                code = res.get('result', '')
                if code and code.startswith('0x'):
                    raw = bytes.fromhex(code[2:])
                    if len(raw) > 1:
                        return raw[1:]  # skip 0x00 STOP
        except Exception:
            continue
    return b''

def fetch_blob(i, renderer):
    arg = hex(i)[2:].zfill(64)
    res = rpc_call(renderer, '0x2abc3d4e' + arg, rpc_idx=i)
    if res:
        ptr_addr = '0x' + res[-40:]
        bdata = get_code(ptr_addr, rpc_idx=i)
        return i, ptr_addr, bdata.hex(), len(bdata)
    return i, '', '', 0

def main():
    renderer = '0x4695062dD890e230074B411233c788dBC68B4f79'
    main_contract = '0x387C41B0B2F1128dE44dB1Bcf8baad085f26392C'
    
    print('1. Fetching metadata & configs...', flush=True)
    layout_res = rpc_call(renderer, '0x00167634')
    raw = bytes.fromhex(layout_res[2:])
    off = int.from_bytes(raw[:32], 'big')
    length = int.from_bytes(raw[off:off+32], 'big')
    layout_hex = raw[off+32:off+32+length].hex()
    print(f'   Layout hex: {layout_hex}', flush=True)
    
    headband_idx = int(rpc_call(renderer, '0x17922f98') or '0', 16)
    vape_mouth = int(rpc_call(renderer, '0xa73b5ba0') or '0', 16)
    vape_smoke = int(rpc_call(renderer, '0x53a8375d') or '0', 16)
    vape_blue = int(rpc_call(renderer, '0x9564738c') or '0', 16)
    vape_dragons = int(rpc_call(renderer, '0xd0f5bf20') or '0', 16)
    print(f'   headband: {headband_idx}, vapeMouth: {vape_mouth}, smoke: {vape_smoke}, blue: {vape_blue}, dragons: {vape_dragons}', flush=True)
    
    underhead_map = {}
    for i in range(25):
        arg = hex(i)[2:].zfill(64)
        res = rpc_call(renderer, '0xfa513197' + arg)
        if res and int(res, 16) != 0:
            underhead_map[i] = int(res, 16)
    print(f'   underhead mappings: {underhead_map}', flush=True)
            
    print('2. Fetching all 81 blobs in parallel...', flush=True)
    blobs = [None] * 81
    with ThreadPoolExecutor(max_workers=8) as pool:
        futures = [pool.submit(fetch_blob, i, renderer) for i in range(81)]
        for f in futures:
            idx, addr, bhex, size = f.result()
            blobs[idx] = {
                'index': idx,
                'address': addr,
                'hex': bhex,
                'size': size
            }
            print(f'   Blob {idx:02d}: {size} bytes ({addr})', flush=True)
            
    output = {
        'main_contract': main_contract,
        'renderer_contract': renderer,
        'blob_count': 81,
        'layout_hex': layout_hex,
        'headbandHeadIndex': headband_idx,
        'vapeMouthIndex': vape_mouth,
        'vapeSmokeBlob': vape_smoke,
        'vapeBlueberryBlob': vape_blue,
        'vapeDragonsBlob': vape_dragons,
        'underheadBlob': underhead_map,
        'blobs': blobs
    }
    
    with open('argonauts_engine_data.json', 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=2)
    print('ALL 81 BLOBS AND CONFIGS SAVED TO argonauts_engine_data.json!', flush=True)

if __name__ == '__main__':
    main()
