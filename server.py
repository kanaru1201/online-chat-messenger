# サーバー側、参加を許可し、トークンを発行する
import socket
import threading
import uuid

rooms = {}  # token: { 'host': username, 'clients': [sock1, sock2, ...] }
client_info = {}  # sock: { 'name': str, 'token': str }

lock = threading.Lock()

def parse_message(msg):
    try:
        opcode, payload = msg.split('|', 1)
        return int(opcode), payload.strip()
    except ValueError:
        return -1, ""

def broadcast(token, message, sender_sock=None):
    with lock:
        for client in rooms[token]['clients']:
            try:
                if client != sender_sock:
                    client.sendall(f"5|{message}".encode('utf-8'))
            except:
                continue

def handle_client(sock):
    try:
        while True:
            data = sock.recv(1024)
            if not data:
                break

            opcode, payload = parse_message(data.decode('utf-8'))

            if opcode == 0:
                # 0: チャットルーム作成（ホスト名）
                username = payload
                token = str(uuid.uuid4())
                with lock:
                    rooms[token] = {'host': username, 'clients': [sock]}
                    client_info[sock] = {'name': username, 'token': token}
                sock.sendall("1|OK".encode())
                sock.sendall(f"2|{token}".encode())
                print(f"[ROOM CREATED] {username} => {token}")

            elif opcode == 3:
                # 3: 参加（トークン,名前）
                try:
                    token, guest_name = payload.split(',', 1)
                except ValueError:
                    sock.sendall("1|ERROR: Format should be token,name".encode())
                    continue

                with lock:
                    if token not in rooms:
                        sock.sendall("1|ERROR: Invalid token".encode())
                    else:
                        rooms[token]['clients'].append(sock)
                        client_info[sock] = {'name': guest_name, 'token': token}
                        sock.sendall("1|JOINED".encode())
                        print(f"[JOINED] {guest_name} joined room {token}")

            elif opcode == 4:
                # 4: メッセージ送信
                with lock:
                    info = client_info.get(sock)
                if not info:
                    sock.sendall("1|ERROR: Not in a room".encode())
                    continue
                sender_name = info['name']
                token = info['token']
                message = f"{sender_name}: {payload}"

                # ブロードキャスト + 自分にも返す
                broadcast(token, message, sender_sock=sock)
                sock.sendall(f"5|{message}".encode())

            else:
                sock.sendall("1|ERROR: Unknown opcode".encode())

    finally:
        with lock:
            info = client_info.pop(sock, None)
            if info and info['token'] in rooms:
                if sock in rooms[info['token']]['clients']:
                    rooms[info['token']]['clients'].remove(sock)
        sock.close()

def main():
    host, port = '127.0.0.1', 12345
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((host, port))
    server.listen(5)
    print(f"[Server] Listening on {host}:{port}")

    while True:
        client_sock, addr = server.accept()
        print(f"[Connection] {addr}")
        threading.Thread(target=handle_client, args=(client_sock,)).start()

if __name__ == "__main__":
    main()


