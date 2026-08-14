# Changelog

## 0.3.0-rc3 - 2026-08-14

- MiniMax H3公式ライセンス全文とSHA-256を配布物へ同梱
- H3の7項目同意、条件版、同意履歴、再同意判定を実装
- 日本RunPodリージョン固定、環境変数による地域バイパスを削除
- H3プロンプトのサーバー側安全検査を受付時と実行直前に追加
- 通報窓口と調査・配布停止方針をUI・文書へ追加
- H3出力ファイル名とHTTPヘッダーにAI生成識別を追加

## 0.3.0-rc2 - 2026-08-14

- GHCR実buildで判明した未公開のローカルComfyUI commit参照を修正
- ComfyUI公式リポジトリの公開commit `7fe8a6138504f90ff7be82f3babf416da32876b1`へ固定

## 0.3.0-rc1 - 2026-08-14

- MiniMax H3のText to Video / Image to Video / First-Last-Frame to Videoを追加
- H3公式4ファイル約53.9GBをUIから取得し、SHA-256確認・中断・再開に対応
- Krea2 Turbo＋H3のおすすめ構成と、全モデル構成を追加
- H3ライセンス同意、RunPodリージョン制限、MiniMax表示、AI生成表示注意を追加
- PNG / JPEG / WebPのフレーム入力、25MB上限、ランダム保存名、処理後削除を実装
- 画像とMP4 / WebMの共通キュー・完成ギャラリーへ拡張
- RunPod一時ディスク既定を150GB、ComfyUIをH3確認済みcommitへ更新

## 0.2.0-rc1 - 2026-08-14

- スマホUIからTurbo / Raw / 両方を選んで公式モデルを取得できるモデル管理を追加
- 容量、ファイル、総合進捗、SHA-256確認、中断、途中再開を画面表示
- UIをモデル未導入のまま先に起動し、初回の長いダウンロード中も状態確認可能に変更
- Network Volumeの継続保存と、永続Volumeなしの都度利用を画面で区別
- 永続VolumeなしではPod完全削除を標準終了とし、継続ストレージ料金を残さない設計へ変更
- ACS ImageGen Lite License 1.0とGHCR公開ワークフローを追加

## 0.1.0-rc1 - 2026-08-14

- 個人用環境から独立したKrea2 Turbo / Raw画像生成UIを新規作成
- 任意LoRA、キュー、ギャラリー、キャンセルを実装
- 初回パスワード、PBKDF2-SHA256、Secure Cookie、同一生成元チェック、ログイン試行制限を実装
- RunPod停止・完全削除とアイドル監視を実装
- 公式モデル取得とSHA-256検証を実装
- Docker / RunPod設定、導入・利用・ACS / Locany下書きを追加
- 自動テストとデスクトップ・スマホ幅の画面検証を実施
