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
        # Перерыв на подключение
        self.retry_timeout = 15



