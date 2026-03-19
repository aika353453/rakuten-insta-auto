import os
import json
import math
import time
import requests
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

RAKUTEN_APP_ID = os.getenv("RAKUTEN_APP_ID")
RAKUTEN_ACCESS_KEY = os.getenv("RAKUTEN_ACCESS_KEY")
RAKUTEN_AFFILIATE_ID = os.getenv("RAKUTEN_AFFILIATE_ID")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

if not RAKUTEN_APP_ID:
    raise ValueError("RAKUTEN_APP_ID が .env に入っていません。")
if not RAKUTEN_ACCESS_KEY:
    raise ValueError("RAKUTEN_ACCESS_KEY が .env に入っていません。")
if not RAKUTEN_AFFILIATE_ID:
    raise ValueError("RAKUTEN_AFFILIATE_ID が .env に入っていません。")
if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY が .env に入っていません。")

client = OpenAI(api_key=OPENAI_API_KEY)

os.makedirs("data", exist_ok=True)
os.makedirs("out", exist_ok=True)
os.makedirs("images", exist_ok=True)

PRODUCTS_FILE = "data/products.json"
ITEMS_PER_PAGE = 20
KEYWORD_COUNT = 3
SEARCH_HITS_PER_KEYWORD = 2
MAX_NEW_PRODUCTS = 3


def generate_keywords() -> list[str]:
    prompt = """
Instagramで紹介しやすく、楽天で商品検索しやすい日本語キーワードを3個だけ作ってください。

条件:
- 季節イベントより「便利」「使いやすい」「買ってよかった」寄り
- 通年で使いやすい商品ジャンル
- 一人暮らし、デスク周り、収納、時短、生活改善、作業効率アップ系を優先
- 短く自然な日本語
- 1行に1キーワード
- 説明文不要
"""

    response = client.responses.create(
        model="gpt-5-mini",
        input=prompt,
    )

    text = response.output_text.strip()
    keywords = [line.strip("・- 　") for line in text.splitlines() if line.strip()]
    return keywords[:KEYWORD_COUNT]


def search_rakuten_items(keyword: str, hits: int = 2) -> list[dict]:
    url = "https://openapi.rakuten.co.jp/ichibams/api/IchibaItem/Search/20220601"

    params = {
        "applicationId": RAKUTEN_APP_ID,
        "accessKey": RAKUTEN_ACCESS_KEY,
        "affiliateId": RAKUTEN_AFFILIATE_ID,
        "keyword": keyword,
        "hits": hits,
        "format": "json",
        "sort": "-reviewCount",
        "availability": 1,
        "imageFlag": 1,
        "hasReviewFlag": 1,
    }

    headers = {
        "Referer": "https://aika353453.github.io/",
        "Origin": "https://aika353453.github.io",
    }

    max_retries = 3

    for attempt in range(max_retries):
        response = requests.get(url, params=params, headers=headers, timeout=20)

        if response.status_code == 429:
            wait_seconds = 5 + attempt * 3
            print(f"楽天APIが混み合っています: {keyword} / {wait_seconds}秒待機")
            time.sleep(wait_seconds)
            continue

        response.raise_for_status()
        data = response.json()
        return data.get("Items", [])

    print(f"楽天検索をスキップしました: {keyword}")
    return []


def download_image(image_url: str, item_code: str):
    if not image_url or not item_code:
        return None

    safe_name = item_code.replace(":", "_").replace("/", "_") + ".jpg"
    file_path = os.path.join("images", safe_name)

    if os.path.exists(file_path):
        return file_path

    try:
        response = requests.get(image_url, timeout=20)
        response.raise_for_status()

        with open(file_path, "wb") as f:
            f.write(response.content)

        return file_path
    except Exception as e:
        print(f"画像保存失敗: {item_code} / {e}")
        return None


