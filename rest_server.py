#!/usr/bin/python3

import os
from functools import wraps
from flask import Flask, request, render_template, send_from_directory, Markup, session, redirect, Response
from flask_restful import Resource, Api, reqparse
from jinja2.exceptions import  *
from auth import requires_auth

app = Flask(__name__)
api = Api(app)

comments = {}
for i in range(1, 50):
    comments[i] = "comment number %s" % i

parser = reqparse.RequestParser()
parser.add_argument('id')
parser.add_argument('comment')


class Comment(Resource):
    def get(self, id=None):
        comment = comments.get(id)
        if not comment:
            # TODO could return http code also, 404
            return {
                "result": "error",
                "error_message": "Comment id not found"
            }
        return {
            "result": "success",
            "comment": comment
        }

    def post(self):
        #json_data = request.get_json(force=True)
        #id = json_data.get("id")
        args = parser.parse_args()
        try:
            id = int(args['id']) # comment ids are numeric
        except ValueError:
            id = None
        if not id:
            # TODO could return http code also
            return {
                "result": "error",
                "error_message": "Invalid id format"
            }
        comment = args.get("comment")
        if not comment:
            # TODO could return http code also
            return {
                "result": "error",
                "error_message": "Comment must not be empty"
            }
        comments[id] = comment
        return {
            "result": "success"
        }

api.add_resource(Comment, '/comment', '/comment/<int:id>')


@app.route("/")
def redirect_home():
    return redirect("/html/tab_1.html", 301)

@app.route('/html/<string:html>')
def tab1_page(html=None):
    if not html:
        html = "tab_1.html"
    try:
        return render_template(html)
    except TemplateNotFound:
        return Response("Page not found: 404", 404)


@app.route("/javascript/<path:path>")
def send_js(path):
    return send_from_directory("javascript", path)


@app.route("/data/<path:path>")
@requires_auth
def send_data(path):
    return send_from_directory("data", path)


app.secret_key = b'YnFGsh7vXDu72hjp7mbhTQQk'
if __name__ == '__main__':
    app.run(debug=True)