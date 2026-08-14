# 公開チェックリスト

## 法務・配布条件

- [x] ACS独自利用許諾を決定し、LICENSEを追加
- [ ] Krea2 LICENSE.pdfを確認し、第三者案内を最終レビュー
- [x] H3公式ライセンス全文、NOTICE、日本語利用条件を配布物へ同梱
- [x] H3の7項目同意・条件版・SHA-256・リージョン・履歴記録を実装
- [x] H3の日本リージョン固定ゲートとサーバー側安全フィルターを実装
- [x] H3の通報窓口、調査・配布停止方針、AI生成ファイル識別を実装
- [x] 同梱H3ライセンスSHA-256不一致・非許可リージョン・同意不足・AUP代表例の拒否テスト
- [ ] H3 Community Licenseと配布地域を法務最終レビュー
- [ ] LoRAと生成物の権利注意を商品ページへ掲載

## イメージとRunPod

- [x] 公開コンテナレジストリをGHCRに決定
- [x] RC2 Dockerイメージをbuild
- [ ] 脆弱性スキャン
- [x] RC2イメージをGHCRへpush
- [x] RC3イメージをbuild・GHCRへpush
- [x] RC4イメージをbuild・GHCRへpush
- [ ] RC4イメージを脆弱性スキャン
- [x] `runpod-template.json`のイメージ名をRC4へ更新
- [x] RunPod非公開テンプレート作成
- [ ] RunPod公開テンプレート作成（法務・H200実測後）
- [ ] 公開テンプレートURLをスターターパックへ追加

## GPU実測

- [ ] 24GB GPUで初回モデル取得とSHA-256成功
- [ ] Turbo 1枚生成
- [ ] Raw 1枚生成
- [ ] 任意LoRA 1枚生成
- [ ] 生成画像のダウンロード
- [x] Krea2 Turbo入力画像1枚をMac既存環境で生成（RunPod LiteのTurbo実測とは数えない）
- [x] Network Volume接続時のRC4再起動とH3モデル再利用
- [x] CLIからPod完全削除しGPU課金0へ復帰
- [ ] Lite UIの「Podを完全削除」が実際の削除完了まで反映されること
- [ ] アイドル自動終了
- [x] H200 / AP-JP-1でH3モデル4件のSHA-256成功
- [x] H3 Text to Video 5秒・音声付き
- [x] H3 Image to Video 5秒
- [x] H3 First / Last Frame 5秒
- [ ] H3 I2V / FLFの入力画像が実環境で処理後削除されること
- [x] H3出力のMP4保存・H.264映像・AACステレオ音声
- [ ] H3出力のスマホ再生
- [ ] 非許可リージョンでH3取得・生成が拒否される

実測詳細: [2026-08-14 RC4 H200検証](VALIDATION-2026-08-14.md)

## 配布導線

- [ ] Locany 0円商品を作成
- [ ] ACS記事を作成し、CTAをLocanyへ設定
- [ ] PC / スマホの表示確認
- [ ] 0円購入からZIP取得まで確認
- [ ] YouTube概要欄URLをACS記事に設定
