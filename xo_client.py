# Импорт модуля для работы с сокетами и потоками
import socket
import threading

# Создание сокета
client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# Установка параметров сервера (хост и порт)
host = '127.0.0.1'  # Локальный хост
port = 12345         # Произвольный порт

# Подключение к серверу
client_socket.connect((host, port))
print("Добро пожаловать в игру 'Крестики-нолики'!\n")

# Запрос имени у игрока
name = input("Введите имя: ")

# Отправка имени на сервер
client_socket.send(name.encode())

# Функция для чтения сообщений от сервера
def receive_messages():
    while True:
        try:
            # Получение данных от сервера
            data = client_socket.recv(1024)
            if not data:
                break
            # Вывод полученных данных на экран
            print(data.decode())
        except Exception as e:
            print(f"Error receiving messages: {e}")
            break

# Запуск потока для приема сообщений от сервера
receive_thread = threading.Thread(target=receive_messages)
receive_thread.start()

# Отправка сообщения серверу
try:
    while True:
        # Ввод сообщения с клавиатуры
        message = input()
        # Отправка сообщения на сервер
        client_socket.send(message.encode())
except Exception as e:
    print(f"Error sending messages: {e}")

# Закрытие соединения
client_socket.close()
