import socket
import threading

from server.protocol.udp_protocol import build_udp_payload, parse_udp_message

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

    def start(self):
        self.register_address()
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
        try:
            payload = build_udp_payload(self.room_name, self.token, "__LEAVE__")
            self.sock.sendto(payload, (self.server_ip, self.server_port))
            print("[退出通知] サーバーに退出メッセージを送りました")
        except Exception as e:
            print(f"[退出通知エラー] {e}")
        self.running = False
        self.sock.close()