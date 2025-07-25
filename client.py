# クライアント側、１，２で状態を管理、複数人の参加可能, ユーザー名で識別、チャットは参加者全員に見られる
import socket
import threading

def send(sock, opcode, payload):
    sock.sendall(f"{opcode}|{payload}".encode())

def receive(sock):
    return sock.recv(1024).decode()

def listen_for_messages(sock):
    try:
        while True:
            data = sock.recv(1024).decode()
            if not data:
                break
            opcode, payload = data.split('|', 1)
            if opcode == '5':
                print(f"\n[受信] {payload}\n> ", end='')
    except:
        pass

def main():
    host, port = '127.0.0.1', 12345
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((host, port))

    print("1: 新しいチャットルームを作成")
    print("2: チャットルームに参加")
    mode = input("番号を選択してください (1/2): ").strip()

    if mode == '1':
        name = input("あなたの名前（ホスト）: ").strip()
        send(sock, 0, name)
        if receive(sock) != "1|OK":
            print("作成失敗")
            sock.close()
            return
        token_msg = receive(sock)
        token = token_msg.split('|', 1)[1]
        print(f"チャットルーム作成成功！トークン: {token}")

    elif mode == '2':
        token = input("参加するトークン: ").strip()
        name = input("あなたの名前（ゲスト）: ").strip()
        send(sock, 3, f"{token},{name}")
        resp = receive(sock)
        if not resp.startswith("1|JOINED"):
            print("参加失敗")
            sock.close()
            return
        print(f"チャットルームに参加しました: {name}")

    else:
        print("無効な選択")
        sock.close()
        return

    threading.Thread(target=listen_for_messages, args=(sock,), daemon=True).start()

    print("=== メッセージ入力（Ctrl+Cで終了） ===")
    try:
        while True:
            msg = input("> ")
            send(sock, 4, msg)
    except KeyboardInterrupt:
        print("\n終了")
        sock.close()

if __name__ == "__main__":
    main()

