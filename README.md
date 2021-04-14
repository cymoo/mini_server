# A toy web server

## Intro

It is a minimum (~100 lines) web server which partially implements WSGI protocol.
It handles requests with a thread pool and can work with web frameworks like Django, Flask.

## Usage

```python3
server = MiniServer(('0.0.0.0', 8888))
server.set_application(your_app)
server.run_forever()
```

## Examples

```python
from flask import Flask, jsonify, request
from server import MiniServer


app = Flask(__name__)


@app.route('/')
def index():
    return 'hello web'


# test file uploads
@app.route('/upload', methods=['GET', 'POST'])
def upload():
    if request.method == 'GET':
        return """
        <html>
            <head><title>upload file</title></head>
            <body>
                <h1>upload file</h1>
                <form action="/upload" method="post" enctype="multipart/form-data">
                    <input type="file" name="file" />
                    <hr>
                    <button type="submit">submit</button>
                </form>
            </body>
        </html>
        """
    else:
        file = request.files['file']
        file.save(file.filename)
        return jsonify(status='ok', message='file uploaded')


server = MiniServer(('0.0.0.0', 8888))
server.set_application(app)
server.run_forever()

```

## License

MIT