def generate_post_text(product: dict, keyword: str) -> str:
    item_name = product.get("item_name", "")
    catchcopy = product.get("catchcopy", "")
    price = product.get("item_price", "")
    shop_name = product.get("shop_name", "")

    prompt = f"""
以下の商品をInstagramで紹介するための、短めで自然な投稿文案を日本語で作ってください。

条件:
- 3〜4文
- 宣伝くさすぎない
- どういう人向けかを入れる
- やさしい言い方
- 最後は「プロフィールのリンクから見れます」系で終える
- ハッシュタグ不要
- 絵文字なし

商品名: {item_name}
キャッチコピー: {catchcopy}
価格: {price}円
ショップ名: {shop_name}
検索キーワード: {keyword}
"""

    response = client.responses.create(
        model="gpt-5-mini",
        input=prompt,
    )
    return response.output_text.strip()


if os.path.exists(PRODUCTS_FILE):
    with open(PRODUCTS_FILE, "r", encoding="utf-8") as f:
        try:
            existing_products = json.load(f)
        except json.JSONDecodeError:
            existing_products = []
else:
    existing_products = []

existing_item_codes = {
    product.get("item_code")
    for product in existing_products
    if product.get("item_code")
}

keywords = generate_keywords()
print("AI検索キーワード:", keywords)

new_products = []

for keyword in keywords:
    try:
        items = search_rakuten_items(keyword, hits=SEARCH_HITS_PER_KEYWORD)
    except Exception as e:
        print(f"楽天検索失敗: {keyword} / {e}")
        continue

    for entry in items:
        if len(new_products) >= MAX_NEW_PRODUCTS:
            break

        item = entry["Item"]
        item_code = item.get("itemCode")

        if not item_code or item_code in existing_item_codes:
            continue

        medium_images = item.get("mediumImageUrls", [])
        image_url = medium_images[0].get("imageUrl") if medium_images else None
        local_image_path = download_image(image_url, item_code)

        product = {
            "item_code": item_code,
            "item_name": item.get("itemName"),
            "item_price": item.get("itemPrice"),
            "item_url": item.get("itemUrl"),
            "affiliate_url": item.get("affiliateUrl"),
            "shop_name": item.get("shopName"),
            "review_count": item.get("reviewCount"),
            "review_average": item.get("reviewAverage"),
            "catchcopy": item.get("catchcopy"),
            "image_url": image_url,
            "local_image_path": local_image_path,
            "source_keyword": keyword,
        }

        existing_item_codes.add(item_code)
        new_products.append(product)

    if len(new_products) >= MAX_NEW_PRODUCTS:
        break

    time.sleep(2)

all_products = existing_products + new_products

with open(PRODUCTS_FILE, "w", encoding="utf-8") as f:
    json.dump(all_products, f, ensure_ascii=False, indent=2)

cards_html = ""
for product in all_products:
    image_html = ""
    if product.get("image_url"):
        image_html = f'<img src="{product["image_url"]}" alt="{product["item_name"]}">'

    price_text = "価格未設定"
    if product.get("item_price") is not None:
        price_text = f'¥{product["item_price"]:,}'

    catchcopy = product.get("catchcopy") or ""
    shop_name = product.get("shop_name") or ""
    affiliate_url = product.get("affiliate_url") or "#"
    item_name = product.get("item_name") or "商品名なし"

    cards_html += f"""
    <div class="card product-card">
        {image_html}
        <h2>{item_name}</h2>
        <p class="price">{price_text}</p>
        <p class="catchcopy">{catchcopy}</p>
        <p class="shop">ショップ: {shop_name}</p>
        <a href="{affiliate_url}" target="_blank" rel="noopener noreferrer">楽天で見る</a>
    </div>
    """

total_pages = math.ceil(len(all_products) / ITEMS_PER_PAGE) if all_products else 1

