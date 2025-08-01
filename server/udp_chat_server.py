import sys
import socket
import json
import os

from server.protocol.udp_protocol import build_udp_message, parse_udp_payload

ROOM_MANAGER_PATH = os.path.join(os.path.dirname(__file__), "room_manager.json")

def get_current_rooms_tokens():
    try:
        with open(ROOM_MANAGER_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        rooms = data.get("rooms", {})
        tokens = data.get("tokens", {})
        return rooms, tokens
    except Exception as e:
        print(f"[json読込エラー] {e}")
        return {}, {}

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
        rooms, tokens = get_current_rooms_tokens()
        if token not in tokens:
            return False, "[拒否] 無効なトークン"

        token_info = tokens[token]
        if token_info["room_name"] != room_name:
            return False, f"[拒否] トークンとルーム名が一致しません: {room_name} ≠ {token_info['room_name']}"

        if room_name not in rooms:
            return False, f"[拒否] ルームが存在しません: {room_name}"

        if token not in rooms[room_name]["members"]:
            return False, "[拒否] トークンがルームのメンバーではありません"

        if "address" not in token_info or token_info["address"] is None:
            return False, f"[拒否] トークン {token} のアドレスが未登録です"

        if address[0] != token_info["address"][0]:
            return False, f"[拒否] IPアドレスが一致しません: {address[0]} ≠ {token_info['address'][0]}"

        return True, ""

    def start(self):
        self.bind()
        print("[待機中] UDPチャットサーバーが起動しました。メッセージを待っています...")

        while True:
            try:
                data, address = self.sock.recvfrom(self.MAX_MESSAGE_SIZE)
                print(f"[DEBUG] UDPパケット受信: {address} サイズ={len(data)}")  # ←追加
            except Exception as e:
                print(f"[受信エラー] {e}")
                continue

            try:
                if not data:
                    continue
                room_name,token,message = parse_udp_payload(data)

                rooms, tokens = get_current_rooms_tokens()

                if message == "__REGISTER__":
                    if token in tokens:
                        tokens[token]["address"] = address
                        try:
                            with open(ROOM_MANAGER_PATH, "r", encoding="utf-8") as f:
                                data = json.load(f)
                            data['tokens'][token]['address'] = address
                            with open(ROOM_MANAGER_PATH, "w", encoding="utf-8") as f:
                                json.dump(data, f, ensure_ascii=False, indent=4)
                            print(f"[登録＆保存しました] トークン {token} にアドレス {address} を登録＆保存しました")
                        except Exception as e:
                            print(f"[登録エラー] トークン {token} のアドレス保存に失敗しました: {e}")
                    else:
                        print(f"[拒否] 未知のトークン {token} のアドレス登録要求を拒否しました")
                    continue

                if message == "__LEAVE__":
                    try:
                        with open(ROOM_MANAGER_PATH, "r", encoding="utf-8") as f:
                            data = json.load(f)
                        tokens = data.get("tokens", {})
                        rooms = data.get("rooms", {})
                        token_info = tokens.get(token)
                        if not token_info:
                            print(f"[退出] 未知のトークン: {token}")
                            continue
                        room_name = token_info["room_name"]
                        if rooms.get(room_name, {}).get("host_token") == token:
                            print(f"[退出] ホスト {token_info['username']} のため、ルーム {room_name} を削除します")
                            # 全メンバーtoken削除
                            for member_token in rooms[room_name]["members"]:
                                if member_token in tokens:
                                    del tokens[member_token]
                            # room情報削除
                            del rooms[room_name]
                            data["rooms"] = rooms
                            data["tokens"] = tokens
                            with open(ROOM_MANAGER_PATH, "w", encoding="utf-8") as f:
                                json.dump(data, f, ensure_ascii=False, indent=4)
                            print(f"[削除完了] ルーム {room_name} と全トークンを削除しました")
                        else:
                            print(f"[退出] ホストではありません（通常メンバーの退出）")
                    except Exception as e:
                        print(f"[退出処理エラー] {e}")
                    continue 

                is_valid, reason = self.is_valid_request(room_name, token, address)
                if not is_valid:
                    print(reason)
                    continue

                rooms, tokens = get_current_rooms_tokens()
                sender = tokens[token]["username"]
                for member_token in rooms[room_name]["members"]:
                    if member_token == token:
                        continue
                    addr = tokens[member_token]["address"]
                    if not addr:
                        print(f"[中継スキップ] {tokens[member_token]['username']} のアドレス未登録のためスキップ")
                        continue
                    if isinstance(addr, list):
                        addr = tuple(addr)
                    payload = build_udp_message(sender, message)
                    self.sock.sendto(payload, addr)
                    print(f"[送信] {tokens[member_token]['username']} へ中継: {message}")

            except Exception as e:
                print(f"[処理エラー] {e}")
