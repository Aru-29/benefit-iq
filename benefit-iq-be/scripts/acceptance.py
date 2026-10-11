"""Local HTTP acceptance ledger. Run against a seeded loopback API only."""
import base64
import json
import os
import re
import time
from datetime import UTC, datetime, timedelta
from pathlib import Path
from uuid import uuid4

import httpx
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "artifacts" / "e2e"
OUT.mkdir(parents=True, exist_ok=True)
records = []
client = httpx.Client(base_url="http://127.0.0.1:8080", timeout=40)
password = os.environ["BENEFITIQ_DEMO_PASSWORD"]
secrets = {"password", "new_password", "current_password", "otp", "token", "access_token", "refresh_token", "hash"}

def clean(value):
    if isinstance(value, dict):
        return {k: "<redacted>" if k in secrets else clean(v) for k, v in value.items()}
    if isinstance(value, list):
        return [clean(v) for v in value]
    return value

def save():
    (OUT / "http.json").write_text(json.dumps(records, indent=2), encoding="utf-8")
    lines = ["# Live local HTTP acceptance ledger", "", "Synthetic accounts only. Credentials and OTPs are redacted.", ""]
    for i, r in enumerate(records, 1):
        lines += [f"## {i}. {r['case']} — {r['result']}", f"Reason: {r['reason']}",
                  f"Time: {r['at']}; duration: {r['ms']} ms", f"`{r['method']} {r['url']}`",
                  f"Authorization: {r['identity']}; expected HTTP: {r['expected']}; actual: {r['status']}",
                  "Request:", "```json", json.dumps(r['request'], indent=2), "```",
                  "Response:", "```json", json.dumps(r['response'], indent=2), "```", ""]
    (OUT / "HTTP_FLOW.md").write_text("\n".join(lines), encoding="utf-8")

identity = "anonymous"
def call(case, method, path, body=None, expected=(200,), reason="Verify the endpoint contract"):
    start = time.monotonic()
    response = client.request(method, path, json=body) if body is not None else client.request(method, path)
    try:
        payload = response.json()
    except ValueError:
        payload = response.text
    records.append(dict(case=case, method=method, url=str(response.url), identity=identity,
                        request=clean(body), response=clean(payload), expected=list(expected),
                        status=response.status_code, result="PASS" if response.status_code in expected else "FAIL",
                        reason=reason, at=datetime.now(UTC).isoformat(), ms=round((time.monotonic()-start)*1000)))
    save()
    print(case, response.status_code, records[-1]['result'], flush=True)
    return payload.get('data', payload) if isinstance(payload, dict) else payload

def otp(email):
    for _ in range(15):
        messages = httpx.get("http://127.0.0.1:18025/api/v1/messages").json()['messages']
        for item in messages:
            if any(x['Address'] == email for x in item['To']):
                mail = httpx.get('http://127.0.0.1:18025/api/v1/message/'+item['ID']).json()
                match = re.search(r'\b[0-9]{6}\b', mail['HTML'] or mail['Text'])
                if match:
                    return match.group()
        time.sleep(.3)
    raise RuntimeError("No local OTP message received")

def login(email):
    global identity
    client.headers.pop('Authorization', None)
    identity = 'anonymous'
    pem = call('Public key', 'GET', '/api/v1/auth/public-key')['public_key']
    key = serialization.load_pem_public_key(pem.encode())
    encrypted = base64.b64encode(key.encrypt(password.encode(), padding.OAEP(mgf=padding.MGF1(hashes.SHA256()), algorithm=hashes.SHA256(), label=None))).decode()
    call('Encrypted login '+email, 'POST', '/api/v1/auth/login', dict(email=email, password=encrypted))
    tokens = call('OTP verification '+email, 'POST', '/api/v1/auth/verify-login-otp', dict(email=email, otp=otp(email)))
    client.headers['Authorization'] = 'Bearer '+tokens['access_token']
    identity = email
    return tokens

