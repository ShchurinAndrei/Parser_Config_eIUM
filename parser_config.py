# -*- coding: utf-8 -*-
import sys
import csv

# функция возвращает словарь хранящий в ключах имя хоста, а в значниях массив с именами коллекторов разварных на этом хосте
def return_hosts_processes(file_name):
    # открытие файла на чтение
    with open(file_name, 'r', encoding='utf-8') as file:
        lines = file.readlines()
        # шаблон поиска строки объявления хостов и коллекторов
        pattern = 'Processes=/deployment/'
        # объявление словаря
        hosts_processes = {}

        # цикл построчного прочтения файла
        for line in lines:
            # условие на нахождение строки соответствующей шаблону
            if pattern in line:
                # фильтрация строки от всего лишнего (после преобразований получим строку: хост/коллектор)
                line_processe = line.replace(pattern, '')
                line_processe = line_processe[:-1]
                # преобразование строки в список из двух элементов
                host_processe = line_processe.split('/')
                if host_processe[0] in hosts_processes.keys():
                    # если на одном хосте установлено несколько коллекторов они добавляется в список коллекторов этого хоста
                    hosts_processes[host_processe[0]].append(host_processe[1])
                else:
                    # если хост встречается первый раз то в словарь добавляться его имя как ключ, а значением становиться пустой список
                    processes = []
                    hosts_processes[host_processe[0]] = processes
                    hosts_processes[host_processe[0]].append(host_processe[1])
    # закрытие сессии работы с файлом
    file.close()
    return hosts_processes

# функция возвращает словарь хранящий в ключах заголовочную строку, а в значениях массив строк того блока
def return_deployment(file_name):
    # открытие файла на чтение
    with open(file_name, 'r', encoding='utf-8') as file:
        lines = file.readlines()
        # объявление шаблона заголовочных строк блока deployment
        pattern = '[/deployment/'
        # объявление словаря
        deployment_dict = {}
        # объявление триггера начала блока отличного от deployment
        valve = False
        # объявление переменной для сохранения заголовочной строки (ключа словаря)
        key_attributes = ''

        # цикл построчного прочтения файла
        for line in lines:
            if line.startswith('#@ '):
                line = line[3:]
            elif line.startswith('#-> '):
                line = line[4:]
            # проверка на заголовочную строку блока
            if pattern in line:
                # указание на то что строки находятся внутри блока
                valve = True
                # объявление пустого массива строк блока
                attributes = []
                # удаление из прочитанной строки знака перевода каретки
                line = line[:-1]
                # в словарь добавляться заголовочная строка как ключ, а подстроки данного блока составят список значений
                deployment_dict[line] = attributes
                # сохранение в переменную заголовочную строку блока (ключ словаря)
                key_attributes = line
            # проверка на начала нового блока начинающегося не с deployment
            elif '[/' in line:
                # указание на то что блок deployment закончился
                valve = False
            # проверка на подстроку блока deployment
            elif valve:
                # удаление из прочитанной строки знака перевода каретки
                line = line[:-1]
                # проверка на пустую строку
                if line != '':
                    # запись подстроки в соответствующий ей массив строк блока
                    deployment_dict[key_attributes].append(line)
    return deployment_dict

