from flask import Flask, render_template

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/p2p/flow_mod')
def flow_modify():
    return render_template('flow_modify.html')

@app.route('/p2p/connect')
def peer_connect():
    return render_template('peer_connect.html')


if __name__ == '__main__':
    app.run(debug=True)