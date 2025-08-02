import socket
import threading

from udp_protocol import build_udp_payload, parse_udp_message

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

        # 受信スレッド開始
    def start(self):
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
    # TCPで情報取得してからUDPチャットクライアントを起動する（この後実装）
    # username, room_name, token = tcp_get_info()
    # server_ip = "127.0.0.1"
    # local_port = 50000  # 任意のローカルポートを指定
    # client = UDPChatClient(username, server_ip, room_name, token, local_port)
    # client.start()
    
    # udp_chat用
    import argparse

    parser = argparse.ArgumentParser(description="UDP Chat Client")
    parser.add_argument("--username", required=True, help="チャット内で使用するユーザー名")
    parser.add_argument("--server-ip", required=True, help="UDPサーバのIPアドレス")
    parser.add_argument("--local-port", type=int, required=True, help="このクライアントが使うUDPポート番号")
    parser.add_argument("--token", required=True, help="チャットルーム用の認証トークン")
    parser.add_argument("--room", required=True, help="チャットルーム名")
    args = parser.parse_args()

    client = UDPChatClient(
        username=args.username,
        server_ip=args.server_ip,
        room_name=args.room,
        token=args.token,
        local_port=args.local_port
    )
    client.start()

if __name__ == "__main__":
    main()
