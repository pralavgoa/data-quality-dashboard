
import re
from functools import wraps
from flask import Response, request, render_template, redirect, session
from flask_restful import reqparse
from defusedxml import cElementTree
from urllib.request import urlopen
from pyquery import PyQuery as pq
from time import time

session_arg_parser = reqparse.RequestParser()
session_arg_parser.add_argument("session_id", type=str)
session_arg_parser.add_argument("username", type=str)
session_arg_parser.add_argument("password", type=str)


def authenticate(session_id=None, username=None, password=None):
    """This function is called to check if a username /
    password combination is valid.
    """
    # Prepare request XML
    if session_id:
        xml = render_template("UserAuthRequest.xml", session_id=session_id)
    else:
        xml = render_template("UserAuthRequest.xml", username=username, password=password)
    # TODO use HTTPS and change address/port
    # Send request and get response
    try:
        response = urlopen("http://localhost:5001/auth", xml.encode("utf8"))
    except:
        # No connection to rest_server
        return False
    if response.code != 200:
        return False
    xml = pq(response.read())
    elements = xml("response_header result_status status")
    if not len(elements):
        return False
    status, text = elements[0].attrib["type"], elements[0].text
    if status == "ERROR":
        return False
    if status == "DONE":
        elements = xml("message_body user > full_name,user_name,password,is_admin")
        full_name_element, user_name_element, pass_element, is_admin_element = elements[:4]
        session_id = re.findall("SessionKey:(.+)", pass_element.text)[0]
        session_expire = pass_element.attrib["token_ms_timeout"]
        session["session_id"] = session_id
        session["session_expire"] = time() + int(session_expire)
        session["full_name"] = full_name_element.text
        session["user_name"] = user_name_element.text
        session["is_admin"] = True if is_admin_element.text == "true" else False
        session["role"] = "admin" if is_admin_element.text == "true" else "user"
        return True


def check_auth(ok_func, fail_func):
    args = session_arg_parser.parse_args()
    session_id = args["session_id"]
    if session_id:
        # Check new session_id
        if authenticate(session_id=session_id):
            return ok_func()
        else:
            return fail_func()
    else:
        # Check new username and password
        username = args["username"]
        password = args["password"]
        if username or password:
            if authenticate(username=username, password=password):
                return ok_func()
            else:
                return fail_func()
        else:
            # Check old session_id
            session_id = session.get("session_id")
            if session_id:
                if authenticate(session_id=session_id):
                    return ok_func()
                else:
                    return fail_func()
            else:
                return fail_func()


def requires_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        return check_auth(lambda: f(*args, **kwargs), lambda: Response(
                'Please authenticate', 401,
                {'WWW-Authenticate': 'Basic realm="Login Required"'}))
    return decorated


def requires_auth_html(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        # TODO this check no longer needed
        if request.path == '/login.html':
            return f(*args, **kwargs)
        session["login_redirect"] = request.path
        return check_auth(lambda: f(*args, **kwargs), lambda: redirect("/login.html"))
    return decorated


def requires_auth_data_role(*roles):
    def wrap(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            # Check if logged in
            response =  check_auth(lambda: None, lambda: Response(
                'Please authenticate', 401,
                {'WWW-Authenticate': 'Basic realm="Login Required"'}))

            if not response:
                # Not logged in, return the "not logged in" response
                return response

            # Check user permissions(role)
            if session["role"] in roles:
                # Permissions ok
                return f(*args, **kwargs)
            else:
                # Not permitted
                return Response(
                    'Please authenticate', 401,
                    {'WWW-Authenticate': 'Basic realm="Login Required"'})
        return decorated
    return wrap



def logout():
    session.pop("session_id")
    session.pop("session_expire")
    session.pop("full_name")
    session.pop("is_admin")
    session.pop("role")
    session["login_redirect"] = request.environ.get("HTTP_REFERER") or "/"