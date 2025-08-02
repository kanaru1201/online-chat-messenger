import sys
import socket

from server.protocol.udp_protocol import build_udp_message, parse_udp_payload

DEFAULT_IP = '127.0.0.1'
DEFAULT_PORT = 9001
MAX_MESSAGE_SIZE = 4096

class UDPChatServer:
    def __init__(self, ip, port, room_manager, max_message_size=MAX_MESSAGE_SIZE):
        self.SERVER_ADDRESS = ip
        self.SERVER_PORT = port
        self.MAX_MESSAGE_SIZE = max_message_size
        self.running = True
        self.room_manager = room_manager
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    def bind(self):
        try:
            self.sock.bind((self.SERVER_ADDRESS, self.SERVER_PORT))
            print(f"[起動] サーバーを {self.SERVER_ADDRESS}:{self.SERVER_PORT} にバインドしました")
        except Exception as e:
            print(f"バインド失敗: {e}")
            sys.exit(1)

    def start(self):
        self.bind()
        print("UDPチャットサーバーが起動しました。メッセージを待っています...")

        while self.running:
            try:
                data, address = self.sock.recvfrom(self.MAX_MESSAGE_SIZE)
                print(f"UDPパケット受信: {address} サイズ={len(data)}")
            except Exception as e:
                print(f"[受信エラー] {e}")
                continue

            try:
                if not data:
                    continue
                room_name,token,message = parse_udp_payload(data)

                rooms, tokens = self.room_manager.rooms, self.room_manager.tokens

                if message == "__REGISTER__":
                    if token in tokens:
                        tokens[token]["address"] = address
                        try:
                            self.room_manager.save_to_json()
                            print(f"トークン {token} にアドレス {address} を登録＆保存しました")
                        except Exception as e:
                            print(f"トークン {token} のアドレス保存に失敗しました: {e}")
                    else:
                        print(f"未知のトークン {token} のアドレス登録要求を拒否しました")
                    continue

                if message == "__LEAVE__":
                    try:
                        self.room_manager.delete_room_if_host_left(room_name, token)
                    except Exception as e:
                        print(f"[退出処理エラー] {e}")
                    continue 

                is_valid, reason = self.room_manager.validate_token_and_address(token, room_name, address)
                if not is_valid:
                    print(reason)
                    continue

                rooms, tokens = self.room_manager.rooms, self.room_manager.tokens
                sender = tokens[token]["username"]
                for member_token in rooms[room_name]["members"]:
                    if member_token == token:
                        continue
                    addr = tokens[member_token]["address"]
                    if not addr:
                        print(f"{tokens[member_token]['username']} のアドレス未登録のためスキップ")
                        continue
                    if isinstance(addr, list):
                        addr = tuple(addr)
                    payload = build_udp_message(sender, message)
                    self.sock.sendto(payload, addr)
                    print(f"[送信] {tokens[member_token]['username']} へ中継: {message}")

            except Exception as e:
                print(f"[処理エラー] {e}")

    def stop(self):
        self.running = False
        self.sock.close()
        print("UDPサーバー停止")
