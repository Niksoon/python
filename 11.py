import os
import ftplib
import re
import logging
import threading
import time
import socket

def setInterval(interval, times = -1):
    # This will be the actual decorator, with fixed interval and times parameter
    def outer_wrap(function):
        # This will be the function to be called
        def wrap(*args, **kwargs):
            stop = threading.Event()
            # This is another function to be executed in a different thread to simulate setInterval
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
            while remote_file_size > f.tell():
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
            print("Получили переменную блок 176 строка", block)
            nonlocal bytes_transferred, total_bytes
            bytes_transferred += len(block)
            if total_bytes > 0:
                percent = round((bytes_transferred / total_bytes) * 100, 2 )
                print("{} / {} bytes ({}%)".format(bytes_transferred, total_bytes, percent))
            else:
                print("{} bytes" .format(bytes_transferred))
            return block
        if os.path.isfile(src):
            print("Просмотр файла строка 185" ,os.path.isfile(src))
            with open(src, 'rb') as fh:
                if self.show_progress:
                    total_bytes = os.path.getsize(src)
                    bytes_transferred = 0
                    self.conn.storbinary(cmd='STOR {}'.format(dest), fp=fh, callback=print_transfer_status)
                else:
                    self.conn.storbinary(cmd='STOR {}'.format(dest), fp=fh)
        else:
            print("Локальный файл не существует: {}".format(src))
    def delete_file(self, path):
        try:
            self.conn.delete(path)
        except ftplib.error_perm as err:
            print("Error with permissions: {}".format(str(err)))
        except ftplib.error_reply as err:
            print("Error: {}".format(str(err)))

    def move_file(self, src, dest):
        self.conn.rename(src, dest)

    ### Permissions properties ###

    def can_write_to_dir(self, path):
        return self._permission_check(path, 'c')

    def can_make_subdirectories(self, path):
        return self._permission_check(path, 'm')

    def can_list_dir(self, path):
        return self._permission_check(path, 'l')

    def _permission_check(self, path, perm):

        try:
            return perm in self._permissons[path]
        except AttributeError:
            self._permissions = {} # first time asking for permissions at all
        except KeyError:
            pass # first time asking for permissions for this path

        # MLSD permission values, from http://tools.ietf.org/html/rfc3659.html
        # ('incoming', {'perm': 'flcdmpe'})
        # a = For files only.  The APPE (append) command may be applied to the file.
        # c = For dirs only.  Files may be created in the directory.
        # d = For all.  The file/dir may be deleted.
        # e = For dirs.  The user can enter the directory, and CWD should work.
        # f = For all.  The file/dir may be renamed.
        # l = For dirs.  List commands can be used.
        # m = For dirs.  MKD may be used to make subdirs.
        # p = For dirs.  Objects in the dir (though not necessarily the dir itself) may be deleted.
        # r = For files.  RETR may be applied (to retrive the file)
        # w = For files.  STOR may be applied (to write files)

        # mlsd() returns an iterator.  next(...) grabs items off the iterator until it finds one called '.',
        # then grabs the string of permissions for it.
        permissions = list(next(obj for obj in self.conn.mlsd(path, ['perm']) if obj[0] == '.')[1]['perm'])
        self._permissions[path] = permissions

        return perm in self._permissions[path]

    def connect(self):
        try:
            self.conn = ftplib.FTP(self.host, self.username, self.password)
            self.conn.sendcmd("TYPE i") # switch to binary mode

            # optimize socket params for download task
            self.conn.sock.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
            #self.conn.sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_KEEPINTVL, 75) # not an option on Windows
            #self.conn.sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_KEEPIDLE, 60) # not an option on Windows

            self.conn.set_debuglevel(self.FTP_DEBUG_LEVEL)
            self.conn.set_pasv(True)
        except ftplib.error_perm as err:
            print("Error: {}".format(str(err)))

    def disconnect(self):
        self.conn.quit()

if __name__ == "__main__":
    while True:
        № path = '/'
        filename = '100GB.zip'

        logging.basicConfig(format='%(asctime)s %(levelname)s: %(message)s', level=logging.DEBUG)
        ftp = Ftp_Connection('"test.rebex.net:22"', 'demo', 'password')
        ftp.put_file(filename, filename)
        ftp.get_file(filename, filename)
        pass

#Запуск бесконечного цикла
"""while True:
    #Цикл просмотра файлов в папке  venv
    for file in os.listdir(dir_name):
        #Проверка налияае файла .py
        if file.endswith(".py"):
            #Имя файла .py
            print(os.path.join("/", file))
"""