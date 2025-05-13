from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse
import os

app = Flask(__name__)

# In-memory store for demonstration
items_for_rent = []
active_rentals = []

@app.route("/webhook", methods=['POST'])
def webhook():
    incoming_msg = request.values.get('Body', '').strip().lower()
    resp = MessagingResponse()
    msg = resp.message()

    if incoming_msg.startswith("list"):
        parts = incoming_msg.split(" ", 2)
        if len(parts) >= 3:
            item = parts[1]
            price = parts[2]
            items_for_rent.append({"item": item, "price": price})
            msg.body(f"✅ Your item '{item}' has been listed for ₹{price}/day.")
        else:
            msg.body("❗Usage: list <item> <price>")
    elif incoming_msg == "view":
        if not items_for_rent:
            msg.body("😕 No items available for rent right now.")
        else:
            response = "📦 Available Items:\n"
            for i, itm in enumerate(items_for_rent, 1):
                response += f"{i}. {itm['item']} – ₹{itm['price']}/day\n"
            msg.body(response)
    elif incoming_msg.startswith("rent"):
        try:
            index = int(incoming_msg.split(" ")[1]) - 1
            if 0 <= index < len(items_for_rent):
                rental = items_for_rent.pop(index)
                active_rentals.append(rental)
                msg.body(f"🎉 You have rented '{rental['item']}' successfully!")
            else:
                msg.body("❗Invalid item number.")
        except:
            msg.body("❗Usage: rent <item_number>")
    elif incoming_msg == "status":
        if not active_rentals:
            msg.body("📭 You have no active rentals.")
        else:
            summary = "📋 Your Active Rentals:\n"
            for i, r in enumerate(active_rentals, 1):
                summary += f"{i}. {r['item']} – ₹{r['price']}/day\n"
            msg.body(summary)
    else:
        msg.body("👋 Welcome to RentMate!\nCommands:\n- list <item> <price>\n- view\n- rent <item_number>\n- status")

    return str(resp)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)

