import socket
import threading

from udp_protocol import build_udp_payload, parse_udp_message
from state import rooms, tokens

SERVER_PORT = 9001
DEFAULT_SERVER_IP = "127.0.0.1"
MAX_MESSAGE_SIZE = 4096

class UDPChatClient:
    def __init__(self, username, server_ip, room_name, token, local_port, server_port=SERVER_PORT):
        self.username = username
        self.room_name = room_name
        self.token = token
        self.server_ip = server_ip
        self.server_port = server_port
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind(("0.0.0.0",local_port))
        self.running = True

    def register_address(self):
        try:
            payload = build_udp_payload(self.room_name, self.token, "__REGISTER__")
            self.sock.sendto(payload, (self.server_ip, self.server_port))
            local_ip, local_port = self.sock.getsockname()
            print(f"[登録] 自分のアドレス: {local_ip}:{local_port}")
        except Exception as e:
            print(f"[登録エラー] {e}")

    # 受信スレッド
    def start(self):
        self.register_address()  # アドレス登録のために最初に送信
        threading.Thread(target=self.receive_messages, daemon=True).start()
        print("=== チャットを開始します。Ctrl+Cで終了 ===")
        self.send_loop()

    def receive_messages(self):
        while self.running:
            try:
                data, _ = self.sock.recvfrom(MAX_MESSAGE_SIZE)
                if not data:
                    continue
                sender, message = parse_udp_message(data)
                print(f"\n{sender}: {message}\n> ", end="")
            except Exception as e:
                print(f"[受信エラー] {e}")
                break
            except KeyboardInterrupt:  
                print("\n[終了] チャットを終了します。")
                self.stop()
                break

    def send_loop(self):
        try:
            while self.running:
                msg = input("> ").strip()
                if not msg:
                    continue

                payload = build_udp_payload(self.room_name, self.token, msg)

                if len(payload) > MAX_MESSAGE_SIZE:
                    print("エラー：メッセージが4096バイトを超えています。")
                else:
                    self.sock.sendto(payload, (self.server_ip, self.server_port))
        except KeyboardInterrupt:
            print("\n[終了] チャットを終了します。")
            self.stop()
        except Exception as e:
            print(f"[送信エラー] {e}")
            self.stop()

    def stop(self):
        self.running = False
        self.sock.close()

def main():
    import argparse

    parser = argparse.ArgumentParser(description="UDP Chat Client")
    parser.add_argument("--token", required=True, help="チャットルーム用の認証トークン")
    args = parser.parse_args()

    token = args.token

    if token not in tokens:
        print("エラー: 指定されたトークンが存在しません。")
        return

    user_info = tokens[token]
    room_name = user_info["room_name"]
    username = user_info["username"]

    host_token = rooms[room_name]["host_token"]
    host_info = tokens.get(host_token)
    if not host_info:
        print("エラー: ホスト情報が見つかりません。")
        return
    # ポートはOS自動割当
    local_port = 0

    client = UDPChatClient(
        username=username,
        server_ip=DEFAULT_SERVER_IP,
        room_name=room_name,
        token=token,
        local_port=local_port
    )
    client.start()

if __name__ == "__main__":
    main()