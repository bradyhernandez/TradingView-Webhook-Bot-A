from flask import Flask, request, jsonify
import os
import alpaca_trade_api as tradeapi
import threading
import time
from queue import Queue

app = Flask(__name__)

# === ENV Variables ===
TOKEN = os.getenv("TOKEN")
USE_PASSPHRASE = os.getenv("USE_PASSPHRASE", "True") == "True"
DEBUG = os.getenv("DEBUG", "False") == "True"

APCA_API_KEY_ID = os.getenv("APCA_API_KEY_ID")
APCA_API_SECRET_KEY = os.getenv("APCA_API_SECRET_KEY")
APCA_API_BASE_URL = os.getenv("APCA_API_BASE_URL")

alpaca = tradeapi.REST(APCA_API_KEY_ID, APCA_API_SECRET_KEY, APCA_API_BASE_URL, api_version='v2')

# === Alert Queue ===
alert_queue = Queue()
processing = False

# === Background Queue Processor ===
def process_alerts():
    global processing
    while True:
        data = alert_queue.get()
        if data is None:
            break  # Allows clean shutdown if needed

        try:
            symbol = data['ticker']
            side = data['strategy'].lower()
            order = alpaca.submit_order(
                symbol=symbol,
                qty=50,
                side=side,
                type='market',
                time_in_force='gtc'
            )
            print(f"Order submitted: {side.upper()} {symbol}")
        except Exception as e:
            print("Order error:", e)
        time.sleep(3)  # Wait 3 seconds before processing next alert
        alert_queue.task_done()

# Start background processor thread
threading.Thread(target=process_alerts, daemon=True).start()

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
        # Validate required fields
        symbol = data['ticker']
        side = data['strategy'].lower()
    except KeyError:
        return jsonify({'code': 'error', 'message': 'Missing required fields'}), 400

    # Add alert to queue
    alert_queue.put(data)

    return jsonify({'code': 'success', 'message': 'Order queued for processing'}), 200

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
