#импортируем нужные библиотеки
import re
import time
import urllib3
import requests
import time
import csv
import datetime
import pytz
from lxml import html
from bs4 import BeautifulSoup

link_org_head = '' #задаём наличие ссылки на страницу ЮЛ в РБК
inn = '' #задаем наличие ИНН

#список ОКОПФ, которые нам подходят, остальные - не нужны:
#okopf = ['12200','12247','12267','12300','14000','14100','14153','14154','14155','14200','15300','20109','20110','20111','20112','20115','20116'] # строка 123

#список НЕНУЖНЫХ разделов ОКВЭД, остальные - подходят:
iskl_okved = []#['55','58','64','69','68','84','85','86','87','88','90','91','92','93','94','97','98']

#задаём заголовок запроса на сайт РБК.Компании - без него данные не дадут :)
headers_rbc = {
    'Authority' : 'companies.rbc.ru',
    'Method' : 'GET',
    'Path' : f"{link_org_head}",
    'Scheme' : 'https',
    'Accept' : 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
    'Accept-Encoding' : 'gzip,deflate,br',
    'Accept-Language' : 'ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7',
    'Cookie': 'splituid=UET9B2QwD+Q2r+4BBY5MAg==; _ga=GA1.2.12832177.1680871397; _ym_uid=1680871397978041325; _ym_d=1680871397; __rmid=x7Tw3K49Rz63tLid1CPv4g; _gid=GA1.2.1658767539.1687766208; _ym_isad=2; __rmsid=iuDUwbZDShG6ggbFmcFDFw; _ym_visorc=w; csrftoken=KYFNwAcMr1cEAaYk6U0k8f0vAgum5UesobAzzz34EKfL6wZnb2EmKxK1zPV2qpVi; __rfabu=0; _gat_RBC=1; tmr_lvid=c65b443a99645868e46ca8b363b8ed7e; tmr_lvidTS=1687849892287; tmr_detect=0%7C1687849894655',
    'Sec-Ch-Ua' : '"Not.A/Brand";v="8", "Chromium";v="114", "Google Chrome";v="114"',
    'Sec-Ch-Ua-Mobile' : '?0',
    'Sec-Ch-Ua-Platform' : '"Linux"',
    'Sec-Fetch-Dest' : 'document',
    'Sec-Fetch-Mode' : 'navigate',
    'Sec-Fetch-Site' : 'none',
    'Sec-Fetch-User' : '?1',
    'Upgrade-Insecure-Requests': '1',
    'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36'
}

#задаём заголовок запроса на сайт https://egrul.itsoft.ru/
headers = {
    'Accept-encoding': 'gzip'
}

#ищем последние зарегистрированные ИНН на сайте РБК по ссылке: с фильтром "Возраст компании" = "менее 3 лет"
#эмпирическим путем устанавливаем начальный ИНН для поиска по каждому району области:
#inn_che = 3528310623 #город Череповец
#zip_che = range(inn_che, inn_che + 5000) #задаем диапазон в количестве 5000 ИНН от начального (для городов)


#объединяем все ИНН в один список
#all_list = list(range(3525379465,3525379465+1)) #list(zip_che) #+list(zip_vol)+list(zip_sok)+list(zip_bel)+list(zip_nyu)+list(zip_vyt)+list(zip_she)+list(zip_har)+list(zip_chr)+list(zip_vor)+list(zip_usg)+list(zip_kdy)+list(zip_bab)+list(zip_vus)+list(zip_nik)+list(zip_szh)+list(zip_vaz)+list(zip_tot)+list(zip_grz)+list(zip_vzh)+list(zip_vsk)+list(zip_bbu)+list(zip_kgr)


#функция создания ЛИДа в ESPOCRM (опишу в отдельной публикации)
def create_lead_espo(data_dict):
    api = ''
    header = {
        'X-Api-Key': '',
        'Content-Type': 'application/json',
        'Accept': 'application/json'
    }
    url = 'https://api/v1/LeadCapture/'
    url_c = f'{url}{api}'
    data = data_dict
    res = requests.post(url_c, data=data)
    if res.text == 'true':
        print(f'Лид создан:{res.text}')
        return 'lead create'
    else:
        print(f'Лид НЕ создан:{res.__dict__}')
        return 'lead not create'


