#!/usr/bin/env python3
# A CORS proxy during development
# allows access to an API running on another domain than the web app working on

from flask import Flask, request, jsonify
import requests, sys, pprint, json, base64

infn = "index.html.tmpl"
outfn = "index.html"
configfn = "config.json"

def parse_args(config):
    for i, key in enumerate(config.keys()):
        try:
            config[key] = sys.argv[i+1]
        except:
            pass

    print(f"Using the following config: ")
    pprint.pprint({k:v for k,v in config.items()
                   if k not in ("qrcode","logoBase64")})
    print(f"Run the web server with:\n"
            f"    python3 -m http.server -b {config["proxyAddr"]} {config["webPort"]}\n")

# change server address to match the proxy address here
def update_index(config):
    with open(infn) as fd:
        # read and workaround curly brackets in JS code
        html = fd.read().replace("{","{{").replace("}","}}")
        html = html.replace("{{{{","{").replace("}}}}","}")
    html = html.format(**config)
    with open(outfn, 'w') as fd:
        fd.write(html)

def readConfig():
    # config configuration values
    config = {}
    with open(configfn) as fd:
        config = json.load(fd)
        config["proxyURL"] = f"http://{config["proxyAddr"]}:{config["proxyPort"]}"
    with open("qrcode.min.js") as fd:
        config["qrcode"] = fd.read()
    with open("img/keyvisual_datastore_pur_bg_square.png", "rb") as fd:
        config["logoBase64"] = base64.b64encode(fd.read()).decode('utf-8')
    return config

def create_app(config):
    app = Flask(__name__)
    # Initialize your model or run custom function here
    parse_args(config)
    update_index(config)

    @app.after_request
    def after_request(response):
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Headers',
                             'Content-Type,Authorization,append,delete,entries,foreach,get,has,keys,set,values')
        response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
        return response

    @app.route('/<path:path>', methods=['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'])
    def proxy(path):
        url = f'{config["siteURL"]}/{path}'  # Replace with your target URL
        headers = dict(request.headers)
        if 'Host' in headers:
            del headers['Host']
        requestArgs = dict(
            method=request.method,
            url=url,
            headers=headers,
            data=request.get_data(),
            allow_redirects=True,
            verify=False) # change this to False for selfsigned certs
        response = requests.request(**requestArgs)
        return response.content, response.status_code

    return app

if __name__ == '__main__':
    config = readConfig()
    app = create_app(config)
    app.run(debug=True, use_reloader=False,
            host=config["proxyAddr"], port=config["proxyPort"])
