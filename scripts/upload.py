#!/usr/bin/env python3
"""Upload an extension package (zip) to extensions.gnome.org.

Usage: EXT_USERNAME=... EXT_PASSWORD=... python3 upload.py pkg.zip
"""
import os, sys, re, json, urllib.request, urllib.parse, urllib.error, http.cookiejar, uuid as _uuid

SITE = 'https://extensions.gnome.org'
user = os.environ['EXT_USERNAME']
pw = os.environ['EXT_PASSWORD']
path = sys.argv[1] if len(sys.argv) > 1 else 'pkg.zip'

cj = http.cookiejar.CookieJar()
op = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))
op.addheaders = [('User-Agent', 'Mozilla/5.0 (X11; Linux x86_64)')]

r = op.open(SITE + '/accounts/login/')
csrf = re.search(r'name="csrfmiddlewaretoken" value="([^"]+)"', r.read().decode()).group(1)
data = urllib.parse.urlencode({'csrfmiddlewaretoken': csrf, 'username': user, 'password': pw, 'next': '/'}).encode()
req = urllib.request.Request(SITE + '/accounts/login/', data=data, method='POST')
req.add_header('Referer', SITE + '/accounts/login/')
req.add_header('Origin', SITE)
r = op.open(req)
if 'logout' not in r.read().decode('utf-8', 'replace').lower():
    print('login failed')
    sys.exit(1)

cr = [c.value for c in cj if c.name == 'csrftoken'][0]
boundary = '----ci' + _uuid.uuid4().hex
with open(path, 'rb') as f:
    fdata = f.read()
parts = []
def field(n, v):
    parts.append(('--' + boundary + '\r\nContent-Disposition: form-data; name="' + n + '"\r\n\r\n' + v + '\r\n').encode())
field('shell_license_compliant', 'true')
field('tos_compliant', 'true')
parts.append(('--' + boundary + '\r\nContent-Disposition: form-data; name="source"; filename="' + os.path.basename(path) + '"\r\nContent-Type: application/zip\r\n\r\n').encode() + fdata + b'\r\n')
parts.append(('--' + boundary + '--\r\n').encode())
payload = b''.join(parts)
req = urllib.request.Request(SITE + '/api/v1/extensions', data=payload, method='POST')
req.add_header('Content-Type', 'multipart/form-data; boundary=' + boundary)
req.add_header('X-CSRFToken', cr)
req.add_header('Referer', SITE + '/upload/')
req.add_header('Origin', SITE)
try:
    r3 = op.open(req)
    body = r3.read().decode('utf-8', 'replace')
    print('status:', r3.status)
    print(body)
    try:
        j = json.loads(body)
        if 'link' in j:
            print('listing:', SITE + j['link'])
    except ValueError:
        pass
except urllib.error.HTTPError as e:
    body = e.read().decode('utf-8', 'replace')
    print('HTTPError', e.code)
    print(body[:1000])
    sys.exit(1)
