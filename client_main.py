from client.tcp_client import TCPClient
from client.udp_chat_client import UDPChatClient

OP_CREATE_ROOM = 1
OP_JOIN_ROOM = 2

def prompt_valid_input(prompt_text):
    while True:
        value = input(prompt_text).strip()
        if not value or value.isspace():
            print("空文字や空白のみは許可されていません。もう一度入力してください。")
            continue
        return value
    
def main():
    server_ip = "127.0.0.1"
    tcp_port = 9090
    udp_port = 0  # OSに任せる
    try:
        while True:
            operation = input("操作（1: 作成, 2: 参加）: ").strip()
            normalized = operation.translate(str.maketrans("１２", "12"))  # 全角 → 半角に変換
            if normalized in ("1", "2"):
                op_code = OP_CREATE_ROOM if normalized == "1" else OP_JOIN_ROOM
                break
            else:
                print("「1」または「2」を選んでください")
            
        room_name = prompt_valid_input("ルーム名: ")
        username = prompt_valid_input("ユーザー名: ")

        tcp_client = TCPClient(server_ip, tcp_port)
        tcp_client.connect()

        try:
            token = tcp_client.get_token(room_name, username, op_code)
        except Exception as e:
            print(f"[エラー] トークン取得失敗: {e}")
            return

        print(f"[TCP] トークン取得成功: {token}")

        client = UDPChatClient(
            username=username,
            server_ip=server_ip,
            room_name=room_name,
            token=token,
            local_port=udp_port
        )
        client.start()
        
    except KeyboardInterrupt:
        print("\n終了します...")

if __name__ == "__main__":
    main()