# функция возвращает словарь хранящий в ключах имя коллектора, а в значениях массив аттрибутов encapsulator коллектора
def return_collector_attributes_encapsulator(hosts_processes, deployment_dict, attributes):
    # объявление словаря коллекторов
    collector = {}

    # цикл по перебору хостов
    for host in hosts_processes.keys():
        # цикл по перебору коллекторов указанного хоста
        for processe in hosts_processes[host]:

            # объявление списка атрибутов коллектора
            parameters = []
            # присвоение выбранному ключу - коллектору пустого списка аттрибутов
            collector[processe] = parameters
            # флаг определения элемента как коллектора
            collector_check = True

            # объявление шаблона строки инициализации коллектора
            pattern = f'[/deployment/{host}/{processe}]'
            # проверка наличия строки инициализация выбранного коллектора на выбранном хосте
            if pattern in deployment_dict.keys():
                # цикл по перебору строк блока инициализации
                for line in deployment_dict[pattern]:
                    if line.startswith('ClassName'):
                        if line != 'ClassName=com.hp.siu.adminagent.procmgr.CollectorProcess':
                            # добавление в пустой список аттрибутов коллектора указание на то что элемент не является коллектором
                            collector[processe].append('Не коллектор')
                            # установление флага на значение, что элемент не является коллектором
                            collector_check = False
                            # выход из цикла перебора строк блока инициализации
                            break

                # проверка, что элемент является коллектором
                if collector_check:
                    # объявление и заполнение листа шаблонов заголовочных строк
                    patterns = []
                    patterns.append(f'[/deployment/{host}/{processe}]')
                    patterns.append(f'[/deployment/{host}/{processe}/Encapsulator/FileRollPolicy]')
                    patterns.append(f'[/deployment/{host}/{processe}/Encapsulator/RecordFactory/StreamSource/FileRollPolicy]')
                    patterns.append(f'[/deployment/{host}/{processe}/Encapsulator]')

                    # цикл по перебору шаблонов заголовочных строк
                    for pattern in patterns:
                        # проверка наличия в deployment выбранной заголовочной строки
                        if pattern in deployment_dict.keys():
                            # цикл по перебору подстрок найденного блока
                            for line in deployment_dict[pattern]:
                                # цикл по перебору атрибутов из переданного в функцию списка
                                for attribute in attributes:
                                    # проверка соответствия начала текущей строки выбранному аттрибуту
                                    if line.startswith(str(attribute + '=')):
                                        # приведение строки к более читаемому виду
                                        parameter = line.replace(str(attribute + '='), str(attribute + ' = '))
                                        # добавление найденного аттрибута в список аттрибутов выбранного коллектора
                                        collector[processe].append(parameter)
            else:
                # если строка инициализации отсутствует, следовательно коллектор объявлен только в Processes
                collector[processe].append('Коллектор объявлен только в Processes')
    return collector

# функция возвращает словарь хранящий в ключах имя коллектора, а в значениях массив аттрибутов datastore коллектора
def return_collector_attributes_datastore(hosts_processes, deployment_dict, attributes):
    # объявление словаря коллекторов
    collector = {}

    # цикл по перебору хостов
    for host in hosts_processes.keys():
        # цикл по перебору коллекторов указанного хоста
        for processe in hosts_processes[host]:
            # объявление шаблона строки инициализации коллектора в Datastore
            pattern = f'[/deployment/{host}/{processe}/Datastore]'

            # объявление списка атрибутов коллектора
            parameters = []
            # объявление словаря схем коллектора
            schemes = {}
            # присвоение выбранному ключу - коллектору пустого списка аттрибутов
            collector[processe] = parameters
            # флаг определения MUX Datastore (наличие в нем схем)
            mux_check = False
            # флаг определения наличия агента вывода в коллекторе
            agent_cheсk = False
            # объявление переменной имени агента вывода
            agent = ''

            # проверка наличия строки инициализация выбранного коллектора на выбранном хосте
            if pattern in deployment_dict.keys():
                # цикл по перебору строк блока инициализации
                for line in deployment_dict[pattern]:
                    # проверка на наличие в подстроках аттрибута ClassName и тому что согласно его значению данный коллектор является MUX Datastore
                    if line.startswith('ClassName') and line == 'ClassName=MuxDatastore':
                        # перевод соответствующего флага в положительное значение
                        mux_check = True

                    # проверка флага, что данный коллектор является MUX Datastore
                    if mux_check:
                        # проверка наличия подстрок с атрибутом SchemeMap
                        if line.startswith('SchemeMap='):
                            # обрезание строки до значения аттрибута
                            scheme = line.replace('SchemeMap=', '')
                            scheme = scheme.split(',')[1]
                            # объявление списка атрибутов схемы
                            argument = []
                            # присвоение выбранному ключу - схемы пустого списка аттрибутов
                            schemes[scheme] = argument
                    # если данный коллектор не является MUX Datastore
                    else:
                        # цикл по перебору атрибутов из переданного в функцию списка
                        for attribute in attributes:
                            # проверка соответствия начала текущей строки выбранному аттрибуту
                            if line.startswith(str(attribute + '=')):
                                # приведение строки к более читаемому виду
                                parameter = line.replace(str(attribute + '='), str(attribute + ' = '))
                                # добавление найденного аттрибута в список аттрибутов выбранного коллектора
                                collector[processe].append(parameter)
                            # проверка соответствия начала текущей строки аттрибуту DeliveryAgent
                            if line.startswith('DeliveryAgent='):
                                # перевод соответствующего флага в положительное значение
                                agent_cheсk = True
                                # обрезание строки до значения аттрибута
                                agent = line.replace('DeliveryAgent=', '')
                                agent = agent.split(',')[0]

                # объявление списка атрибутов коллектора
                patterns = []
                if mux_check:
                    collector[processe] = schemes
                    for scheme in schemes.keys():
                        patterns.append(f'[/deployment/{host}/{processe}/Datastore/{scheme}]')
                    for pattern in patterns:
                        scheme = pattern[1:-1]
                        scheme = scheme.split('/')[5]
                        if pattern in deployment_dict.keys():
                            for line in deployment_dict[pattern]:
                                for attribute in attributes:
                                    if line.startswith(str(attribute + '=')):
                                        parameter = line.replace(str(attribute + '='), str(attribute + ' = '))
                                        collector[processe][scheme].append(parameter)
                                    if line.startswith('DeliveryAgent='):
                                        agent = line.replace('DeliveryAgent=', '')
                                        agent = agent.split(',')[0]
                                        patterns.append(f'[/deployment/{host}/{processe}/Datastore/{scheme}/{agent}]')
                                        break
                                    if line.startswith('Transport='):
                                        transport = line.replace('Transport=', 'Transport = ')
                                        collector[processe][scheme].append(transport)
                                        transport = line.replace('Transport=', '')
                                        patterns.append(pattern[:-1] + f'/{transport}]')
                                        break
                                    if line.startswith('SchemaNames='):
                                        scheme_name = line.replace('SchemaNames=', '')
                                        patterns.append(f'[/deployment/{host}/{processe}/Datastore/{scheme}/{scheme_name}]')
                                        break
                else:
                    if agent_cheсk:
                        patterns.append(f'[/deployment/{host}/{processe}/Datastore/{agent}]')
                        for pattern in patterns:
                            if pattern in deployment_dict.keys():
                                for line in deployment_dict[pattern]:
                                    for attribute in attributes:
                                        if line.startswith(str(attribute + '=')):
                                            parameter = line.replace(str(attribute + '='), str(attribute + ' = '))
                                            collector[processe].append(parameter)
                                        if line.startswith('Transport='):
                                            transport = line.replace('Transport=', 'Transport = ')
                                            collector[processe].append(transport)
                                            transport = line.replace('Transport=', '')
                                            patterns.append(pattern[:-1] + f'/{transport}]')
                                            break
            else:
                collector[processe].append('Не найден Datastore')
    return collector

