import os
import ftplib
import re
import logging
import threading
import time
import socket

dir_name = "venv/"

class Ftp_Connection():
    FTP_DEBUG_LVL = 2 # 0 - нет, 1 - вывод инфы 2 - max инфы
    #метод для подключения к  ftp
    def __init__(self, host, user_name, password, show_progress=False):
        self.host = host
        self.user_name = user_name
        self.password = password
        self.show_progress = show_progress
        #создание  self.connect
        self.connect()

        #Интервал мониторинга 1 минута
        self.monitoring_interval = 1
        self.ptr = None
        #Максимальное число попыток 15
        self.max_attemps = 15
        #Ожидание ответа сервера 15 мин
        self.waiting = True
        #Перерыв 15мин для переподключения
        self.retry_timeout = 15

    def isdir(self, directory):
        try:
            self.conn.nlst(directory)
            return True
        except ftplib.error_temp as err:
            print('Time run out reconnect: ', err)
            #Поиск "450\s" на строке
            if re.match('450\s', str(err)):
                print('def isdir 35 str',re.match('450\s', str(err)))
                return False
            else:
                raise

    def list(self,directory=''):
        '''Вернуть список имен файлов '''
        data = []
        try:
            data = self.conn.nlst(directory)
        except ftplib.error_temp as err:
            if str(err) == "550 No files found":
                print('47 str 550 no file found')
                pass
            else:
                print("Error: {}".format(str(err)))
        return data

    def make_directory(self, path):
        try:
            self.conn.mkd(path)
            return True
        except:
            return False

    def delete_directory(self, path):
        try:
            self.conn.rmd(path)
            return True
        except:
            return False

    #получение файлов
    def get_file(self, src, dest):
        with open(dest, 'w+b') as f:
            self.ptr = f.tell()
            print("Конечный размер указателя 76 строка", self.ptr)
            @setInterval(self.monitoring_interval)

            def monitor():
                if not self.waiting:
                    #Текущая позиция указателя — это позиция (количество байт), с которой будет осуществляться следующее чтение/запись.
                    print("Текущая позиция указателя 81 строка", f.tell())
                    i = f.tell()
                    if self.ptr < i:
                        logging.debug("%d - %0.1f Kb/s" % (i, i-self.ptr) / (1024 * self.monitoring_interval))
                        self.ptr = i
                    else:
                        self.conn.close()
            #Удаленный размер файла
            remote_file_size = self.conn.size(src)
            res = ''

            mon = monitor()
            while
#Запуск бесконечного цикла
while True:
    #Цикл просмотра файлов в папке  venv
    for file in os.listdir(dir_name):
        #Проверка налияае файла .py
        if file.endswith(".py"):
            #Имя файла .py
            print(os.path.join("/", file))
