from flask import Flask, request, jsonify
from playwright.sync_api import sync_playwright
from pytesseract import image_to_string
from PIL import Image
from io import BytesIO
import re
import statistics
import datetime

app = Flask(__name__)

def calculate_price_stats(prices):
    if not prices:
        return {
            'average': 0,
            'median': 0,
            'min': 0,
            'max': 0,
            'count': 0
        }

    return {
        'average': round(statistics.mean(prices), 2),
        'median': round(statistics.median(prices), 2),
        'min': min(prices),
        'max': max(prices),
        'count': len(prices)
    }

def auto_scroll(page):
    page.evaluate("""
        async () => {
            await new Promise(resolve => {
                let totalHeight = 0;
                const distance = 400;
                const timer = setInterval(() => {
                    window.scrollBy(0, distance);
                    totalHeight += distance;
                    if (totalHeight >= document.body.scrollHeight - window.innerHeight) {
                        clearInterval(timer);
                        resolve();
                    }
                }, 200);
            });
        }
    """)

def get_prices_from_text(text):
    matches = re.findall(r'R\s?(\d{1,3}(?:,\d{3})*(?:\.\d{1,2})?)', text)
    prices = [float(p.replace(',', '')) for p in matches if p]
    return [p for p in prices if p > 0]

def get_screenshot_and_extract_prices(search_term):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        url = f'https://www.takealot.com/all?qsearch={search_term}'
        page.goto(url, timeout=60000)

        # Try to accept cookies
        try:
            page.click('button[class*="cookie"]', timeout=3000)
        except:
            pass

        auto_scroll(page)

        # Take screenshot
        screenshot_bytes = page.screenshot(full_page=True)
        image = Image.open(BytesIO(screenshot_bytes))

        # OCR
        raw_text = image_to_string(image)

        # Extract prices
        prices = get_prices_from_text(raw_text)
        stats = calculate_price_stats(prices)

        browser.close()

        return {
            'searchTerm': search_term,
            'timestamp': datetime.datetime.utcnow().isoformat(),
            'results': {
                'totalPricesFound': len(prices),
                'prices': prices,
                'stats': stats
            }
        }

@app.route('/api/prices', methods=['GET'])
def api_prices():
    search_term = request.args.get('search')
    if not search_term:
        return jsonify({'error': 'Search term is required'}), 400

    try:
        data = get_screenshot_and_extract_prices(search_term)
        return jsonify(data)
    except Exception as e:
        print("Error:", e)
        return jsonify({'error': 'Failed to process request', 'message': str(e)}), 500

if __name__ == '__main__':
    app.run(port=3000, debug=True)
