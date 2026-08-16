# 2026-08-16 0.4.0 検証記録

0.4.0でZ-Image Turboを第3の画像エンジンとして追加した。前半はローカル検証、後半（「公開フェーズ実測」以降）は同日に実施したGHCR build・GPU実測・配布物の記録。Locany商品ページとACS記事への反映だけが残っている。

## ライセンス判断

| 項目 | 結果 | 出典 |
|---|---|---|
| 上流ライセンス | Apache License 2.0 | https://huggingface.co/Tongyi-MAI/Z-Image-Turbo （モデルカードYAML `license: apache-2.0`、HF API `cardData.license`） |
| ゲート | なし（`gated: false` / `private: false`） | 同上のHF APIメタデータ |
| 追加AUP・商用売上条件・AI表示義務・他AI学習禁止 | いずれも記載なし | モデルカード全文を`licen|commercial|acceptable|terms|agree|prohibit|responsib|abus|misuse|comply`で検査。該当は front-matterのライセンス宣言のみ |
| リパック配布元のライセンス表記 | **なし**（LICENSEファイルなし、`cardData`にlicenseキーなし） | https://huggingface.co/Comfy-Org/z_image_turbo （HF API・ファイルツリー） |

判断: 同意ゲートは設けない。ライセンスの根拠は上流Tongyi-MAIのApache-2.0許諾に置き、Comfy-Orgリパックは取得の利便性のためだけに参照する。Apache-2.0原文を`APACHE-2.0-LICENSE.txt`として同梱し、`Z_IMAGE_NOTICE.txt`と`docs/Z-IMAGE-TERMS.md`で出典・SHA-256・判断根拠を明示した。

ACS独自方針として、Krea2/H3と同じプロンプト安全検査、AI生成ファイル名`zimage-ai`、`X-AI-Generated-By`ヘッダー、人による完成画像確認の案内は適用する。

同梱Apache-2.0原文 SHA-256: `cfc7749b96f63bd31c3c42b5c471bf756814053e847c10f3eb003417bc523d30`（https://www.apache.org/licenses/LICENSE-2.0.txt から取得、11,358 bytes）

## モデル取得元とSHA-256実測

取得元: `Comfy-Org/z_image_turbo`、固定revision `d24c4cf2a0cd98a42f23467e27e3d76ee9438b8e`

この3ファイルの組み合わせは、ComfyUI公式の`image_z_image_turbo_int8`テンプレートと同じ構成。

| 配置 | ファイル | サイズ | SHA-256 | 照合方法 |
|---|---|---:|---|---|
| `diffusion_models/` | `z_image_turbo_int8_convrot.safetensors` | 6,201,001,296 | `be517ebd47c912a5626a588e1aeea43e6be4a43c0cdcd2b48a2a780d9f358635` | ローカル実ファイルを`shasum -a 256`で実測、HF LFS oidと一致 |
| `text_encoders/` | `qwen_3_4b_fp8_mixed.safetensors` | 5,631,994,051 | `72450b19758172c5a7273cf7de729d1c17e7f434a104a00167624cba94f68f15` | 固定revisionから実ダウンロードし`shasum -a 256`で実測、HF LFS oidと一致 |
| `vae/` | `ae.safetensors` | 335,304,388 | `afc8e28272cd15db3919bacdb6918ce9c1ed22e96cb12c4d5ed0fba823529e38` | ローカル実ファイルを`shasum -a 256`で実測、HF LFS oidと一致 |

合計 12,168,299,735 bytes（約12.2GB）。Krea2 Turbo構成（約18.6GB）より約6.5GB軽い。

bf16版（12.31GB）とnvfp4版（4.51GB）も同リポジトリにあるが、bf16は16GB級GPUには重く、nvfp4はBlackwell世代が前提のため、int8 ConvRotを既定にした。

## 生成設定

ComfyUI公式テンプレート（`Comfy-Org/workflow_templates`の`image_z_image_turbo.json` / `image_z_image_turbo_int8.json`）と同値で固定した。

