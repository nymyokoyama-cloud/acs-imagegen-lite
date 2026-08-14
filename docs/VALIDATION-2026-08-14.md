# 2026-08-14 安定版・RC4検証記録

## 安定版0.3.1 公開判定

安定版`0.3.1`では、RC4で残っていたKrea2 Turboの新規RunPod実測と終了失敗の誤表示を解消した。配布対象は個人データを含まないスターターパックで、モデル本体・LoRA・生成物・認証情報は含めていない。

- Git commit / tag: `67e9c04403dc1deba7b8e91b70b4607451ac0263` / `v0.3.1`
- OCI index digest: `sha256:bb90c6093d48761e465197b0435cc72770e01ea252dda57603fa320719a2467a`
- linux/amd64 image digest: `sha256:5dc7a7f2ae64397cfaaa98c6c634110b6476fbc12a52cea74dc8bc5272ea3936`
- SPDX SBOM SHA-256: `2e2182a4fde98e128d995c9afda6e611958264c6cdc13ac4ab61b47934b56992`
- GitHub Actions: 27テストとコンテナbuild / pushに成功
- Python依存: `pip-audit --local` 既知脆弱性0件
- 静的監査: Bandit未対処指摘0件、Gitleaks秘密情報0件
- 完成SBOMのTrivy監査: Critical 0 / High 0 / Medium 1 / Low 2

### Krea2 Turbo RunPod実測

- GPU: NVIDIA L40S 1枚
- モデル取得: 18,638,004,998 bytes、42.275秒、3ファイルすべてSHA-256一致
- 生成: 1344x768 PNG、seed `20260814`、実行14.023秒
- 出力: `job-1-krea2-ai.png`、1,064,706 bytes
- 出力SHA-256: `550ee1880839109de1153cf68e8650c78eeaf2d9ad0abf0cb2b936cbeb47a675`
- HTTP確認: `image/png`、`X-AI-Generated-By: Krea 2`
- 目視確認: 顔・手・アイスコーヒー・カフェ背景に明らかな破綻、文字、ロゴなし

モデル導入APIの応答形状と長いプロンプトの表示崩れをこの実測で発見し、0.3.1で修正した。RunPodのPod終了APIがHTTP 403を返した場合は成功表示にせず、コンソールでの終了を明示することも確認した。

### 配布ZIP

- ファイル: `ACS-ImageGen-Lite-0.3.1-Starter-Pack.zip`
- SHA-256: `dc60248b73ecc749158f0c42343b77a0122416c53481c689e566dc7df0f6d7f9`
- ZIP整合性: `unzip -t`成功
- 除外確認: モデル、LoRA、生成物、学習素材、認証情報、メールアドレス、個人名、個人パス、内部検証ファイルを含まない

### 最終起動・公開導線

- RunPodテンプレート: `evkauvs9oe`、Public表示を管理画面で確認
- 公開リンク: `https://console.runpod.io/deploy?template=evkauvs9oe`
- 未ログイン確認: ゲストブラウザで公開リンクからGPU選択画面へ到達
- 最終起動: 新規150GB一時ディスク、Network Volumeなし、A40、`/opt/acs-imagegen-lite/scripts/start.sh`
- ヘルスチェック: HTTP 200、`{"ok":true,"version":"0.3.1"}`
- UI: 初回設定、ログイン、PC 1470px、スマホ390x844、横スクロールなしを確認
- 終了確認: 検証Pod 0件、GPU課金停止。既存Network Volumeの`$0.024/hour`だけ継続
- 今回の0.3.x公開前検証差額: `$19.4027589942`から`$17.0705652767`、約`$2.33`

### 公開・0円受取確認

