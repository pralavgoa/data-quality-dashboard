#!/usr/bin/python3

import os
from functools import wraps
from flask import Flask, request, render_template, send_from_directory, Markup, session, redirect, Response
from flask_restful import Resource, Api, reqparse
from pyquery import PyQuery as pq
from random import getrandbits

app = Flask(__name__)
api = Api(app)

users = {
    "admin": {
        "full_name": "Pralav Dessai Admin",
        "username": "admin",
        "password": "11",
        "session_id": "NZFStGkenW25gbicLG6g",
        "is_admin": True,
    },
    "user": {
        "full_name": "Pralav Dessai User",
        "username": "user",
        "password": "11",
        "session_id": "NZFStGkenW25gbicLG6f",
        "is_admin": False,
    },
    "user2": {
        "full_name": "Pralav Dessai User2",
        "username": "user2",
        "password": "11",
        "session_id": "NZFStGkenW25gbicLG6h",
        "is_admin": False,
    }
}

sessions = dict()
for user in users:
    user = users[user]
    sessions[user["session_id"]] = user


@app.route("/auth", methods=["POST"])
def auth_api():
    xml = pq(request.get_data())
    elements = xml("message_header security session_id,username,password")

    params = {}
    for element in elements:
        params[element.tag] = element.text

    context = dict()

    # Check session
    session_id = params.get("session_id")
    user = sessions.get(session_id)
    if not user:
        # Continue down if username or password available
        if not params.get("username") and not params.get("password"):
            context["type"] = "ERROR"
            context["message"] = "Invalid session id"
            return render_template("UserAuthResponse.xml", c=context)
        else:
            # Check username
            user = users.get(params.get("username"))
            if not user:
                context["type"] = "ERROR"
                context["message"] = "Invalid username"
                return render_template("UserAuthResponse.xml", c=context)

            # Check password
            if user["password"] != params.get("password"):
                context["type"] = "ERROR"
                context["message"] = "Invalid password"
                return render_template("UserAuthResponse.xml", c=context)

            # User authenticated
            session_id = user["session_id"]

    context["type"] = "DONE"
    context["message"] = "PM processing completed"
    context["user"] = user
    context["session_id"] = session_id
    return render_template("UserAuthResponse.xml", c=context)


app.secret_key = b'YnFGsh7vXDu72hjp7mbhTQQk'
if __name__ == '__main__':
    app.run(debug=True, port=5001)