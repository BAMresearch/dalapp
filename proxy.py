#!/usr/bin/env python3
# A CORS proxy during development
# allows access to an API running on another domain than the web app working on

from flask import Flask, request, jsonify
import requests, sys, pprint

config = dict( # defaults, order of cmdline arguments
    hostAddr = "127.0.0.1",
    hostPort = "5000",
    targetURL = "https://bam-openbis02.germanywestcentral.cloudapp.azure.com",
    webPort = "8000",
)
app = Flask(__name__)

# parse args
for i, key in enumerate(config.keys()):
    try:
        config[key] = sys.argv[i+1]
    except:
        pass

print(f"Using the following config: ")
pprint.pprint(config)
print(f"Run the web server with:\n"
        f"    python3 -m http.server -b {config["hostAddr"]} {config["webPort"]}\n")

@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
    return response

@app.route('/<path:path>', methods=['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'])
def proxy(path):
    url = f'{config["targetURL"]}/{path}'  # Replace with your target URL
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
    app.run(debug=True, host=config["hostAddr"], port=config["hostPort"])
