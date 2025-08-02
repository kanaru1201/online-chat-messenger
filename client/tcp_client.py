import json
import os
import socket
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from server.protocol.tcrp import TCRProtocol, OP_CREATE_ROOM, OP_JOIN_ROOM, STATE_REQUEST, STATE_COMPLIANCE, STATE_COMPLETE

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
            
    def get_token(self, room_name, username, op_code):
        self.connect()
        TCRProtocol.send_tcrp_message(
            self.client_socket, room_name, op_code, STATE_REQUEST, username
        )

        op_c, state_c, room_c, payload_c = TCRProtocol.receive_tcrp_message(self.client_socket)
        if state_c != STATE_COMPLIANCE:
            raise ValueError("準拠応答エラー")

        compliance_result = json.loads(payload_c)
        if not compliance_result.get("success", False):
            raise ValueError("サーバーによる操作拒否")

        op_f, state_f, room_f, payload_f = TCRProtocol.receive_tcrp_message(self.client_socket)
        if state_f != STATE_COMPLETE:
            raise ValueError("完了応答が不正")

        complete_result = json.loads(payload_f)
        token = complete_result.get("token")
        return token