html = f"""
<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>おすすめ商品まとめ</title>
    <style>
        body {{
            font-family: sans-serif;
            background: #f7f7f7;
            margin: 0;
            padding: 20px;
        }}
        h1 {{
            text-align: center;
            margin-bottom: 24px;
        }}
        .grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
            gap: 20px;
        }}
        .card {{
            background: white;
            border-radius: 12px;
            padding: 16px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.08);
        }}
        .card img {{
            width: 100%;
            border-radius: 8px;
            margin-bottom: 12px;
        }}
        .card h2 {{
            font-size: 16px;
            margin: 0 0 10px;
            line-height: 1.5;
        }}
        .price {{
            font-size: 20px;
            font-weight: bold;
            color: #d32f2f;
            margin: 8px 0;
        }}
        .catchcopy {{
            font-size: 14px;
            color: #444;
            margin: 8px 0;
        }}
        .shop {{
            font-size: 13px;
            color: #666;
            margin: 8px 0 16px;
        }}
        .card a {{
            display: inline-block;
            background: #bf0000;
            color: white;
            text-decoration: none;
            padding: 10px 14px;
            border-radius: 8px;
        }}
        .pagination {{
            margin-top: 30px;
            display: flex;
            justify-content: center;
            gap: 8px;
            flex-wrap: wrap;
        }}
        .pagination button {{
            border: none;
            background: white;
            padding: 10px 14px;
            border-radius: 8px;
            cursor: pointer;
            box-shadow: 0 2px 6px rgba(0,0,0,0.08);
        }}
        .pagination button.active {{
            background: #bf0000;
            color: white;
        }}
        .hidden {{
            display: none;
        }}
    </style>
</head>
<body>
    <h1>おすすめ商品まとめ</h1>
    <div id="product-list" class="grid">
        {cards_html}
    </div>
    <div id="pagination" class="pagination"></div>

    <script>
        const itemsPerPage = {ITEMS_PER_PAGE};
        const cards = Array.from(document.querySelectorAll(".product-card"));
        const pagination = document.getElementById("pagination");
        const totalPages = Math.ceil(cards.length / itemsPerPage);

        function showPage(page) {{
            const start = (page - 1) * itemsPerPage;
            const end = start + itemsPerPage;

            cards.forEach((card, index) => {{
                if (index >= start && index < end) {{
                    card.classList.remove("hidden");
                }} else {{
                    card.classList.add("hidden");
                }}
            }});

            const buttons = pagination.querySelectorAll("button");
            buttons.forEach((btn, index) => {{
                if (index + 1 === page) {{
                    btn.classList.add("active");
                }} else {{
                    btn.classList.remove("active");
                }}
            }});
        }}

        function createPagination() {{
            pagination.innerHTML = "";
            if (totalPages <= 1) return;

            for (let i = 1; i <= totalPages; i++) {{
                const button = document.createElement("button");
                button.textContent = i;
                button.addEventListener("click", () => showPage(i));
                pagination.appendChild(button);
            }}
        }}

        createPagination();
        showPage(1);
    </script>
</body>
</html>
"""

with open("index.html", "w", encoding="utf-8") as f:
    f.write(html)

post_lines = []
for i, product in enumerate(new_products, start=1):
    try:
        post_text = generate_post_text(product, product.get("source_keyword", ""))
    except Exception as e:
        post_text = f"投稿文生成失敗: {e}"

    price_text = "価格未設定"
    if product.get("item_price") is not None:
        price_text = f'{product["item_price"]:,}円'

    post_lines.append(
        f"""【候補{i}】
商品名: {product.get("item_name", "")}
価格: {price_text}
検索キーワード: {product.get("source_keyword", "")}
ショップ: {product.get("shop_name", "")}
アフィリエイトURL: {product.get("affiliate_url", "")}
画像URL: {product.get("image_url", "")}
保存画像: {product.get("local_image_path", "")}

投稿文案:
{post_text}

----------------------------------------
"""
    )

with open("out/post_candidates.txt", "w", encoding="utf-8") as f:
    f.write("\n".join(post_lines))

print("products.json を更新しました！")
print("index.html を更新しました！")
print("out/post_candidates.txt を出力しました！")
print(f"AIキーワード数: {len(keywords)}")
print(f"既存商品数: {len(existing_products)}")
print(f"新しく追加した商品数: {len(new_products)}")
print(f"合計商品数: {len(all_products)}")
print(f"ページ数: {total_pages}")