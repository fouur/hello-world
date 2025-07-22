import os
import sqlite3
from flask import Flask, request, redirect, url_for, render_template_string

DB_PATH = os.path.join(os.path.dirname(__file__), 'tags.db')

app = Flask(__name__)

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS tags (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            color TEXT NOT NULL
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS file_tags (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            file_path TEXT NOT NULL,
            tag_id INTEGER NOT NULL,
            FOREIGN KEY(tag_id) REFERENCES tags(id)
        )
    """)
    conn.commit()
    conn.close()

@app.before_first_request
def setup():
    init_db()

@app.route('/')
def index():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    tags = c.execute('SELECT id, name, color, (SELECT COUNT(*) FROM file_tags WHERE tag_id = tags.id) as count FROM tags').fetchall()
    conn.close()
    html = '''
    <html><body>
    <h1>Tags</h1>
    <ul>
    {% for id, name, color, count in tags %}
      <li><a style="background-color: {{color}}; padding: 3px;" href="{{ url_for('view_tag', tag_id=id) }}">{{name}} ({{count}})</a></li>
    {% endfor %}
    </ul>
    <h2>Add Tag</h2>
    <form method="post" action="/add_tag">
      Name: <input name="name" /> Color (css name or hex): <input name="color" />
      <button type="submit">Add</button>
    </form>
    <h2>Tag File</h2>
    <form method="post" action="/tag_file">
      File path: <input name="path" /> Tag:
      <select name="tag_id">
      {% for id, name, color, count in tags %}
        <option value="{{id}}">{{name}}</option>
      {% endfor %}
      </select>
      <button type="submit">Tag File</button>
    </form>
    </body></html>
    '''
    return render_template_string(html, tags=tags)

@app.route('/add_tag', methods=['POST'])
def add_tag():
    name = request.form['name']
    color = request.form['color'] or '#ffffff'
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    try:
        c.execute('INSERT INTO tags (name, color) VALUES (?, ?)', (name, color))
        conn.commit()
    except sqlite3.IntegrityError:
        pass
    conn.close()
    return redirect(url_for('index'))

@app.route('/tag_file', methods=['POST'])
def tag_file():
    path = request.form['path']
    tag_id = request.form['tag_id']
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('INSERT INTO file_tags (file_path, tag_id) VALUES (?, ?)', (path, tag_id))
    conn.commit()
    conn.close()
    return redirect(url_for('index'))

@app.route('/tag/<int:tag_id>')
def view_tag(tag_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    tag = c.execute('SELECT name, color FROM tags WHERE id = ?', (tag_id,)).fetchone()
    files = c.execute('SELECT file_path FROM file_tags WHERE tag_id = ?', (tag_id,)).fetchall()
    conn.close()
    html = '''
    <html><body>
    <h1 style="background-color: {{tag[1]}}; padding: 5px;">{{tag[0]}}</h1>
    <ul>
    {% for (path,) in files %}
      <li>{{path}}</li>
    {% endfor %}
    </ul>
    <a href="{{ url_for('index') }}">Back</a>
    </body></html>
    '''
    return render_template_string(html, tag=tag, files=files)

if __name__ == '__main__':
    app.run(debug=True)
