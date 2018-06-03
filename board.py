from flask import Flask, jsonify, request, redirect
from flask_pymongo import PyMongo
from flask_jwt import JWT, jwt_required, current_identity
from datetime import timedelta, datetime
from werkzeug.security import safe_str_cmp
from bson.objectid import ObjectId
from user import User
import validator


app = Flask(__name__)
app.debug = True
app.config['MONGO_HOST'] = 'ds053305.mlab.com'
app.config['MONGO_PORT'] = 53305
app.config['MONGO_DBNAME'] = 'adverts_board'
app.config['MONGO_USERNAME'] = 'adverts_admin'
app.config['MONGO_PASSWORD'] = 'qwerty1'

mongo = PyMongo(app)


def authenticate(username, password):
    user = User(mongo.db.Users.find_one({"login": username}))
    if user and safe_str_cmp(user.password.encode('utf-8'), password.encode('utf-8')):
        return user


def identity(payload):
    user_id = payload['identity']
    user = User(mongo.db.Users.find_one({"_id": ObjectId(user_id)}))
    return user


app.config['JWT_EXPIRATION_DELTA'] = timedelta(seconds=900)
app.config['SECRET_KEY'] = 'super-secret'
jwt = JWT(app, authenticate, identity)


@app.route('/register', methods=['POST'])
def register_new_user():
    if request.method == 'POST':
        post_data = request.get_json()
        print(post_data)
        
        if not validator.register_data(json_data=post_data):
            return jsonify({"user_id": 'None', "error": "you must provide a valid data"}), 400
        login = post_data['username']
        password = post_data['password']
        if not mongo.db.Users.find_one({'login': login }):
            user = {"login": login, "password": password}
            user_id = mongo.db.Users.insert_one(user).inserted_id
            return jsonify({"user_id" : str(user_id)}), 201
        else:
            return jsonify({"user_id": None, "error": "this username has already been taken"}), 409
        

@app.route('/adverts', methods=['GET', 'POST'])
@jwt_required()
def adverts():
    print(current_identity)
    if request.method == 'POST':
        post_data = request.get_json()
        print(post_data)
        if not validator.new_advert(post_data):
            return jsonify({"advert": 'None', "error": "you must provide a valid data"}), 400
        new_advert = {
            "data": post_data["data"],
            "creator_id": current_identity.id,
            "datetime": datetime.strftime(datetime.now(), "%Y-%m-%d %H:%M:%S"),
            "comments": []
        }
        advert_id = str(mongo.db.Adverts.insert_one(new_advert).inserted_id)
        return redirect('/adverts/%s' % advert_id)
    
    adverts_dict = []
    for advert in mongo.db.Adverts.find():
        advert["_id"] = str(advert["_id"])
        adverts_dict.append(advert)
    print(adverts_dict)
    if len(adverts_dict) > 0:
        return jsonify({"adverts": adverts_dict}), 200
    else:
        return jsonify({"adverts": "None"}), 404


@app.route('/adverts/<advert_id>', methods=['GET', 'POST'])
@jwt_required()
def get_one_advert_with_comments(advert_id):
    print(advert_id)
    if request.method == 'POST':
        post_data = request.get_json()
        if not validator.new_comment(post_data):
            return jsonify({"comment": 'None', "error": "you must provide a valid data"}), 400
        
        new_comment = {
            "text": post_data["data"],
            "creator_id": current_identity.id,
            "datetime": datetime.strftime(datetime.now(), "%Y-%m-%d %H:%M:%S"),
        }
        
        advert = mongo.db.Adverts.find_one({"_id": ObjectId(advert_id)})
        advert["comments"].append(new_comment)
        print(advert)
        mongo.db.Adverts.update({"_id": ObjectId(advert_id)}, advert)
        return redirect('/adverts/%s' % advert_id)
    
    advert = mongo.db.Adverts.find_one({"_id": ObjectId(advert_id)})
    advert["_id"] = str(advert["_id"])
    return jsonify({"advert": advert}), 200


if __name__ == '__main__':
    app.run()
