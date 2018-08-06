from flask import Flask
from flask_env import MetaFlaskEnv


class Configuration(metaclass=MetaFlaskEnv):
    MESSAGE = 'Hello, World!'


app = Flask(__name__)
app.config.from_object(Configuration)


@app.route('/')
def hello_world():
    return app.config['MESSAGE']


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80, debug=True, use_reloader=False, threaded=False)
