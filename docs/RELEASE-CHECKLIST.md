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
- [ ] RC3イメージをbuild・スキャン・GHCRへpush
- [ ] `runpod-template.json`のイメージ名をRC3へ更新
- [x] RunPod非公開テンプレート作成
- [ ] RunPod公開テンプレート作成（法務・H200実測後）
- [ ] 公開テンプレートURLをスターターパックへ追加

## GPU実測

- [ ] 24GB GPUで初回モデル取得とSHA-256成功
- [ ] Turbo 1枚生成
- [ ] Raw 1枚生成
- [ ] 任意LoRA 1枚生成
- [ ] 生成画像のダウンロード
- [ ] GPU停止
- [ ] Network Volume接続時のPod完全削除と再起動
- [ ] アイドル自動終了
- [ ] H200 / AP-JP-1でH3モデル4件のSHA-256成功
- [ ] H3 Text to Video 5秒・音声付き
- [ ] H3 Image to Video 5秒・入力画像削除
- [ ] H3 First / Last Frame 5秒・入力画像削除
- [ ] H3出力のMP4保存とスマホ再生
- [ ] 非許可リージョンでH3取得・生成が拒否される

## 配布導線

- [ ] Locany 0円商品を作成
- [ ] ACS記事を作成し、CTAをLocanyへ設定
- [ ] PC / スマホの表示確認
- [ ] 0円購入からZIP取得まで確認
- [ ] YouTube概要欄URLをACS記事に設定
