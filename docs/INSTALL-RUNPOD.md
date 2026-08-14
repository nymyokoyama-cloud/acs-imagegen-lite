# RunPod導入手順

## 一般利用者向け

1. ACS Developerの配布ページから0円スターターパックを入手します。
2. パック内の「RunPodで起動」を開きます。
3. H3を使う場合は日本リージョン`AP-JP-1`のH200を選びます。Krea2だけなら24GB以上のGPUが目安です。
4. 一時ディスクは150GBにします。継続保存したい人だけ150GB以上のNetwork Volumeを`/workspace`へ接続します。
5. Deploy後、Connect画面からHTTP Port 8080を開きます。
6. 10文字以上のパスワードを設定してログインします。
7. Krea2を使う場合は公式ライセンスPDFとAUPを読み、年商条件を含む画面の5項目へ同意します。
8. H3を使う場合は同梱ライセンス全文と日本語条件を読み、画面の7項目へ同意します。
9. 「おすすめ：Krea2 Turbo + MiniMax H3」または必要なモデルだけを選び、100%まで待ちます。Xet高速転送中は大きい1ファイルの進捗が完了時にまとまって動く場合があります。中断後は同じボタンで再開できます。
10. 生成物を人が確認してスマホへ保存し、Network Volumeを使わない場合は「Podを完全削除」を押します。
11. 最後にRunPodコンソールで対象Podが消えたことを確認します。これが課金停止の確定です。

モデル取得や生成のためにRunPod APIキーをUIへ入力する必要はありません。終了ボタンはPod環境のAPI資格情報で自動終了を試しますが、権限不足時はエラーとコンソール導線を表示します。モデルはスマホではなくRunPodへ保存されます。

## 容量の目安

- Krea2 Turbo: 約18.6GB
- Krea2 Turbo + Raw: 約31.8GB
- MiniMax H3: 約53.9GB
- おすすめ（Turbo + H3）: 約72.6GB
- すべて（Turbo + Raw + H3）: 約85.7GB

環境、ComfyUI、作業領域、生成物の余裕を含め、一時ディスク150GBを既定にしています。

## 保存方式

- Network Volumeあり: Pod削除後もモデル、LoRA、設定、生成物を保持できます。Volume料金は継続します。
- Network Volumeなし: 一時ディスクはPod停止・削除時に消えます。Podの完全削除完了後は継続ストレージ料金が発生しません。次回はモデルを再取得します。

重要な生成物は終了前に端末へ保存してください。料金と保存仕様はRunPod公式の最新情報を確認してください。

## テンプレート作成者向け

`runpod-template.json`は設定値の正本です。RunPodのCustom Templatesへ次を反映します。

- Container image: `ghcr.io/nymyokoyama-cloud/acs-imagegen-lite:0.3.0`
- Container disk: 150GB
- Volume disk: 0GB（利用者の任意）
- Volume mount: `/workspace`
- HTTP port: `8080`
- H3を案内するGPU: 日本リージョンのH200

Lite UIはComfyUIをローカル8188、Web UIを8080で起動します。モデルはDockerイメージや配布ZIPに含めません。

## 環境変数

| 変数 | 既定値 | 内容 |
|---|---:|---|
| `ACS_AUTO_INSTALL_MODELS` | `none` | UI選択。管理者向けKrea2のみ`turbo` / `all` |
| `ACS_IDLE_MINUTES` | `20` | ジョブがない状態で自動終了するまで |
| `ACS_MAX_UPTIME_MINUTES` | `180` | ジョブ終了後に適用する最大稼働時間 |
| `ACS_IDLE_ACTION` | `auto` | `auto` / `stop` / `terminate` |
| `ACS_RUNPOD_API_KEY` | 未設定 | 任意。終了API専用のRunPod Secretを注入する場合だけ設定 |
| `ACS_MAX_INPUT_IMAGE_BYTES` | `25MB` | H3フレーム画像1枚の上限 |
| `ACS_MAX_LORA_BYTES` | `2GB` | LoRAアップロード上限 |

H3の許可リージョンはアプリ内で日本`AP-JP-1`へ固定しています。配布テンプレートに地域ゲートを解除する環境変数はありません。通報先を自社窓口へ変更する再配布者だけ、`ACS_H3_REPORT_URL`を設定できます。

Krea 2は公式ライセンスとAUPへの同意前にモデル取得と画像生成を拒否します。受付時と実行直前のプロンプト検査を無効化する環境変数はありません。商用利用の年商条件と完成画像の人による確認も必要です。

## トラブル時

- H3を有効にできない: RunPodのデータセンターが日本`AP-JP-1`か確認します。
- 容量不足: 一時ディスクまたはNetwork Volumeを150GB以上にします。
- ComfyUI準備中: 数分待ってから再読込します。
- H3メモリ不足: H200を選び、他ジョブがない状態で5秒動画から試します。
- 停止に失敗: 画面に成功を装わずエラーを表示します。RunPodコンソールから手動でPodを停止・削除します。
