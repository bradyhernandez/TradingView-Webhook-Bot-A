from flask import Flask, request, jsonify
import os
import alpaca_trade_api as tradeapi

app = Flask(__name__)

# Load ENV vars
TOKEN = os.getenv("TOKEN")
USE_PASSPHRASE = os.getenv("USE_PASSPHRASE", "True") == "True"
DEBUG = os.getenv("DEBUG", "False") == "True"

APCA_API_KEY_ID = os.getenv("APCA_API_KEY_ID")
APCA_API_SECRET_KEY = os.getenv("APCA_API_SECRET_KEY")
APCA_API_BASE_URL = os.getenv("APCA_API_BASE_URL")

alpaca = tradeapi.REST(APCA_API_KEY_ID, APCA_API_SECRET_KEY, APCA_API_BASE_URL, api_version='v2')


@app.route('/')
def home():
    return 'TradingView Webhook Bot is online.'


@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.get_json()

    if DEBUG:
        print("Webhook received:", data)

    if USE_PASSPHRASE:
        if data.get("passphrase") != TOKEN:
            return jsonify({'code': 'error', 'message': 'Invalid passphrase'}), 403

    try:
        symbol = data['ticker']
        side = data['strategy'].lower()  # "buy" or "sell"
    except KeyError:
        return jsonify({'code': 'error', 'message': 'Missing required fields'}), 400

    try:
        order = alpaca.submit_order(
            symbol=symbol,
            qty=1,  # You can customize this as needed
            side=side,
            type='market',
            time_in_force='gtc'
        )
        print(f"Order submitted: {side.upper()} {symbol}")
        return jsonify({'code': 'success', 'message': f'{side} order executed for {symbol}'}), 200
    except Exception as e:
        print("Order error:", e)
        return jsonify({'code': 'error', 'message': str(e)}), 500


if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
