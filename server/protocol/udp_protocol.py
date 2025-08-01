# パケット構築: [RoomNameLength (1バイト)][TokenLength (1バイト)][RoomName][Token][Message]
def build_udp_payload(room_name: str, token: str, message: str) -> bytes:
    room_bytes = room_name.encode('utf-8')
    token_bytes = token.encode('utf-8')
    message_bytes = message.encode('utf-8')

    if len(room_bytes) > 255 or len(token_bytes) > 255:
        raise ValueError("ルーム名またはトークンが255バイトを超えています。")

    return bytes([len(room_bytes), len(token_bytes)]) + room_bytes + token_bytes + message_bytes

# パケット解析: [RoomNameLength (1バイト)][TokenLength (1バイト)][RoomName][Token][Message]
def parse_udp_payload(data: bytes) -> tuple[str, str, str]:
    if len(data) < 2:
        raise ValueError("パケットが短すぎます")

    room_len = data[0]
    token_len = data[1]
    room_start = 2
    token_start = room_start + room_len
    msg_start = token_start + token_len

    if len(data) < msg_start:
        raise ValueError("ヘッダーが不正です")

    room_name = data[room_start:token_start].decode('utf-8')
    token = data[token_start:msg_start].decode('utf-8')
    message = data[msg_start:].decode('utf-8')
    return room_name, token, message

# メッセージ構築: [UsernameLength (1バイト)][Username][Message]
def build_udp_message(sender: str, message: str) -> bytes:
    sender_bytes = sender.encode('utf-8')
    message_bytes = message.encode('utf-8')
    sender_length = len(sender_bytes)

    if sender_length > 255:
        raise ValueError("ユーザー名が長すぎます（最大255バイト）")

    return bytes([sender_length]) + sender_bytes + message_bytes

# メッセージ解析: [UsernameLength (1バイト)][Username][Message]
def parse_udp_message(data: bytes) -> tuple[str, str]:
    if not data or len(data) < 1:
        return "", ""

    username_len = data[0]
    sender = data[1:1 + username_len].decode("utf-8")
    message = data[1 + username_len:].decode("utf-8")
    return sender, message