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

def parse_args():
    for i, key in enumerate(config.keys()):
        try:
            config[key] = sys.argv[i+1]
        except:
            pass

    print(f"Using the following config: ")
    pprint.pprint(config)
    print(f"Run the web server with:\n"
            f"    python3 -m http.server -b {config["hostAddr"]} {config["webPort"]}\n")

# change server address to match the proxy address here
def update_index():
    fn = "index.html"
    with open(fn) as fd:
        content = fd.read()
    content = content.replace("127.0.0.1:5000",
                              f"{config["hostAddr"]}:{config["hostPort"]}")
    with open(fn, 'w') as fd:
        fd.write(content)

def create_app():
    app = Flask(__name__)

    # Initialize your model or run custom function here
    parse_args()
    update_index()

    @app.after_request
    def after_request(response):
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Headers',
                             'Content-Type,Authorization,append,delete,entries,foreach,get,has,keys,set,values')
        response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
        return response

    @app.route('/<path:path>', methods=['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'])
    def proxy(path):
        url = f'{config["targetURL"]}/{path}'  # Replace with your target URL
        headers = dict(request.headers)
        if 'Host' in headers:
            del headers['Host']
        requestArgs = dict(
            method=request.method,
            url=url,
            headers=headers,
            data=request.get_data(),
            allow_redirects=True,
            verify=True) # change this to False for selfsigned certs
        response = requests.request(**requestArgs)
        return response.content, response.status_code

    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True, use_reloader=False,
            host=config["hostAddr"], port=config["hostPort"])
