import socket
import threading

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
            
            elif state == tcp_protocol.STATE_ERROR:
                print(f"[サーバーエラー応答] {payload}")
                return False
            
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

    # TODO:後ほど改めて実装
    def start_udp_chat(self, room_name, username, server_ip, udp_port=9999):
        udp_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        server_addr = (server_ip, udp_port)

        # TODO:後ほど改めて実装
        def receive_messages():
            """メッセージ受信用の内部専用関数"""
            while True:
                try:
                    data, _ = udp_sock.recvfrom(4096)
                    print(f"\n{data.decode('utf-8')}\n> ", end='', flush=True)
                except Exception:
                    break
        
        # TODO:後ほど改めて実装
        def send_messages():
            """メッセージ送信用の内部専用関数"""
            while True:
                msg = input("> ").strip()
                if msg.lower() == "exit":
                    print("チャットを終了します。")
                    udp_sock.close()
                    break
                # 送信フォーマット: room|token|username|message
                packet = f"{room_name}|{self.token}|{username}|{msg}"
                udp_sock.sendto(packet.encode('utf-8'), server_addr)
        
        # チャット参加通知
        join_packet = f"{room_name}|{self.token}|{username}|__JOIN__"
        udp_sock.sendto(join_packet.encode('utf-8'), server_addr)

        print(f"UDPチャットモードに入りました。'exit' と入力で終了します。")
        
        recv_thread = threading.Thread(target=receive_messages, daemon=True)
        recv_thread.start()
        send_messages()

def main():
    client = Client()
    
    server_address = input("サーバーアドレスを入力してください (デフォルト: localhost): ").strip()
    if not server_address:
        server_address = 'localhost'
    try:
        while True:
            print("\n=== クライアント ===")
            print("1. ルーム作成")
            print("2. ルーム参加")
            print("3. 終了")
            
            choice = input("選択してください (1-3): ").strip()
            
            if choice in ['1', '2']:
                room_name = input("ルーム名を入力してください: ").strip()
                username = input("ユーザー名を入力してください: ").strip()
                if not (room_name and username):
                    print("ルーム名とユーザー名を入力してください")
                    continue

                if client.connect(server_address, 9090):
                    operation = tcp_protocol.OP_CREATE_ROOM if choice == '1' else tcp_protocol.OP_JOIN_ROOM
                    if client.send_request(room_name, operation, username):
                        if client.receive_response():
                            client.disconnect()
                            # TCP通信成功→UDPチャット開始
                            client.start_udp_chat(room_name, username, server_address)
                            break  # チャット終了後はプログラム終了
                    else:
                        client.disconnect()
                else:
                    print("サーバーに接続できませんでした")

            elif choice == '3':
                break
            else:
                print("1-3の数字を入力してください")
    except KeyboardInterrupt:
        print("\nクライアントを終了します")

if __name__ == "__main__":
    main()
