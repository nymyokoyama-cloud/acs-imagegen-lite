# Third-party notices

ACS ImageGen Lite本体とは別に、次の第三者ソフトウェアとモデルを利用します。本パッケージにモデル本体は含みません。

## Krea 2

- 配布元: https://huggingface.co/Comfy-Org/Krea-2
- ライセンス原文: https://huggingface.co/Comfy-Org/Krea-2/blob/main/LICENSE.pdf
- Acceptable Use Policy: https://www.krea.ai/krea-2-use-policy
- 確認時のライセンスPDF SHA-256: `b82a2805162bde714a4eb27b9063c4fc3345d08a30be055134a6160e5430ba74`
- 必須表示: `KREA2_NOTICE.txt`
- Lite版が初回取得するもの: Turbo FP8、Raw FP8、Qwen3-VL FP8 text encoder、Qwen image VAE

Krea 2には独自ライセンスが適用されます。商用利用は関連会社を含む会社全体の直近12か月売上100万米ドル未満に限られ、以上の場合はKreaのEnterprise Licenseが必要です。デプロイ時は合理的なContent Filtersも必要です。Lite版はモデルを再配布せず、公式URLから取得し、5項目同意、受付時と実行直前のプロンプト検査、人による完成画像確認、AI生成ファイル名とヘッダーを実装します。

## ComfyUI

- ソース: https://github.com/Comfy-Org/ComfyUI
- Docker buildで固定するcommit: `7fe8a6138504f90ff7be82f3babf416da32876b1`
- ライセンス: ComfyUI公式リポジトリのLICENSEを参照

Dockerイメージを配布するときは、そのイメージ内に含まれるComfyUIと依存パッケージのライセンス表示・ソース提供条件を満たしてください。

## MiniMax H3

- モデル取得元: https://huggingface.co/Comfy-Org/MiniMax-H3
- ライセンス原文: https://huggingface.co/MiniMaxAI/MiniMax-H3/blob/main/LICENSE
- 同梱原文: `MINIMAX_H3_LICENSE.txt`（SHA-256 `59b99642b95ea21630e311198ddbfffbfe05aadba0c2f5d884cbdf4efcc90f44`）
- Lite版が取得するもの: FP8 diffusion model、Qwen3-VL 32B int8 text encoder、video VAE、audio VAE
- 必須表示: `MINIMAX_H3_NOTICE.txt`

MiniMax H3には地域・商用規模・公開時のAI生成表示・他AI学習禁止等の条件があります。Lite版は日本RunPodリージョンだけを許可し、7項目の同意記録、サーバー側安全フィルター、通報・停止方針を実装しています。詳細は`docs/H3-TERMS.md`と`docs/H3-ENFORCEMENT.md`を確認してください。

## RunPod

RunPodは外部クラウドサービスです。利用料金、保存料金、利用規約はRunPod側の最新情報を確認してください。
