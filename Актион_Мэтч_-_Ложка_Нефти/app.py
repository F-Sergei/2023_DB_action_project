from flask import Flask, render_template, request, redirect, flash, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin, login_required, login_user, logout_user, LoginManager
from datetime import datetime
import pandas as pd
from werkzeug.security import check_password_hash, generate_password_hash
import os
from dotenv import load_dotenv # Локальные переменные среды

from py_addons.parser import parse_info
from py_addons import gantt

load_dotenv() # Загрузка переменных среды

app = Flask(__name__)
app.secret_key = os.getenv('API_KEY')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///user.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
manager = LoginManager(app)


# --------------------------------------
# Конвертация из кортежа в лист
# --------------------------------------
def convert_to_list(tuple_list, result=None):
    if result is None:
        result = []
    if len(tuple_list) == 0:
        return result
    else:
        result.extend(tuple_list[0])
        return convert_to_list(tuple_list[1:], result)


# --------------------------------------
# Создание комбинаций
# --------------------------------------
def pairs(num, reg, w_type):
    # --------------------------------------
    # Создадим dataframe
    # --------------------------------------
    # Получаем столбцы-кортежи
    names = DataBase.query.with_entities(DataBase.name).all()
    free_d_rigs = DataBase.query.with_entities(DataBase.free_d_rig).all()
    region = DataBase.query.with_entities(DataBase.region).all()
    work_type = DataBase.query.with_entities(DataBase.work_type).all()

    # Преобразуем кортеж в список
    names = convert_to_list(names)
    free_d_rigs = convert_to_list(free_d_rigs)
    region = convert_to_list(region)
    work_type = convert_to_list(work_type)

    df = pd.DataFrame(data={'Компания': names, 'Количество_БУ': free_d_rigs, 'Регион':region, 'Тип_работ':work_type})
    df = df[df['Количество_БУ'] != 0]

    # -----------------
    # Фильтруем по типу работ
    indexes = []
    for el in df.index:
        if w_type in df.loc[el, 'Тип_работ']:
            indexes.append(el)

    df = df.loc[indexes, :]

    del indexes
    # -----------------

    # --------------------------------------
    # Создание комбинаций
    # --------------------------------------
    # Необходимое число БУ
    number = int(num)

    # Поиск пар для составления числа необходимых установок
    counter = 0
    massive = []
    reg_mass_1 = []
    reg_mass_2 = []

    if df.sort_values(by='Количество_БУ', ascending=False).head(2)['Количество_БУ'].sum() >= num:
        for i in range(df.shape[0]):
            flag = 0

            for j in range(i, df.shape[0]):
                if i != j:
                    if (df.loc[i, 'Количество_БУ'] >= number) & (flag != 1):
                        massive.append(df.loc[i, 'Компания'] + ' = ' + str(number))
                        reg_mass_1.append(df.loc[i, 'Регион'])
                        reg_mass_2.append('')
                        flag = 1
                        counter += 1

                    elif (df.loc[i, 'Количество_БУ'] + df.loc[j, 'Количество_БУ'] >= number):
                        if (df.loc[i, 'Количество_БУ'] < df.loc[j, 'Количество_БУ'])&(number - df.loc[i, 'Количество_БУ'] > 0):
                            massive.append(str(df.loc[i, 'Количество_БУ']) + ' от ' +
                                           df.loc[i, 'Компания'] + ' + ' +
                                           str(number - df.loc[i, 'Количество_БУ']) + ' от ' +
                                           df.loc[j, 'Компания'] + ' = ' + str(number))
                            reg_mass_1.append(df.loc[i, 'Регион'])
                            reg_mass_2.append(df.loc[j, 'Регион'])
                            counter += 1

                        else:
                            if (number - df.loc[j, 'Количество_БУ'] > 0):
                                massive.append(str(df.loc[j, 'Количество_БУ']) + ' от ' +
                                               df.loc[j, 'Компания'] + ' + ' +
                                               str(number - df.loc[j, 'Количество_БУ']) + ' от ' +
                                               df.loc[i, 'Компания'] + ' = ' + str(number))
                                reg_mass_1.append(df.loc[i, 'Регион'])
                                reg_mass_2.append(df.loc[j, 'Регион'])
                                counter += 1

        pair = pd.DataFrame(data={'Комбинации': massive, 'Регион первой компании': reg_mass_1, 'Регион второй компании': reg_mass_2})
    else:
        reg_mass_3 = []
        for i in range(df.shape[0]):
            flag = 0

            for j in range(i, df.shape[0]):
                if i != j:
                    if (df.loc[i, 'Количество_БУ'] == number) & (flag != 1):
                        massive.append(df.loc[i, 'Компания'], '=',
                                       df.loc[i, 'Количество_БУ'])
                        reg_mass_1.append(df.loc[i, 'Регион'])
                        reg_mass_2.append('')
                        reg_mass_3.append('')
                        flag = 1
                        counter += 1

                    for p in range(j, df.shape[0]):
                        if j != p:
                            if (df.loc[i, 'Количество_БУ'] + df.loc[j, 'Количество_БУ'] + df.loc[p, 'Количество_БУ'] >= number):
                                massive.append(
                                    str(df.loc[i, 'Количество_БУ']) + ' от ' + df.loc[i, 'Компания'] + ' + ' +
                                    str(df.loc[j, 'Количество_БУ']) + ' от ' + df.loc[j, 'Компания'] + ' + ' +
                                    str(number - df.loc[i, 'Количество_БУ'] - df.loc[j, 'Количество_БУ']) + ' от ' +
                                    df.loc[p, 'Компания'] + ' = ' +
                                    str(df.loc[i, 'Количество_БУ'] + df.loc[i, 'Количество_БУ'] + (
                                                number - (df.loc[i, 'Количество_БУ'] + df.loc[i, 'Количество_БУ'])))
                                    )
                                reg_mass_1.append(df.loc[i, 'Регион'])
                                reg_mass_2.append(df.loc[j, 'Регион'])
                                reg_mass_3.append(df.loc[p, 'Регион'])
                                counter += 1
        pair = pd.DataFrame(data={'Комбинации': massive, 'Регион первой компании': reg_mass_1, 'Регион второй компании': reg_mass_2, 'Регион третьей компании': reg_mass_3})

    # ------------------------
    # Начисление баллов
    # ------------------------
    for el_str in df.index:
        # Баллы за регион
        df.loc[el_str, 'reg_counts'] = 0

        if df.loc[el_str, 'Регион'] == reg:
            df.loc[el_str, 'reg_counts'] += 1

        # Баллы за БУ
        df.loc[el_str, 'dig_counts'] = 0

        if df.loc[el_str, 'Количество_БУ'] > num:
            df.loc[el_str, 'dig_counts'] += num
        else:
            df.loc[el_str, 'dig_counts'] += df.loc[el_str, 'Количество_БУ']

        # Баллы за тип работ
        df.loc[el_str, 'w_type_counts'] = 0

        if w_type in df.loc[el_str, 'Тип_работ']:
            df.loc[el_str, 'w_type_counts'] += 1

    # Суммарный балл
    df['sum_counts'] = df['reg_counts'] + df['dig_counts'] + df['w_type_counts']

    df = df.sort_values(by=['sum_counts', 'reg_counts'], ascending=False).head(5)

    # Сдвиг индексов
    df = df.set_index(pd.Index(range(1, (df.shape[0] + 1))))

    # Убираем ненужные колонки
    df = df[['Компания', 'Количество_БУ', 'Регион', 'Тип_работ', 'sum_counts']].rename(columns={'sum_counts':'Баллы', 'Количество_БУ':'БУ', 'Тип_работ':'Тип работ'})

    return pair, counter, df # massive, counter, reg_mass_1, reg_mass_2


