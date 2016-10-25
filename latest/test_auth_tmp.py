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
        "full_name": "Pralav Dessai",
        "username": "admin",
        "password": "1234",
        "session_ids": [

        ],
        "is_admin": True,
    },
    "user": {
        "full_name": "Pralav Dessai",
        "username": "user",
        "password": "1234",
        "session_ids": [

        ],
        "is_admin": False,
    }
}

sessions = dict()
for user in users:
    user = users[user]
    for session_id in user["session_ids"]:
        sessions[session_id] = user


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
            # FIXME id generator may be faulty
            session_id = "%020x" % getrandbits(80)
            while session_id in sessions:
                session_id = "%020x" % getrandbits(80)
            sessions[session_id] = user
            user["session_ids"].append(session_id)

    context["type"] = "DONE"
    context["message"] = "PM processing completed"
    context["user"] = user
    context["session_id"] = session_id
    return render_template("UserAuthResponse.xml", c=context)


app.secret_key = b'YnFGsh7vXDu72hjp7mbhTQQk'
if __name__ == '__main__':
    app.run(debug=True, port=5001)