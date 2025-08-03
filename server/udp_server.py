import socket

class UDP_Chat_Server:
    def __init__(self, host, udp_port, room_manager):
        self.host = host
        self.udp_port = udp_port
        self.room_manager = room_manager
        self.udp_sock = None
        self.running = False
    
    def bind(self):
        try:
            self.udp_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.udp_sock.bind((self.host, self.udp_port))
            self.running = True
            print(f"UDPサーバー開始: {self.host}:{self.udp_port}")
            
            while self.running:
                try:
                    data, client_addr = self.udp_sock.recvfrom(4096)
                    message = data.decode('utf-8')
                    self._handle_udp_message(message, client_addr)
                except Exception as e:
                    if self.running:
                        print(f"UDP処理エラー: {e}")
                        
        except Exception as e:
            print(f"UDPサーバー起動エラー: {e}")
    
    def _handle_udp_message(self, message, client_addr):
        try:
            parts = message.split('|', 3)
            if len(parts) != 4:
                return
                
            room_name, token, username, content = parts
            
            is_valid, reason = self.room_manager.validate_token_and_address(
                token, room_name
            )
            
            if not is_valid:
                print(f"無効なUDPメッセージ: {reason}")
                return
            
            if content == "__JOIN__":
                print(f"[UDP] 接続: {username} がルーム '{room_name}' に参加")
                
                confirmation = f"ルーム '{room_name}' への参加が完了しました。"
                self.udp_sock.sendto(confirmation.encode('utf-8'), client_addr)
                print(f"参加確認メッセージ送信: {client_addr}")
                
        except Exception as e:
            print(f"UDPメッセージ処理エラー: {e}")
    
    def stop(self):
        self.running = False
        if self.udp_sock:
            self.udp_sock.close()
            self.udp_sock = None
            print("UDPサーバー停止")