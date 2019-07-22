import os
import re
import ftplib
import time
import threading

def setInterval(interval, time = -1):
    print('Вывод первой функции INTERVAL = {0}  TIME = {1} '.format(interval, time))
    # Это будет декоратор с фиксированныи интервалом и параметром times
    def outer_wrap(function):
        #Это вызываемая функция
        def wrap(*args, **kwargs):
            stop = threading.Event()
            print('Идентификатор текущего потока = ', threading.get_ident())
            # Это еще одна функция, которая будет выполняться в другом потоке для имитации setInterval
            def inner_wrap():
                i = 0
                while i != times and not stop.isSet():
                    stop.wait(interval)
                    function(*args, **kwargs)
                    i += 1

            t = threading.Timer(0, inner_wrap)
            t.daemon = True
            t.start()
            return stop
        return wrap
    return outer_wrap

class FTP_Connection():

    FTP_DEBUG_LEVEL = 2 # 0=none, 1=some output, 2=max debugging output

    def __init__(self, host, username, password, show_progress = False):
        self.host = host
        self.username = username
        self.password = password
        self.show_progress = show_progress

        self.connect()

        # Управление передачей файлов
        self.monitoring_interval = 1
        self.ptr = None
        # Максимальное количество попыток для подключения
        self.max_attempts = 15
        # Ожидание ответа
        self.waiting = True
        # Перерыв на подключение ожидание прежде чем переподключиться
        self.retry_timeout = 15

    # Директория (является ли путь директорией)
    def isdir(self, directory):
        try:
            #Вернуть список имен файлов возврощаемых командой NLST
            self.conn.nlst(directory)
            print('Список имен файлов: ', self.conn.nlst(directory))
            return True
        except ftplib.error_temp as err:
            print('Отлавоиваем ошибки: ',str(err))
            if re.match('450\s', str(err)):
                return False
            else:
                raise
    def list(self, directory = ''):
        # Вернуть список имен файлов используя ftplib.nlst
        # По умолчанию это список файлов в коревом каталоге пользователя
        # Или вы можете перейти в путь к каталогу
        data = []
        try:
            data = self.conn.nlst(directory)
            print('Вернуть список имен файлов используя ftplib.nlst: ', data)
        except ftplib.error_temp as err:
            print('Отлавливаем ошибки nlst:',str(err))
            if str(err) == "550 No files found":
                # Данные остаются
                pass
            else:
                print("Ошибка: ",format(str(err)))
        return data

    def make_directory(self, path):
        try:
            # Создание нового каталога на сервере
            self.conn.mkd(path)
            print('Создание нового каталога: ',self.conn.mkd(path))
            return  True
        except:
            return False

    def delete_directory(self, path):
        try:
            # Удаление каталога с имененм path на сервере
            self.conn.rdm(path)
            return True
        except:
            return False

    def get_file(self, src, dest):





