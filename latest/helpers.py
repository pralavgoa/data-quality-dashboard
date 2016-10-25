from flask import request

def get_arg(name, default=None):
    return request.args.get(name, request.form.get(name, default))