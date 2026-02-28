"""List all Bedrock vision models with pricing."""
import boto3, json, base64

bedrock = boto3.client('bedrock', region_name='us-east-1',
    aws_access_key_id='AKIA3C7X6BGV764OTVIP',
    aws_secret_access_key='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')
runtime = boto3.client('bedrock-runtime', region_name='us-east-1',
    aws_access_key_id='AKIA3C7X6BGV764OTVIP',
    aws_secret_access_key='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')

resp = bedrock.list_foundation_models()
vision = [m for m in resp['modelSummaries'] if 'IMAGE' in m.get('inputModalities', [])]

print("BEDROCK VISION-CAPABLE MODELS")
print("=" * 90)
for m in vision:
    mid = m['modelId']
    prov = m.get('providerName', '?')
    name = m.get('modelName', '?')
    out = ','.join(m.get('outputModalities', []))
    # Skip sub-variants (28k, 200k, 24k, 300k versions)
    if ':' in mid and any(x in mid.split(':')[-1] for x in ['k', 'K']):
        continue
    print(f"  {prov:15s} | {name:35s} | {mid}")

print("\n\nTESTING VISION with a tiny image...")
print("=" * 90)

# Create a tiny 1x1 red PNG
import struct, zlib
def make_png():
    header = b'\x89PNG\r\n\x1a\n'
    ihdr_data = struct.pack('>IIBBBBB', 1, 1, 8, 2, 0, 0, 0)
    ihdr_crc = zlib.crc32(b'IHDR' + ihdr_data)
    ihdr = struct.pack('>I', 13) + b'IHDR' + ihdr_data + struct.pack('>I', ihdr_crc)
    raw = b'\x00\xff\x00\x00'
    compressed = zlib.compress(raw)
    idat_crc = zlib.crc32(b'IDAT' + compressed)
    idat = struct.pack('>I', len(compressed)) + b'IDAT' + compressed + struct.pack('>I', idat_crc)
    iend_crc = zlib.crc32(b'IEND')
    iend = struct.pack('>I', 0) + b'IEND' + struct.pack('>I', iend_crc)
    return header + ihdr + idat + iend

img_b64 = base64.b64encode(make_png()).decode()

test_models = [
    # Anthropic Claude
    'anthropic.claude-3-haiku-20240307-v1:0',
    'anthropic.claude-3-sonnet-20240229-v1:0',
    'us.anthropic.claude-3-5-haiku-20241022-v1:0',
    'us.anthropic.claude-3-5-sonnet-20241022-v2:0',
    'us.anthropic.claude-3-7-sonnet-20250219-v1:0',
    # Amazon Nova
    'amazon.nova-lite-v1:0',
    'amazon.nova-pro-v1:0',
    'us.amazon.nova-lite-v1:0',
    'us.amazon.nova-pro-v1:0',
]

for mid in test_models:
    if 'anthropic' in mid:
        body = json.dumps({
            'anthropic_version': 'bedrock-2023-05-31',
            'max_tokens': 10,
            'messages': [{'role': 'user', 'content': [
                {'type': 'image', 'source': {'type': 'base64', 'media_type': 'image/png', 'data': img_b64}},
                {'type': 'text', 'text': 'What color?'},
            ]}],
        })
    elif 'nova' in mid:
        body = json.dumps({
            'messages': [{'role': 'user', 'content': [
                {'image': {'format': 'png', 'source': {'bytes': img_b64}}},
                {'text': 'What color?'},
            ]}],
            'inferenceConfig': {'maxNewTokens': 10},
        })
    try:
        r = runtime.invoke_model(modelId=mid, contentType='application/json', accept='application/json', body=body)
        result = json.loads(r['body'].read())
        if 'content' in result:
            txt = result['content'][0].get('text', '')[:30]
        elif 'output' in result:
            txt = str(result['output'])[:30]
        else:
            txt = str(result)[:30]
        print(f"  YES  {mid:55s} -> {txt}")
    except Exception as e:
        err = str(e)[:60]
        print(f"  NO   {mid:55s} -> {err}")
