import json
import re
from urllib.parse import parse_qs

async def app(scope, receive, send):
    if scope['type'] != 'http':
        return

    method = scope['method']
    path = scope['path']

    if method == 'GET' and path == '/factorial':
        await handle_factorial(scope, receive, send)
    elif method == 'GET' and path.startswith('/fibonacci'):
        await handle_fibonacci(scope, receive, send)
    elif method == 'GET' and path == '/mean':
        await handle_mean(scope, receive, send)
    else:
        await not_found(send)

async def handle_factorial(scope, receive, send):
    query_string = scope.get('query_string', b'').decode()
    query_params = parse_qs(query_string)
    n_values = query_params.get('n')

    if not n_values:
        await send_response(send, 422, {'detail': 'Parameter n is required'})
    else:
        try:
            n = int(n_values[0])
            if n < 0:
                await send_response(send, 400, {'detail': 'Parameter n must be non-negative'})
            else:
                result = factorial(n)
                await send_response(send, 200, {'result': result})
        except ValueError:
            await send_response(send, 422, {'detail': 'Parameter n must be an integer'})

def factorial(n):
    if n == 0:
        return 1
    else:
        return n * factorial(n - 1)

async def handle_fibonacci(scope, receive, send):
    path = scope['path']
    match = re.match(r'^/fibonacci/(-?\d+)$', path)
    if match:
        n = int(match.group(1))
        if n < 0:
            await send_response(send, 400, {'detail': 'Parameter n must be non-negative'})
        else:
            result = fibonacci(n)
            await send_response(send, 200, {'result': result})
    else:
        await send_response(send, 422, {'detail': 'Invalid parameter n'})

def fibonacci(n):
    a, b = 0, 1
    for _ in range(n):
        a, b = b, a + b
    return a

async def handle_mean(scope, receive, send):
    body = b''
    more_body = True

    while more_body:
        message = await receive()
        body += message.get('body', b'')
        more_body = message.get('more_body', False)

    if not body:
        await send_response(send, 422, {'detail': 'Request body is required'})
    else:
        try:
            data = json.loads(body)
            if not isinstance(data, list):
                await send_response(send, 422, {'detail': 'Body must be a JSON array'})
            elif not data:
                await send_response(send, 400, {'detail': 'Array must not be empty'})
            elif not all(isinstance(x, (int, float)) for x in data):
                await send_response(send, 422, {'detail': 'All elements must be numbers'})
            else:
                mean_value = sum(data) / len(data)
                await send_response(send, 200, {'result': mean_value})
        except json.JSONDecodeError:
            await send_response(send, 422, {'detail': 'Invalid JSON'})

async def send_response(send, status, data):
    response_body = json.dumps(data).encode('utf-8')
    headers = [
        (b'content-type', b'application/json'),
    ]
    await send({
        'type': 'http.response.start',
        'status': status,
        'headers': headers,
    })
    await send({
        'type': 'http.response.body',
        'body': response_body,
    })

async def not_found(send):
    await send({
        'type': 'http.response.start',
        'status': 404,
        'headers': [(b'content-type', b'text/plain')],
    })
    await send({
        'type': 'http.response.body',
        'body': b'Not Found',
    })