# --------------------------------------
# Создание подключения к БД
# --------------------------------------
# Таблица с данными приложения
class DataBase(db.Model):
    __tablename__ = 'companies'
    id = db.Column(db.Integer, primary_key=True) # уникальный id для компании
    name = db.Column(db.String(100), nullable=False) # название компании
    free_d_rig = db.Column(db.Integer, nullable=False) # количество свободных БУ
    region = db.Column(db.String(100), nullable=False) # домашний регион компании
    work_type = db.Column(db.String(100), nullable=False) # тип работ
    inn = db.Column(db.Integer, nullable=False) # ИНН компании
    date = db.Column(db.DateTime, default=datetime.utcnow) # дата добавления

    def __repr__(self):
        return '<DataBase %r>' % self.name


# Таблица с данными авторизации
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    login = db.Column(db.String(128), nullable=False, unique=True)
    password = db.Column(db.String(255), nullable=False)


# --------------------------------------
# Авторизация
# --------------------------------------
@manager.user_loader
def load_user(user_id):
    return User.query.get(user_id)


@app.route('/login', methods=['GET', 'POST'])
def login_page():
    login = request.form.get('login')
    password = request.form.get('password')

    if login and password:
        user = User.query.filter_by(login=login).first()
        if user and check_password_hash(user.password, password):
            login_user(user)
            next_page = request.args.get('next')

            if next_page == None:
                return redirect(url_for('index'))

            #print(next_page, str(next_page), request.args.get('next'))

            return redirect(next_page)
        else:
            flash('Неправильный логин или пароль')
    else:
        flash('Заполните логин и пароль')

    return render_template('login.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    login = request.form.get('login')
    password = request.form.get('password')
    password2 = request.form.get('password2')
    #logins = User.query.with_entities(User.login).all()
    #logins = convert_to_list(logins)
    logins = User.query.filter_by(login=login).first()

    if request.method == 'POST':
        print(request.form.getlist('form2Example3g'))
        if not (login or password or password2):
            flash('Заполните все поля')
        elif logins is not None:#login in logins:
            flash('Такой пользователь уже существует')
        elif password != password2:
            flash('Пароли не совпадают')
        elif request.form.getlist('form2Example3g') == []:
            flash('Мы не можем работать без вашего согласия')
        else:
            hash_pwd = generate_password_hash(password)
            new_user = User(login=login, password=hash_pwd)
            db.session.add(new_user)
            db.session.commit()

            return redirect(url_for('login_page'))

    return render_template('register.html')


@app.route('/logout', methods=['GET', 'POST'])
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))


