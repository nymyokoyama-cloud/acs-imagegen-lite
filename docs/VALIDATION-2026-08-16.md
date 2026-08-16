# 2026-08-16 0.4.0 ローカル検証記録

0.4.0でZ-Image Turboを第3の画像エンジンとして追加した。この記録は**実装とローカル検証まで**であり、GHCR build、RunPodテンプレート更新、配布ZIP更新、商品ページ更新、GPU実測は未実施。公開完成扱いにしない。

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

結論: **16GB以上のGPU**を目安として案内する。これは公式表明と実ファイルサイズからの**見積**であり、Lite版でのGPU実測値ではない。実測は公開フェーズで行う。

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

## 未実施（公開フェーズ）

1. GHCR 0.4.0のbuild・push・完成コンテナSBOMとTrivy監査
2. `pip-audit --local`の再実行（依存関係は0.3.1から未変更）
3. RunPod 16GB級GPUでのZ-Imageモデル取得・SHA-256一致・1枚生成の実測
4. 生成画像の目視確認とダウンロード・ヘッダー確認
5. 持ち込みLoRAのZ-Image実生成
6. RunPod公開テンプレートの0.4.0更新
7. 配布ZIPの再作成・SHA-256記録
8. Locany商品ページとACS記事の0.4.0反映
9. RunPod実機・スマホ実機での表示確認（ローカル390px幅は確認済み）
