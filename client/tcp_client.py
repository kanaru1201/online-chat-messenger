import json
import os
import socket
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from tcrp import TCRProtocol, OP_CREATE_ROOM, OP_JOIN_ROOM, STATE_REQUEST, STATE_COMPLIANCE, STATE_COMPLETE

class TCPClient:
    def __init__(self, host='localhost', port=9090):
        self.host = host
        self.port = port
        self.client_socket = None

    def connect(self):
        try:
            self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.client_socket.connect((self.host, self.port))
            print(f"接続成功: {self.host}:{self.port}")
        except Exception as e:
            print(f"サーバーに接続できません: {e}")
            sys.exit(1)

    def run(self):
        try:
            while True:
                print("\n--- メニュー ---")
                print("1. ルーム作成")
                print("2. ルーム参加")
                print("3. 終了")
                choice = input("選択 (1-3): ").strip()

                if choice == '3':
                    print("終了します。")
                    break
                elif choice in ('1', '2'):
                    self.handle_create_or_join(choice)
                else:
                    print("無効な選択肢です")
        finally:
            self.client_socket.close()
            print("クライアント終了")
            sys.exit(0)

    def handle_create_or_join(self, choice):
        op = OP_CREATE_ROOM if choice == '1' else OP_JOIN_ROOM
        room_name = input("ルーム名: ").strip()
        username = input("ユーザー名: ").strip()

        try:
            TCRProtocol.send_tcrp_message(
                self.client_socket, room_name, op, STATE_REQUEST, username
            )

            op_c, state_c, room_c, payload_c = TCRProtocol.receive_tcrp_message(self.client_socket)
            if state_c != STATE_COMPLIANCE:
                print("準拠応答受信エラー")
                return

            compliance_result = json.loads(payload_c)
            if not compliance_result.get("success", False):
                print("操作失敗（サーバー応答）")
                return

            op_f, state_f, room_f, payload_f = TCRProtocol.receive_tcrp_message(self.client_socket)
            if state_f == STATE_COMPLETE:
                complete_result = json.loads(payload_f)
                token = complete_result.get("token")
                print(f"トークン受信: {token}")
                sys.exit(0)
            else:
                print("完了応答が受信できませんでした")

        except Exception as e:
            print(f"処理エラー: {e}")