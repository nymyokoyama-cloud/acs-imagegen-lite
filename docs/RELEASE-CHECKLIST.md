# 公開チェックリスト

## 法務・配布条件

- [x] ACS独自利用許諾を決定し、LICENSEを追加
- [ ] Krea2 LICENSE.pdfを確認し、第三者案内を最終レビュー
- [ ] LoRAと生成物の権利注意を商品ページへ掲載

## イメージとRunPod

- [x] 公開コンテナレジストリをGHCRに決定
- [ ] Dockerイメージをbuild
- [ ] 脆弱性スキャン
- [ ] イメージをpush
- [ ] `runpod-template.json`のイメージ名を置換
- [ ] RunPod公開テンプレート作成
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

## 配布導線

- [ ] Locany 0円商品を作成
- [ ] ACS記事を作成し、CTAをLocanyへ設定
- [ ] PC / スマホの表示確認
- [ ] 0円購入からZIP取得まで確認
- [ ] YouTube概要欄URLをACS記事に設定
