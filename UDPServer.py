import socket
from state import rooms, tokens

# TODO:後ほど改めて実装
class UDPServer:
    def __init__(self, host='0.0.0.0', port=9999):
        self.host = host
        self.port = port
        self.clients = {}  # {room_name: {username: (ip, port)}}
    
    def start(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.bind((self.host, self.port))
        print(f"[UDP] サーバ起動: {self.host}:{self.port}")
        
        while True:
            try:
                data, addr = sock.recvfrom(4096)
                # 必要に応じて parse & dispatch
                self.handle_message(data, addr, sock)
            except Exception as e:
                print(f"[UDP受信エラー] {e}")
    
    def handle_message(self, data, addr, sock):
        try:
            room, token, message = self.parse_packet(data)
            if not self.verify_token(room, token):
                print("[UDP] 不正なトークン")
                return
            
            username = self.get_username_from_token(token)
            print(f"[UDP] {username}@{room}: {message}")

            # ルーム内の他の参加者へ転送
            for user, user_addr in self.clients[room].items():
                if user_addr != addr:
                    sock.sendto(f"{username}: {message}".encode('utf-8'), user_addr)
        
        except Exception as e:
            print(f"[UDP処理エラー] {e}")

    def register_client(self, room, username, addr):
        if room not in self.clients:
            self.clients[room] = {}
        self.clients[room][username] = addr

    def parse_packet(self, data):
        """例: room|token|message の形式を想定"""
        decoded = data.decode('utf-8')
        parts = decoded.split('|', 2)
        return parts[0], parts[1], parts[2]

    def verify_token(self, room, token):
        # TCP側の token 情報と連携する必要あり（共有状態 or シングルトンなどで）
        return token in tokens and tokens[token][0] == room
        # return True  # 仮実装

    def get_username_from_token(self, token):
        # token から username を復元（TCP側で保存した情報を使う）
        return "user"  # 仮実装
