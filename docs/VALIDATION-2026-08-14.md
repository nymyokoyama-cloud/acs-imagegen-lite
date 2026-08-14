# 2026-08-14 RC4 H200検証

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

## 公開前の残件

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
4. I2V / FLF入力画像の処理後削除を実環境で確認する。
5. スマホから3本のMP4再生を確認する。
