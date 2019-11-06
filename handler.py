import json
import subprocess
import http.client
import re
import boto3

from config import AUTH0_API_URL, SSM_CLIENT_ID, SSM_CLIENT_SECRET


def ssm_read(path):
    ssm = boto3.client('ssm')
    parameter = ssm.get_parameter(Name=path, WithDecryption=True)
    return parameter['Parameter']['Value']


def get_token_header():
    client_id = ssm_read(SSM_CLIENT_ID)
    client_secret = ssm_read(SSM_CLIENT_SECRET)

    print(f"Using {client_id} auth0 application to obtain api creds.")

    payload = json.dumps({
        "client_id": client_id,
        "client_secret": client_secret,
        "audience": f"https://{AUTH0_API_URL}/api/v2/",
        "grant_type": "client_credentials"})

    headers = {"content-type": "application/json"}
    response = rest_api_call("POST", AUTH0_API_URL, "/oauth/token", payload,
                             headers)

    if not response:
        print("Couldnt obtain token from Auth0")
        return None
    token = json.loads(response)['access_token']
    return {"Authorization": f"Bearer {token}"}


def rest_api_call(method, url, path, payload=None, headers=None, scheme='https'):
    if not headers:
        headers = {}
    try:
        if scheme == "http":
            conn = http.client.HTTPConnection(url)
        else:
            conn = http.client.HTTPSConnection(url)

        conn.request(method, path, payload, headers)
        res = conn.getresponse()
        print(
            f"{url} API call({method}, {path}): status {res.status} reason: {res.reason}")
        if res.status != 200:
            return None
    except ConnectionError:
        print(f"Cannot connect to {url}.")
        return None

    data = res.read()
    return data.decode('utf-8')


def set_or_append(d, k, v):
    # If eg. no web_origins are set in auth0 then API returns dict with no
    # 'web_orgins' key at all. Not event set to empty list [].
    try:
        d[k].append(v)
    except KeyError:
        d[k] = [v]


def validate_event(event):
    try:
        event['callback_path']
        event['domain']
        event['client_id']
        return True
    except KeyError as e:
        print(f"Missing {e} parameter in lambda payload. See README.")
        return False


def configure(event, context):
    if not validate_event(event):
        return None

    headers = get_token_header()
    if not headers:
        return None
    headers['content-type'] = "application/json"

    resp = rest_api_call("GET",
                         AUTH0_API_URL,
                         f"/api/v2/clients/{event['client_id']}",
                         headers=headers)
    if not resp:
        return None

    current = json.loads(resp)

    # append domain to current configuration
    set_or_append(current, 'callbacks',
                  event['domain'] + event['callback_path'])
    set_or_append(current, 'allowed_origins', event['domain'])
    set_or_append(current, 'allowed_logout_urls', event['domain'])
    set_or_append(current, 'web_origins', event['domain'])

    # prepare patch_body removing duplicates in list - list(set())
    patch_body = {
        "callbacks": list(set(current['callbacks'])),
        "allowed_origins": list(set(current['allowed_origins'])),
        "web_origins": list(set(current['web_origins'])),
        "allowed_logout_urls": list(set(current['allowed_logout_urls']))
    }

    print(f"Patch body:\n{json.dumps(patch_body)}")

    resp = rest_api_call("PATCH",
                         AUTH0_API_URL,
                         f"/api/v2/clients/{event['client_id']}",
                         payload=json.dumps(patch_body),
                         headers=headers)
    if not resp:
        return None
    return True