def main():
    global identity
    call('Liveness','GET','/api/v1/health/live')
    call('Readiness','GET','/api/v1/health/ready')
    spec = client.get('/openapi.json').json()
    (OUT/'openapi.json').write_text(json.dumps(spec, indent=2), encoding='utf-8')
    call('Anonymous cards denied','GET','/api/v1/analytics/me/cards',expected=(401,403))
    call('Login schema rejected','POST','/api/v1/auth/login',{},(422,))
    call('Wrong password','POST','/api/v1/auth/login',dict(email='customer@example.com',password='invalid'),(401,400))
    call('Wrong OTP','POST','/api/v1/auth/verify-login-otp',dict(email='customer@example.com',otp='000000'),(400,401))
    tokens = login('customer@example.com')
    for path in ['/users/me','/analytics/cards','/analytics/benefits','/analytics/me/cards','/analytics/me/transactions','/analytics/me/utilization','/analytics/me/recommendations','/analytics/me/nudges','/analytics/me/redemption-predictions']:
        call('Member read '+path,'GET','/api/v1'+path)
    for path in ['/analytics/kpi','/users','/config','/secrets','/system/redis/stats']:
        call('Member admin boundary '+path,'GET','/api/v1'+path,expected=(403,))
    call('Other customer denied','GET',f'/api/v1/analytics/customers/{uuid4()}/utilization',expected=(403,))
    products = call('Catalogue','GET','/api/v1/analytics/cards')
    product = next(p for p in products if p['name']=='Demo Explorer')
    cardbody=dict(product_id=product['id'],last_four=str(uuid4().int%10000).zfill(4),alias='E2E ledger card')
    card=call('Create card','POST','/api/v1/analytics/me/cards',cardbody,(201,))
    call('Card idempotency','POST','/api/v1/analytics/me/cards',cardbody,(201,))
    call('Invalid last four','POST','/api/v1/analytics/me/cards',{**cardbody,'last_four':'x'},(422,))
    call('Unknown product','POST','/api/v1/analytics/me/cards',{**cardbody,'product_id':str(uuid4())},(404,))
    # ClickHouse stores card timestamps at second resolution.
    time.sleep(1)
    tx=dict(external_id=str(uuid4()),card_id=card['id'],amount='23.45',currency='USD',merchant_name='Synthetic merchant',merchant_category_code='5812',transaction_date=datetime.now(UTC).isoformat())
    transaction=call('Transaction ingest','POST','/api/v1/analytics/me/transactions',tx,(201,))
    call('Transaction duplicate','POST','/api/v1/analytics/me/transactions',tx,(201,))
    call('Transaction conflicting retry','POST','/api/v1/analytics/me/transactions',{**tx,'amount':'99'},(422,))
    call('Negative amount','POST','/api/v1/analytics/me/transactions',{**tx,'amount':'-1'},(422,))
    call('Future timestamp','POST','/api/v1/analytics/me/transactions',{**tx,'transaction_date':(datetime.now(UTC)+timedelta(days=1)).isoformat()},(422,))
    call('Unknown card','POST','/api/v1/analytics/me/transactions',{**tx,'card_id':str(uuid4())},(404,))
    call('Reverse transaction','POST',f"/api/v1/analytics/me/transactions/{transaction['id']}/reverse")
    summary=call('Rule utilization','GET','/api/v1/analytics/me/utilization')
    benefit=next(b for b in summary['utilizations'] if b['card_id']==card['id'] and b['benefit_category']=='travel_credit')
    usage=dict(external_id=str(uuid4()),card_id=card['id'],benefit_id=benefit['benefit_id'],value='12.34',currency='USD')
    call('Redemption','POST','/api/v1/analytics/me/usage',usage,(201,))
    call('Redemption duplicate','POST','/api/v1/analytics/me/usage',usage,(201,))
    call('Redemption conflicting retry','POST','/api/v1/analytics/me/usage',{**usage,'value':'13'},(422,))
    call('Over redemption','POST','/api/v1/analytics/me/usage',{**usage,'external_id':str(uuid4()),'value':'99999'},(422,))
    call('Invalid currency','GET','/api/v1/analytics/me/utilization?currency=bad',expected=(422,))
    call('Currency isolation','GET','/api/v1/analytics/me/utilization?currency=INR')
    enrollment=dict(card_id=card['id'],benefit_id=benefit['benefit_id'])
    call('Enroll','POST','/api/v1/analytics/me/enrollments',enrollment)
    call('Enroll retry','POST','/api/v1/analytics/me/enrollments',enrollment)
    nudges=call('Generate nudges','POST','/api/v1/analytics/me/nudges')
    call('Nudge duplicate generation','POST','/api/v1/analytics/me/nudges')
    nudge=next(n for n in nudges if n['card_id']==card['id'])
    for state in ['opened','dismissed']:
        call('Nudge '+state,'POST',f"/api/v1/analytics/me/nudges/{nudge['id']}/status",{'status':state})
    call('Forged conversion denied','POST',f"/api/v1/analytics/me/nudges/{nudge['id']}/status",{'status':'converted'},(422,))
    call('Unknown nudge','POST',f'/api/v1/analytics/me/nudges/{uuid4()}/status',{'status':'opened'},(404,))
    refreshed=call('Refresh rotation','POST','/api/v1/auth/refresh',{'refresh_token':tokens['refresh_token']})
    call('Logout','POST','/api/v1/auth/logout',{'refresh_token':refreshed['refresh_token']})
    call('Revoked refresh denied','POST','/api/v1/auth/refresh',{'refresh_token':refreshed['refresh_token']},(401,400))
    login('admin@example.com')
    for path in ['/users','/roles','/roles/lookup','/users/lookup','/config','/analytics/kpi','/system/redis/stats']:
        call('Admin read '+path,'GET','/api/v1'+path)
    role=call('Create test role','POST','/api/v1/roles',dict(name='E2E_'+uuid4().hex[:8],description='Disposable local test'),(201,))
    if 'id' in role:
        call('Read test role','GET','/api/v1/roles/'+role['id'])
        call('Update test role','PUT','/api/v1/roles/'+role['id'],dict(name=role['name'],description='Updated',is_active=True))
        call('Deactivate test role','PATCH','/api/v1/roles/'+role['id']+'/deactivate')
    key='E2E_'+uuid4().hex[:8]
    call('Create nonsecret config','POST','/api/v1/config',dict(config_key=key,value='one'),(201,))
    call('Read config','GET','/api/v1/config/'+key)
    call('Update config','PUT','/api/v1/config/'+key,dict(value='two'))
    call('Delete test config','DELETE','/api/v1/config/'+key)
    call('Unmanaged secret denied','POST','/api/v1/secrets/value',dict(path='invalid',key='test',value='synthetic'),(422,))
    for enc, dec, field in [('encrypt','decrypt','encrypted_data'),('encrypt-alphanumeric','decrypt-alphanumeric','alphanumeric_data')]:
        data=call(enc,'POST','/api/v1/crypto/'+enc,{'data':'synthetic-roundtrip'})
        call(dec,'POST','/api/v1/crypto/'+dec,{field:data['result']})
        call(dec+' invalid','POST','/api/v1/crypto/'+dec,{field:'invalid'},(400,))
    hashed=call('Hash','POST','/api/v1/crypto/hash',{'data':'synthetic-roundtrip'})
    for plain in ['synthetic-roundtrip','wrong']:
        call('Verify hash '+plain,'POST','/api/v1/crypto/verify-hash',dict(plain_text=plain,hash=hashed['result']))
    save()
    print('Ledger:',OUT, flush=True)

if __name__=='__main__':
    try:
        main()
    finally:
        save()
