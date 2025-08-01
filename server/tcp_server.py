from datetime import datetime
import json
import os
import secrets
import socket
import sys
import threading
import time

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from server.protocol.tcrp import TCRProtocol, OP_CREATE_ROOM, OP_JOIN_ROOM, STATE_REQUEST

class TCPServer:
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.socket = None
        self.running = False
        # チャットルーム情報
        # {room_name: {"host_token": token, "members": [tokens], "created_at": timestamp}}
        self.rooms = {}
        # トークン情報
        # {token: {"username": name, "room_name": room, "is_host": bool, "address": (ip, port)}}
        self.tokens = {}
        
        print("サーバー起動時にキャッシュを初期化しました")

    def start(self):
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.socket.bind((self.host, self.port))
            self.socket.listen()
            self.running = True
            print(f"TCPサーバー開始: {self.host}:{self.port}")

            while self.running:
                try:
                    client_socket, address = self.socket.accept()
                    print(f"[TCP] 接続: {address}")
                    thread = threading.Thread(target=self._handle_client, args=(client_socket, address), daemon=True)
                    thread.start()
                except OSError:
                    break
                except Exception as e:
                    print(f"接続処理エラー: {e}")
        except Exception as e:
            print(f"サーバー起動エラー: {e}")

    def _handle_client(self, client_socket,address):
        try:
            op, state, room_name, payload = TCRProtocol.receive_tcrp_message(client_socket)

            if state != STATE_REQUEST:
                print(f"無効な状態コード: {state}")
                return

            if op == OP_CREATE_ROOM:
                success, token = self.create_room(room_name, payload, address)
                print(f"{'作成成功' if success else '既に存在'}: ルーム '{room_name}' (ユーザー: {payload}")
                if success:
                    print(f"  → 発行されたトークン: {token}")
                    self.save_to_json()
            elif op == OP_JOIN_ROOM:
                success, token = self.join_room(room_name, payload, address)
                print(f"{'参加成功' if success else '参加失敗'}: ルーム '{room_name}' に {payload} 入室")
                if success:
                    print(f"  → 発行されたトークン: {token}")
                    self.save_to_json()
            else:
                print(f"その操作コードは使えません（コード: {op}）")
                return

            compliance = TCRProtocol.build_response_compliance(room_name, op, int(success))
            complete = TCRProtocol.build_response_complete(room_name, op, token if success else "")
            client_socket.sendall(compliance + complete)

        except Exception as e:
            print(f"クライアント処理エラー: {e}")
        finally:
            client_socket.close()
            print(f"[TCP] 切断")

    def stop(self):
        self.running = False
        if self.socket:
            self.socket.close()
            self.socket = None
            print("ソケット閉じた")
        
        self.save_to_json()

    def generate_token(self):
        return "token_" + secrets.token_hex(8)

    def room_exists(self, room_name):
        return room_name in self.rooms

    def create_room(self, room_name, username, address):
        self.load_from_json()
        if self.room_exists(room_name):
            return False, None

        token = self.generate_token()
        
        self.rooms[room_name] = {
            "host_token": token,
            "members": [token],
            "created_at": time.time()
        }
        
        self.tokens[token] = {
            "username": username,
            "room_name": room_name,
            "is_host": True,
            "address": None
        }
        return True, token

    def join_room(self, room_name, username, address):
        self.load_from_json()
        if not self.room_exists(room_name):
            return False, None

        existing_token = self.find_user_token_in_room(room_name, username)
        if existing_token:
            return True, existing_token

        token = self.generate_token()
        self.rooms[room_name]["members"].append(token)
        self.tokens[token] = {
            "username": username,
            "room_name": room_name,
            "is_host": False,
            "address": None
        }
        return True, token

    def find_user_token_in_room(self, room_name, username):
        if room_name not in self.rooms:
            return None
        
        for token in self.rooms[room_name]["members"]:
            if token in self.tokens and self.tokens[token]["username"] == username:
                return token
        return None
    
