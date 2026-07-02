import urllib.request
import urllib.error

boundary = '----WebKitFormBoundary7MA4YWxkTrZu0gW'
token = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ1cGxvYWR1c2VyIiwiZXhwIjoxNzgyOTY0ODMzfQ.h1lUD3x42oWyo7SlkKsWDvxlh9_fULR1e_Kex_v4YDg'
body = (
    f'--{boundary}\r\n'
    'Content-Disposition: form-data; name="header"\r\n\r\n'
    'Test Header\r\n'
    f'--{boundary}\r\n'
    'Content-Disposition: form-data; name="question_text"\r\n\r\n'
    'Test Question\r\n'
    f'--{boundary}\r\n'
    'Content-Disposition: form-data; name="option1"\r\n\r\n'
    'One\r\n'
    f'--{boundary}\r\n'
    'Content-Disposition: form-data; name="option2"\r\n\r\n'
    'Two\r\n'
    f'--{boundary}\r\n'
    'Content-Disposition: form-data; name="file"; filename="test.txt"\r\n'
    'Content-Type: text/plain\r\n\r\n'
    'hello\r\n'
    f'--{boundary}--\r\n'
).encode()

req = urllib.request.Request('http://127.0.0.1:9016/add_your_question', data=body, method='POST')
req.add_header('Content-Type', f'multipart/form-data; boundary={boundary}')
req.add_header('Authorization', f'Bearer {token}')

try:
    with urllib.request.urlopen(req) as r:
        print(r.status)
        print(r.read().decode())
except urllib.error.HTTPError as e:
    print('HTTP', e.code)
    print(e.read().decode())
except Exception as e:
    import traceback
    traceback.print_exc()
