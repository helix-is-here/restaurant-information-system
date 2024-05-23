from logic.analytics_collector import AnalyticsCollector
from logic.order_creator import OrderCreator
from logic.order_mediator import OrderMediator
from logic.order_parser import OrderParser
from logic.order_notifier import OrderNotifier
from db.db_access import DBAccess

from flask import Flask, jsonify, request
from flask_cors import CORS
from datetime import datetime

db_access = DBAccess()
analytics_collector = AnalyticsCollector(db_access=db_access)
order_creator = OrderCreator()
order_parser = OrderParser()
order_notifer = OrderNotifier()

order_mediator = OrderMediator(order_parser=order_parser, 
                                order_creator=order_creator,
                                order_notifier=order_notifer,
                                analytics_collector=analytics_collector)

app = Flask(__name__)
CORS(app)

@app.route("/")
def hello_world():
    return "<p>Hello, World</p>"

@app.route("/api/login/<username>/<password>")
def authenticate_user(username, password):
    db_access = DBAccess()
    db_access.connect()

    query = "SELECT Username FROM account WHERE Username=%s AND PassWord=%s"
    values = (username, password)

    result = db_access.make_query(query=query, values=values)

    if result and len(result) == 1:
        data = {
            "username": result[0][0]
        }
        return jsonify(data), 200

    data = {
        "err": "couldn't find a exact match for your credentials"
    }
    return jsonify(data), 404

# There is definitely a problem with the database tables wise, but for now this should work for the reservation stuff 
@app.route("/api/reservation/create", methods=['POST'])
def create_reservation():
    data = None

    if request.is_json:
        data = request.json

    if not data:
        return jsonify({"error": "Request body must be in JSON format"}), 400

    db_access = DBAccess()

    db_access.connect()

    conn = db_access.retrieve_connection()

    cursor = conn.cursor()

    return_data = {}

    try:
        conn.start_transaction()
        query = "INSERT INTO reservation (ResDate, ResTime) VALUES (%s, %s)"
        structured_res_date = datetime.strptime(data["reservationDate"], "%d-%m-%Y")
        values = (structured_res_date, data["resTime"])
        cursor.execute(query, values)
        reservation_id = cursor.lastrowid
        conn.commit()
        db_access.disconnect()
        return_data["reservation_id"] = reservation_id
    except Exception as e:
        print("ERROR HAS OCCURRED: ", e)
        return jsonify({"err": "We had an error with the server"}), 500

    return jsonify(return_data), 200

@app.route("/api/reservation/delete", methods=['DELETE'])
def delete_reservation():
    data = None

    if request.is_json:
        data = request.json

    if not data:
        return jsonify({"error": "Request body must be in JSON format"}), 400

    db_access = DBAccess()

    db_access.connect()

    conn = db_access.retrieve_connection()

    cursor = conn.cursor()

    try:
        conn.start_transaction()
        query = "DELETE FROM reservation WHERE ReservationID = %s"
        values = [data["reservationId"]]
        cursor.execute(query, values)
        conn.commit()
        db_access.disconnect()
    except Exception as e:
        print("ERROR HAS OCCURRED: ", e)
        return jsonify({"err": "We had an error with the server"}), 500

    return jsonify({"success": "Reservation deleted"}), 200

@app.route("/api/reservation/<reservation_id>")
def get_reservation(reservation_id):
    db_access = DBAccess()

    db_access.connect()

    conn = db_access.retrieve_connection()

    cursor = conn.cursor()

    response_data = None

    try:
        conn.start_transaction()
        query = "SELECT * FROM reservation WHERE ReservationID = %s"
        values = [reservation_id]
        cursor.execute(query, values)
        response_data = cursor.fetchall()
        conn.commit()
        db_access.disconnect()
    except Exception as e:
        print("ERROR HAS OCCURRED: ", e)
        return jsonify({"err": "We had an error with the server"}), 500

    if not response_data:
        return jsonify({"error": "Request body must be in JSON format"}), 404

    reservation_date = response_data[0][1].strftime("%d-%m-%Y")
    return_data = {
        "id": response_data[0][0],
        "reservationDate": reservation_date,
        "reservationTime": response_data[0][2]
    }
    return jsonify(return_data), 200

