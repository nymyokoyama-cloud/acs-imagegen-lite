# Z-Image Turbo 利用条件

条件版: `2026-08-16-1`

対象ライセンス: `Apache License, Version 2.0`

同梱ライセンス原文 SHA-256: `cfc7749b96f63bd31c3c42b5c471bf756814053e847c10f3eb003417bc523d30`

## ライセンスの結論

Z-Image Turboは、Tongyi-MAIチーム（Alibaba Group）が**Apache License 2.0**で公開しているモデルです。2026-08-16に公式モデルカードとリポジトリのメタデータを確認した時点で、次のいずれも存在しませんでした。

- 追加のAcceptable Use Policy
- ゲート（利用申請・規約同意・アクセストークン）の要求
- 商用利用の売上規模条件
- 生成物のAI表示義務や他AIモデルへの学習禁止条項

したがってACS ImageGen Liteは、Krea 2やMiniMax H3のような**同意ゲートをZ-Image Turboには設けていません**。モデル管理画面からそのまま取得でき、取得後すぐ画像生成に使えます。

## モデルの取得元

| 用途 | 取得元 | 備考 |
|---|---|---|
| ライセンスの根拠 | https://huggingface.co/Tongyi-MAI/Z-Image-Turbo | Apache-2.0の公式表明。diffusers形式 |
| 実際のファイル取得 | https://huggingface.co/Comfy-Org/z_image_turbo | ComfyUI公式のsingle-fileリパック |

固定revision: `d24c4cf2a0cd98a42f23467e27e3d76ee9438b8e`

Comfy-Orgのリパックリポジトリは**自身のライセンス表記を持ちません**。ACS ImageGen Liteは、上流Tongyi-MAIのApache-2.0許諾を根拠として利用し、リパックは取得の利便性のためだけに参照しています。

Lite版はモデル本体をZIPやコンテナに同梱せず、公式URLから取得してSHA-256で照合します。不一致のファイルは使用せず退避します。

## 取得するファイル

| 配置 | ファイル | サイズ | SHA-256 |
|---|---|---:|---|
| `diffusion_models/` | `z_image_turbo_int8_convrot.safetensors` | 6,201,001,296 | `be517ebd47c912a5626a588e1aeea43e6be4a43c0cdcd2b48a2a780d9f358635` |
| `text_encoders/` | `qwen_3_4b_fp8_mixed.safetensors` | 5,631,994,051 | `72450b19758172c5a7273cf7de729d1c17e7f434a104a00167624cba94f68f15` |
| `vae/` | `ae.safetensors` | 335,304,388 | `afc8e28272cd15db3919bacdb6918ce9c1ed22e96cb12c4d5ed0fba823529e38` |

合計 12,168,299,735 バイト（約12.2GB）。この組み合わせはComfyUI公式のZ-Image Turbo int8テンプレートと同じ構成です。

## 生成設定を変えない理由

Lite版は8 steps / cfg 1.0 / `res_multistep` / `simple` / `ModelSamplingAuraFlow` shift 3.0で固定しています。これはTurbo蒸留モデルの学習グリッドと一致する公式設定で、変更すると品質が崩れます。cfgが1.0のため、ネガティブプロンプトは使いません（内部で`ConditioningZeroOut`を使います）。

## 利用者の責任

Apache-2.0はモデルの利用を広く許可しますが、生成物にまつわる法令・第三者の権利までを免責するものではありません。ACS ImageGen Liteの利用者は次を守ってください。

1. 入力、LoRA、写り込む人物、生成物に必要な権利と同意を持つこと。
2. CSAM、同意のない親密画像、違法ななりすまし、詐欺、嫌がらせ、差別、暴力扇動、選挙妨害、無断の大量監視など、違法・有害な目的に使わないこと。
3. Lite版のプロンプト安全検査を無効化しないこと。
4. 完成画像を公開・利用する前に人が確認し、問題がある出力は削除すること。
5. 法令または投稿先の規約で求められる場合、AI生成であることを明確に表示すること。

Z-Image Turboの生成物には保存ファイル名に`zimage-ai`が付き、ダウンロード時に`X-AI-Generated-By`ヘッダーを返します。

安全検査はACS独自の運用方針であり、モデル提供者の義務ではありません。文字列検査だけでは文脈や完成画像のすべてを判定できないため、利用者による出力確認と組み合わせて運用します。

## LoRAについて

Z-Image TurboはComfyUI標準の`LoraLoaderModelOnly`に対応しており、Lite版のLoRAアップロードからそのまま使えます。ただしLoRAは学習したベースモデルと同じエンジンでだけ効きます。Krea2用LoRAをZ-Imageで選んでも、エラーにならず効果が出ないことがあります。

Z-Image Turboは蒸留モデルのため、公式モデルカードはFine-Tunabilityを`N/A`とし、追加学習には非蒸留版の`Tongyi-MAI/Z-Image`を推奨しています。Turbo向けLoRA学習は学習アダプタ経由のコミュニティ手法であり、公式に保証された手順ではありません。

## 注意

ここに記載した内容は法的助言ではありません。英語の公式原文が優先します。ライセンスは変更される場合があるため、重要な用途の前に最新の公式モデルカードを確認してください。

- 公式モデルカード: https://huggingface.co/Tongyi-MAI/Z-Image-Turbo
- Apache License 2.0原文: https://www.apache.org/licenses/LICENSE-2.0
- 同梱原文: `APACHE-2.0-LICENSE.txt`（`/legal/z-image-license`でも表示）
