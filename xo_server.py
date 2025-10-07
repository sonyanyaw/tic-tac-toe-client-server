import socket
import threading

# Создание сокета
server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# Установка параметров сервера (хост и порт)
host = '127.0.0.1'  # Локальный хост
port = 12345  # Произвольный порт

# Привязка сокета к адресу и порту
server_socket.bind((host, port))

# Слушаем входящие соединения
server_socket.listen(2)

print(F"Сервер запущен на {host}:{port} и ожидает подключения...")

# Список для хранения клиентских соединений
clients = []
symbols = {'X': None, 'O': None}
fields = [
    ["_1_"], ["_2_"], ["_3_"],
    ["_4_"], ["_5_"], ["_6_"],
    ["_7_"], ["_8_"], ["_9_"]
]
board_sent = False
game_started = False
# Флаг, чтобы показать присоединился ли второй игрок
second_player_joined = False
# Словарь для хранения информации о каждом клиенте
players_info = {}
# Индекс текущего активного игрока
active_player_index = 0
# Флаг, чтобы показать, чей сейчас ход
current_player_turn = 0
# Мьютекс для синхронизации доступа к общим данным
mutex = threading.Lock()

# Функция для отправки доски
def send_board():
    global board_sent
    with mutex:
        if not board_sent:
            board = "\n"
            for i in range(0, len(fields), 3):
                row = [fields[i][0], fields[i + 1][0], fields[i + 2][0]]
                board += ' | '.join(row) + "\n"

            # Определение текущего активного игрока
            active_player_info = players_info.get(clients[active_player_index])

            win, message = check_win()

            if not win and active_player_info is not None:
                board += f"\nТекущий ход: {active_player_info['symbol']}\n"

            for c in clients:
                try:
                    c.send(board.encode('utf-8'))
                    if not win:
                        # Если текущий клиент - активный игрок, отправляем приглашение к ходу
                        if c == clients[active_player_index]:
                            c.send("Ваш ход (введите номер ячейки от 1 до 9): ".encode())
                        else:
                            c.send("Ход другого игрока. Пожалуйста, подождите...".encode())
                except Exception as e:
                    print(f"Ошибка отправки доски клиенту: {e}")

            # Установка флага в True после отправки доски
            board_sent = True


def check_win():
    # Проверка условия победы или ничьи
    current_player_info = players_info[clients[active_player_index]]
    current_symbol = current_player_info['name']
    if (
            (fields[0][0] == fields[1][0] == fields[2][0] != ' ') or
            (fields[3][0] == fields[4][0] == fields[5][0] != ' ') or
            (fields[6][0] == fields[7][0] == fields[8][0] != ' ') or
            (fields[0][0] == fields[3][0] == fields[6][0] != ' ') or
            (fields[1][0] == fields[4][0] == fields[7][0] != ' ') or
            (fields[2][0] == fields[5][0] == fields[8][0] != ' ') or
            (fields[0][0] == fields[4][0] == fields[8][0] != ' ') or
            (fields[2][0] == fields[4][0] == fields[6][0] != ' ')
    ):
        return True, f"Игрок {current_symbol} победил!"
    elif all(cell[0] != f"_{i + 1}_" for i, cell in enumerate(fields)):
        return True, "Ничья!"

    return False, ""




def handle_client(client_socket):
    global active_player_index
    global board_sent
    global second_player_joined
    global game_started
    global current_player_turn

    player_name = client_socket.recv(1024).decode()

    # Обработка максимального количества клиентов
    if len(clients) >= 2:
        print("Максимальное количество игроков. Отключаем нового игрока.")
        client_socket.send("Извините, максимальное количество игроков уже подключено.".encode())
        client_socket.close()
        return

    # Добавление клиента в список
    clients.append(client_socket)

    # Добавление информации о новом игроке в словарь
    players_info[client_socket] = {'symbol': 'X' if len(players_info) == 0 else 'O', 'name': player_name}

    # Выбор символ для нового игрока
    player_symbol = players_info[client_socket]['symbol']

    for c in clients:
        if c == client_socket and not second_player_joined:
            # Уведомление первому игроку подождать второго
            c.send(f"{player_name}, Вы играете за '{player_symbol}'. Ожидаем второго игрока...\n".encode())
        elif c == client_socket and second_player_joined:
            # Уведомление второго игрока чем он играет
            c.send(f"{player_name}, Вы играете за '{player_symbol}'.\n".encode())
        elif c != client_socket and second_player_joined:
            # Уведомление первого игрока о присоединении второго
            c.send(f"Игрок {player_name} присоединился и играет за '{player_symbol}'.\n".encode())
            game_started = True


    # Установка флага, если второй игрок зашел
    second_player_joined = True

    # Проверка, есть ли два клиента, чтобы начать игру
    while len(clients) < 2 and (game_started == False):
        pass

    while True:
        try:
            send_board()

            current_player_info = players_info[client_socket]

            data = client_socket.recv(1024).decode()
            if not data:
                break

            # Проверка, что введен корректный номер ячейки
            try:
                move = int(data) - 1

                # Проверка, занята ли уже ячейка
                if not (0 <= move < 9 and fields[move][0] == f"_{move + 1}_"):
                    raise ValueError("Некорректный номер ячейки")

                fields[move] = [f" {current_player_info['symbol']} "]

                # Проверка условия победы или ничьи после каждого хода
                win, message = check_win()
                if win:
                    board_sent = False
                    send_board()
                    for c in clients:
                        try:
                            c.send(f"{message}\n".encode())
                        except Exception as e:
                            print(f"Ошибка отправки результата клиенту: {e}")
                    break


                # Переключение активного игрока
                with mutex:
                    active_player_index = 1 - active_player_index  # Переключаем между 0 и 1
                    board_sent = False

            except ValueError as ve:
                print(f"Ошибка обработки хода: {ve}")
                client_socket.send(f"Ошибка: {ve}. Повторите ввод.\n".encode())

        except Exception as e:
            print(f"Ошибка обработки клиента: {e}")
            break

    # Удаление клиента из списка и информации о нем из словаря
    clients.remove(client_socket)
    del players_info[client_socket]

    # Закрытие соединение
    client_socket.close()


# Прием входящих соединения
while True:
    client_socket, client_address = server_socket.accept()
    print(f"Успешное подключение от {client_address}")

    # Запускаем поток для обработки данного клиента
    client_handler = threading.Thread(target=handle_client, args=(client_socket,))
    client_handler.start()

    # Проверка, если подключилось два игрока, начать игру
    if len(clients) == 2:
        print("Игра начинается!")
        break
