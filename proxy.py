# A CORS proxy during development
# allows access to an API running on another domain than the web app working on

from flask import Flask, request, jsonify
import requests

targetURL = "https://main.datastore.bam.de"
app = Flask(__name__)

@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
    return response

@app.route('/<path:path>', methods=['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'])
def proxy(path):
    url = f'{targetURL}/{path}'  # Replace with your target URL
    headers = dict(request.headers)
    if 'Host' in headers:
        del headers['Host']
    response = requests.request(
        method=request.method,
        url=url,
        headers=headers,
        data=request.get_data(),
        allow_redirects=True
    )
    return response.content, response.status_code

if __name__ == '__main__':
    app.run(debug=True)