def return_collector_class(hosts_processes, deployment_dict):
    # объявление словаря коллекторов
    collector = {}

    # цикл по перебору хостов
    for host in hosts_processes.keys():
        # цикл по перебору коллекторов указанного хоста
        for processe in hosts_processes[host]:

            # объявление списка атрибутов коллектора
            parameters = []
            # присвоение выбранному ключу - коллектору пустого списка аттрибутов
            collector[processe] = parameters
            custom_class = {}

            # объявление шаблона строки
            pattern = f'[/deployment/{host}/{processe}/'
            deployment_keys = filter(lambda block: block.startswith(pattern), deployment_dict.keys())
            for deployment_key in deployment_keys:
                # цикл по перебору строк блока
                for line in deployment_dict[deployment_key]:
                    if line.startswith('ClassName'):
                        if '.' in line:
                            if not line.startswith('ClassName=com.hp.'):
                                line = line.replace('ClassName=', '')
                                if line in custom_class.keys():
                                    custom_class[line] += 1
                                else:
                                    custom_class[line] = 0
                                num_class = len(collector[processe])
                                if num_class > 0:
                                    for class_line in collector[processe]:
                                        if line in class_line:
                                            break
                                        else:
                                            if num_class == 1:
                                                deployment_key = deployment_key.replace(pattern, '')
                                                deployment_key = deployment_key[:-1]
                                                custom = ['', '', 'Custom class:', deployment_key, line]
                                                collector[processe].append(custom)
                                            else:
                                                num_class -= 1
                                else:
                                    deployment_key = deployment_key.replace(pattern, '')
                                    deployment_key = deployment_key[:-1]
                                    custom = ['', '', 'Custom class:', deployment_key, line]
                                    collector[processe].append(custom)
                                break
                            break
                        break
            for cust in custom_class.keys():
                if custom_class[cust] > 0:
                    for class_line in collector[processe]:
                        if cust in class_line and f'and {custom_class[cust]} more' not in class_line:
                            class_line.append(f'and {custom_class[cust]} more')

    return collector

