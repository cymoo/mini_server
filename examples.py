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
