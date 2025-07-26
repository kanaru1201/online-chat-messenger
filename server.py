import socket
import tcp_protocol
import secrets

class Server:
    def __init__(self, host='localhost', port=9090):
        self.host = host
        self.port = port
        self.rooms = {}  # {room_name: {'host': username, 'members': [usernames]}}
        self.tokens = {}  # {token: (room_name, username, is_host)}
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
                    # 1. COMPLIANCE応答を送信
                    self.send_compliance_response(client_socket, room_name, operation)
                    # 2. COMPLETE応答を送信
                    self.send_complete_response(client_socket, room_name, operation)
                
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
            
        except Exception as e:
            print(f"COMPLIANCE応答送信エラー: {e}")
    
    def send_complete_response(self, client_socket, room_name, operation):
        """COMPLETE応答を送信"""
        try:
            room_name_bytes = room_name.encode('utf-8')
            token = self.generate_token()
            token_bytes = token.encode('utf-8')

            header = tcp_protocol.encode_tcrp_header(
                len(room_name_bytes), 
                int(operation),
                int(tcp_protocol.STATE_COMPLETE),
                len(token_bytes)
            )
            packet = header + room_name_bytes + token_bytes
            client_socket.send(packet)
            print(f"COMPLETE応答送信: トークン={token}")
            
        except Exception as e:
            print(f"COMPLETE応答送信エラー: {e}")
    
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

if __name__ == "__main__":
    server = Server()
    server.start()
