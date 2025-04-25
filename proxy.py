#!/usr/bin/env python3
# A CORS proxy during development
# allows access to an API running on another domain than the web app working on

from flask import Flask, request, jsonify
from pathlib import Path
import requests, sys, pprint, json, base64

infn = "index.html.tmpl"
outfn = "index.html"

# change server address to match the proxy address here
def update_index(config):
    with open(infn) as fd:
        # read and workaround curly brackets in JS code
        html = fd.read().replace("{","{{").replace("}","}}")
        html = html.replace("{{{{","{").replace("}}}}","}")
    html = html.format(**config)
    with open(outfn, 'w') as fd:
        fd.write(html)

def gitInfo():
    from git import Repo
    repo = Repo('.')  # assumes current directory is inside the git repo
    # Short commit hash (first 7 characters)
    lastCommit = repo.head.commit
    shortHash = lastCommit.hexsha[:7]
    # Remote origin URL
    remoteUrl = repo.remotes.origin.url.replace("git@github.com:", "https://github.com/").removesuffix(".git")
    # Commit date as ISO string
    commitDate = lastCommit.committed_datetime
    html = (f"Version <a href=\"{remoteUrl}/commit/{shortHash}\">{shortHash}</a> "
        f"changed at {commitDate.strftime("%H:%M on %Y-%m-%d")} "
        f"by {lastCommit.author.name} "
        f"(<a href=\"mailto:{lastCommit.author.email}\">{lastCommit.author.email}</a>)")
    print(html, type(html))
    return html

def readConfig(argv):
    if not argv or len(argv) < 2:
        print(f"Please provide a config file path as first argument.")
        sys.exit(1)
    if not Path(argv[1]).is_file():
        print(f"Given config file '{argv[1]}' does not exist! Giving up.")
        sys.exit(1)
    # config configuration values
    config = {}
    with open(argv[1]) as fd:
        config = json.load(fd)
        config["proxyURL"] = f"{config["proxyProto"]}://{config["proxyAddr"]}:{config["proxyPort"]}"
    with open("qrcode.min.js") as fd:
        config["qrcode"] = fd.read()
    with open("img/keyvisual_datastore_pur_bg_square.png", "rb") as fd:
        config["logoBase64"] = base64.b64encode(fd.read()).decode('utf-8')
    config["gitinfo"] = gitInfo()
    return config

def create_app(config):
    app = Flask(__name__)
    print(f"Using the following config: ")
    pprint.pprint({k:v for k,v in config.items()
                   if k not in ("qrcode","logoBase64")})
    print(f"Run the web server with:\n"
            f"    python3 -m http.server -b {config["proxyAddr"]} {config["webPort"]}\n")
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
    config = readConfig(sys.argv)
    app = create_app(config)
    app.run(debug=True, use_reloader=False,
            host=config["proxyAddr"], port=config["proxyPort"])
