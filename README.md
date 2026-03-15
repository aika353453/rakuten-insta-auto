# 楽天アフィリエイト × Instagram カルーセル自動投稿セット

この版でできること

1. 楽天市場APIから商品候補を自動取得
2. 未投稿商品を優先して複数件選定
3. AIでおすすめポイントつきのカルーセル用文章を自動生成
4. プロフィール固定URL向けのまとめページ `site/index.html` を自動更新
5. GitHub Pages 用の workflow を同梱
6. 手動確認用の `out/manual_publish_package.json` と `out/caption.txt` を自動出力
7. 条件を満たしたときだけ Instagram Graph API でカルーセル投稿

## かなり大事な前提

- Instagram の `/media` と `/media_publish` で作れるのは通常の画像・動画・リール・カルーセル投稿です。
- このスクリプトは **Paid partnership label そのものを API で付けません**。
- そのため、`REQUIRE_PAID_PARTNERSHIP_LABEL=1` のままでは **自動公開を止めて**、手動確認用パッケージを出す安全設計です。
- どうしても API でそのまま公開したい場合だけ `ALLOW_PUBLISH_WITHOUT_PAID_PARTNERSHIP_API=1` を明示します。
- GitHub Pages には `site/` をそのまま載せるので、プロフィールURLは固定のまま中身だけ更新できます。

## フォルダ構成

- `main.py` 実行本体
- `requirements.txt` 依存ライブラリ
- `.env.example` 環境変数サンプル
- `.github/workflows/deploy-pages.yml` GitHub Pages 自動公開
- `data/posted_items.json` 投稿済み商品コード
- `data/hub_items.json` まとめページの商品データ
- `site/index.html` プロフィールから飛ばす固定ページ
- `out/manual_publish_package.json` 手動投稿確認用データ
- `out/caption.txt` 投稿文テキスト

## セットアップ

```bash
pip install -r requirements.txt
cp .env.example .env
python main.py
```

## まずおすすめの使い方

1. `PROFILE_PAGE_URL` に GitHub Pages のURLを入れる
2. `ENABLE_INSTAGRAM_PUBLISH=0` のまま実行する
3. `site/index.html` と `out/manual_publish_package.json` を確認する
4. GitHub に push して Pages を更新する
5. Instagramアプリ側で Paid partnership label を確認してから投稿する

## GitHub Pages の使い方

### いちばん簡単な流れ

1. このフォルダを GitHub リポジトリに入れる
2. GitHub の `Settings > Pages` で **Source = GitHub Actions** を選ぶ
3. `main` か `master` に push する
4. workflow が `site/` を GitHub Pages にデプロイする
5. 発行された URL を Instagram プロフィールの固定リンクに設定する

### 補足

- workflow は `actions/upload-pages-artifact` と `actions/deploy-pages` を使う構成です。
- `site/.nojekyll` も自動生成するので静的HTMLのまま載せられます。

## Instagram 自動公開の考え方

### 安全モード

```env
ENABLE_INSTAGRAM_PUBLISH=0
REQUIRE_PAID_PARTNERSHIP_LABEL=1
```

この場合は投稿しません。代わりに以下を出力します。

- `site/index.html`
- `out/manual_publish_package.json`
- `out/caption.txt`

### そのままAPIで公開するモード

```env
ENABLE_INSTAGRAM_PUBLISH=1
ALLOW_PUBLISH_WITHOUT_PAID_PARTNERSHIP_API=1
```

この設定では公開しますが、Paid partnership label の API 自動付与は入っていません。

## 主要な環境変数

- `RAKUTEN_APP_ID` 楽天アプリID
- `RAKUTEN_AFFILIATE_ID` 楽天アフィリエイトID
- `INSTAGRAM_IG_USER_ID` Instagram IG User ID
- `INSTAGRAM_ACCESS_TOKEN` Instagram長期アクセストークン
- `GRAPH_API_VERSION` 例 `v24.0`
- `KEYWORD` 商品検索キーワード
- `GENRE_ID` 楽天ジャンルID
- `MIN_PRICE` / `MAX_PRICE` 価格帯
- `CAROUSEL_SIZE` 1回の投稿で使う枚数
- `PROFILE_LINK_TEXT` キャプション内のプロフィール誘導文
- `PROFILE_PAGE_TITLE` まとめページのタイトル
- `PROFILE_PAGE_URL` GitHub Pages などの固定URL
- `HASHTAGS` キャプション末尾のハッシュタグ
- `ENABLE_INSTAGRAM_PUBLISH` `1` で Instagram API 公開を実行
- `REQUIRE_PAID_PARTNERSHIP_LABEL` `1` なら自動公開前にガードをかける
- `ALLOW_PUBLISH_WITHOUT_PAID_PARTNERSHIP_API` ガードを手動解除する危険設定
- `SITE_SYNC_COMMAND` ローカルから push まで一気にやるコマンド
- `OPENAI_API_KEY` AI文章生成を有効にする場合のみ
- `OPENAI_MODEL` 使いたいモデル名

## 注意点

- Instagram API は画像URLが公開URLである必要があります。
- 楽天APIの `affiliateId` を付けるとレスポンスに `affiliateUrl` が含まれる前提です。
- 商品画像の取り扱いは楽天のルールに従ってください。
- Paid partnership label が必要な投稿かどうかは、毎回 Meta / Instagram 側の最新要件も確認してください。
