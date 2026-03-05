import requests
import json
import os

KC_URL = 'http://localhost:8080'
ADMIN_USER = 'admin'
ADMIN_PASS = 'Soeuso410863'
REALM = 'intellicare'

# 1. Get Token
data = {'client_id': 'admin-cli', 'username': ADMIN_USER, 'password': ADMIN_PASS, 'grant_type': 'password'}
r = requests.post(f'{KC_URL}/realms/master/protocol/openid-connect/token', data=data)
r.raise_for_status()
token = r.json()['access_token']
headers = {'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'}

try:
    requests.post(f'{KC_URL}/admin/realms', headers=headers, json={'realm': REALM, 'enabled': True})
    print('Realm created')
except Exception as e:
    print('Realm might exist', e)

# 3. Create client
client_payload = {
    'clientId': 'intellicare-portal',
    'publicClient': True,
    'standardFlowEnabled': True,
    'implicitFlowEnabled': False,
    'directAccessGrantsEnabled': True,
    'redirectUris': ['http://localhost:3001/*', 'https://portal.intellicare.ia.br/*'],
    'webOrigins': ['http://localhost:3001', 'https://portal.intellicare.ia.br'],
    'protocolMappers': [
        {
            'name': 'tenant_id',
            'protocol': 'openid-connect',
            'protocolMapper': 'oidc-usermodel-attribute-mapper',
            'consentRequired': False,
            'config': {
                'user.attribute': 'tenant_id',
                'claim.name': 'tenant_id',
                'jsonType.label': 'String',
                'id.token.claim': 'true',
                'access.token.claim': 'true',
                'userinfo.token.claim': 'true'
            }
        },
        {
            'name': 'realm_roles',
            'protocol': 'openid-connect',
            'protocolMapper': 'oidc-usermodel-realm-role-mapper',
            'consentRequired': False,
            'config': {
                'claim.name': 'realm_roles',
                'multivalued': 'true',
                'id.token.claim': 'true',
                'access.token.claim': 'true',
                'userinfo.token.claim': 'true'
            }
        }
    ]
}

requests.post(f'{KC_URL}/admin/realms/{REALM}/clients', headers=headers, json=client_payload)

roles = ['PLATFORM_ADMIN', 'TENANT_GESTOR', 'CLINICO', 'MEDICO', 'ENFERMEIRO', 'PACIENTE']
for role in roles:
    requests.post(f'{KC_URL}/admin/realms/{REALM}/roles', headers=headers, json={'name': role})

users = [
    {
        'username': 'admin@intellicare.ia.br', 'email': 'admin@intellicare.ia.br', 'enabled': True,
        'credentials': [{'type': 'password', 'value': 'P@ssw0rd123', 'temporary': False}],
        'realmRoles': ['PLATFORM_ADMIN']
    },
    {
        'username': 'gestor@hsaolucas.com.br', 'email': 'gestor@hsaolucas.com.br', 'enabled': True,
        'credentials': [{'type': 'password', 'value': 'P@ssw0rd123', 'temporary': False}],
        'attributes': {'tenant_id': ['hospital_sao_lucas']},
        'realmRoles': ['TENANT_GESTOR']
    }
]

for u in users:
    roles_to_add = u.pop('realmRoles', [])
    res = requests.post(f'{KC_URL}/admin/realms/{REALM}/users', headers=headers, json=u)
    
    if res.status_code == 201:
        users_res = requests.get(f'{KC_URL}/admin/realms/{REALM}/users?username={u["username"]}', headers=headers)
        user_id = users_res.json()[0]['id']
        
        roles_payload = []
        for role in roles_to_add:
            role_res = requests.get(f'{KC_URL}/admin/realms/{REALM}/roles/{role}', headers=headers)
            roles_payload.append(role_res.json())
            
        requests.post(f'{KC_URL}/admin/realms/{REALM}/users/{user_id}/role-mappings/realm', headers=headers, json=roles_payload)
