import socket
import tcp_protocol
import secrets
from state import rooms, tokens

class TCPServer:
    def __init__(self, host='localhost', port=9090):
        self.host = host
        self.port = port
        # self.rooms = {}  # {room_name: {'host': username, 'members': [usernames]}}
        # self.tokens = {}  # {token: (room_name, username, is_host)}
        self.room_tokens = {}  # {room_name: host_token} - ルーム名とホストトークンのマッピング
    
    def generate_token(self):
        return secrets.token_hex(16)
    
    def handle_client(self, client_socket, address):
        print(f"クライアント {address} が接続しました")
        try:
            while True:
                header_data = client_socket.recv(32)
                if not header_data:
                    break
                
                if len(header_data) != 32:
                    print(f"不正なヘッダーサイズ: {len(header_data)}")
                    break
                
                room_name_size, operation, state, payload_size = tcp_protocol.decode_tcrp_header(header_data)
                
                body_data = client_socket.recv(room_name_size + payload_size)
                if len(body_data) != room_name_size + payload_size:
                    print("ボディサイズが一致しません")
                    break
                
                room_name = body_data[:room_name_size].decode('utf-8')
                payload = body_data[room_name_size:].decode('utf-8') if payload_size > 0 else ""
                
                if operation == tcp_protocol.OP_CREATE_ROOM:
                    print(f"受信: 作成したいルーム名={room_name}, 操作コード={operation}, 状態コード={state}, ユーザー名={payload}")
                elif operation == tcp_protocol.OP_JOIN_ROOM:
                    print(f"受信: 参加したいルーム名={room_name}, 操作コード={operation}, 状態コード={state}, ユーザー名={payload}")

                # リクエスト処理（STATE_REQUESTの場合のみ）
                if state == tcp_protocol.STATE_REQUEST:
                    if operation == tcp_protocol.OP_CREATE_ROOM:
                        # 既に存在するルームがないかチェック
                        if room_name in rooms:
                            print(f"[ERROR] ルーム {room_name} は既に存在しています")
                            self.send_error_response(client_socket, room_name, operation, "このルームは既に存在しています")
                            break
                    elif operation == tcp_protocol.OP_JOIN_ROOM:
                        # 存在しないルームかどうかチェック
                        if room_name not in rooms:
                            print(f"[ERROR] ルーム {room_name} は存在しません")
                            self.send_error_response(client_socket, room_name, operation, "このルームは存在しません")
                            break

                    # 1. COMPLIANCE応答を送信
                    isCompliance = self.send_compliance_response(client_socket, room_name, operation)
                    if not isCompliance:
                        print(f"COMPLIANCE応答送信に失敗しました")
                        break
                    # 2. COMPLETE応答を送信
                    isComplete = self.send_complete_response(client_socket, room_name, operation, payload)
                    if not isComplete:
                        print(f"COMPLETE応答送信に失敗しました")
                        break
                    print("すべての応答を送信したので接続を終了します")
                    break  # 明示的に終了させる
                
        except Exception as e:
            print(f"エラー: {e}")
        finally:
            client_socket.close()
            print(f"クライアント {address} が切断しました")
    
    def send_compliance_response(self, client_socket, room_name, operation):
        """COMPLIANCE応答を送信"""
        try:
            room_name_bytes = room_name.encode('utf-8')
            status_code = 1
            status_bytes = str(status_code).encode('utf-8')

            header = tcp_protocol.encode_tcrp_header(
                len(room_name_bytes), 
                int(operation),
                int(tcp_protocol.STATE_COMPLIANCE),
                len(status_bytes)
            )
            packet = header + room_name_bytes + status_bytes
            client_socket.send(packet)
            print(f"COMPLIANCE応答送信: ステータス={status_code}")
            return True
            
        except Exception as e:
            print(f"COMPLIANCE応答送信エラー: {e}")
            return False
    
    def send_complete_response(self, client_socket, room_name, operation, username):
        """COMPLETE応答を送信"""
        try:
            room_name_bytes = room_name.encode('utf-8')
            token = self.generate_token()
            token_bytes = token.encode('utf-8')

            # ルームを作成する場合はそのユーザーをホストとみなす
            is_host = (operation == tcp_protocol.OP_CREATE_ROOM)

            # ホストの場合はhostとmembers双方をクラス変数に格納する
            if is_host:
                rooms[room_name] = {
                    'host': username,
                    'members': [username]
                }
            # メンバーの場合はmembersのみをクラス変数に格納する
            else:
                rooms[room_name]['members'].append(username)

            # トークン情報を保存する
            tokens[token] = (room_name, username, is_host)

            header = tcp_protocol.encode_tcrp_header(
                len(room_name_bytes), 
                int(operation),
                int(tcp_protocol.STATE_COMPLETE),
                len(token_bytes)
            )
            packet = header + room_name_bytes + token_bytes
            client_socket.send(packet)
            print(f"COMPLETE応答送信: トークン={token}")
            return True
            
        except Exception as e:
            print(f"COMPLETE応答送信エラー: {e}")
            return False

    def send_error_response(self, client_socket, room_name, operation, message):
        """エラー応答を送信（STATE=ERRORなど任意の番号）"""
        try:
            room_name_bytes = room_name.encode('utf-8')
            message_bytes = message.encode('utf-8')

            header = tcp_protocol.encode_tcrp_header(
                len(room_name_bytes),
                int(operation),
                tcp_protocol.STATE_ERROR, # エラー用の状態コード
                len(message_bytes)
            )
            packet = header + room_name_bytes + message_bytes
            client_socket.send(packet)
            print(f"[エラー応答] {message}")
        except Exception as e:
            print(f"エラー応答送信失敗: {e}")

    
    def start(self):
        """サーバー開始"""
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        
        try:
            server_socket.bind((self.host, self.port))
            server_socket.listen(1)
            print(f"サーバーが {self.host}:{self.port} で開始されました")
            print("クライアントからの接続を待機中...")
            
            while True:
                try:
                    client_socket, address = server_socket.accept()
                    self.handle_client(client_socket, address)
                except socket.error as e:
                    print(f"接続受け入れエラー: {e}")
                    break    
        except KeyboardInterrupt:
            print("\nサーバーを停止します...")
        except Exception as e:
            print(f"サーバーエラー: {e}")
        finally:
            server_socket.close()
            print("サーバーが停止しました")
