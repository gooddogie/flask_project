from flask import Flask, render_template, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_caching import Cache
import logging
logging.basicConfig()
logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)

#Инициализация Flask
app = Flask(__name__)
#Кэширование
cache = Cache(app, config={'CACHE_TYPE': 'simple'})  

#Настройка базы данных через SQLAlchemy
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///employees.db'
db = SQLAlchemy(app)

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

if __name__ == "__main__":
    # with app.app_context():
    #     db.create_all()
    app.run(debug=True)