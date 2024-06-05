from flask import Flask, render_template, request, jsonify, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_caching import Cache
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from flask_bcrypt import Bcrypt
import logging, os
from werkzeug.utils import secure_filename

logging.basicConfig()
logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)

#Логин
logging.basicConfig()
logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)

#Инициализация Flask
app = Flask(__name__)
#Кэширование
cache = Cache(app, config={'CACHE_TYPE': 'simple'})  

#Фото папка
app.config['UPLOAD_FOLDER'] = 'static/photos'

#Настройка базы данных через SQLAlchemy
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///employees.db'
app.config['SECRET_KEY'] = '\x1e\x99\x9b\x80\xea<\x89\xa6\xc6\xfc\xc5\xc8]\xa6\xa3\xd9\x00E8\x89N\xb4\xc7'
db = SQLAlchemy(app)
bcrypt = Bcrypt(app)

#Настройка Flask-Login
login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.login_message_category = 'info'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

#Модель базы пользователей
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(60), nullable=False)
    photo = db.Column(db.String(100), nullable=True) 

    def save_photo(self, photo):
        if photo:
            photo_filename = secure_filename(photo.filename)
            photo_path = os.path.join(app.config['UPLOAD_FOLDER'], photo_filename)
            photo.save(photo_path)
            self.photo = photo_filename
            db.session.commit() 
            return True
        return False

#Модель базы данных
class Employee(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(100), nullable=False)
    position = db.Column(db.String(100), nullable=False)
    hire_date = db.Column(db.Date, nullable=False)
    salary = db.Column(db.Float, nullable=False)
    manager_id = db.Column(db.Integer, db.ForeignKey('employee.id'))
    manager = db.relationship('Employee', remote_side=[id], backref='subordinates')

    def __repr__(self):
        return f'<Employee {self.id}: {self.full_name}, {self.position}>'

#Функция для сортировки и поиска
def get_employees(sort_by, search_query, page, per_page):
    query = Employee.query

    if search_query:
        search = f"%{search_query}%"
        query = query.filter(
            db.or_(
                Employee.full_name.ilike(search),
                Employee.position.ilike(search),
                Employee.hire_date.ilike(search),
                Employee.salary.ilike(search)
            )
        )

    if sort_by == 'manager':
        employees = query.order_by(Employee.manager_id).paginate(page=page, per_page=per_page)
    else:
        employees = query.order_by(getattr(Employee, sort_by)).paginate(page=page, per_page=per_page)

    return employees


#AJAX-маршрут для получения списка сотрудников
@app.route('/ajax_list')
def ajax_list(next_page):
    sort_by = request.args.get('sort_by', 'id')
    search_query = request.args.get('search', '')
    page = request.args.get('page', next_page)  #Получаем номер страницы из запроса
    per_page = 1000  #Задаем количество записей на странице

    employees = get_employees(sort_by, search_query, page, per_page)

    return render_template('employee_table.html', employees=employees.items, int=int)

#Страница всех сотрудников
@app.route('/')
def index():
    sort_by = request.args.get('sort_by', 'id')
    search_query = request.args.get('search', '')
    page = request.args.get('page', 1)  #Получаем номер страницы из запроса, по умолчанию 1
    per_page = 1000  #Задаем количество записей на странице

    employees = get_employees(sort_by, search_query, page, per_page)

    return render_template('index.html', employees=employees.items, int=int)


#Иерархия
#AJAX-маршрут для получения подчиненных сотрудника
@app.route('/ajax_subordinates/<int:employee_id>', methods=['GET'])
def ajax_get_subordinates(employee_id):
    employee = Employee.query.get(employee_id)
    subordinates = []
    if employee:
        for subordinate in employee.subordinates:
            subordinates.append({
                'id': subordinate.id,
                'full_name': subordinate.full_name,
                'position': subordinate.position,
                'has_subordinates': len(subordinate.subordinates) > 0
            })
    return jsonify(subordinates)

#Страница иерархии сотрудников
@app.route('/list')
def list():
    #Фильтр по первым сотрудникам без начальников
    root_employees = Employee.query.filter(Employee.manager_id.is_(None)).all()
    return render_template('list.html', root_employees=root_employees)

#Маршрут для регистрации
@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
        user = User(username=username, email=email, password=hashed_password)
        db.session.add(user)
        db.session.commit()
        flash('Ваш аккаунт был успешно зарегистрирован, вы можете войти теперь.', 'success')
        return redirect(url_for('login'))
    return render_template('register.html')

#Маршрут для входа
@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        user = User.query.filter_by(email=email).first()
        if user and bcrypt.check_password_hash(user.password, password):
            login_user(user)
            return redirect(url_for('index'))
        else:
            flash('Не получилось войти. Проверьте пароль и логин', 'danger')
    return render_template('login.html')

#Маршрут для выхода
@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index'))

#Страница профиля пользователя (только для авторизованных пользователей)
@app.route('/account')
@login_required
def account():
    return render_template('account.html')

@app.route('/upload_photo', methods=['POST'])
def upload_photo():
    if 'photo' in request.files:
        photo = request.files['photo']
        # Сохранение файла на сервере, в папке static/photos
        photo.save(os.path.join(app.config['UPLOAD_FOLDER'], photo.filename))
        current_user.photo = photo.filename
        db.session.commit()
        flash('Фотография успешно загружена', 'success')
    else:
        flash('Фотография не была загружена', 'danger')
    return redirect(url_for('account'))

@app.route('/account_settings', methods=['GET', 'POST'])
@login_required
def account_settings():
    if request.method == 'POST':
        #Получение данных из формы
        username = request.form['username']
        email = request.form['email']
        photo = request.files['photo']

        #Обновление данных текущего пользователя
        current_user.username = username
        current_user.email = email
        if photo:
            current_user.save_photo(photo)

        #Сохранение изменений в базе данных
        db.session.commit()

        #Перенаправление на страницу аккаунта после сохранения изменений
        return redirect(url_for('account'))

    #Возвращение шаблона
    return render_template('account_settings.html')

if __name__ == "__main__":
    # with app.app_context():
    #     db.create_all()
    app.run(debug=True)