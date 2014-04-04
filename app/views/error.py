import sys
import traceback

from flask import render_template
from app import app
from markdown2 import markdown

ERROR_MESSAGES = {
    403: 'Tsk Tsk. You shouldn\'t be here.',
    404: 'Huh? That page doesn\'t even exist.',
    500: 'Dang. Something broke.'
}


def catchall_error_handler(error):
    error.code = getattr(error, 'code', 500)  # default uncaught errors to HTTP 500 error
    error.description = getattr(error, 'description', 'An uncaught error has occurred.')
    error.message = ERROR_MESSAGES.get(error.code, 'Congrats! You found an unknown error.')
    error.stacktrace = traceback.format_exception(*sys.exc_info())

    return render_template('error.html', error=error), error.code


for code in ERROR_MESSAGES.keys():
    app.register_error_handler(code, catchall_error_handler)
