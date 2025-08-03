from tcp_client import TCP_Create_Join_Client
from udp_client import UDP_Chat_Client

class Client:
    def __init__(self, host, tcp_port, udp_port):
        self.host = host
        self.tcp_client = TCP_Create_Join_Client(host, tcp_port)
        self.udp_client = UDP_Chat_Client(host, udp_port)

    def run(self):
        try:
            while True:
                print("\n=== クライアント ===")
                print("1. ルーム作成")
                print("2. ルーム参加")
                print("3. 終了")
                
                choice = input("選択してください (1-3): ").strip()
                
                if choice == '3':
                    print("終了します。")
                    break
                elif choice in ['1', '2']:
                    if self._handle_room_operation(choice):
                        break
                else:
                    print("無効な選択肢です")
        except KeyboardInterrupt:
            print("\nユーザーが中断しました。")
        finally:
            print("クライアント終了")

    def _handle_room_operation(self, choice):
        room_name = input("ルーム名を入力してください: ").strip()
        username = input("ユーザー名を入力してください: ").strip()
        
        if not (room_name and username):
            print("ルーム名とユーザー名を入力してください")
            return False

        if not self.tcp_client.connect():
            return False

        try:
            success = False
            if choice == '1':
                print(f"ルーム '{room_name}' を作成中...")
                success = self.tcp_client.create_room(room_name, username)
            elif choice == '2':
                print(f"ルーム '{room_name}' に参加中...")
                success = self.tcp_client.join_room(room_name, username)

            if success:
                token = self.tcp_client.get_token()
                print(f"TCP認証成功。トークン取得完了")
                
                self.tcp_client.disconnect()
                
                print(f"\n--- UDP参加フェーズ ---")
                join_success = False
                if choice == '1':
                    join_success = self.udp_client.create_and_enter_room(room_name, username, token)
                elif choice == '2':
                    join_success = self.udp_client.join_existing_room(room_name, username, token)
                
                if join_success:
                    print(f"\nすべての処理が完了しました")
                    print(f"   ルーム: {room_name}")
                    print(f"   ユーザー: {username}")
                    if choice == '1':
                        print(f"   状態: ルーム作成者として入室完了")
                    else:
                        print(f"   状態: ルーム参加完了")
                    return True
                else:
                    if choice == '1':
                        print("ルーム作成者入室に失敗しました")
                    else:
                        print("ルーム参加に失敗しました")
                    return False
            else:
                print("ルーム操作に失敗しました")
                return False
                
        finally:
            self.tcp_client.disconnect()

def main():
    server_address = input("サーバーアドレス名 (デフォルト: localhost): ").strip() or 'localhost'
    
    tcp_port = input("TCPポート番号 (デフォルト: 9090): ").strip()
    tcp_port = int(tcp_port) if tcp_port else 9090
    
    udp_port = input("UDPポート番号 (デフォルト: 9091): ").strip()
    udp_port = int(udp_port) if udp_port else 9091

    try:
        client = Client(server_address, tcp_port, udp_port)
        client.run()
    except KeyboardInterrupt:
        print("\nユーザーが中断しました")
    except Exception as e:
        print(f"エラー発生: {e}")

if __name__ == "__main__":
    main()