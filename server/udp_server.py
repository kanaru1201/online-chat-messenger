import os
import socket
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from protocol.ucrp import build_udp_message, parse_udp_payload

MAX_MESSAGE_SIZE = 4096

class UDP_Chat_Server:
    def __init__(self, host: str, udp_port: int, room_manager):
        self.host = host
        self.udp_port = udp_port
        self.room_manager = room_manager
        self.udp_sock = None
        self.running = False

    def bind(self):
        self.udp_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.udp_sock.bind((self.host, self.udp_port))
        self.running = True
        print(f"[起動] UDPサーバーを {self.host}:{self.udp_port} にバインドしました\n")

    def start(self):
        self.bind()
        print("UDPチャットサーバーが起動しました。メッセージを待っています...\n")

        while self.running:
            try:
                data, address = self.udp_sock.recvfrom(MAX_MESSAGE_SIZE)
                if not data:
                    continue
                print(f"[受信] UDPパケット: {address} サイズ={len(data)}")
                self.handle_packet(data, address)
            except Exception as e:
                if self.running:
                    print(f"[受信エラー] {e}")

    def handle_packet(self, data: bytes, address: tuple):
        try:
            room_name, token, message = parse_udp_payload(data)
            print(f"[受信処理] ルーム: {room_name}, トークン: {token[:8]}..., メッセージ: {message}")
            self.process_message(room_name, token, message, address)
        except Exception as e:
            print(f"[処理エラー] {e}")

    def process_message(self, room_name: str, token: str, message: str, address: tuple):
        rooms = self.room_manager.rooms
        tokens = self.room_manager.tokens

        if message == "__REGISTER__":
            if token in tokens:
                tokens[token]["address"] = address
                self.room_manager.save_to_json()
                print(f"[登録] トークン {token[:8]}... にアドレス {address} を登録しました\n")
            else:
                print(f"[登録拒否] 未知のトークン {token[:8]}...")
            return

        if message == "__JOIN__":
            if self.room_manager.validate_token_and_address(token, room_name)[0]:
                confirmation = f"ルーム '{room_name}' に参加しました"
                self.udp_sock.sendto(confirmation.encode('utf-8'), address)
                print(f"[JOIN] {token[:8]}... がルーム {room_name} に参加しました")
            else:
                print(f"[JOIN失敗] バリデーションエラー: token={token[:8]}...")
            return

        is_valid, reason = self.room_manager.validate_token_and_address(token, room_name)
        if not is_valid:
            print(f"[バリデーション失敗] {reason}")
            return

        if room_name not in rooms or token not in tokens:
            print("[中継失敗] ルームまたはトークンが存在しません")
            return

        sender = tokens[token]["username"]
        members = rooms[room_name]["members"]

        for member_token in members:
            if member_token == token:
                continue

            addr = tokens[member_token].get("address")
            if not addr:
                continue

            if isinstance(addr, list):
                addr = tuple(addr)

            try:
                payload = build_udp_message(sender, message)
                self.udp_sock.sendto(payload, addr)
                print(f"[送信] {tokens[member_token]['username']} へ: {message}")
            except Exception as e:
                print(f"[送信エラー] {tokens[member_token]['username']}: {e}")

    def stop(self):
        self.running = False
        if self.udp_sock:
            self.udp_sock.close()
            print("[停止] UDPサーバーを停止しました")