- Locany商品: `https://locany.net/shop/acs-imagegen-lite-starter-pack/`、商品ID `6508`、0円、公開、downloadable
- ACS記事: `https://acs-developer.com/acs-imagegen-lite-runpod-krea2-minimax-h3/`、記事ID `1824`、公開
- 両ページ: HTTP 200、PC / 390px表示、画像、本文、CTA、RunPodリンクを確認
- ゲスト注文: 注文番号 `6509`、合計0円、注文完了画面にダウンロードリンク表示
- 再取得ZIP: 70,976 bytes、`unzip -t`成功、SHA-256が配布正本の`dc60248b73ecc749158f0c42343b77a0122416c53481c689e566dc7df0f6d7f9`と一致

## RC4 H200検証（履歴）

## 結論

MiniMax H3の4モデル、Text to Video、Image to Video、First / Last Frame to Videoは、日本リージョンのH200実機で動作した。3本とも5秒指定から5.167秒のMP4が完成し、H.264映像とAACステレオ音声を確認した。

一方、モデル未導入の新規一時ディスクでは公式配布元からの取得が予算内に終わる速度ではなく、Krea2 Turbo本体のRunPod Lite実測は未完了だった。また、UIのPod完全削除APIは受付を返したが約30秒後もRUNNINGだったため、CLIで完全削除した。RC4はこの2点を未完了のまま公開完成扱いにしない。

## 環境

- Version: `0.3.0-rc4`
- Git commit: `93050490a697c5ec77c8e213241842866d6f462c`
- GHCR digest: `sha256:2c798bc6b4844a2fd917bf00b9a93aa570c297ff84f4f455ca961c8e98479640`
- GPU: NVIDIA H200 1枚、Secure Cloud、日本`AP-JP-1`
- GPU単価: `$4.59/hour`
- Container Disk: 150GB
- モデル検証時のみ既存250GB Network Volumeを再利用

## 実測結果

| 対象 | 結果 | 実測 |
|---|---|---|
| RunPod HTTPSプロキシ経由の初回設定 | 成功 | setup `303` |
| RunPod HTTPSプロキシ経由のログイン | 成功 | login `303` |
| H3リージョン判定 | 成功 | `AP-JP-1` / allowed |
| H3ライセンス完全性 | 成功 | 同梱SHA-256一致 |
| H3 7項目同意 | 成功 | accepted=true |
| H3モデル4件 | 成功 | 合計53,912,611,064 bytesを約2分23秒で再検証、4件ともSHA-256一致 |
| H3 Text to Video | 成功 | 5秒指定、約92秒、864x480、H.264 + AAC stereo |
| H3 Image to Video | 成功 | 5秒指定、約72秒、672x672、H.264 + AAC stereo |
| H3 First / Last Frame | 成功 | 5秒指定、実行約75秒、672x672、H.264 + AAC stereo |
| AI生成識別 | 成功 | 3件とも`-minimax-h3-ai.mp4`、`X-AI-Generated-By: MiniMax H3` |
| Krea2入力画像 | 成功・範囲外 | Mac既存GGUF環境、個人LoRAなし、512x512、約2分29秒。RunPod LiteのTurbo実測ではない |
| 新規モデル取得 | 未完了 | 新規一時ディスクで約2分後も約0.4%。予算保護のため停止 |
| UI Pod完全削除 | 未完了 | APIは`ok=true`を返したが約30秒後もRUNNING |
| CLI Pod完全削除 | 成功 | Pod 0台、GPU課金0へ復帰 |

## 費用

- 検証開始残高: `$21.8590211637`
- 削除直後残高: `$19.5864869554`
- 差額: 約`$2.27`
- アカウント既存Network Volume料金`$0.024/hour`はPod削除後も継続しており、この検証のGPU料金とは区別する。

RunPodの請求反映には遅延があり得るため、差額は削除直後の残高ベース。ユーザー指定の約3ドル上限内で停止した。

## 成果物

保存先:

`iCloud Drive/Codex/制作物/Desktop software/ACS ImageGen Lite/validation/2026-08-14-rc4/`

- `ACS_Lite_H3_Input_00001_.png`
- `job-1-minimax-h3-ai.mp4`
- `job-2-minimax-h3-ai.mp4`
- `job-3-minimax-h3-ai.mp4`
- 各動画の中間フレームと3点コンタクトシート