| 項目 | 値 |
|---|---|
| steps | 8 |
| cfg | 1.0（ComfyUI表記。diffusers側の`guidance_scale=0.0`と同義） |
| sampler_name | `res_multistep` |
| scheduler | `simple` |
| ModelSamplingAuraFlow shift | 3.0（ノード既定値ではないため明示指定） |
| latent | `EmptySD3LatentImage` |
| negative | `ConditioningZeroOut`（cfg 1.0のため常時） |
| CLIPLoader type | `lumina2` |

固定ComfyUI commit `7fe8a6138504f90ff7be82f3babf416da32876b1`のソースで、Z-Image対応を確認した。

- `comfy/supported_models.py`: `class ZImage(Lumina2)`、`sampling_settings`の`shift: 3.0`、`memory_usage_factor 2.8`
- `comfy/sd.py`: Qwen3-4B text encoderは`CLIPType.FLUX` / `FLUX2`以外で`comfy.text_encoders.z_image.te` / `ZImageTokenizer`へ分岐する。よって`type: lumina2`で正しく読み込まれる
- `comfy/ops.py`: `int8_tensorwise` + `convrot`量子化形式に対応（H3のint8 ConvRot text encoderと同系統）
- `nodes.py`の`CLIPLoader`のtype一覧に`lumina2`が存在

## LoRA

Z-Image TurboはComfyUI標準の`LoraLoaderModelOnly`に対応する。`comfy/supported_models.py`の`class ZImage(Lumina2)`と`comfy/lora.py`の`Lumina2`分岐（`z_image_to_diffusers`によるキー再マップ）で確認した。持ち込みLoRAはKrea2と同じアップロード経路をそのまま使える。

グラフ上はLoRAを`ModelSamplingAuraFlow`の**前**に適用する（UNETLoader → LoraLoaderModelOnly → ModelSamplingAuraFlow → KSampler）。

注意点として、Z-Imageはattentionが融合QKVのため、`to_q`/`to_k`/`to_v`が分かれた形式のLoRAはエラーにならず無効化されることがある。UIと利用ガイドに「LoRAはエンジン一致が必要」「合わないLoRAは効果が出ないことがある」と明記した。

## VRAM・GPU要件

| 根拠 | 内容 |
|---|---|
| 公式モデルカードの表明 | Z-Image Turboは「fits comfortably within 16G VRAM consumer devices」 |
| Lite版int8構成の重み実サイズ | DiT 6.20GB + text encoder 5.63GB = 約11.8GB（VAE 0.34GBは別） |
| ComfyUIの挙動 | text encoderとDiTを順次ロード・退避するため、両者の同時常駐は前提としない |

結論: **16GB以上のGPU**を目安として案内する。実装時点では公式表明と実ファイルサイズからの見積だったが、同日の公開フェーズでRTX A4000 16GBの実測により裏づけた（下記「RunPod GPU実測」。ピーク72% ≒ 約11.5GB）。

比較のため、Krea2は24GB以上（0.3.1でL40S実測）、H3はH200（0.3.1で実測）を維持する。

## ローカル検証結果

| 検査 | 結果 |
|---|---|
| pytest | **37件合格**（0.3.1の27件を維持し、Z-Image分9件とバージョン整合1件を追加） |
| Python構文（`compileall app scripts tests`） | 合格 |
| Bash構文（`bash -n scripts/bootstrap.sh scripts/start.sh`） | 合格 |
| JSON（`runpod-template.json`） | 合格 |
| JavaScript（`node --check`、index.html埋め込みスクリプト） | 合格 |
| Bandit（`-q -r app scripts -x tests`） | 未対処指摘0件 |
| Gitleaks（`.gitleaks.toml`適用） | 秘密情報0件、18 commits走査 |
| 個人パス・人物ラベル・APIキー・モデルファイル混入検査（`tests/test_security.py`） | 合格 |
| `split_files/`取得→ComfyUI配置→SHA-256照合の実動作 | `file://`で再現したリポジトリで成功。3ファイルとも正しい配置先へ移動、`split_files/`残骸なし、全件verified |
| ローカル実起動（uvicorn・ComfyUIなし） | `/healthz`が`{"ok":true,"version":"0.4.0"}`、ログイン、UI描画に成功 |
| ブラウザ実画面 | 下記 |

### ブラウザ実画面（ローカル起動）