@app.after_request
def redirect_to_signin(response):
    if response.status_code == 401:
        return redirect(url_for('login_page') + '?next=' + request.url)

    return response


# --------------------------------------
# Отслеживание url
# --------------------------------------
@app.route('/') # декоратор  / - главная страница
@app.route('/home')
@login_required
def index():
    names = DataBase.query.with_entities(DataBase.name).all()
    names = convert_to_list(names)
    region = DataBase.query.with_entities(DataBase.region).all()
    region = convert_to_list(region)
    last_date = DataBase.query.with_entities(DataBase.date).all()
    last_date = convert_to_list(last_date)

    names = len(names)
    region = len(set(region))
    if len(last_date) != 0:
        last_date = max(last_date)
        last_date = last_date.strftime("%d.%m.%Y")

    # Для компаний
    if names == 1:
        end_comp = 'ия'
    elif (names < 5)&(names > 1):
        end_comp = 'ии'
    else:
        end_comp = 'ий'

    # Для регионов
    if region == 1:
        end_reg = ''
    elif (region % 100) % 10 == 1 or region % 10 > 4 or region % 10 == 0:
        end_reg = 'ов'
    elif region % 10 == 1:
        end_reg = ''
    else:
        end_reg = 'a'

    return render_template("index.html", companies=names, regions=region, end_reg=end_reg,
                           end_comp=end_comp, last_date=last_date)


@app.route('/about')
@login_required
def about():
    return render_template("about.html")


@app.route('/gantt')
@login_required
def plot_png():
    gantt.create_figure()
    return render_template('gantt.html')


@app.route('/data') # Просмотр записей
@login_required
def posts():
    data = DataBase.query.order_by(DataBase.date.desc()).all()
    return render_template("data.html", data=data)


@app.route('/data/<int:id>') # Просмотр записи
@login_required
def post_detail(id):
    data = DataBase.query.get(id)
    get_inn = int(data.inn)  # количество БУ за весь проект
    #get_inn = 3525379465
    inn_kpp, ogrn, comp_name, okvd, okopff, comp_link, mistake, licvidation_status, licvidation_status_full, email = parse_info(get_inn)
    return render_template("data_detail.html", data=data, inn_kpp=inn_kpp, ogrn=ogrn, comp_name=comp_name,
                           okvd=okvd, okopff=okopff, comp_link=comp_link, mistake=mistake,
                           licvidation_status=licvidation_status, licvidation_status_full=licvidation_status_full, email=email)


@app.route('/data/<int:id>/del') # Удаление записи
@login_required
def post_delete(id):
    data = DataBase.query.get_or_404(id)

    try:
        db.session.delete(data)
        db.session.commit()
        return redirect('/data')
    except:
        return "При удалении произошла ошибка"