## RC4時点の公開前残件（安定版0.3.1で解消済み）

1. 新規一時ディスクでKrea2 Turbo + H3の取得速度を改善し、7ファイルのSHA-256完了を実測する。
2. RunPod Lite上でKrea2 Turboを1枚生成し、ダウンロードまで確認する。
3. UIのPod完全削除が失敗を隠さず、RunPod側の削除完了を確認できるようにする。

## RC6 公開前監査（2026-08-14追記）

RC5でHugging Face Xet高速取得とPod終了結果APIを実装したが、Krea 2公式ライセンスの公開条件監査で追加対応が必要と判明したため、RC5のGHCR buildは中止し公開していない。

- Krea 2 Community License Agreement v.1（2026-06-22）全6ページを文字抽出とPNG表示で確認
- 公式Krea Acceptable Use Policyを確認
- 商用利用の会社全体年商100万米ドル未満条件、Content Filtering Requirement、AUPを日本語条件と5項目同意へ反映
- Krea2のモデル取得と画像生成を同意前はサーバー側で拒否
- Krea2プロンプトを受付時と実行直前に検査し、人による完成画像確認を必須化
- Krea 2出力に`krea2-ai`ファイル名と`X-AI-Generated-By: Krea 2`を追加
- Hugging Face取得元をKrea 2 commit `952f49d49653cb42e7d6cf7cbfad74738073ec7d`、MiniMax H3 commit `014cd40f7e177756c6b2473c0d93b1c89a790dd2`へ固定し、既存SHA-256確認と二重化
- Python 3.12クリーン環境で27テスト成功
- `pip-audit --local`: 既知脆弱性0件
- `bandit -q -r app scripts -x tests`: 未対処指摘0件
- 固定commitからのHugging Face小ファイル実取得: 成功

RC6のGHCRイメージは完成後SBOMを取得してTrivyで確認した。アプリの固定Python依存関係には既知脆弱性がなかった一方、従来の`runpod/pytorch`基盤にLite版で使わないJupyter / File Browser等の重大指摘が残っていた。このためRC6は不採用とし、NVIDIA公式CUDA runtimeをdigest固定した最小基盤、専用Python仮想環境、PyTorch 2.8 / CUDA 12.8公式wheelへ切り替えた。

安定版は、新基盤の完成コンテナSBOM、新規RunPod一時ディスクでのKrea2 Turbo取得・1枚生成・課金停止確認を残す。ここまでは公開完成扱いにしない。

### NVIDIA CUDA最小基盤のSBOM監査

- edge index digest: `sha256:842401f4709819c9656f21d1514419debce1d7fdda2819277e74058f283fdb15`
- linux/amd64 image digest: `sha256:8c61b8824ce0f22d7c5a4324c8f7b084963d5ffb2718d536131ab197cc9092fb`
- SPDX SBOM digest: `sha256:6a9b6eba7bd6c3d0b96b09d15b0e23564d4eca4d580530ac983a392a4cb64680`
- Trivy: Critical 0 / High 0 / Medium 1 / Low 2
- 残件はPyTorch 2.8に対するローカル操作前提の`unpack_sequence` 1件（Medium）と同系統2件（Low）。Web UIのモデル・LoRA入力はsafetensorsに限定し、公式モデルはcommit・サイズ・SHA-256を固定している
- PyTorch公式の`torch.load(weights_only=True)`悪性checkpoint注意も確認したが、Lite UIはpickle / pth / pt / ckptを受け付けず、当該読み込み経路を公開していない。H3実測済みのPyTorch 2.8互換性を維持する判断とした
- Pythonアプリ固定依存: `pip-audit --local`既知脆弱性0件、Bandit未対処指摘0件、Gitleaks秘密情報0件

安定版タグの完成イメージでも同じ監査を再実施し、RunPodはその後に起動する。
4. I2V / FLF入力画像の処理後削除を実環境で確認する。（追加ハードニング項目）
5. スマホ実機から3本のMP4再生を確認する。（追加端末互換確認）
