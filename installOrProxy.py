#!/usr/bin/env python3
# A CORS proxy during development
# allows access to an API running on another domain than the web app working on

from flask import Flask, request, jsonify
from pathlib import Path
import requests
import sys
import pprint
import json
import base64

infn = "index.html.tmpl"
outfn = "index.html"

# change server address to match the proxy address here


def update_index(config):
    with open(infn) as fd:
        # read and workaround curly brackets in JS code
        html = fd.read().replace("{", "{{").replace("}", "}}")
        html = html.replace("{{{{", "{").replace("}}}}", "}")
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
    remoteUrl = repo.remotes.origin.url.replace(
        "git@github.com:", "https://github.com/").removesuffix(".git")
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
        config["proxyURL"] = f"{config["proxyProto"]
                                }://{config["proxyAddr"]}:{config["proxyPort"]}"
    with open("qrcode.min.js") as fd:
        config["qrcode"] = fd.read()
    with open("img/keyvisual_datastore_pur_bg_square.png", "rb") as fd:
        config["logoBase64"] = base64.b64encode(fd.read()).decode('utf-8')
    with open("img/repo_qr.png", "rb") as fd:
        config["repoQRBase64"] = base64.b64encode(fd.read()).decode('utf-8')
    config["gitinfo"] = gitInfo()
    print(f"Using the following config: ")
    pprint.pprint({k: v for k, v in config.items()
                   if k not in ("qrcode", "logoBase64", "repoQRBase64")})
    return config


def create_app(config):
    app = Flask(__name__)
    print(f"Run the web server with:\n"
          f"    python3 -m http.server -b {config["proxyAddr"]} {config["webPort"]}\n")

    @app.after_request
    def after_request(response):
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Headers',
                             'Content-Type,Authorization,append,delete,entries,foreach,get,has,keys,set,values')
        response.headers.add('Access-Control-Allow-Methods',
                             'GET,PUT,POST,DELETE,OPTIONS')
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
            verify=False)  # change this to False for selfsigned certs
        response = requests.request(**requestArgs)
        return response.content, response.status_code

    return app


def upload(config):
    print("Uploading app:")
    from jupyter_analysis_tools.datastore import DataStore
    ds = DataStore(config["siteURL"], username=config["uploadUsername"])
    filename = outfn
    spaceName = ds.userspace
    projectName = "NEXT_PROJECT"
    collectionName = "example_collection"
    datasetType = "SOURCE_CODE"
    props = {"$name": config["appTitle"],
             "$show_in_project_overview": True,
             "$document": f"Please find the <p><strong>{config["appTitle"]}</strong></p> "
             f"as {datasetType} dataset, attached here."}
    obj = ds.createObject(projectName, collectionName, space=spaceName,
                          objType="ENTRY", props=props)
    obj.save()
    # print(obj)
    ds.uploadDataset(obj, datasetType, filename)
    data = obj.get_datasets(type="SOURCE_CODE")
    # file path would be f"{ds.url}/datastore_server/{data[0].permId}/original/index.html"
    # -> but missing session token here, exists in browser only, therefore link to parent:
    print(f"App was uploaded as {datasetType} dataset of object {
          obj.identifier}, link:")
    print(f"{ds.url}/openbis/webapp/eln-lims/?menuUniqueId=%7B%22type%22:%22EXPERIMENT%22,%22id%22:%22{
          obj.collection.permId}%22%7D&viewName=showViewDataSetPageFromPermId&viewData=%22{data[0].permId}%22")


if __name__ == '__main__':
    config = readConfig(sys.argv)
    update_index(config)
    if "uploadNoProxy" in config and config["uploadNoProxy"]:
        upload(config)
    else:
        print("Launching proxy app ...")
        app = create_app(config)
        app.run(debug=True, use_reloader=False,
                host=config["proxyAddr"], port=config["proxyPort"])
