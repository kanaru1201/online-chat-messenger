import socket
import threading
import sys
import os
import secrets

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from tcrp import TCRProtocol, OP_CREATE_ROOM, OP_JOIN_ROOM, STATE_REQUEST

class TCPServer:
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.socket = None
        self.running = False
        self.rooms = {}
        self.tokens = {}
        self.room_tokens = {}
        self.user_tokens = {}

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
                    threading.Thread(target=self._handle_client, args=(client_socket, address), daemon=True).start()
                except OSError:
                    break
                except Exception as e:
                    print(f"接続処理エラー: {e}")
        except Exception as e:
            print(f"サーバー起動エラー: {e}")

    def _handle_client(self, client_socket, address):
        try:
            op, state, room_name, payload = TCRProtocol.receive_tcrp_message(client_socket)

            if state != STATE_REQUEST:
                print(f"無効な状態コード: {state}")
                return

            if op == OP_CREATE_ROOM:
                success, token = self.create_room(room_name, payload)
                print(f"{'作成成功' if success else '既に存在'}: ルーム '{room_name}'")
            elif op == OP_JOIN_ROOM:
                success, token = self.join_room(room_name, payload)
                print(f"{'参加成功' if success else '参加失敗'}: ルーム '{room_name}' に {payload} 入室")
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
            print(f"[TCP] 切断: {address}")

    def stop(self):
        self.running = False
        if self.socket:
            self.socket.close()
            self.socket = None
            print("ソケット閉じた")

    def generate_token(self):
        return secrets.token_hex(16)

    def room_exists(self, room_name):
        return room_name in self.rooms

    def create_room(self, room_name, username):
        if self.room_exists(room_name):
            return False, None

        token = self.generate_token()
        self.rooms[room_name] = {
            'host': username,
            'members': [username],
            'tokens': [token]
        }
        self.tokens[token] = (room_name, username, True, None)
        self.room_tokens[room_name] = [token]
        self.user_tokens[(room_name, username)] = token

        return True, token

    def join_room(self, room_name, username):
        if not self.room_exists(room_name):
            return False, None

        if (room_name, username) in self.user_tokens:
            return True, self.user_tokens[(room_name, username)]

        token = self.room_tokens[room_name][0]
        self.rooms[room_name]['members'].append(username)
        self.tokens[token] = (room_name, username, False, None)
        self.user_tokens[(room_name, username)] = token

        return True, token