@app.route("/api/menu/create-item", methods=["POST"])
def create_menu_item():
    data = None

    if request.is_json:
        data = request.json

    if not data:
        return jsonify({"error": "Request body must be in JSON format"}), 400

    db_access = DBAccess()

    db_access.connect()

    conn = db_access.retrieve_connection()

    cursor = conn.cursor()

    try:
        conn.start_transaction()
        query = "INSERT INTO menuitem (Name, Description, Price, NutritionInfo, MenuStatus) VALUES (%s, %s, %s, %s, 1)"
        values = [data['name'], data['description'], data['price'], data['nutritionInfo']]
        cursor.execute(query, values)
        conn.commit()
        db_access.disconnect()
    except Exception as e:
        print("ERROR HAS OCCURRED: ", e)
        return jsonify({"err": "We had an error with the server"}), 500

    return jsonify({"success": "Item added"}), 200

@app.route("/api/menu/get-menu")
def get_full_menu():

    db_access = DBAccess()

    db_access.connect()

    conn = db_access.retrieve_connection()

    cursor = conn.cursor()

    data = {
        "menu": []
    }

    try:
        conn.start_transaction()
        query = "SELECT * FROM menuitem"
        cursor.execute(query)
        response_data = cursor.fetchall()
        for menu_item in response_data:
            currently_on_menu = lambda x: True if x == 1 else False
            item = {
                "id": menu_item[0],
                "name": menu_item[1],
                "description": menu_item[2],
                "price": menu_item[3],
                "nutritionInfo": menu_item[4],
                "menuStatus": currently_on_menu(menu_item[5])
            }
            data["menu"].append(item)

        conn.commit()
        db_access.disconnect()
    except Exception as e:
        print("ERROR HAS OCCURRED: ", e)
        return jsonify({"err": "We had an error with the server"}), 500

    return jsonify(data), 200

@app.route("/api/menu/remove-item-from-active-menu", methods=["PUT"])
def remove_item_from_active_menu():
    data = None

    if request.is_json:
        data = request.json

    if not data:
        return jsonify({"error": "Request body must be in JSON format"}), 400

    db_access = DBAccess()

    db_access.connect()

    conn = db_access.retrieve_connection()

    cursor = conn.cursor()

    try:
        conn.start_transaction()
        query = "UPDATE menuItem SET MenuStatus = 0 WHERE MenuItemID = %s"
        values = [data["menuItem"]]
        cursor.execute(query, values)
        conn.commit()
        db_access.disconnect()
    except Exception as e:
        print("ERROR HAS OCCURRED: ", e)
        return jsonify({"err": "We had an error with the server"}), 500

    return jsonify({"success": "Menu Item updated"}), 200
    
@app.route("/api/menu/add-item-to-active-menu", methods=["PUT"])
def add_item_to_active_menu():
    data = None

    if request.is_json:
        data = request.json

    if not data:
        return jsonify({"error": "Request body must be in JSON format"}), 400

    db_access = DBAccess()

    db_access.connect()

    conn = db_access.retrieve_connection()

    cursor = conn.cursor()

    try:
        conn.start_transaction()
        query = "UPDATE menuItem SET MenuStatus = 1 WHERE MenuItemID = %s"
        values = [data["menuItem"]]
        cursor.execute(query, values)
        conn.commit()
        db_access.disconnect()
    except Exception as e:
        print("ERROR HAS OCCURRED: ", e)
        return jsonify({"err": "We had an error with the server"}), 500

    return jsonify({"success": "Menu Item updated"}), 200

@app.route("/api/order/create", methods=["POST"])
def create_order():
    data = None

    if request.is_json:
        data = request.json

    if not data:
        return jsonify({"error": "Request body must be in JSON format"}), 400

    print(data)

    # Need to implement the following when able to:
    # Go to order creator to "confirm payment"
    # return success
    # Need to figure out how to get the order to still be sent to be built and the rest of the stuff that is needed, maybe some async thingy?

    return jsonify({"success": "Order was created"}), 200

# This is an example of how to add routes + how to use the currently configured shitty database code. IT WILL CHANGE DEFINITELY YEP. (but please don't use it, it will spam the tables with duplicate data)
# @app.route("/test4")
# def test():
#     db_access = DBAccess()
#     db_access.connect()
#     query = 'INSERT INTO TableSeating (TableNum, OccupiedStatus) VALUES (%s, %s)'
#     data_query = (2, 1)
#     db_access.make_query(query, data_query)

#     return {
#         "test": 1
#     }