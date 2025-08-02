from datetime import datetime
import json
import secrets
import time

class RoomManager:
    def __init__(self):
        # チャットルーム情報
        # {room_name: {"host_token": token, "members": [tokens], "created_at": timestamp}}
        self.rooms = {}
        # トークン情報
        # {token: {"username": name, "room_name": room, "is_host": bool, "address": (ip, port)}}
        self.tokens = {}
        
        print("RoomManager初期化: キャッシュをクリアしました")

    def generate_token(self):
        return "token_" + secrets.token_hex(16)

    def room_exists(self, room_name):
        return room_name in self.rooms

    def create_room(self, room_name, username, address):
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
            "address": address
        }

        return True, token

    def join_room(self, room_name, username, address):
        if not self.room_exists(room_name):
            return False, None

        existing_token = self.find_user_token_in_room(room_name, username)
        if existing_token:
            self.tokens[existing_token]["address"] = address
            print(f"  既存ユーザー: {username} (アドレス更新: {address}, トークン: {existing_token})")
            return True, existing_token

        token = self.generate_token()
        
        self.rooms[room_name]["members"].append(token)
        
        self.tokens[token] = {
            "username": username,
            "room_name": room_name,
            "is_host": False,
            "address": address
        }

        return True, token

    def find_user_token_in_room(self, room_name, username):
        if room_name not in self.rooms:
            return None
        
        for token in self.rooms[room_name]["members"]:
            if token in self.tokens and self.tokens[token]["username"] == username:
                return token
        return None

    def validate_token_and_address(self, token, room_name, address):
        if token not in self.tokens:
            return False, "無効なトークンです"
        
        if room_name not in self.rooms:
            return False, "ルームが存在しません"
        
        if token not in self.rooms[room_name]["members"]:
            return False, "トークンがこのルームのメンバーではありません"
        
        if self.tokens[token]["room_name"] != room_name:
            return False, "トークンが別のルームに属しています"
        
        if self.tokens[token]["address"] != address:
            return False, "アドレスが一致しません"
        
        return True, "有効なトークンとアドレスです"

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

    def send_message_validation(self, token, room_name, address, message):
        is_valid, reason = self.validate_token_and_address(token, room_name, address)
        
        if not is_valid:
            return False, reason
        
        sender_info = self.tokens[token]
        
        return True, {
            'sender': sender_info['username'],
            'room': room_name,
            'message': message,
            'timestamp': time.time()
        }

    def save_to_json(self, filename="room_manager.json"):
        try:
            data = {
                'rooms': self.rooms,
                'tokens': self.tokens,
                'saved_at': datetime.now().isoformat()
            }

            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            print(f"データを {filename} に保存しました")
            return True

        except Exception as e:
            print(f"保存エラー: {e}")
            return False

    def load_from_json(self, filename="room_manager.json"):
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                data = json.load(f)

            self.rooms = data.get('rooms', {})
            self.tokens = data.get('tokens', {})

            print(f"データを {filename} から手動で読み込みました")
            if 'saved_at' in data:
                print(f"保存日時: {data['saved_at']}")
            
            print(f"読み込み結果: {len(self.rooms)}個のルーム, {len(self.tokens)}個のトークン")
            return True

        except FileNotFoundError:
            print(f"ファイル {filename} が見つかりません")
            return False
        except Exception as e:
            print(f"読み込みエラー: {e}")
            return False

    def display_status(self):
        print("=== ルームマネージャー状態 ===")
        print(f"総ルーム数: {len(self.rooms)}")
        
        for room_name, room_info in self.rooms.items():
            print(f"\nルーム名: {room_name}")
            print(f"  ホストトークン: {room_info['host_token']}")
            print(f"  作成日時: {datetime.fromtimestamp(room_info['created_at']).isoformat()}")
            print(f"  メンバー数: {len(room_info['members'])}")
            
            for token in room_info['members']:
                if token in self.tokens:
                    token_info = self.tokens[token]
                    role = "ホスト" if token_info['is_host'] else "メンバー"
                    print(f"    {token} → {token_info['username']} ({role}) [アドレス: {token_info['address']}]")

        print(f"\n総トークン数: {len(self.tokens)}")