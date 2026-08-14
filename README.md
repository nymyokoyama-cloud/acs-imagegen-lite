# ACS ImageGen Lite

RunPod上でKrea2画像生成とMiniMax H3動画生成を、スマホから扱いやすくする配布用Web UIです。個人用環境とは独立し、個人LoRA、生成履歴、学習素材、認証情報、モデル本体は含みません。

## 主な機能

- Krea2 Turbo / RawのText to Image、任意LoRA
- MiniMax H3のText to Video / Image to Video / First-Last-Frame to Video
- H3ネイティブ音声、3〜10秒、16:9 / 9:16 / 1:1
- スマホUIから公式モデルを取得、進捗・中断・再開・SHA-256確認
- 初回パスワード、生成キュー、キャンセル、画像・動画ギャラリー
- RunPod停止・完全削除、アイドル時と最大稼働時間の自動終了

## 初心者向けのおすすめ

UIの「おすすめ：Krea2 Turbo + MiniMax H3」を選ぶと、Krea2画像生成とH3の3種類の動画生成をまとめて準備します。取得量は約72.6GBです。Rawも含める場合は約85.7GBです。

テンプレートの一時ディスク既定は150GBです。モデルはRunPod側へ保存され、スマホやパソコン本体には保存されません。Network Volumeを接続しなければ、Pod完全削除後に継続ストレージ料金は残りません。再利用したい場合だけ150GB以上のNetwork Volumeを`/workspace`へ接続します。

## MiniMax H3の条件

H3には独自ライセンスがあります。Lite版は既定で日本のRunPodリージョンだけを許可し、UIで利用条件への確認が完了するまでH3の取得・生成を拒否します。モデルは同梱せず、公式URLから取得します。

MiniMax H3 is licensed under the MiniMax H3 Community License Agreement, Copyright © 2026 MiniMax. All Rights Reserved.

詳細は[H3利用条件](docs/H3-TERMS.md)と[第三者ライセンス案内](THIRD_PARTY_NOTICES.md)を確認してください。

## パソコンは必要か

RunPodアカウントと支払い設定が済んでいれば、一般利用者のパソコンは必須ではありません。スマホのブラウザだけでPod起動、モデル取得、画像・動画生成、保存、Pod削除まで操作できます。

## 開発

```bash
docker build -t acs-imagegen-lite:0.3.0-rc2 .
docker run --gpus all -p 8080:8080 acs-imagegen-lite:0.3.0-rc2
```

```bash
.venv-test/bin/python -m pytest -q
bash -n scripts/bootstrap.sh scripts/start.sh
```

公開前候補です。GHCR公開、RunPodテンプレート作成、H200実機での3動画モード確認、法務最終確認が一般配布ゲートです。
