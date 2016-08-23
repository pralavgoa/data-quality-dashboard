
from functools import wraps
from flask import Response, request, render_template
from defusedxml import cElementTree
from urllib.request import urlopen
from pyquery import PyQuery as pq



"""
We have an "xml" based authentication api. This api "accepts" an xml file (which has username/password along with some other things).
This api returns an xml, that tells you whether the user got authenticated or not. If user got authenticated,
it returns the user roles. I will share a sample request-xml, as well as response-xml for success/failure cases with you in google drive.

Task 1.c: Here's the mechanism i'd like you to implement:
the "check_auth" function changes:- this function should generate the "request-xml" using username and password and post it to the backed authentication api.
Since you don't have access to the backend api, you can create a dummy auth api that returns "success-xml" if username/password is correct,
and "failure-xml" if incorrect, using the sample xmls i have shared. The "check_auth" function should then parse this response xml,
and return with "sucess" or "failure" accordingly. Please convert the xmls i share with you into templates,
making only username/password as variables. Also use a good python xml library for xml parsing. This way the code will be cleaner.
"""


def check_auth(username, password):
    """This function is called to check if a username /
    password combination is valid.
    """
    xml = render_template("UserAuthRequest.xml", username=username, password=password)
    # TODO use HTTPS and change address/port
    #response = urlopen("http://localhost:5001/auth", xml.encode("utf8"))
    response = urlopen("http://164.67.204.132/devladrshrine/shrine-proxy/request", xml.encode("utf-8"))
    if response.code != 200:
        return False
    response_string=response.read()
    xml = pq(response_string)
    elements = xml("response_header result_status status")
    if not len(elements):
        print("Response header not found")
        return False
    status, text = elements[0].attrib["type"], elements[0].text
    if status == "ERROR":
        return False
    #return username == 'admin' and password == '1234'
    return True

def authenticate():
    """Sends a 401 response that enables basic auth"""
    return Response(
    'Please authenticate', 401,
    {'WWW-Authenticate': 'Basic realm="Login Required"'})


def requires_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.authorization
        if not auth or not check_auth(auth.username, auth.password):
            return authenticate()
        return f(*args, **kwargs)
    return decorated