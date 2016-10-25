# Place all data APIs here, including REST comments, graph, tree...

import json
from flask import send_from_directory, Response, request, session
from flask_restful import Resource, Api, reqparse
from werkzeug.exceptions import *
from datetime import datetime

from auth import requires_auth
from dashdb import set_comment, get_comments, insert_comment, get_tab_data, update_comment_visibility
from helpers import get_arg


def json_serial(obj):
    """JSON serializer for objects not serializable by default json code"""

    if isinstance(obj, datetime):
        serial = obj.isoformat()
        return serial
    raise TypeError ("Type not serializable")


def init(_app):
    global app, api
    app = _app
    api = Api(app)
    api.add_resource(Comment, '/comment', '/comment/<int:id>')

    @app.route("/data/<path:path>")
    @requires_auth
    def send_csv(path):
        return send_from_directory("data", path)

    @app.route("/api/data/<string:tab>", methods=["GET", "POST"])
    @requires_auth
    def data_api(tab):
        data = get_tab_data(tab)
        if isinstance(data, Response):
            return data
        return Response(json.dumps(data, default=json_serial, ensure_ascii=False).encode("utf8"), data.get("code", 200), mimetype="application/json")

    @app.route("/api/comment/update", methods=["GET", "POST"])
    @requires_auth
    def update_comment():
        comment_id = get_arg("comment_id")
        is_public = get_arg("is_public")
        if not comment_id.isdigit():
            return Response(json.dumps(dict(
                result="error",
                error_message="Invalid comment_id format, must be numeric"
            )))
        if not is_public.isdigit():
            return Response(json.dumps(dict(
                result="error",
                error_message="Invalid is_public format, must be numeric"
            )))
        update_comment_visibility(comment_id, is_public)
        return Response(json.dumps(dict(result="success")))


class Comment(Resource):
    def __init__(self):
        self.reqparse = reqparse.RequestParser()
        self.reqparse.add_argument("ontology_id", required=True, type=int, help="Missing or invalid 'id' paremeter")
        self.reqparse.add_argument("hospital", required=True, type=str, help="Missing 'hospital' parameter")
        self.reqparse.add_argument("comment", required=True, type=str, help="Missing 'comment' parameter")

    @requires_auth
    def get(self, id=None):
        comments = get_comments(id)
        if not comments:
            return {
                "result": "error",
                "error_message": "Comment id not found"
            }, 404
        return {
            "result": "success",
            "role": session["role"],
            "comments": comments
        }

    @requires_auth
    def post(self):
        try:
            args = self.reqparse.parse_args()
        except BadRequest as ex:
            return {
                "result": "error",
                "error_message": list(ex.data["message"].values())[0]
            }, 400

        ontology_id = args["ontology_id"]
        hospital = args["hospital"]
        comment = args["comment"]
        insert_comment(ontology_id, hospital, comment)
