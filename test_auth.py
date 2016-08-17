#!/usr/bin/python3

import os
from functools import wraps
from flask import Flask, request, render_template, send_from_directory, Markup, session, redirect, Response
from flask_restful import Resource, Api, reqparse
from jinja2.exceptions import  *
from auth import requires_auth

app = Flask(__name__)
api = Api(app)


# TODO Temporary auth
@app.route("/auth", methods=["POST"])
def auth_api():
    from pyquery import PyQuery as pq
    xml = pq(request.get_data())
    elements = xml("message_header security username,password")
    username = elements[0].text if elements[0].tag == "username" else elements[1].text
    password = elements[0].text if elements[0].tag == "password" else elements[1].text
    response_filename = "UserAuthResponse_Success.xml" if username == "admin" and password == "1234" else "UserAuthResponse_Failure.xml"
    with open("templates/" + response_filename, "r") as f:
        return f.read()




app.secret_key = b'YnFGsh7vXDu72hjp7mbhTQQk'
if __name__ == '__main__':
    app.run(debug=True, port=5001)