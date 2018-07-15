@app.route('/')
@app.route('/index')
def index():
    return "Index Pages"