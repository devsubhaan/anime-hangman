"""Taken from CS50 Finance project but modified."""
from flask import redirect, render_template, session
from functools import wraps


def apology(message, code=400):
    def escape(s):
        for old, new in [
            ("-", "--"),
            (" ", "-"),
            ("_", "__"),
            ("?", "~q"),
            ("%", "~p"),
            ("#", "~h"),
            ("/", "~s"),
            ('"', "''"),
        ]:
            s = s.replace(old, new)
        return s

    return render_template(
        "apology.html", top=code, bottom=escape(message), message=message
    ), code

def loginRequired(f):
    @wraps(f)
    def decoratedFunction(*args, **kwargs):
        if session.get("user_id") is None:
            return redirect("/login")
        return f(*args, **kwargs)

    return decoratedFunction
