import urllib.request
import json
import ssl
import time

RPC_ENDPOINTS = [
    'https://ethereum-rpc.publicnode.com',
    'https://eth-mainnet.public.blastapi.io',
    'https://1rpc.io/eth',
    'https://rpc.mevblocker.io'
]

ctx = ssl._create_unverified_context()

def rpc_call(to, data):
    payload = json.dumps({
        'jsonrpc': '2.0',
        'id': 1,
        'method': 'eth_call',
        'params': [{'to': to, 'data': data}, 'latest']
    }).encode('utf-8')
    for ep in RPC_ENDPOINTS:
        try:
            req = urllib.request.Request(
                ep,
                headers={'Content-Type': 'application/json', 'User-Agent': 'Mozilla/5.0'},
                data=payload
            )
            with urllib.request.urlopen(req, context=ctx, timeout=5) as resp:
                res = json.loads(resp.read().decode('utf-8'))
                if 'result' in res:
                    return res['result']
        except Exception:
            continue
    return None

def get_code(addr):
    payload = json.dumps({
        'jsonrpc': '2.0',
        'id': 1,
        'method': 'eth_getCode',
        'params': [addr, 'latest']
    }).encode('utf-8')
    for ep in RPC_ENDPOINTS:
        try:
            req = urllib.request.Request(
                ep,
                headers={'Content-Type': 'application/json', 'User-Agent': 'Mozilla/5.0'},
                data=payload
            )
            with urllib.request.urlopen(req, context=ctx, timeout=5) as resp:
                res = json.loads(resp.read().decode('utf-8'))
                if 'result' in res:
                    return res['result']
        except Exception:
            continue
    return None

def read_sstore2(addr):
    code = get_code(addr)
    if code and code.startswith('0x'):
        raw = bytes.fromhex(code[2:])
        if len(raw) > 1:
            return raw[1:]  # discard the 0x00 STOP byte
    return b''

def main():
    renderer = '0x4695062dD890e230074B411233c788dBC68B4f79'
    main_contract = '0x387C41B0B2F1128dE44dB1Bcf8baad085f26392C'
    
    print('1. Reading blobCount()...')
    blob_count_res = rpc_call(renderer, '0x6fd7549f')
    blob_count = int(blob_count_res, 16) if blob_count_res else 81
    print(f'   Blob count: {blob_count}')
    
    print('2. Reading layout()...')
    layout_res = rpc_call(renderer, '0x00167634')
    layout_hex = ''
    if layout_res:
        raw = bytes.fromhex(layout_res[2:])
        off = int.from_bytes(raw[:32], 'big')
        length = int.from_bytes(raw[off:off+32], 'big')
        layout_bytes = raw[off+32:off+32+length]
        layout_hex = layout_bytes.hex()
    print(f'   Layout bytes ({len(bytes.fromhex(layout_hex))} bytes): {layout_hex}')
    
    print('3. Reading configs...')
    headband_idx = int(rpc_call(renderer, '0x17922f98') or '0', 16)
    vape_mouth = int(rpc_call(renderer, '0xa73b5ba0') or '0', 16)
    vape_smoke = int(rpc_call(renderer, '0x53a8375d') or '0', 16)
    vape_blue = int(rpc_call(renderer, '0x9564738c') or '0', 16)
    vape_dragons = int(rpc_call(renderer, '0xd0f5bf20') or '0', 16)
    
    print(f'   headband: {headband_idx}, vapeMouth: {vape_mouth}, smoke: {vape_smoke}, blue: {vape_blue}, dragons: {vape_dragons}')
    
    print('4. Reading underheadBlob mapping for eyes 0..20...')
    underhead_map = {}
    for i in range(25):
        arg = hex(i)[2:].zfill(64)
        res = rpc_call(renderer, '0xfa513197' + arg) # underheadBlob(uint8)
        if res:
            val = int(res, 16)
            if val != 0:
                underhead_map[i] = val
                print(f'   underheadBlob[{i}] = {val}')
                
    print(f'5. Fetching all {blob_count} blobs from SSTORE2...')
    blobs = []
    for i in range(blob_count):
        arg = hex(i)[2:].zfill(64)
        res = rpc_call(renderer, '0x2abc3d4e' + arg) # blobs(uint256)
        if not res:
            print(f'   ERROR fetching blobs({i})')
            continue
        ptr_addr = '0x' + res[-40:]
        bdata = read_sstore2(ptr_addr)
        blobs.append({
            'index': i,
            'address': ptr_addr,
            'hex': bdata.hex(),
            'size': len(bdata)
        })
        if i % 10 == 0 or i == blob_count - 1:
            print(f'   Fetched blob {i}/{blob_count}: {ptr_addr} ({len(bdata)} bytes)')
        time.sleep(0.02)
        
    print('6. Saving complete dataset to argonauts_engine_data.json...')
    data = {
        'main_contract': main_contract,
        'renderer_contract': renderer,
        'blob_count': blob_count,
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
        json.dump(data, f, indent=2)
    print('DONE! argonauts_engine_data.json written successfully.')

if __name__ == '__main__':
    main()
