# Third-party notices

ACS ImageGen Lite本体とは別に、次の第三者ソフトウェアとモデルを利用します。本パッケージにモデル本体は含みません。

## Krea 2

- 配布元: https://huggingface.co/Comfy-Org/Krea-2
- ライセンス原文: https://huggingface.co/Comfy-Org/Krea-2/blob/main/LICENSE.pdf
- Lite版が初回取得するもの: Turbo FP8、Raw FP8、Qwen3-VL FP8 text encoder、Qwen image VAE

Krea 2には独自ライセンスが適用されます。利用者はモデルと生成物を使用する前に原文を確認してください。Lite版はモデルを再配布せず、公式URLから取得します。

## ComfyUI

- ソース: https://github.com/Comfy-Org/ComfyUI
- Docker buildで固定するcommit: `7fe8a6138504f90ff7be82f3babf416da32876b1`
- ライセンス: ComfyUI公式リポジトリのLICENSEを参照

Dockerイメージを配布するときは、そのイメージ内に含まれるComfyUIと依存パッケージのライセンス表示・ソース提供条件を満たしてください。

## MiniMax H3

- モデル取得元: https://huggingface.co/Comfy-Org/MiniMax-H3
- ライセンス原文: https://huggingface.co/MiniMaxAI/MiniMax-H3/blob/main/LICENSE
- Lite版が取得するもの: FP8 diffusion model、Qwen3-VL 32B int8 text encoder、video VAE、audio VAE
- 必須表示: `MINIMAX_H3_NOTICE.txt`

MiniMax H3には地域・商用規模・公開時のAI生成表示・他AI学習禁止等の条件があります。Lite版は既定で日本RunPodリージョンだけを許可し、UIで利用者の確認を取得します。詳細は`docs/H3-TERMS.md`を確認してください。

## RunPod

RunPodは外部クラウドサービスです。利用料金、保存料金、利用規約はRunPod側の最新情報を確認してください。
