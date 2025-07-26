import socket

import tcp_protocol

class Client:
    def __init__(self):
        self.socket = None
        self.token = None
    
    def connect(self, host='localhost', port=9090):
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.connect((host, port))
            print(f"サーバー {host}:{port} に接続しました")
            return True
        except Exception as e:
            print(f"接続エラー: {e}")
            return False
    
    def send_request(self, room_name, operation, username):
        try:
            room_name_bytes = room_name.encode('utf-8')
            username_bytes = username.encode('utf-8')
            
            header = tcp_protocol.encode_tcrp_header(
                len(room_name_bytes), 
                int(operation),
                int(tcp_protocol.STATE_REQUEST),
                len(username_bytes)
            )
            packet = header + room_name_bytes + username_bytes
            
            self.socket.send(packet)
            if int(operation) == tcp_protocol.OP_CREATE_ROOM:
                print(f"リクエスト送信: 作成したいルーム名={room_name}, 操作コード={operation}, 状態コード={tcp_protocol.STATE_REQUEST}, ユーザー名={username}")
            elif int(operation) == tcp_protocol.OP_JOIN_ROOM:
                print(f"リクエスト送信: 参加したいルーム名={room_name}, 操作コード={operation}, 状態コード={tcp_protocol.STATE_REQUEST}, ユーザー名={username}")
        except Exception as e:
            print(f"送信エラー: {e}")
            return False
        return True
    
    def receive_response(self):
        """レスポンスを受信（COMPLIANCE + COMPLETE の両方）"""
        try:
            # 1. COMPLIANCE レスポンスを受信
            if not self._receive_single_response():
                return False
            # 2. COMPLETE レスポンスを受信
            if not self._receive_single_response():
                return False
                
            return True
        except Exception as e:
            print(f"レスポンス受信エラー: {e}")
            return False
    
    def _receive_single_response(self):
        """単一のレスポンスを受信"""
        try:
            header_data = self.socket.recv(32)
            if len(header_data) != 32:
                print("ヘッダー受信エラー")
                return False
            
            room_name_size, operation, state, payload_size = tcp_protocol.decode_tcrp_header(header_data)
            
            body_data = self.socket.recv(room_name_size + payload_size)
            if len(body_data) != room_name_size + payload_size:
                print("ボディ受信エラー")
                return False
            
            room_name = body_data[:room_name_size].decode('utf-8')
            payload = body_data[room_name_size:].decode('utf-8') if payload_size > 0 else ""
            
            if operation == tcp_protocol.OP_CREATE_ROOM:
                if state == tcp_protocol.STATE_COMPLIANCE:
                    print(f"レスポンス受信: 作成リクエストを送ったルーム={room_name}, 操作コード={operation}, 状態コード={state}, ステータス={payload}")
                elif state == tcp_protocol.STATE_COMPLETE:
                    print(f"レスポンス受信: 作成リクエストを送ったルーム={room_name}, 操作コード={operation}, 状態コード={state}, トークン={payload}")
            elif operation == tcp_protocol.OP_JOIN_ROOM:
                if state == tcp_protocol.STATE_COMPLIANCE:
                    print(f"レスポンス受信: 参加リクエストを送ったルーム={room_name}, 操作コード={operation}, 状態コード={state}, ステータス={payload}")
                elif state == tcp_protocol.STATE_COMPLETE:
                    print(f"レスポンス受信: 参加リクエストを送ったルームのトークン={payload}, 操作コード={operation}, 状態コード={state}, ルーム名={room_name}")

            if state == tcp_protocol.STATE_COMPLIANCE:
                status_code = int(payload)
                if status_code == 1:
                    print("サーバー準拠: OK")
                    return True
                else:
                    print("サーバー準拠: エラー")
                    return False
            
            elif state == tcp_protocol.STATE_COMPLETE:
                token = payload
                if operation == tcp_protocol.OP_CREATE_ROOM:
                    print(f"サーバー完了: 新しいルームトークン受信 = {token}")
                elif operation == tcp_protocol.OP_JOIN_ROOM:
                    print(f"サーバー完了: 既存ルームトークン受信 = {token}")
                self.token = token
                return True
            
        except Exception as e:
            print(f"受信エラー: {e}")
            return False
    
    def disconnect(self):
        if self.socket:
            try:
                self.socket.close()
                print("サーバーとの接続を切断しました")
            except Exception as e:
                print(f"切断エラー: {e}")
            finally:
                self.socket = None
                self.token = None
        else:
            print("接続されていません")

def main():
    client = Client()
    
    server_address = input("サーバーアドレスを入力してください (デフォルト: localhost): ").strip()
    if not server_address:
        server_address = 'localhost'
    
    if not client.connect(server_address, 9090):
        return
    
    try:
        while True:
            print("\n=== クライアント ===")
            print("1. ルーム作成")
            print("2. ルーム参加")
            print("3. 終了")
            
            choice = input("選択してください (1-3): ").strip()
            
            if choice == '1':
                room_name = input("ルーム名を入力してください: ").strip()
                username = input("ユーザー名を入力してください: ").strip()
                if room_name and username:
                    if client.send_request(room_name, tcp_protocol.OP_CREATE_ROOM, username):
                        client.receive_response()
                else:
                    print("ルーム名とユーザー名を入力してください")
                    
            elif choice == '2':
                room_name = input("参加するルーム名を入力してください: ").strip()
                username = input("ユーザー名を入力してください: ").strip()
                if room_name and username:
                    if client.send_request(room_name, tcp_protocol.OP_JOIN_ROOM, username):
                        client.receive_response()
                else:
                    print("ルーム名とユーザー名を入力してください")
                    
            elif choice == '3':
                break
                
            else:
                print("1-3の数字を入力してください")
    
    except KeyboardInterrupt:
        print("\n終了します...")
    
    finally:
        client.disconnect()

if __name__ == "__main__":
    main()
