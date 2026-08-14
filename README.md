# ACS ImageGen Lite

RunPod上でKrea2画像生成とMiniMax H3動画生成を、スマホから扱いやすくする配布用Web UIです。個人用環境とは独立し、個人LoRA、生成履歴、学習素材、認証情報、モデル本体は含みません。

- [無料スターターパックを入手](https://locany.net/shop/acs-imagegen-lite-starter-pack/)
- [導入手順と実機検証を読む](https://acs-developer.com/acs-imagegen-lite-runpod-krea2-minimax-h3/)
- [RunPod公開テンプレートを開く](https://console.runpod.io/deploy?template=evkauvs9oe)

## 主な機能

- Krea2 Turbo / RawのText to Image、任意LoRA
- Krea 2公式ライセンス・AUP同意、年商条件確認、安全フィルター、人による出力確認
- MiniMax H3のText to Video / Image to Video / First-Last-Frame to Video
- H3ネイティブ音声、3〜10秒、16:9 / 9:16 / 1:1
- H3の公式ライセンス全文同梱、7項目の同意履歴、地域ゲート、安全フィルター、通報導線
- スマホUIから公式モデルをXet高速取得、中断・再開・SHA-256確認
- 初回パスワード、生成キュー、キャンセル、画像・動画ギャラリー
- RunPod停止・完全削除要求、結果表示、アイドル時と最大稼働時間の自動終了試行

## 初心者向けのおすすめ

Krea 2の公式ライセンスとAcceptable Use Policyを確認し、5項目へ同意します。商用利用は、関連会社を含む会社全体の直近12か月売上100万米ドル未満の場合に限られ、以上の場合はKreaのEnterprise Licenseが必要です。その後、UIの「おすすめ：Krea2 Turbo + MiniMax H3」を選ぶと、Krea2画像生成とH3の3種類の動画生成をまとめて準備します。取得量は約72.6GBです。Rawも含める場合は約85.7GBです。

テンプレートの一時ディスク既定は150GBです。モデルはRunPod側へ保存され、スマホやパソコン本体には保存されません。Network Volumeを接続しなければ、Podの完全削除が完了した後は継続ストレージ料金が発生しません。再利用したい場合だけ150GB以上のNetwork Volumeを`/workspace`へ接続します。

## MiniMax H3の条件

H3には独自ライセンスがあります。Lite版は日本のRunPodリージョンだけを許可し、UIで7項目への同意が完了するまでH3の取得・生成をサーバー側で拒否します。同意履歴、プロンプト安全検査、AI生成ファイル名、通報・停止方針も実装しています。モデルは同梱せず、公式URLから取得します。

MiniMax H3 is licensed under the MiniMax H3 Community License Agreement, Copyright © 2026 MiniMax. All Rights Reserved.

Krea 2は[日本語の利用条件](docs/KREA2-TERMS.md)、[公式ライセンスPDF](https://huggingface.co/Comfy-Org/Krea-2/blob/main/LICENSE.pdf)、[公式AUP](https://www.krea.ai/krea-2-use-policy)を確認してください。H3は[H3利用条件](docs/H3-TERMS.md)、[通報・調査・停止方針](docs/H3-ENFORCEMENT.md)、[公式ライセンス同梱版](MINIMAX_H3_LICENSE.txt)、[第三者ライセンス案内](THIRD_PARTY_NOTICES.md)を確認してください。

## パソコンは必要か

RunPodアカウントと支払い設定が済んでいれば、一般利用者のパソコンは必須ではありません。スマホのブラウザだけでPod起動、モデル取得、画像・動画生成、保存、終了操作まで行えます。最後はRunPodコンソールでPodが消えたことを確認します。

## 開発

```bash
docker build -t acs-imagegen-lite:0.3.1 .
docker run --gpus all -p 8080:8080 acs-imagegen-lite:0.3.1
```

```bash
.venv-test/bin/python -m pytest -q
bash -n scripts/bootstrap.sh scripts/start.sh
```

安定版0.3.1です。H200実機でH3の3動画モードを確認し、モデル高速取得、終了結果表示、Krea 2の公式条件ゲートと安全対策を実装しています。実測条件と結果は[検証記録](docs/VALIDATION-2026-08-14.md)を確認してください。
