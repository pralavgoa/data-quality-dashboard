#!/usr/bin/python3

import os
from functools import wraps
from flask import Flask, request, render_template, send_from_directory, Markup, session, redirect, Response, url_for
from flask_restful import Resource, Api, reqparse
from jinja2.exceptions import *
from werkzeug.exceptions import *
from auth import requires_auth, requires_auth_html, authenticate, logout, requires_auth_data_role
from dashdb import get_tab_data, get_comments, set_comment, get_tab4_data

app = Flask(__name__)

import data_api
data_api.init(app)


@app.route("/")
def redirect_home():
    return redirect(url_for("send_html", html="tab_1.html"), 301)


@app.route('/html/<string:html>')
@requires_auth_html
def send_html(html=None):
    if not html:
        html = "tab_1.html"
    config = dict()
    if html == "tab_4.html":
        config["data"] = get_tab4_data()
    try:
        return render_template(html, selected=html, full_user_name=session.get("full_name"), config=config)
    except TemplateNotFound:
        return "Page not found: 404", 404


@app.route("/login.html")
def login_html():
    return render_template("login.html")


@app.route("/auth", methods=["POST"])
def auth_url():
    if "login_redirect" not in session:
        session["login_redirect"] = request.environ.get("HTTP_REFERER") or url_for("send_html", html="tab_1.html")
    if "/login.html" in session["login_redirect"]:
        session["login_redirect"] = url_for("send_html", html="tab_1.html")

    username = request.args.get("username", request.form.get("username", ""))
    password = request.args.get("password", request.form.get("password", ""))
    if username and password and authenticate(username=username, password=password):
        return redirect(session.pop("login_redirect"))
    return redirect(url_for("login_html"))


@app.route("/logout")
def logout_url():
    logout()
    return redirect(request.environ.get("HTTP_REFERER") or "/")


app.secret_key = b'YnFGsh7vXDu72hjp7mbhTQQf'  # change key to reset all sessions
if __name__ == '__main__':
    try:
        app.run(debug=True, port=80)
    except:
        try:
            app.run(debug=True)
        except:
            print("No connection")
