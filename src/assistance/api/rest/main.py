import logging
logging.getLogger().setLevel(logging.DEBUG)
import sys
import os
from dateutil import parser

from werkzeug.contrib.fixers import ProxyFix

from flask import Flask, abort, make_response, jsonify, url_for, request, json
from flask_jsontools import jsonapi
from dateutil import parser

from rest_utils import register_encoder

from assistance.model.AssistanceModel import AssistanceModel
from assistance.model import Session

# set the project root directory as the static folder, you can set others.
app = Flask(__name__, static_url_path='/src/sileg/web')
app.wsgi_app = ProxyFix(app.wsgi_app)
register_encoder(app)

API_BASE = os.environ['API_BASE']

@app.route(API_BASE + '/usuarios/', methods=['GET', 'OPTIONS'], defaults={'uid':None})
@app.route(API_BASE + '/usuarios/<uid>', methods=['GET', 'OPTIONS'])
@jsonapi
def usuarios(uid=None):
    search = request.args.get('q',None)
    offset = request.args.get('offset',None,int)
    limit = request.args.get('limit',None,int)
    c = request.args.get('c',False,bool)

    if uid:
        return AssistanceModel.usuario(uid, retornarClave=c)
    else:
        fecha_str = request.args.get('f', None)
        fecha = parser.parse(fecha_str) if fecha_str else None
        return AssistanceModel.usuarios(search=search, retornarClave=c, offset=offset, limit=limit, fecha=fecha)


@app.after_request
def cors_after_request(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE')
    return response

@app.after_request
def add_header(r):
    """
    Add headers to both force latest IE rendering engine or Chrome Frame,
    and also to cache the rendered page for 10 minutes.
    """
    r.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    r.headers["Pragma"] = "no-cache"
    r.headers["Expires"] = "0"
    r.headers['Cache-Control'] = 'public, max-age=0'

    return r

def main():
    app.run(host='0.0.0.0', port=5000, debug=True)

if __name__ == '__main__':
    main()
