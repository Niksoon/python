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
            while remote_file_size > f.tell()
                try:
                    self.connect()
                    self.waiting = False
                    # Получить позицию файла где произошл разрыв соединения
                    if f.tell() == 0:
                        res = self.conn.retrbinary('RETR %s' % src, f.write)
                    else:
                        res = self.conn.retrbinary('RETR %s' % src, f.write, rest = f.tell())
                except:
                    self.max_attemps -= 1
                    #Доработать эту часть кода(уменьшение количесва максимального обращения
                    if self.max_attemps == 0:
                        mon.set()
                        #print("Множество строка 108",mon.set())
                        logging.exception('')
                        raise
                    self.waiting = True
                    #waiting
                    logging.info('Ожидание состовляет {} sec...'.formate(self.retry_timeout))
                    #Приостонавливает выпаолнение программы на self.retry_timeout секунд
                    time.sleep(self.retry_timeout)
                    #reconnect
                    logging.info('Переподключение->>>', time.clock())
            mon.set()

            if not res.startswith('226 Transfer complete'):
                logging.error('Файл {} загружен не полностью.' .formate(dest))
                #os.remove(dest)
                return None
            return 1


    def put_file(self, src, dest):
        #Загрузка локального файла в удаленный коталог
        with open(src, 'rb') as f:
            self.ptr = f.tell()

            @setInterval(self.monitoring_interval)
            def monitor():
                if not self.waiting:
                    i = f.tell()
                    if self.ptr < i:
                        logging.debug("%d - %0.1f Kb/s" %(i, (i - self.ptr) / (1024 * self.monitoring_interval)))
                        self.ptr = i
                    else:
                        self.conn.close()
            local_file_size = os.stat(src).st_size
            res = ''

            mon = monitor()

            while local_file_size > f.tell():
                try:
                    self.connect()
                    self.waiting = False
                    #Возобновить передачу с позиции гле были отключены
                if f.tell() == 0:
                    res = self.conn.storbinary('STOR %s' % dest, fp=f)
                else:
                    res = self.conn.storbinary('STOR %s' % dest, fp=f, rest=f.tell())
                except:
                self.max_attempts -= 1
                if self.max_attempts == 0:
                    mon.set()
                    logging.exception('')
                    raise
                self.waiting = True
                logging.info('waiting {} sec...'.format(self.retry_timeout))
                time.sleep(self.retry_timeout)
                logging.info('reconnect')

            mon.set()  # stop monitor

            if not res.startswith('226 Transfer complete'):
                logging.error('Uploaded file {} is not full. res = {}'.format(dest, res))
                return None
            return 1

    def put_file_old(self, src, dest):
        #Отображение процесса переноса данных на сервер
        def print_transfer_status(block):
            nonlocal bytes_transferred, total_bytes
            bytes_transferred += len(block)
            if total_bytes > 0:
                percent = round((bytes_transferred / total_bytes) )





#Запуск бесконечного цикла
while True:
    #Цикл просмотра файлов в папке  venv
    for file in os.listdir(dir_name):
        #Проверка налияае файла .py
        if file.endswith(".py"):
            #Имя файла .py
            print(os.path.join("/", file))
