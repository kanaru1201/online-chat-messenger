# Online chat messenger

TCPでルーム作成、参加を行い、UDPでチャットメッセージを中継するCUIチャットアプリケーションです。

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python Version](https://img.shields.io/badge/python-3.x-blue.svg)](https://www.python.org/)

## デモ

[![Online-Chat-Messenger](https://img.youtube.com/vi/Qref4Lx3Rug/0.jpg)](https://youtu.be/Qref4Lx3Rug)


## 主な機能

*   **ハイブリッドサーバー**: TCPサーバーでルーム作成・参加といった信頼性が必要な処理を担い、UDPサーバーでリアルタイム性の高いチャットメッセージの中継を行います。
*   **トークンベースの認証**: ルームの作成・参加時にユニークなトークンを発行し、以降の通信でそのトークンを利用してユーザーを識別します。
*   **動的なアドレス登録**: クライアントは起動時にUDPソケットのアドレス（IP、ポート）をサーバーに登録します。
*   **ホストによるルーム管理**: ルームを作成したホストがチャットを退出すると、サーバーは該当のルームと関連するすべての情報を自動的に削除します。
*   **複数クライアント対応**: マルチスレッドを利用して、複数のクライアント接続を同時に処理します。
 
## インストール方法

### 前提条件
*   Python 3.x

### 手順
1.  このリポジトリをクローンします。
    ```bash
    git clone https://github.com/kanaru1201/online-chat-messenger.git
    cd online-chat-messenger
    ```
2.  このプロジェクトはPythonの標準ライブラリのみで動作するため、追加のパッケージインストールの必要はありません。

## 使い方

### 1. サーバーを起動する

まず、サーバーを起動してクライアントからの接続を待ち受けます。

```bash
python -m server.main
```

成功すると、以下のようなログが表示されます。
```
[Main] TCP/UDPサーバー両方起動完了
TCPサーバー開始: localhost:9090
[待機中] UDPチャットサーバーが起動しました。メッセージを待っています...
```

### 2. クライアントを起動してルームを作成する（1人目）

新しいターミナルを開き、クライアントを起動します。

```bash
python -m client.client_main
```

プロンプトに従い、操作 `1` を選択してルーム名とユーザー名を入力します。

```
操作（1: 作成, 2: 参加）: 1
ルーム名: room1
ユーザー名: Kanaru
```

成功するとトークンが発行され、チャット入力待機状態になります。

```
[TCP] トークン取得成功: token_a1b2c3d4e5f6g7h8
...
=== チャットを開始します。Ctrl+Cで終了 ===
>
```

### 3. 別のクライアントでルームに参加する（2人目以降）

さらに別のターミナルを開き、同様にクライアントを起動します。

```bash
python -m client.client_main
```

今度は操作 `2` を選択し、先ほど作成したルーム名と、あなたのユーザー名を入力します。

```
操作（1: 作成, 2: 参加）: 2
ルーム名: room1
ユーザー名: Hiroki
```

これで、同じルームに参加しているメンバー間でチャットができます。

```
> こんにちは！

Kanaru: こんにちは！
> 
```

### 4. チャットを終了する

チャットを終了するには、クライアントのターミナルで `Ctrl+C` を押してください。サーバーに退出が通知されます。

## プロジェクトのディレクトリ構成

```
.
├── server/                 # サーバーサイド関連のコード
│   ├── main.py             # サーバーサイドのメインエントリポイント（TCP/UDPサーバー起動）
│   ├── udp_chat_server.py  # UDPサーバーの実装（チャットメッセージ中継、クライアントアドレス登録）
│   ├── room_manager.json   # サーバーがルームとトークンの情報を保存するJSONファイル（実行時に生成）
|   └── tcp_server.py       # TCPサーバーの実装（ルーム管理、トークン発行）
└── client/                 # クライアントサイド関連のコード
|   ├── client_main.py      # クライアントサイドのメインエントリポイント
|   ├── tcp_client.py       # TCPクライアントの実装（ルーム作成・参加、トークン取得）
|   └── udp_chat_client.py  # UDPチャットクライアントの実装（メッセージ送受信、アドレス登録）
└── protocol/               # 通信プロトコル関連
    ├── tcrp.py             # TCP通信用のプロトコル定義（TCRProtocol）
    └── udp_protocol.py     # UDP通信用のプロトコル定義
```


---


## チーム

このプロジェクトは以下のチームメンバーによって開発されました。

*   **[Kanaru]** - [GitHubプロフィールへのリンク](https://github.com/kanaru1201)
*   **[Matsufuji]** - [GitHubプロフィールへのリンク](https://github.com/matsufuji06)
*   **[Kevin]** - [GitHubプロフィールへのリンク](https://github.com/KevinRyouInoue)
*   **[Hiroki]** - [GitHubプロフィールへのリンク](https://github.com/hiroki-jandararin)

## コントリビューション

プルリクエストの手順は以下の通りです。
1.  このリポジトリをフォークします。
2.  新しいブランチを作成します (`git checkout -b feature/new-feature`)。
3.  変更をコミットします (`git commit -am 'Add some feature'`)。
4.  ブランチをプッシュします (`git push origin feature/new-feature`)。
5.  プルリクエストを作成します。








