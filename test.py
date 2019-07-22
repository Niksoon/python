import os
import re
import ftplib
import time
import threading
import logging
import socket

def setInterval(interval, times = -1):
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

class FtpConnection():

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

    def put_file(self, src, dest):
        # Загрузка локального файла  src на сервер
        # Открытие файла на чтение - r открытие в двоичном коде b
        with open(src, 'rb') as f:
            # Возвращает текущую позицию указателя в файле относительно его начала.
            self.ptr = f.tell()
            print('Текущая позиция указателя относительно его начала: ', f.tell())

            @setInterval(self.monitoring_interval)

            def monitor():
                if not self.waiting:
                    i = f.tell()
                    if self.ptr <i:
                        logging.debug("%d - %0.1f Kb/s" % (i, (i-self.ptr) / (1024 * self.monitoring_interval)))
                    self.ptr = i
                else:
                    self.conn.close()
            #  размер файла в байтах
            local_file_size = os.stat(src).st_size
            print('Размер файла в байтах: ',local_file_size)
            print('Размер файла в байтах: ',local_file_size)
            res = ''

            mon = monitor()
            while local_file_size > f.tell():
                try:
                    self.connect()
                    self.waiting = False
                    # возобновить перевод с позиции, где мы были отключены
                    if f.tell() == 0:
                        res = self.conn.storbinary('STOR %s' % dest, fp = f)
                    else:
                        res = self.conn.storbynary('STOR $s' % dest, fp = f, rest = f.tell())
                except:
                    self.max_attempts -= 1
                    if self.max_attempts == 0:
                        # Множества вида Пример: {'h', 'o', 'l', 'e'}
                        mon.set()
                        logging.exception('')
                        raise
                    self.waiting = True
                    logging.info('Ожидание ответа {} секунд...'.format(self.retry_timeout))
                    time.sleep(self.retry_timeout)
                    logging.info('Попытка подключения к серверу...')

            mon.set()
            if not res.startswith('226 Transfer complete'):
                logging.error('Загружаемый файл {} не полон.' .format(dest, res))
                return None
            return 1

    def put_file_old(self,src, dest):
        # Загрузка локального файла src в удаленный каталог

        def print_transfered_status(block):
            #В случае успешно установленного соединения show_progress = True
            #обратный вызов будет печатать сообщения о текущем прогрессе
            nonlocal bytes_transferred, total_bytes
            bytes_transferrede =+len(block)
            #
            if total_bytes > 0:
                # округление переданой информации в процентах
                percent = round((bytes_transferred / total_bytes) * 100, 2)
                print("{} / {}  байт ({}%)".format(bytes_transferred, total_bytes, percent))
            else:
                print("{} байт ".format(bytes_transferred))
            return block
        # путь является файлом
        if os.path.isfile(src):
            with open(src, 'rb') as fh:
                if self.show_progress:
                    total_bytes = os.path.getsize(src)
                    bytes_transferred = 0
                    self.conn.storbinary(cmd='STOR {}'.format(dest), fp = fh, callback = print_transfered_status)
                else:
                    self.conn.storbinary(cmd='STOR {}'.format(dest), fp = fh)
        else:
            print("Локальный файл {} не найден!".format(src))

    def delete_file(self, path):
        try:
            self.conn.delete(path)
        except ftplib.error_perm as err:
            print("Ошибка с расшерением файла: {}".format(str(err)))
        except ftplib.error_reply as err:
            print("Ошибка: {}".format(str(err)))

    def move_file(self, src, dest):
        print("Перемещение файла {}" .format(self.conn.rename(src, dest)))
        self.conn.rename(src, dest)

    ### Свойство разрешений! ###

    # Можем писать в каталог
    def can_write_to_dir(self, path):
        print("Можем писать в каталог? - ",self._permission_check(path, 'c' ))
        return self._permission_check(path, 'c')

    # Можем создать каталог
    def can_make_subdirectories(self, path):
        print("Можем создать каталог? - ", self._permission_check(path, 'm'))
        return self._permission_check(path, 'm')

    # Можем перечислить директории
    def can_list_dir(self, path):
        print("Можем перечислить директории? - " , self._permission_check(path, 'l'))
        return self._permission_check(path, 'l')

    # Проверка разрешений
    def _permission_check(self, path, perm):
        try:
            return perm in self._permissions[path]
        except AttributeError:
            # Запрос всех разрешений
            self._permissions = {}
        except KeyError:
            pass
        permissions = list(next(obj for obj in self.conn.mlsd(path, ['perm']) if obj[0] == '.')[1]['perm'])
        self._permissions[path] = permissions
        print("Заглянем? - ", self._permissions[path])
        return perm in self._permissions[path]

    def connect(self):
        try:
            self.conn = ftplib.FTP(self.host, self.username, self.password)
            # Переключение в двоичный режим
            self.conn.sendcmd("TYPE i")
            # оптимизировать параметры сокета для задачи загрузки
            self.conn.sock.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
            # Установите уровень вывода отладки
            self.conn.set_debuglevel(self.FTP_DEBUG_LEVEL)
            # Включение пассивного режима
            self.conn.set_pasv(True)
        except ftplib.error_perm as err:
            print("Ошибка: ".format(str(err)))

    def diaconnect(self):
        self.conn.quit()

if __name__ == "__main__":
    path = '/'
    filename = ''
    logging.basicConfig(format='%(asctime)s %(levelname)s: %(message)s', level=logging.DEBUG)
    ftp = FtpConnection('10.58.2.23', 'ftp-user', 'Qw123456')
    ftp.put_file(path + filename, path + filename)
    pass











