from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from faker import Faker
from random import randint
from app import app,db,Employee

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///employees.db'
fake = Faker(['ru_RU'])

# class Employee(db.Model):
#     id = db.Column(db.Integer, primary_key=True)
#     full_name = db.Column(db.String(100))
#     position = db.Column(db.String(100))
#     hire_date = db.Column(db.Date)
#     salary = db.Column(db.Float)
#     manager_id = db.Column(db.Integer, db.ForeignKey('employee.id'))
#     subordinates = db.relationship('Employee', backref='manager',remote_side=[id])

# def generate_hierarchy(level, manager=None):
#     if level == 0:
#         return
#     for _ in range(randint(10, 20)):
#         employee = Company(
#             full_name=fake.name(),
#             position=fake.job(),
#             hire_date=fake.date_this_decade(),
#             salary=randint(50000, 250000),
#             manager=manager
#         )
#         db.session.add(employee)
#         db.session.commit()
#         generate_hierarchy(level - 1, manager=employee)

# def trim_employees(limit):
#     # Общее количество
#     total_employees = db.session.query(Company).count()
#     if total_employees > limit:
#         #Подсчет сколько удалять
#         to_delete = total_employees - limit
#         ids_to_delete = db.session.query(Company.id).order_by(Company.id.desc()).limit(to_delete).all()
#         ids_to_delete = [id[0] for id in ids_to_delete]
#         #Удаление сотрудников
#         db.session.query(Company).filter(Company.id.in_(ids_to_delete)).delete(synchronize_session=False)
#         db.session.commit()

def assign_managers():
    employees = Employee.query.all()

    manager_index = 0

    for index, employee in enumerate(employees):
        if index < 9:
            continue
        else:
            #Индекс начальника будет определяться делением индекса сотрудника на 9 (с округлением вниз)
            manager_index = int(index / 9)
            if manager_index < 30:
                print(manager_index)
            #Назначаем начальника для текущего сотрудника
            employee.manager_id = employees[manager_index-1].id
    db.session.commit()


if __name__ == '__main__':
    # pass
    with app.app_context():
        assign_managers()
        # trim_employees(50000)
        #db.create_all()
        #generate_hierarchy(5)

