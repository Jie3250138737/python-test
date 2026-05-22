from flask import Flask, render_template, request, redirect, url_for, session, flash
import pymysql
from functools import wraps

app = Flask(__name__)
# 用于 session 和 flash 消息的密钥
app.secret_key = 'super_secret_key_student_grade'


# --- 数据库连接配置 (已适配你的环境) ---
def get_db_connection():
    return pymysql.connect(
        host='localhost',
        port=3306,
        user='root',
        password='root',  # ⚠️ 必须修改：换成你真实的 MySQL root 密码
        database='student_grade',
        cursorclass=pymysql.cursors.DictCursor
    )


# --- 登录拦截装饰器 ---
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'logged_in' not in session:
            flash('请先登录系统', 'danger')
            return redirect(url_for('login'))
        return f(*args, **kwargs)

    return decorated_function


# --- 路由：登录 ---
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        conn = get_db_connection()
        with conn.cursor() as cursor:
            sql = "SELECT * FROM user WHERE username=%s AND password=%s"
            cursor.execute(sql, (username, password))
            user = cursor.fetchone()
        conn.close()

        if user:
            session['logged_in'] = True
            session['username'] = user['username']
            return redirect(url_for('index'))
        else:
            flash('用户名或密码错误，请重试', 'danger')

    return render_template('login.html')


# --- 路由：退出登录 ---
@app.route('/logout')
def logout():
    session.clear()
    flash('已安全退出', 'success')
    return redirect(url_for('login'))


# --- 路由：主页 ---
@app.route('/')
@login_required
def index():
    return render_template('index.html', username=session.get('username'))


# --- 路由：成绩录入 ---
@app.route('/add', methods=['GET', 'POST'])
@login_required
def add_grade():
    if request.method == 'POST':
        student_id = request.form['student_id']
        name = request.form['name']
        chinese = request.form['chinese']
        math = request.form['math']
        english = request.form['english']
        physics = request.form['physics']
        chemistry = request.form['chemistry']

        conn = get_db_connection()
        try:
            with conn.cursor() as cursor:
                sql = """INSERT INTO grade
                             (student_id, name, chinese, math, english, physics, chemistry)
                         VALUES (%s, %s, %s, %s, %s, %s, %s)"""
                cursor.execute(sql, (student_id, name, chinese, math, english, physics, chemistry))
            conn.commit()
            flash('成绩录入成功！', 'success')
        except pymysql.IntegrityError:
            flash('学号已存在，录入失败！', 'danger')
        finally:
            conn.close()
        return redirect(url_for('manage_grades'))

    return render_template('add.html')


# --- 路由：成绩管理（展示与删除） ---
@app.route('/manage')
@login_required
def manage_grades():
    conn = get_db_connection()
    with conn.cursor() as cursor:
        cursor.execute("SELECT * FROM grade ORDER BY id DESC")
        grades = cursor.fetchall()
    conn.close()
    return render_template('manage.html', grades=grades)


# --- 路由：删除成绩 ---
@app.route('/delete/<int:id>')
@login_required
def delete_grade(id):
    conn = get_db_connection()
    with conn.cursor() as cursor:
        cursor.execute("DELETE FROM grade WHERE id=%s", (id,))
    conn.commit()
    conn.close()
    flash('记录已删除', 'success')
    return redirect(url_for('manage_grades'))


# --- 路由：修改成绩 ---
@app.route('/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_grade(id):
    conn = get_db_connection()
    if request.method == 'POST':
        name = request.form['name']
        chinese = request.form['chinese']
        math = request.form['math']
        english = request.form['english']
        physics = request.form['physics']
        chemistry = request.form['chemistry']

        with conn.cursor() as cursor:
            sql = """UPDATE grade \
                     SET name=%s, \
                         chinese=%s, \
                         math=%s, \
                         english=%s, \
                         physics=%s, \
                         chemistry=%s \
                     WHERE id = %s"""
            cursor.execute(sql, (name, chinese, math, english, physics, chemistry, id))
        conn.commit()
        conn.close()
        flash('成绩更新成功！', 'success')
        return redirect(url_for('manage_grades'))

    with conn.cursor() as cursor:
        cursor.execute("SELECT * FROM grade WHERE id=%s", (id,))
        grade = cursor.fetchone()
    conn.close()
    return render_template('edit.html', grade=grade)


# --- 路由：成绩查询 ---
@app.route('/search', methods=['GET', 'POST'])
@login_required
def search_grade():
    grades = []
    has_searched = False

    if request.method == 'POST':
        keyword = request.form['keyword']
        search_type = request.form['search_type']
        has_searched = True

        conn = get_db_connection()
        with conn.cursor() as cursor:
            if search_type == 'student_id':
                sql = "SELECT * FROM grade WHERE student_id = %s"
            else:
                sql = "SELECT * FROM grade WHERE name LIKE %s"
                keyword = f"%{keyword}%"

            cursor.execute(sql, (keyword,))
            grades = cursor.fetchall()
        conn.close()

    return render_template('search.html', grades=grades, has_searched=has_searched)


if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True, port=5000)