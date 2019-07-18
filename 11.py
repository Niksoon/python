import os
dir_name = "venv/"

def my():
    print('1')
#Запуск бесконечного цикла
while True:
    #Цикл просмотра файлов в папке  venv
    for file in os.listdir(dir_name):
        #Проверка налияае файла .py
        if file.endswith(".py"):
            #Имя файла .py
            print(os.path.join("/", file))
            print("990")
            print("11")