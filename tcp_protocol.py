import struct

# 操作コード
OP_CREATE_ROOM = 1  # ルーム作成
OP_JOIN_ROOM = 2    # ルーム参加

# 状態コード
STATE_REQUEST = 0     # リクエスト
STATE_COMPLIANCE = 1  # 準拠
STATE_COMPLETE = 2    # 完了
STATE_ERROR = 9       # エラー

def encode_tcrp_header(room_name_size, operation, state, operation_payload_size):
    """
    TCRPプロトコルヘッダーを作成する関数
    
    引数:
        room_name_size: ルーム名のサイズ（1バイト）
        operation: 操作コード（1バイト）
        state: 状態コード（1バイト）
        operation_payload_size: 操作ペイロードのサイズ（29バイト）
    
    戻り値:
        bytes: 32バイトのTCRPヘッダー
    """
    if room_name_size > 2**8 - 1:
        raise ValueError(f"ルーム名サイズが制限を超えています: {room_name_size} > {2**8-1}")
    
    if operation_payload_size > 2**232 - 1:
        raise ValueError(f"ペイロードサイズが制限を超えています: {operation_payload_size} > {2**232-1}")
    
    header = room_name_size.to_bytes(1, "big") + operation.to_bytes(1, "big") + state.to_bytes(1, "big")
    header += operation_payload_size.to_bytes(29, "big")
    
    return header

def decode_tcrp_header(header_bytes):
    """
    TCRPヘッダーをデコードする関数
    
    引数:
        header_bytes: 32バイトのヘッダーデータ
    
    戻り値:
        tuple: (room_name_size, operation, state, operation_payload_size)
    """
    if len(header_bytes) != 32:
        raise ValueError(f"ヘッダーサイズが正しくありません: {len(header_bytes)} != 32")
    
    room_name_size, operation, state = struct.unpack('!BBB', header_bytes[:3])
    operation_payload_size = int.from_bytes(header_bytes[3:32], byteorder='big')
    
    return room_name_size, operation, state, operation_payload_size
