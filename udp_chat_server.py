import sys
import socket

from udp_protocol import build_udp_message, parse_udp_payload
from state import rooms, tokens

DEFAULT_IP = '127.0.0.1'
DEFAULT_PORT = 9001
MAX_MESSAGE_SIZE = 4096

class UDPChatServer:
    def __init__(self, ip, port, max_message_size=MAX_MESSAGE_SIZE):
        self.SERVER_ADDRESS = ip
        self.SERVER_PORT = port
        self.MAX_MESSAGE_SIZE = max_message_size
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    def bind(self):
        try:
            self.sock.bind((self.SERVER_ADDRESS, self.SERVER_PORT))
            print(f"[起動] サーバーを {self.SERVER_ADDRESS}:{self.SERVER_PORT} にバインドしました")
        except Exception as e:
            print(f"[エラー] バインド失敗: {e}")
            sys.exit(1)

    def is_valid_request(self,room_name, token, address) -> tuple[bool, str]:
        if token not in tokens:
            return False, "[拒否] 無効なトークン"

        token_info = tokens[token]
        if token_info["room_name"] != room_name:
            return False, f"[拒否] トークンとルーム名が一致しません: {room_name} ≠ {token_info['room_name']}"

        if room_name not in rooms:
            return False, f"[拒否] ルームが存在しません: {room_name}"

        if token not in rooms[room_name]["members"]:
            return False, "[拒否] トークンがルームのメンバーではありません"

        if address[0] != token_info["address"][0]:
            return False, f"[拒否] IPアドレスが一致しません: {address[0]} ≠ {token_info['address'][0]}"

        return True, ""

    def start(self):
        self.bind()
        print("[待機中] UDPチャットサーバーが起動しました。メッセージを待っています...")

        while True:
            try:
                data, address = self.sock.recvfrom(self.MAX_MESSAGE_SIZE)
            except Exception as e:
                print(f"[受信エラー] {e}")
                continue

            try:
                if not data:
                    continue
                room_name,token,message = parse_udp_payload(data)

                is_valid, reason = self.is_valid_request(room_name, token, address)
                if not is_valid:
                    print(reason)
                    continue

                sender = tokens[token]["username"]
                for member_token in rooms[room_name]["members"]:
                    if member_token == token:
                        continue
                    addr = tokens[member_token]["address"]
                    payload = build_udp_message(sender, message)
                    self.sock.sendto(payload, addr)
                    print(f"[送信] {tokens[member_token]['username']} へ中継: {message}")

            except Exception as e:
                print(f"[処理エラー] {e}")

def main():
    ip = input(f"サーバーIPを入力してください（デフォルト: {DEFAULT_IP}）: ").strip()
    port = input(f"ポート番号を入力してください（デフォルト: {DEFAULT_PORT}）: ").strip()

    ip = ip if ip else DEFAULT_IP
    port = int(port) if port else DEFAULT_PORT

    server = UDPChatServer(ip=ip, port=port)
    server.start()

if __name__ == "__main__":
    main()