#Функция сбора и анализа требуемых данных
def parse_info(get_inn):
    all_list = list(range(get_inn, get_inn + 1))

    ch = 1 #счетчик
    data_dict = {} #словарь требуемых данных
    inn_kpp = ''
    ogrn = ''
    comp_name = ''
    okvd = ''
    okopff = ''
    comp_link = ''
    mistake = ''
    licvidation_status = ''
    licvidation_status_full = ''
    email = ''

    for inn in all_list: #начинаем перебор ИНН из списка ALL_LIST
        org_email = '' #задаем наличие строки EMAIL
        url = f'https://egrul.itsoft.ru/{str(inn)}.json' #шаблон ссылки на запрос, в которую подставляется строковое значение ИНН (не число, как задано изначально)
        result = requests.get(url) #делаем GET-запрос
        print(f'Обрабатывается ИНН: [{inn}]') #выводим на экран обрабатываемый ИНН
        #print(result.status_code == 200 and result.text != 'false')
        #print(result.status_code)
        #print(result.text)

        if result.status_code == 200 and result.text != 'false': #обрабатываем условия возникновения ошибок
            a = result.json() #извлекаем JSON из ответа сервера

            try: #"ЕСЛИ НЕТ ОШИБОК", все переменные и ключи присутствуют в ответе сервера
                try:
                    if str(a['СвИП']['@attributes']['НаимВидИП']) == "Индивидуальный предприниматель":
                        print(f"ИНН: {str(inn)}")  # выводим ИНН ИП из ответа сервера
                        inn_kpp = f"ИНН: {str(inn)}"

                        print(f"ОГРНИП: {a['СвИП']['@attributes']['ОГРНИП']}")
                        ogrn = f"ОГРНИП: {a['СвИП']['@attributes']['ОГРНИП']}"

                        print(f"Вид деятельности: {a['СвИП']['@attributes']['НаимВидИП']}")  # выводим из ответа сервера
                        okopff = f"{a['СвИП']['@attributes']['НаимВидИП']}"

                        print(
                            f"Основной вид деятельности: {a['СвИП']['СвОКВЭД']['СвОКВЭДОсн']['@attributes']['НаимОКВЭД']} "
                            f"{a['СвИП']['СвОКВЭД']['СвОКВЭДОсн']['@attributes']['КодОКВЭД']}")
                        mistake = f"Основной вид деятельности: {a['СвИП']['СвОКВЭД']['СвОКВЭДОсн']['@attributes']['НаимОКВЭД']} " \
                                 f"({a['СвИП']['СвОКВЭД']['СвОКВЭДОсн']['@attributes']['КодОКВЭД']})"

                        #print(f"Дата обновления информации: {a['СвИП']['@attributes']['ДатаВып']}")

                        #print(f"Дата ОГРНИП: {a['СвИП']['@attributes']['ДатаОГРНИП']}")

                        # ---------------------------------
                        # Получаем ссылку на РБК
                        url = f"https://companies.rbc.ru/search/persons/?query={str(inn)}"  # Ищем ссылку на страницу компании на сайте РБК
                        response = requests.get(url,
                                                headers=headers_rbc)  # делаем GET-запрос с обязательным "спецзаголовком" headers_rbc
                        tree = html.fromstring(response.content)  # извлекаем xml-данные из ответа
                        link_org = tree.xpath(
                            '/html/body/div[5]/main/div[2]/a/@href')  # находим среди них ссылку на страницу нужной компании
                        print(link_org)

                        link_org1 = str(link_org).replace("[", "").replace("'", "").replace("]",
                                                                                            "")  # убираем из строки лишние символы [],
                        link_org_head = link_org1[24:len(
                            link_org1)]  # убираем из строки https://companies.rbc.ru или первые 24 символа
                        headers_rbc[
                            'Path'] = link_org_head  # добавляем урезанную строку в ключ "Path" заголовка "headers_rbc" запроса
                        print(link_org_head)
                        print(
                            f'Ссылка на сайте РБК: https://companies.rbc.ru{link_org1}')  # выводим всю ссылку на экран
                        comp_link = f'https://companies.rbc.ru{link_org1}'
                        # ------------------------------

                        print(f"{a['СвИП']['СвПрекращ']['СвСтатус']['@attributes']['НаимСтатус']}")
                        licvidation_status = f"Дата: {a['СвИП']['СвПрекращ']['СвСтатус']['@attributes']['ДатаПрекращ']} "\
                                             f"{a['СвИП']['СвПрекращ']['СвСтатус']['@attributes']['НаимСтатус']}"

                        print(f"Дата: {a['СвИП']['СвПрекращ']['СвСтатус']['@attributes']['ДатаПрекращ']}")

                except:
                    print(f"ИНН/КПП:{str(inn)}/{a['СвЮЛ']['@attributes']['КПП']}") #выводим ИНН/КПП из ответа сервера
                    inn_kpp = f"ИНН/КПП: {str(inn)}/{a['СвЮЛ']['@attributes']['КПП']}"

                    #print(f"ОГРН: {a['СвЮЛ']['@attributes']['ОГРН']}  Дата:{a['СвЮЛ']['@attributes']['ДатаОГРН']}") #выводим ОРГН и его дату из ответа сервера
                    ogrn = f"ОГРН: {a['СвЮЛ']['@attributes']['ОГРН']}    Дата: {a['СвЮЛ']['@attributes']['ДатаОГРН']}"

                    #print(f"{a['СвЮЛ']['СвНаимЮЛ']['@attributes']['НаимЮЛПолн']}") #выводим Полное наименование ЮЛ из ответа сервера
                    comp_name = f"{a['СвЮЛ']['СвНаимЮЛ']['@attributes']['НаимЮЛПолн']}"

                    #print(f"ОКВЭД:{a['СвЮЛ']['СвОКВЭД']['СвОКВЭДОсн']['@attributes']['КодОКВЭД']}") #выводим КОД ОКВЭД из ответа сервера
                    okvd = f"ОКВЭД: {a['СвЮЛ']['СвОКВЭД']['СвОКВЭДОсн']['@attributes']['КодОКВЭД']}"

                    #print(f"ОКОПФ:{a['СвЮЛ']['@attributes']['КодОПФ']}:{a['СвЮЛ']['@attributes']['ПолнНаимОПФ']}") #выводим КОД ОКОПФ из ответа сервера
                    okopff = f"ОКОПФ: {a['СвЮЛ']['@attributes']['КодОПФ']} : {a['СвЮЛ']['@attributes']['ПолнНаимОПФ']}"

                    if str(a['СвЮЛ']['СвОКВЭД']['СвОКВЭДОсн']['@attributes']['КодОКВЭД'])[0:2] in iskl_okved: #Сравниваем первые два символа КОДа ОКВЭД со списком исключений [iskl_okved]
                        print('ОКВЭД не подходит') #Если код в списке
                    else: #иначе
                        if str(a['СвЮЛ']['@attributes']['КодОПФ']) != '': #Если КОД ОКОПФ в списке [okopf] и не равен пустой строке /old:/ if str(a['СвЮЛ']['@attributes']['КодОПФ']) in okopf and str(a['СвЮЛ']['@attributes']['КодОПФ']) != '':
                            url = f"https://companies.rbc.ru/search/?query={str(inn)}" #Ищем ссылку на страницу компании на сайте РБК
                            response = requests.get(url, headers=headers_rbc) #делаем GET-запрос с обязательным "спецзаголовком" headers_rbc
                            tree = html.fromstring(response.content) #извлекаем xml-данные из ответа
                            link_org = tree.xpath('/html/body/div[5]/main/div[2]/a/@href') #находим среди них ссылку на страницу нужной компании

                            link_org1 = str(link_org).replace("[", "").replace("'", "").replace("]", "")#убираем из строки лишние символы [],
                            link_org_head = link_org1[24:len(link_org1)] #убираем из строки https://companies.rbc.ru или первые 24 символа
                            headers_rbc['Path'] = link_org_head #добавляем уразанную строку в ключ "Path" заголовка "headers_rbc" запроса
                            print(f'Ссылка на сайте РБК: {link_org1}') #выводим всю ссылку на экран
                            comp_link = f'{link_org1}'


                            if str(link_org1) != '': #если ссылка не пустая
                                response1 = requests.get(str(link_org1), headers=headers_rbc)#делаем по ней GET-запрос с тем же спецзаголовком "headers_rbc"
                                print('Ссылка:'+str(response1.status_code)) #выводим на экран статус ответа, нужен 200, все остальные - неуспешные

                                if response1.status_code == 200: #если статус-код 200
                                    soup = BeautifulSoup(response1.text, 'html.parser') #парсим данные из ответа
                                    tree = html.fromstring(response1.content) #извлекаем xml-формат
                                    desc = tree.xpath('//*[@id="description"]/p[2]/text()') #находим блок с описанием компании
                                    #print(str(desc[-2])) #выводим второй с конца элемент описания
                                    licvidation_status_full = str(desc[-2])

                                    if 'ликвидирована' in str(desc[-2]): #если элемент содержит слово "ликвидирована"
                                        #print('ОРГАНИЗАЦИЯ ЛИКВИДИРОВАНА') #выводим информацию на экран, заканчиваем обработку данного ИНН
                                        licvidation_status = 'ОРГАНИЗАЦИЯ ЛИКВИДИРОВАНА'
                                    else: #иначе
                                        #print('['+str(ch)+']:')#выводим счетчик успешно обработанных ИНН
                                        links1 = soup.findAll('span', class_='copy-text') #ищем в коде xml все span с классом "copy-text"
                                        for link in links1: #перебираем все найденные span
                                            emails = re.findall("([a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+)", str(link))# ищем в них Email-адрес по маске [a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+
                                        for email in emails:
                                            org_email = email #присваиваем найденный адрес переменной "org_email"
                                            #print(f'Email: {org_email}') #выводим на экран
                                            email = f'{org_email}'
                                        try: #если все данные без ошибок получены, то формируем словарь data_dict с правильными ["ключами"] для передачи в ESPO CRM
                                            data_dict["accountName"] = str(a['СвЮЛ']['СвНаимЮЛ']['СвНаимЮЛСокр']['@attributes']['НаимСокр'])
                                        except:
                                            data_dict["accountName"] = str(a['СвЮЛ']['СвНаимЮЛ']['@attributes']['НаимЮЛПолн'])
                                            data_dict["emailAddress"] = str(org_email)
                                            data_dict["inn"] = str(inn)
                                            data_dict["oGRN"] = str(a['СвЮЛ']['@attributes']['ОГРН'])
                                            data_dict["dateGRN"] = str(a['СвЮЛ']['@attributes']['ДатаОГРН'])
                                            data_dict["oKVED"] = str(a['СвЮЛ']['СвОКВЭД']['СвОКВЭДОсн']['@attributes']['КодОКВЭД'])
                                            data_dict["okopf"] = f"{str(a['СвЮЛ']['@attributes']['КодОПФ'])} {str(a['СвЮЛ']['@attributes']['ПолнНаимОПФ'])}"
                                            data_dict["status"] = "AutoCreate"
                                            data_dict["rBCURL"] = str(link_org1)
                                            data_dict["assignedUserId"] = 1
                                            data_dict["date"] = str(datetime.datetime.now(pytz.timezone('utc')))[:19]
                                            #print(data_dict) #выводим словарь на экран
                                            create_lead_espo(data_dict) #передаем сведения в карточку ЛИДа ESPO CRM
                                            time.sleep(3) #делаем паузу
                                            ch = ch+1 #крутим счетчик
                                else: #обрабатываем исключения и ошибки
                                    org_email = ''
                                    #print(f'Email: {org_email}, RBC: нет данных EMAIL')
                                    email = f'Email: {org_email}, RBC: нет данных EMAIL'
                            else:
                                print('RBC not LINK!')
                        else:
                            print(f"ОКОПФ:{a['СвЮЛ']['@attributes']['КодОПФ']} не подходит под условия")
            except Exception as e: print(e)
            #print('Нет данных в каком-либо блоке!')
        else:
            #print(f'https://egrul.itsoft.ru/ не выдал данных!')
            mistake = f'https://egrul.itsoft.ru/ не выдал данных!'
    return inn_kpp, ogrn, comp_name, okvd, okopff, comp_link, mistake, licvidation_status, licvidation_status_full, email


#parse_info() #запускаем основную функцию