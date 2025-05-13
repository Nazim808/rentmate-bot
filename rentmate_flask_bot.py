
from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse
import os
import uuid

app = Flask(__name__)

# In-memory store (for prototype)
items_for_rent = []
active_rentals = {}
users = {}
user_sessions = {}

@app.route("/webhook", methods=['POST'])
def webhook():
    incoming_msg = request.values.get('Body', '').strip()
    sender = request.values.get('From')
    media_url = request.values.get('MediaUrl0')
    resp = MessagingResponse()
    msg = resp.message()

    # Ensure sender is tracked
    if sender not in users:
        users[sender] = {'id': str(uuid.uuid4()), 'name': sender.split(':')[-1], 'history': []}

    users[sender]['history'].append(incoming_msg)

    if sender in user_sessions:
        session = user_sessions[sender]
        if session['step'] == 'awaiting_image':
            if media_url:
                session['item']['image'] = media_url
                items_for_rent.append(session['item'])
                msg.body(f"✅ Listed '{session['item']['item']}' for ₹{session['item']['price']}/day with photo.")
                del user_sessions[sender]
            else:
                msg.body("❗ Please attach an image for the item.")
            return str(resp)

    command = incoming_msg.lower().split()[0]

    if command == "help":
        msg.body("""✉️ RentMate Help Menu:
- list <item> <price>
- view
- rent <item_number>
- myrentals
- return <item_number>
- myid
- help
        """)

    elif command == "list":
        try:
            _, item, price = incoming_msg.split(" ", 2)
            user_sessions[sender] = {
                'step': 'awaiting_image',
                'item': {"item": item, "price": price, "owner": sender, "image": None}
            }
            msg.body(f"📸 Please send an image of the '{item}' to complete the listing.")
        except:
            msg.body("❗ Usage: list <item> <price>")

    elif command == "view":
        if not items_for_rent:
            msg.body("😕 No items available for rent.")
        else:
            for idx, itm in enumerate(items_for_rent, 1):
                message = f"📦 {idx}. {itm['item']} - ₹{itm['price']}/day"
                item_msg = resp.message(message)
                if itm.get('image'):
                    item_msg.media(itm['image'])

    elif command == "rent":
        try:
            index = int(incoming_msg.split()[1]) - 1
            if 0 <= index < len(items_for_rent):
                rental = items_for_rent.pop(index)
                if sender not in active_rentals:
                    active_rentals[sender] = []
                active_rentals[sender].append(rental)
                msg.body(f"🎉 You have rented '{rental['item']}' successfully!")
            else:
                msg.body("❗ Invalid item number.")
        except:
            msg.body("❗ Usage: rent <item_number>")

    elif command == "myrentals":
        rentals = active_rentals.get(sender, [])
        if not rentals:
            msg.body("📝 You have no active rentals.")
        else:
            summary = "📄 Your Rentals:\n"
            for idx, r in enumerate(rentals, 1):
                summary += f"{idx}. {r['item']} - ₹{r['price']}/day\n"
            msg.body(summary)

    elif command == "return":
        try:
            index = int(incoming_msg.split()[1]) - 1
            rentals = active_rentals.get(sender, [])
            if 0 <= index < len(rentals):
                returned = rentals.pop(index)
                msg.body(f"✅ '{returned['item']}' has been marked as returned.")
            else:
                msg.body("❗ Invalid item number.")
        except:
            msg.body("❗ Usage: return <item_number>")

    elif command == "myid":
        msg.body(f"🆔 Your RentMate ID: {users[sender]['id']}")

    else:
        msg.body("Unrecognized command. Type 'help' for options.")

    return str(resp)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
