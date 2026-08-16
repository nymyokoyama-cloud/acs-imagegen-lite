# 公開チェックリスト

## 0.4.0 Z-Image Turbo追加（実装完了・未公開）

ローカル検証記録: [2026-08-16 0.4.0ローカル検証記録](VALIDATION-2026-08-16.md)

### 完了

- [x] 上流Tongyi-MAIのApache-2.0とゲートなしを一次情報で確認し、同意ゲート不要と判断
- [x] Comfy-Orgリパックがライセンス表記を持たないことを記録し、根拠を上流Apache-2.0に置く方針を明記
- [x] Apache-2.0原文同梱、`Z_IMAGE_NOTICE.txt`、日本語利用条件、THIRD_PARTY_NOTICES・READMEへ追記
- [x] Z-Image Turbo Text to Imageを第3エンジンとして実装（5比率・スタイル・Seed・持ち込みLoRA）
- [x] 公式蒸留設定（8 steps / cfg 1.0 / `res_multistep` / `simple` / shift 3.0）で固定
- [x] モデル管理へZ-Image構成を追加し、固定revisionと実測SHA-256で照合
- [x] `split_files/`取得と配置パスの分離を実装し、`file://`再現で動作確認
- [x] Z-Imageにも安全検査・AI生成ファイル名・`X-AI-Generated-By`を適用
- [x] pytest 37件合格、Python / Bash / JSON / JavaScript静的検査合格
- [x] Bandit 0件、Gitleaks 0件、個人パス・人物ラベル・APIキー・モデル混入検査合格
- [x] Krea2 / H3の同意ゲートとfail closed機構が無回帰であることをテストで確認

### 未実施（公開フェーズ）

- [ ] GHCR `0.4.0`のbuild・push（Actions）
- [ ] 完成コンテナSBOMのTrivy監査、`pip-audit --local`
- [ ] RunPod 16GB級GPUでZ-Imageモデル取得・SHA-256一致を実測
- [ ] RunPod上でZ-Image 1枚生成・ダウンロード・ヘッダー確認
- [ ] 持ち込みLoRAのZ-Image実生成
- [ ] RunPod公開テンプレートを`0.4.0`へ更新
- [ ] 配布ZIPを再作成しSHA-256・サイズを記録
- [ ] Locany 0円商品とACS記事へ0.4.0を反映
- [ ] RunPod実機でのスマホ表示確認（ローカル390px幅の横スクロールなしは確認済み）

## 法務・配布条件

- [x] ACS独自利用許諾を決定し、LICENSEを追加
- [x] Krea2 LICENSE.pdf全6ページと公式AUPを確認し、第三者案内を最終レビュー
- [x] Krea 2の5項目同意、年商条件、安全フィルター、人による出力確認を実装
- [x] Krea 2同意不足・AUP代表例の拒否テストとAI生成識別を実装
- [x] H3公式ライセンス全文、NOTICE、日本語利用条件を配布物へ同梱
- [x] H3の7項目同意・条件版・SHA-256・リージョン・履歴記録を実装
- [x] H3の日本リージョン固定ゲートとサーバー側安全フィルターを実装
- [x] H3の通報窓口、調査・配布停止方針、AI生成ファイル識別を実装
- [x] 同梱H3ライセンスSHA-256不一致・非許可リージョン・同意不足・AUP代表例の拒否テスト
- [x] H3 Community License原文・配布地域・技術ゲートを公開前監査（専門家による法的助言ではない）
- [x] LoRAと生成物の権利注意を商品ページへ掲載

## イメージとRunPod

- [x] 公開コンテナレジストリをGHCRに決定
- [x] RC2 Dockerイメージをbuild
- [x] RC6依存パッケージ監査（既知脆弱性0件）とPython静的セキュリティ監査
- [x] RC2イメージをGHCRへpush
- [x] RC3イメージをbuild・GHCRへpush
- [x] RC4イメージをbuild・GHCRへpush
- [x] RC6完成コンテナSBOMを脆弱性スキャンし、旧基盤の重大指摘により不採用
- [x] NVIDIA公式CUDA最小基盤のedge SBOMをスキャン（Critical 0 / High 0）
- [x] 安定版タグの完成コンテナを同じ手順で再スキャン（Critical 0 / High 0）
- [x] `runpod-template.json`のイメージ名を0.3.1へ更新
- [x] RunPod非公開テンプレート作成
- [x] RunPod公開テンプレート作成（法務・H200実測後）
- [x] 公開テンプレートURLをスターターパックへ追加

## 公開前必須のGPU実測

- [x] L40SでKrea2 Turbo初回モデル取得とSHA-256成功
- [x] Turbo 1枚生成
- [x] 生成画像のダウンロードとPNG / SHA-256確認
- [x] Krea2 Turbo入力画像1枚をMac既存環境で生成（RunPod LiteのTurbo実測とは数えない）
- [x] Network Volume接続時のRC4再起動とH3モデル再利用
- [x] CLIからPod完全削除しGPU課金0へ復帰
- [x] Lite UIのPod終了失敗を成功表示せず、RunPodコンソール終了を案内
- [x] H200 / AP-JP-1でH3モデル4件のSHA-256成功
- [x] H3 Text to Video 5秒・音声付き
- [x] H3 Image to Video 5秒
- [x] H3 First / Last Frame 5秒
- [x] H3出力のMP4保存・H.264映像・AACステレオ音声
- [x] 非許可リージョンでH3取得・生成が拒否されることを自動テスト

実測詳細: [2026-08-14 安定版・RC4検証記録](VALIDATION-2026-08-14.md)

## 配布導線

- [x] Locany 0円商品を作成
- [x] ACS記事を作成し、CTAをLocanyへ設定
- [x] PC / スマホの表示確認
- [x] 0円購入からZIP取得・SHA-256一致まで確認
- [x] YouTube概要欄に使える正規URLをACS記事へ固定

## 公開後の追加検証（公開阻害ではない）

- [ ] Krea2 RawのGPU実生成
- [ ] 利用者持ち込みLoRAのGPU実生成
- [ ] H3 I2V / FLF入力画像の実環境での処理後削除
- [ ] H3出力3本のスマホ実機再生
- [ ] 20分アイドル自動終了の時間経過試験