- モデル選択に3件（`krea2_turbo` / `krea2_raw` / `zimage_turbo`）が並び、Z-Imageのラベル・engine・unetが`/api/config`と一致
- モデル管理に7構成が並ぶ（Z-Image Turbo 12.2GB、すべて 97.9GB）
- 「Z-Image Turbo について」カードが描画され、Apache-2.0・同意ゲートなしの状態文と3リンク（公式モデルカード / 同梱Apache-2.0原文 / 日本語利用条件）を表示
- 見出しが「2A. 画像生成（Krea2 / Z-Image Turbo）」に更新
- 比率セレクトはZ-Imageでも5種類
- ネガティブ欄はKrea2 Rawのときだけ表示され、Z-Image選択時は非表示
- クライアント側ゲート: Krea 2未同意でもZ-Imageの生成ボタンは有効、Krea2 Turbo / Rawは無効のまま（サーバー側の451と一致）
- H3カードは`RUNPOD_DC_ID`なしのためfail closed表示のまま（無回帰）
- 390x844幅: 横スクロールなし（`scrollWidth` 390 = `clientWidth` 390）、Z-Imageカードは1列で収まる
- コンソールエラー0件

### 追加した自動テスト（9件）

- Z-Imageグラフが公式蒸留設定（8 / 1.0 / `res_multistep` / `simple` / shift 3.0 / `lumina2` / `EmptySD3LatentImage`）であること
- ネガティブ文字列がグラフへ混入せず`ConditioningZeroOut`になること
- LoRAが`ModelSamplingAuraFlow`の前段へ入り、トリガーワードとスタイルが合成されること
- 辺が16の倍数へ丸められること、5比率すべてがそのまま通ること
- 空プロンプトが拒否されること
- Z-Imageパッケージが最軽量で、同意ゲート要求フラグを持たないこと。`everything`の合計が整合すること
- Z-Image 3ファイルが固定revisionで、`remote_path`が`split_files/`始まりかつ`relative_path`で終わること。取得スクリプトのallowlistが一致すること
- 取得スクリプトが`split_files/`からComfyUI配置先へ移動し、`../`のような脱出パスを拒否すること
- API: Z-Imageは`install`が451にならないこと、`acceptance_required: false`であること、**Krea 2未同意でもZ-Image生成が通り、同時にKrea2生成は451のままであること**、安全フィルターがZ-Image側ログへ分類だけを記録すること、`zimage-ai`出力に`X-AI-Generated-By: Z-Image Turbo`が付くこと
- `/legal/z-image-license`が認証なしで公開され、同梱Apache-2.0原文のSHA-256と一致すること

## 回帰させていないことの確認

- Krea 2の5項目同意ゲート、H3の7項目同意ゲート、H3の日本リージョン固定、H3ライセンス完全性のfail closedは変更していない
- Krea2は同意前の取得・生成が451で拒否されることをテストで再確認した
- `build_workflow`のKrea2経路は既存コードのまま。Z-Imageはエンジン判定で分岐する
- 0.3.1から存在する27件のテストはすべて修正なしで通っている（パッケージ集合とダミーモデル配置の2箇所だけZ-Image追加に合わせて拡張）

## 公開フェーズ実測（2026-08-16）

### GitHubとGHCR

| 項目 | 値 |
|---|---|
| main commit | `af9887d`（`98b54e6`実装＋`af9887d`export-ignore修正をfast-forward） |
| タグ | `v0.4.0` |
| Actions run | `31923061257`（成功・約21分） |
| OCI index digest | `sha256:b0905792cc0ff531a580ab1bae7a781cd1494691e3e1b2ec5a9dd4f77e91698e` |
| linux/amd64 digest | `sha256:f812a873c6477ea45d3660ca01f99c53823e0185357cf17dfd0e210609108d49` |

`.gitattributes`のexport-ignoreが`docs/VALIDATION-2026-08-14.md`をファイル名で指定していたため、この記録が配布ZIPへ入る状態だった。`docs/VALIDATION-*.md`のパターンへ変更してから公開した。

### セキュリティ

| 検査 | 結果 |
|---|---|
| `pip-audit --local`（Python 3.12・`requirements-dev.txt`のピン構成） | 既知脆弱性0件 |
| pytest（同環境・GitHub Actions内でも実行） | 37件合格 |
| 完成コンテナSBOM（buildxのSPDX添付証明）のTrivy・Python依存124件 | Critical 0 / High 0 / Medium 1 / Low 2 |
| 同SBOMのOSパッケージ347件（Ubuntu 24.04） | Critical 0 / High 0 / Medium 38 / Low 2 |
| 合計 | **Critical 0 / High 0** / Medium 39 / Low 4 |

