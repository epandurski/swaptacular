#!/usr/bin/env python

#######################################################################
# Change the following lines to import/create your flask application! #
#######################################################################
from users import create_app

app = create_app()


if __name__ == '__main__':
    try:
        from pudb import set_trace
    except ImportError:
        pass
    else:
        set_trace(paused=False)
    app.run(host='0.0.0.0', port=app.config.get('PORT', 8000), debug=True, use_reloader=False, threaded=False)
