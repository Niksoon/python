import  os
import ftplib

class FTP_Connection():

    def __init__(self, host, username, password):
        self.host = host
        self.username = username
        self.password = password

    def isdir (self, directiry):
        try:
            self.conn.nlst(directiry)
            print(self.conn.nlst(directiry))
            return True
        except ftplib.error_temp as err:
            if re.match('450\s', str(err)):
                return False
            else:
                raise


if __name__ == "__main__":
    #Данные для подключения на FTP Сервер (логин / пароль)
    ftp = FTP_Connection('"speedtest.tele2.net"', 'anonymous', '')