**修正版が存在する指摘は3件だけ**で、いずれもtorch 2.8.0のCVE-2025-2999 / 3000 / 3001（0.3.1と同一）。ComfyUI公式固定commitが要求するtorchバージョンのため据え置く。残る40件はすべて`affected`（Ubuntu 24.04に修正パッケージが出ていない）で、内訳はffmpeg 38件、libgcrypt20 1件、util-linux 1件。ffmpegはH3出力のMP4処理に必要なため同梱を続ける。

0.3.1の記録「Medium 1 / Low 2」はPython依存だけを見た値だった。0.4.0からはOSパッケージも同じ表に載せる。SBOMにはdebとrpmのpurlが混在し、Trivyがそのままでは集計できないため、rpm 8件（Pythonホイール由来のメタデータ）を分離し、Ubuntu 24.04のOS宣言を補ってから走査した。

### RunPod GPU実測（Z-Image Turbo）

| 項目 | 実測値 |
|---|---|
| GPU | NVIDIA RTX A4000 16GB（Community Cloud・$0.17/hr） |
| イメージ | `ghcr.io/nymyokoyama-cloud/acs-imagegen-lite:0.4.0` |
| Pod作成から`/healthz` 200まで | 320秒 |
| `/healthz`の版 | `{"ok":true,"version":"0.4.0"}` |
| Z-Image 3ファイル取得＋SHA-256照合 | 12,168,299,735バイトを34.5秒（3件ともverified） |
| 1枚目の生成（1344×768・8 steps・初回モデルロード込み） | 28.1秒 |
| 2枚目以降（同条件・ロード済み） | 24.3秒 |
| 持ち込みLoRAあり | 26.0秒 |
| GPUメモリ利用率ピーク | 72%（16GBに対し約11.5GB） |
| GPU利用率 | 生成中100% |
| Pod稼働時間と費用 | 10.6分・約$0.06 |

出力は`job-N-zimage-ai.png`で、`/api/images/`のレスポンスに`X-AI-Generated-By: Z-Image Turbo`が付いた。PNGを実ダウンロードして目視確認し、構図・描写ともに破綻なし。

持ち込みLoRA（検証専用・配布物には一切含めない）は170,128,288バイトをUIの`/api/loras`へ62.6秒でアップロードでき、そのまま生成に使えた。**同一プロンプト・同一Seed 999でLoRAあり／なしを生成し、PNGのSHA-256が異なることを確認**した。Z-Imageは融合QKVのため合わないLoRAが無言で無効化されることがあるが、この構成では実際に重みが効いている。検証後はPodごと削除した。

### 無回帰（同じPod上で確認）

| 検査 | 結果 |
|---|---|
| `/api/config` | 画像3モデル（`krea2_turbo` / `krea2_raw` / `zimage_turbo`）を返す |
| Krea 2未同意での生成 | 451 |
| Krea 2未同意でのモデル取得 | 451 |
| Krea 2同意APIへ5項目のうち1項目を`no`で送信 | 400 |
| H3（非`AP-JP-1`リージョン） | 451・fail closed表示 |
| Z-Image安全フィルター | 禁止カテゴリのプロンプトを422で拒否し、分類だけを返す |
| `/legal/z-image-license` / `/legal/z-image-terms` | 認証なしで200（11,358 / 5,303バイト） |
| UI本体 | Z-Image Turbo・Krea 2・MiniMax H3の3カードとApache-2.0表示を描画 |

UIの「Podを完全削除」は202と「まだ完了ではありません」を返し、成功を装わない0.3.1の仕様どおりだった。実際の削除はRunPod APIで行い、Pod一覧が空であることを確認した。

## 未実施

1. Locany 0円商品とACS記事の0.4.0反映
2. スマホ実機での表示確認（ローカル390px幅は確認済み）
3. Krea2 RawのGPU実生成、H3入力画像の実環境削除確認、20分アイドル自動終了の時間経過試験（0.3.1から継続の公開後検証）