@app.route('/data/<int:id>/update', methods=['POST', 'GET']) # Обновление записи
@login_required
def data_update(id):
    data = DataBase.query.get(id)

    if request.method == "POST":
        data.name = request.form['name']  # название компании
        data.free_d_rig = request.form['free_d_rig']  # количество свободных БУ
        data.region = request.form['region']  # домашний регион компании
        data.work_type = request.form['work_type']  # тип работ
        data.inn = request.form['inn'] # ИНН

        try:
            db.session.commit()
            return redirect('/data')
        except:
            return 'Произошла ошибка при обновлении записи'
    else:
        return render_template("data_update.html", data=data)


@app.route('/add-company', methods=['POST', 'GET'])
@login_required
def create_article():
    if request.method == "POST":
        name = request.form['name']
        free_d_rig = request.form['free_d_rig']
        region = request.form['region']
        work_type = request.form['work_type']
        inn = request.form['inn']

        company = DataBase(name=name, free_d_rig=free_d_rig, region=region, work_type=work_type, inn=inn)

        try:
            db.session.add(company)
            db.session.commit()
            return redirect('/data')
        except:
            return 'Произошла ошибка при добавлении статьи'

    else:
        return render_template("add-company.html")


@app.route('/request', methods=['POST', 'GET'])
@login_required
def request_form():
    if request.method == "POST":
        # --------------------------------------
        # Получение информации из формы
        # --------------------------------------
        date = datetime.strptime(
                     request.form['theDate'],
                     '%Y-%m-%d') # начало проекта
        prj_region = request.form['prj_region'] # регион проекта
        prj_full_d_rig = int(request.form['prj_full_d_rig']) # количество БУ за весь проект
        prj_d_rig = int(request.form['prj_d_rig']) # количество БУ в год
        d_1_bur = int(request.form['d_1_bur']) # время бурения
        d_tr_kust = int(request.form['d_tr_kust'])  # время перевозки на другой куст
        d_tr = int(request.form['d_tr'])  # время транспортировки на место в ДО
        w_type = request.form['w_type'] # тип работ

        w_types = DataBase.query.with_entities(DataBase.work_type).all()
        w_types = convert_to_list(w_types)

        # Галочка автономности проекта
        check_auto = 0
        if request.form.get('check_auto') != None:
            check_auto = 1
        # --------------------------------------

        # Проверка типа работ
        flag = 0
        for el in w_types:
            if w_type in el:
                flag = 1
                break


        if (prj_d_rig <= prj_full_d_rig)&(prj_d_rig > 0)&(d_1_bur > 0)&(d_tr_kust > 0)&(d_tr > 0)&(flag != 0):
            print('ok')
            # Составление пар
            pair, counter, sum_counts = pairs(prj_d_rig, prj_region, w_type)

            pair = pair.sort_values(by=['Регион первой компании', 'Регион второй компании']).reset_index(drop=True)
            pair = pair.set_index(pd.Index(range(1, (pair.shape[0] + 1))))

            gantt.create_figure(date, d_tr, prj_full_d_rig, d_1_bur, d_tr_kust, prj_d_rig)

            return render_template('request.html',
                                   tables=[sum_counts.to_html(classes='sum_counts'), pair.to_html(classes='pair')],
                                   titles=['Таблицы', 'Совместимость интересов', 'Таблица'], prj_d_rig=prj_d_rig,
                                   counter=counter,
                                   date=date, d_tr=d_tr, prj_full_d_rig=prj_full_d_rig, d_1_bur=d_1_bur,
                                   d_tr_kust=d_tr_kust, prj_region=prj_region, w_type=w_type
                                   )
        else:
            print('bad')
            return render_template('request.html', mistake='Ошибка ввода. Проверьте введенные данные', date=date,
                                   d_tr=d_tr, prj_full_d_rig=prj_full_d_rig, prj_d_rig=prj_d_rig, d_1_bur=d_1_bur,
                                   d_tr_kust=d_tr_kust, prj_region=prj_region, w_type=w_type)

    else:
        return render_template("request.html")


if __name__ == "__main__":
    #app.run(debug=True) # выводит ошибки на сайте
    app.run(host='0.0.0.0', port=8080)#
    #from waitress import serve
    #serve(app, host="0.0.0.0", port=8080)