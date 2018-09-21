#!/usr/bin/env python

if __name__ == '__main__':
    ###############################################################
    # Change the following line to import your flask application! #
    ###############################################################
    from users import app

    try:
        from pudb import set_trace
    except ImportError:
        pass
    else:
        set_trace(paused=False)
    app.run(host='0.0.0.0', port=app.config.get('PORT', 8000), debug=True, use_reloader=False, threaded=False)