# TCPでアドレス登録しないので削除
    # def validate_token_and_address(self, token, room_name):
    #     if token not in self.tokens:
    #         return False, "Invalid token"
        
    #     if room_name not in self.rooms:
    #         return False, "Room does not exist"
        
    #     if token not in self.rooms[room_name]["members"]:
    #         return False, "Token not member of this room"
        
    #     if self.tokens[token]["room_name"] != room_name:
    #         return False, "Token belongs to different room"
        
    #     # if self.tokens[token]["address"] != address:
    #     #     return False, "Address mismatch"
        
    #     return True, "Valid token and address"

    def get_user_info_by_token(self, token):
        return self.tokens.get(token)

    def get_room_members_info(self, room_name):
        if room_name not in self.rooms:
            return []
        
        members_info = []
        for token in self.rooms[room_name]["members"]:
            if token in self.tokens:
                token_info = self.tokens[token]
                members_info.append({
                    'token': token,
                    'username': token_info['username'],
                    'address': token_info['address'],
                    'is_host': token_info['is_host']
                })
        return members_info

    def get_room_host_token(self, room_name):
        if room_name in self.rooms:
            return self.rooms[room_name]["host_token"]
        return None

    # def send_message_validation(self, token, room_name, address, message):
        # is_valid, reason = self.validate_token_and_address(token, room_name, address)
        
        # if not is_valid:
        #     return False, reason
        
        # sender_info = self.tokens[token]
        
        # return True, {
        #     'sender': sender_info['username'],
        #     'room': room_name,
        #     'message': message,
        #     'timestamp': time.time()
        # }

    def save_to_json(self, filename="room_manager.json"):
        base_dir = os.path.dirname(os.path.abspath(__file__))
        filepath = os.path.join(base_dir, filename)
        try:
            data = {
                'rooms': self.rooms,
                'tokens': self.tokens,
                'saved_at': datetime.now().isoformat()
            }

            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            print(f"データを {filename} に保存しました")
            return True

        except Exception as e:
            print(f"保存エラー: {e}")
            return False

    def load_from_json(self, filename="room_manager.json"):
        base_dir = os.path.dirname(os.path.abspath(__file__))
        filepath = os.path.join(base_dir, filename)
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)

            self.rooms = data.get('rooms', {})
            self.tokens = data.get('tokens', {})

            print(f"データを {filepath} から手動で読み込みました")
            if 'saved_at' in data:
                print(f"保存日時: {data['saved_at']}")
            
            print(f"読み込み結果: {len(self.rooms)}個のルーム, {len(self.tokens)}個のトークン")
            return True

        except FileNotFoundError:
            print(f"ファイル {filepath} が見つかりません")
            return False
        except Exception as e:
            print(f"読み込みエラー: {e}")
            return False

    def display_status(self):
        print("=== TCP Server Status ===")
        print(f"Total rooms: {len(self.rooms)}")
        
        for room_name, room_info in self.rooms.items():
            print(f"\nRoom: {room_name}")
            print(f"  Host Token: {room_info['host_token']}")
            print(f"  Created: {datetime.fromtimestamp(room_info['created_at']).isoformat()}")
            print(f"  Members: {len(room_info['members'])}")
            
            for token in room_info['members']:
                if token in self.tokens:
                    token_info = self.tokens[token]
                    role = "Host" if token_info['is_host'] else "Member"
                    print(f"    {token} → {token_info['username']} ({role}) [Address: {token_info['address']}]")

        print(f"\nTotal unique tokens: {len(self.tokens)}")

if __name__ == "__main__":
    server = TCPServer("localhost", 9090)
    
    try:
        server.display_status()
        server.start()
    except KeyboardInterrupt:
        print("\nサーバーを停止しています...")
        server.stop()
        print("サーバーが停止しました")