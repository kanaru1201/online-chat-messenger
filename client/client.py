import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from tcp_client import TCP_Create_Join_Client
from udp_client import UDP_Chat_Client

def prompt_valid_input(prompt_text):
    while True:
        value = input(prompt_text).strip()
        if not value or value.isspace():
            print("空文字や空白のみは許可されていません。もう一度入力してください。")
            continue
        return value

class Client:
    def __init__(self, server_ip, tcp_port, udp_port):
        self.server_ip = server_ip
        self.tcp_port = tcp_port
        self.udp_port = udp_port
        self.tcp_client = TCP_Create_Join_Client(server_ip, tcp_port)

    def run(self):
        try:
            while True:
                print("\n=== クライアント操作メニュー ===")
                print("1. ルーム作成")
                print("2. ルーム参加")
                print("3. 終了")

                choice = input("選択してください (1-3): ").strip().translate(str.maketrans("１２３", "123"))

                if choice == '3':
                    print("終了します。")
                    break
                elif choice in ['1', '2']:
                    if self._handle_room_operation(choice):
                        break
                else:
                    print("「1」、「2」、または「3」を選んでください")
        except KeyboardInterrupt:
            print("\n終了します...")
        finally:
            print("クライアント終了")

    def _handle_room_operation(self, choice):
        room_name = prompt_valid_input("ルーム名を入力してください: ")
        username = prompt_valid_input("ユーザー名を入力してください: ")

        print(f"\n--- TCP接続フェーズ ---")
        if not self.tcp_client.connect():
            print("[エラー] TCP接続失敗")
            return False

        success = False
        if choice == '1':
            print(f"ルーム'{room_name}'を作成中...")
            success = self.tcp_client.create_room(room_name, username)
        elif choice == '2':
            print(f"ルーム'{room_name}'に参加中...")
            success = self.tcp_client.join_room(room_name, username)

        if not success:
            print("[エラー] トークン取得失敗")
            self.tcp_client.disconnect()
            return False

        token = self.tcp_client.get_token()
        print("トークン取得成功")
        self.tcp_client.disconnect()
        print("TCP接続を切断しました")

        print(f"\n--- UDP接続フェーズ ---")
        print(f"ルーム: {room_name}")
        print(f"ユーザー: {username}")
        print(f"状態: {'ルーム作成者として入室' if choice == '1' else 'ルームに参加'}")

        udp_client = UDP_Chat_Client(
            username=username,
            server_ip=self.server_ip,
            server_port=self.udp_port,
            room_name=room_name,
            token=token
        )
        udp_client.start()

        return True

def main():
    try:
        server_ip = input("サーバーアドレス (デフォルト: 127.0.0.1): ").strip() or "127.0.0.1"

        tcp_port_input = input("TCPポート番号 (デフォルト: 9090): ").strip()
        tcp_port = int(tcp_port_input) if tcp_port_input else 9090

        udp_port_input = input("UDPポート番号 (デフォルト: 9091): ").strip()
        udp_port = int(udp_port_input) if udp_port_input else 9091

        client = Client(server_ip, tcp_port, udp_port)
        client.run()

    except ValueError:
        print("[エラー] ポート番号は数値で入力してください")
    except KeyboardInterrupt:
        print("\n終了します...")
    except Exception as e:
        print(f"[エラー] 予期しないエラーが発生しました: {e}")

if __name__ == "__main__":
    main()