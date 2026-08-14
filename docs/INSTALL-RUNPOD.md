# RunPod導入手順

## 一般利用者向け（公開テンプレート完成後）

1. ACS Developerの配布ページから0円スターターパックを入手します。
2. パックに記載された「RunPodで起動」を開きます。
3. 24GB以上のVRAMを持つGPUを選びます。24GBは推奨の目安で、構成や空き状況によって結果は変わります。
4. 保存方式を選びます。継続保存したい人だけ50GB以上のNetwork Volumeを`/workspace`へ接続します。毎回取得でよければ接続不要です。
5. Deployを実行します。
6. PodのConnect画面からHTTP Port 8080を開きます。
7. 10文字以上のパスワードを設定し、ログインします。
8. 画面上部の「Turboを入れる」または「Turbo＋Rawをまとめて準備」を押し、進捗が100%になるまで待ちます。中断後は同じボタンで再開できます。
9. 画像生成後は「Podを完全削除」を実行します。Network Volume接続時はモデルだけ保持されます。

RunPodのAPIキーを画面へ入力する必要はありません。Pod内で提供されるPod IDとPodスコープのAPIキーを停止処理に使用します。

## データ保持の違い

- Network Volumeあり: Podを完全削除しても、Volume側のモデル、LoRA、設定、画像を保持できます。Volume料金は別途継続します。
- Network Volumeなし: Pod完全削除でモデル、LoRA、設定、画像が消え、継続ストレージ料金を残しません。次回はUIから再取得します。

重要な画像は終了前に端末へ保存してください。

## テンプレート作成者向け

`runpod-template.json`は設定値の正本であり、現時点ではそのままRunPod APIへ投入することを保証するファイルではありません。RunPodコンソールのCustom Templatesで次を設定します。

- Container image: 公開レジストリへpushしたイメージ
- Container disk: 70GB
- Volume disk: 0GB
- Volume mount path: `/workspace`
- Expose HTTP port: `8080`
- Environment variables: `runpod-template.json`の`env`

モデルをTurboのみにする場合は`ACS_INSTALL_RAW=0`にします。この場合のモデル取得量は約18.6GBです。

## 初回起動で行うこと

起動スクリプトは次を自動実行します。

1. ComfyUIをローカルポート8188で起動
2. Lite UIをポート8080で起動
3. アイドル監視を開始
4. 利用者がUIで選んだ時だけ、公式`Comfy-Org/Krea-2`から再開可能な形でモデルを取得
5. SHA-256照合後に生成モデルを有効化

モデルファイルはDockerイメージや配布ZIPに含めません。

## 環境変数

| 変数 | 既定値 | 内容 |
|---|---:|---|
| `ACS_AUTO_INSTALL_MODELS` | `none` | `none`ならUI選択。管理者用に`turbo` / `all` |
| `ACS_IDLE_MINUTES` | `20` | ジョブがない状態で自動終了するまで |
| `ACS_MAX_UPTIME_MINUTES` | `180` | ジョブ終了後に適用する最大稼働時間 |
| `ACS_IDLE_ACTION` | `auto` | `auto` / `stop` / `terminate` |
| `ACS_WEB_PASSWORD` | 未設定 | 設定時は初回画面を省略。10文字以上 |
| `ACS_MAX_LORA_BYTES` | 2GB | LoRAアップロード上限 |

`auto`は継続課金の見落としを避けるため`terminate`を選びます。Network VolumeはPodから独立して保持されます。

## トラブル時

- 8080が開かない: Container Logsでモデル取得中か確認します。
- モデル未導入と表示: 起動スクリプトのSHA-256エラーを確認します。
- GPUメモリ不足: 解像度を下げる構成へ変更するか、VRAMの多いGPUを選びます。
- 停止ボタンが失敗: RunPodコンソールから手動停止し、PodスコープAPIキーの提供状態を確認します。
