from flask import Flask, request, jsonify
import requests
from bs4 import BeautifulSoup
import re

app = Flask(__name__)

@app.route("/api/prices", methods=["GET"])
def get_prices():
    search = request.args.get("search")
    if not search:
        return jsonify({"error": "Search term is required"}), 400

    url = f"https://www.takealot.com/all?qsearch={search}"
    headers = {
        "User-Agent": "Mozilla/5.0"
    }

    try:
        response = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.text, "html.parser")

        # You may need to inspect Takealot's site structure for actual selectors
        text = soup.get_text()

        # Extract R prices like "R 1,299.00"
        matches = re.findall(r'R\s?(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)', text)
        prices = [float(p.replace(',', '')) for p in matches if p]

        if not prices:
            return jsonify({"message": "No prices found", "searchTerm": search})

        return jsonify({
            "searchTerm": search,
            "results": {
                "totalPricesFound": len(prices),
                "prices": prices,
                "stats": calculate_stats(prices)
            }
        })

    except Exception as e:
        return jsonify({"error": "Failed to fetch or process page", "details": str(e)}), 500

def calculate_stats(prices):
    prices.sort()
    count = len(prices)
    total = sum(prices)
    average = round(total / count, 2)
    median = round((prices[count // 2] if count % 2 else (prices[count // 2 - 1] + prices[count // 2]) / 2), 2)
    return {
        "average": average,
        "median": median,
        "min": prices[0],
        "max": prices[-1],
        "count": count
    }

if __name__ == "__main__":
    app.run(debug=True)