#-----------------------------------------------------------------------------------------------------------------------

# массивы с перечислением атрибутов поиска в encapsulator и datastore соответсвенно
attributes_encapsulator = ['DirectoryName', 'FileNameSuffix', 'FilePattern', 'TableName', 'Link', 'Command']
attributes_datastore = ['FileNameTemplate', 'NotifyCommand', 'DestinationDir', 'CacheDir', 'FileNameTZ', 'TableName']

file_in = 'dec.config'
parts = file_in.split('.')
file_out = parts[0]

hosts_processes = return_hosts_processes(file_in)
deployment_dict = return_deployment(file_in)
coll_encaps = return_collector_attributes_encapsulator(hosts_processes, deployment_dict, attributes_encapsulator)
coll_dat = return_collector_attributes_datastore(hosts_processes, deployment_dict, attributes_datastore)
coll_class = return_collector_class(hosts_processes, deployment_dict)

# запись вывода в консоль
# print('В данной конфигурации найдены:\n')
# for host in hosts_processes.keys():
#     print(host)
#     for processe in hosts_processes[host]:
#         if not 'Коллектор объявлен только в Processes' in coll_encaps[processe]:
#             print(f'\t{processe}')
#             if len(coll_encaps[processe]) != 0:
#                 for attribute in coll_encaps[processe]:
#                     print(f'\t\t{attribute}')
#             else:
#                print(f'\t\tАтрибуты Encasulator не найдены')
# if not 'Не коллектор' in coll_encaps[processe]:
#                 if len(coll_class[processe]) != 0:
#                    for col in coll_class[processe]:
#                           print(f'\t\t', end = '')
#                           for col_atr in col:
#                               print(col_atr, end = '')
#                           print(' ')
#                else:
#                     print(f'\t\tCustom class в данном коллекторе не найдены')
#                 if len(coll_dat[processe]) != 0:
#                     if type(coll_dat[processe]).__name__ == 'dict':
#                         for scheme in coll_dat[processe].keys():
#                             print(f'\t\t{scheme}')
#                             if len(coll_dat[processe][scheme]):
#                                 for attribute in coll_dat[processe][scheme]:
#                                    print(f'\t\t\t{attribute}')
#                             else:
#                                 print(f'\t\t\tАтрибуты схемы {scheme} не найдены')
#                     else:
#                         for attribute in coll_dat[processe]:
#                             print(f'\t\t{attribute}')
#                 else:
#                     print(f'\t\tАтрибуты Datastore не найдены')

# запись вывода в csv-файл
with open(f'{file_out}.csv', mode='w', newline='', encoding='utf-8') as file:
    writer = csv.writer(file, delimiter='\t')
    for host in hosts_processes.keys():
        writer.writerow([host])
        for processe in hosts_processes[host]:
            if not 'Коллектор объявлен только в Processes' in coll_encaps[processe]:
                writer.writerow(['', f'{processe}'])
                if len(coll_encaps[processe]) != 0:
                    for attribute in coll_encaps[processe]:
                        writer.writerow(['', '', f'{attribute}'])
                else:
                    writer.writerow(['', '', 'Атрибуты Encasulator не найдены'])
                if not 'Не коллектор' in coll_encaps[processe]:
                    if len (coll_class[processe]) != 0:
                        for col in coll_class[processe]:
                            writer.writerow(col)
                    else:
                        writer.writerow(['', '', 'Custom class в данном коллекторе не найдены'])
                    if len(coll_dat[processe]) != 0:
                        if type(coll_dat[processe]).__name__ == 'dict':
                            for scheme in coll_dat[processe].keys():
                                writer.writerow(['', '', f'{scheme}'])
                                if len(coll_dat[processe][scheme]):
                                    for attribute in coll_dat[processe][scheme]:
                                        writer.writerow(['', '', '', attribute])
                                else:
                                    writer.writerow(['', '', '', f'Атрибуты схемы {scheme} не найдены'])
                        else:
                            for attribute in coll_dat[processe]:
                                writer.writerow(['', '', f'{attribute}'])
                    else:
                        writer.writerow(['', '', 'Атрибуты Datastore не найдены'])