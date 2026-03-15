import os
import requests
from dotenv import load_dotenv

load_dotenv()

RAKUTEN_APP_ID = os.getenv("RAKUTEN_APP_ID")
RAKUTEN_ACCESS_KEY = os.getenv("RAKUTEN_ACCESS_KEY")
RAKUTEN_AFFILIATE_ID = os.getenv("RAKUTEN_AFFILIATE_ID")

if not RAKUTEN_APP_ID:
    raise ValueError("RAKUTEN_APP_ID が .env に入っていません。")

if not RAKUTEN_ACCESS_KEY:
    raise ValueError("RAKUTEN_ACCESS_KEY が .env に入っていません。")

if not RAKUTEN_AFFILIATE_ID:
    raise ValueError("RAKUTEN_AFFILIATE_ID が .env に入っていません。")

url = "https://openapi.rakuten.co.jp/ichibams/api/IchibaItem/Search/20220601"

params = {
    "applicationId": RAKUTEN_APP_ID,
    "accessKey": RAKUTEN_ACCESS_KEY,
    "affiliateId": RAKUTEN_AFFILIATE_ID,
    "keyword": "デスクライト",
    "hits": 1,
    "format": "json"
}

response = requests.get(url, params=params, timeout=20)

print("status_code:", response.status_code)
print("response_text:", response.text)

response.raise_for_status()

data = response.json()
items = data.get("Items", [])

if not items:
    print("商品が見つかりませんでした。")
else:
    item = items[0]["Item"]
    print("商品取得成功！")
    print("商品名:", item.get("itemName"))
    print("価格:", item.get("itemPrice"))
    print("商品URL:", item.get("itemUrl"))
    print("アフィリエイトURL:", item.get("affiliateUrl"))