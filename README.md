# ACS ImageGen Lite

RunPod上でKrea2の画像生成を使いやすくする、配布用の軽量Web UIです。個人用環境から独立しており、個人LoRA、生成履歴、学習素材、認証情報、モデル本体は含みません。

## 主な機能

- Krea2 Turbo / Krea2 RawのText to Image
- 16:9、9:16、1:1、4:3、3:4
- 任意LoRAのアップロードと強度・トリガーワード指定
- 生成キュー、キャンセル、ギャラリー
- 初回パスワード設定、Cookie認証、同一生成元チェック
- RunPodのGPU停止 / Pod完全削除
- アイドル時と最大稼働時間の自動停止
- スマホUIからの公式モデル初回取得、進捗表示、中断・再開、SHA-256検証

## 視聴者が使う流れ

公開後は、ACS Developerの案内ページからLocanyの0円商品ページへ進み、スターターパックを入手します。パック内のRunPodテンプレートリンクを開き、GPUを選んで起動するだけの導線を想定しています。

現在の`0.2.0-rc1`は公開前候補です。ACS独自ライセンスとGHCRを採用済みで、公開RunPodテンプレートとGPU実機確認を一般配布ゲートとしています。

詳しい手順は[RunPod導入手順](docs/INSTALL-RUNPOD.md)、操作は[利用ガイド](docs/USER-GUIDE.md)を参照してください。

## 配布物に含まれないもの

- Krea2、ComfyUI、LoRAなどのモデル・第三者ファイル
- APIキー、Cookie、パスワード、生成履歴
- 個人向けのモード、人物名、保存先、学習素材

モデルはログイン後にスマホUIの「Turboを入れる」「Rawを入れる」からRunPod側へ取得します。スマホやパソコン本体へ保存する機能ではありません。Krea2には独自ライセンスがあります。使用前に[第三者ライセンス案内](THIRD_PARTY_NOTICES.md)を確認してください。

## パソコンは必要か

一般利用者のパソコンは必須ではありません。RunPodアカウントと支払い設定が済んでいれば、スマホのブラウザだけでPod起動、モデル取得、画像生成、保存、Pod削除まで操作できます。

## 保存料金を選ぶ

- 継続保存: 50GB以上のNetwork Volumeを`/workspace`へ接続。モデルを再利用できますが、GPUを削除してもVolume料金は継続します。
- 都度利用: Network Volumeを接続しない。Pod稼働中の一時ディスクは従量課金ですが、Podを完全削除するとモデルも消え、以後のストレージ料金は残りません。次回は再取得します。

公開テンプレートの既定は都度利用です。意図しない継続ストレージ契約を作りません。

## 開発者向け

```bash
docker build -t acs-imagegen-lite:0.2.0-rc1 .
docker run --gpus all -p 8080:8080 acs-imagegen-lite:0.2.0-rc1
```

自動取得が必要な管理者は`ACS_AUTO_INSTALL_MODELS=turbo`または`all`を設定できます。通常利用では`none`のままUIから選びます。自動停止の既定値はアイドル20分、最大180分です。

テスト:

```bash
python -m venv .venv-test
.venv-test/bin/python -m pip install -r requirements-dev.txt
.venv-test/bin/python -m pytest -q
bash -n scripts/bootstrap.sh scripts/start.sh
```

## 公開前ブロッカー

1. GitHub ActionsでDockerイメージをGHCRへ登録する
2. RunPod公開テンプレートを作成し、URLをスターターパックへ記載する
3. GPU実機でUIモデル取得 / Turbo / Raw / LoRA / 自動停止を確認する

アプリ本体には[ACS ImageGen Lite License 1.0](LICENSE)が適用されます。
