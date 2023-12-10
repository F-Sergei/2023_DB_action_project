import math
import os

import matplotlib.pyplot as plt
import datetime as dt
from datetime import timedelta
from datetime import date


# Создание Диаграммы Ганта
def create_figure(start_dt, d_tr, num_dig, d_1_bur, d_tr_kust, dig_year):
    try:
        # Удаление старого изображения
        filename = 'gantt1.png'
        path = 'static/Diagramms/' + filename
        os.remove(path)
    except:
        pass

    # --------------------
    # Расчёты
    # --------------------
    datemax = 0
    massive = [0]
    steps = []

    # Подсчёт даты окончания проекта
    for num in range(1, math.ceil(num_dig/dig_year)+1):
        if (num == 1):
            datemax += d_tr
            massive.append(datemax)
            steps.append('Доставка БУ')
            datemax += d_1_bur
            massive.append(datemax)
            steps.append('Бурение')
        else:
            datemax += d_tr_kust
            massive.append(datemax)
            steps.append('Перевозка БУ')
            datemax += d_1_bur
            massive.append(datemax)
            steps.append('Бурение')

    end_date = start_dt + dt.timedelta(days=datemax)

    # --------------------
    # График
    # --------------------
    fig, gnt = plt.subplots()

    # gnt.set_xlim(start_dt, end_date)

    gnt.set_xlabel('Дата')
    gnt.set_ylabel('Этап')

    # Setting ticks on y-axis
    gnt.set_yticks(range(0, len(massive)-1, 1))

    # Labelling tickes of y-axis
    gnt.set_yticklabels(steps)

    #print(massive)
    #print(range(len(massive) - 1))

    # Setting graph attribute
    gnt.grid(True)

    st_dt = start_dt
    for el in range(len(massive) - 1):
        delta = massive[el + 1] - massive[el]
        gnt.broken_barh([
            (
                st_dt,
                dt.timedelta(days=delta)  # This adds a width of 10 days
            )],
            (el-0.5, 1),
            facecolors=('tab:blue')
        )
        st_dt = st_dt + dt.timedelta(days=delta)

    fig.set_size_inches(12, 8)

    plt.savefig('static/Diagramms/gantt1.png')

    return fig