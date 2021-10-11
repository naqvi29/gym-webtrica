import re
import os
from os.path import join, dirname, realpath
from sys import meta_path
from pymongo.message import query
from werkzeug.utils import secure_filename
from bson import objectid
from flask import Flask, render_template, request, url_for, jsonify, json, send_file, send_from_directory
import json
import pymongo
from bson.objectid import ObjectId
from bson.json_util import dumps
from werkzeug.utils import redirect
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)

# MONGOGB DATABASE CONNECTION
connection_url = "mongodb://localhost:27017/"
client = pymongo.MongoClient(connection_url)
client.list_database_names()
database_name = "fitness-app"
db = client[database_name]

# USER IMAGES UPLOAD FOLDER
UPLOAD_FOLDER = join(dirname(realpath(__file__)), 'static/images/certificates')
UPLOAD_FOLDER2 = join(dirname(realpath(__file__)), 'static/images/customers/profile-pics')
UPLOAD_FOLDER3 = join(dirname(realpath(__file__)), 'static/images/company/company-profile-pics')
UPLOAD_FOLDER4 = join(dirname(realpath(__file__)), 'static/images/trainers/trainer-profile-pics')
UPLOAD_FOLDER5 = join(dirname(realpath(__file__)), 'static/images/customers/mud-schemes')
ALLOWED_EXTENSIONS = {'pdf', 'png', 'jpg', 'jpeg',}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['UPLOAD_FOLDER2'] = UPLOAD_FOLDER2
app.config['UPLOAD_FOLDER3'] = UPLOAD_FOLDER3
app.config['UPLOAD_FOLDER4'] = UPLOAD_FOLDER4
app.config['UPLOAD_FOLDER5'] = UPLOAD_FOLDER5


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


# configure secret key for session
app.secret_key = '_5#y2L"F4Q8z\n\xec]/'


# Homepage route
@app.route("/")
def index():
    # return render_template("home.html")
    return render_template("index.html")


# Dashboard route
@app.route("/dashboard")
def dashboard():
    return render_template("dashboard.html")


# Edit accounts route
@app.route('/edit/<cat>-<id>', methods=['GET', 'POST'])
def edit(cat, id):
    if request.method == 'GET':
        # fetch data which will edit
        query = {'_id': ObjectId(id)}
        edit = db[cat].find_one(query)
        return render_template("edit.html", edit=edit, cat=cat, id=id)
    else:
        email = request.form.get("email")
        phone = request.form.get("phone")
        password = request.form.get("password")
        # Replace Updated data in database
        newvalues = {
            "$set": {
                'email': email,
                'phone': phone,
                'password': password
            }
        }
        filter = {'_id': ObjectId(id)}
        db[cat].update_one(filter, newvalues)
        return redirect(url_for(cat))


# Delete accounts route
@app.route('/delete/<cat>-<id>')
def delete(cat, id):
    # delete data
    query = {'_id': ObjectId(id)}
    db[cat].delete_one(query)
    return redirect(url_for(cat))


# View new signedin accounts route
@app.route('/newaccounts')
def newaccounts():
    # fetch recent 2 documents from customers collection
    customers = db.customers.find().sort('_id', -1).limit(2)
    # fetch recent 2 documents from company collection
    company = db.company.find().sort('_id', -1).limit(2)
    # fetch recent 2 documents from trainers collection
    trainers = db.trainers.find().sort('_id', -1).limit(2)
    return render_template("newaccounts.html",
                           customers=customers,
                           company=company,
                           trainers=trainers)


# View customers route
@app.route('/customers')
def customers():
    # fetch data from customers table
    customers = db.customers.find()
    return render_template("customers.html", customers=customers)


# View companies route
@app.route('/company')
def company():
    # fetch data from company table
    company = db.company.find()
    return render_template("company.html", company=company)


# View trainers route
@app.route('/trainers')
def trainers():
    # fetch data from trainers table
    trainers = db.trainers.find()
    return render_template("trainers.html", trainers=trainers)


# route for view trainer's certificate
@app.route('/certificate/<certificatename>')
def viewcertificate(certificatename):
    return render_template('certificate.html', certificatename=certificatename)


# Add new account route
@app.route('/addnew/<cat>', methods=['GET', 'POST'])
def addnew(cat):
    if request.method == 'POST':
        name = request.form.get("name")
        email = request.form.get("email")
        phone = request.form.get("phone")
        password = request.form.get("password")
        hash_password = generate_password_hash(password)
        address = request.form.get("address")
        # Insert into db
        newAccount = {
            "name": name,
            "email": email,
            "phone": phone,
            "password": password,
            "hash": hash_password,
            "address": address
        }
        db[cat].insert_one(newAccount)
        return redirect(url_for(cat))
    else:
        return render_template('addnew.html', cat=cat)


# View completed sessions route
@app.route('/completed-sessions')
def completed_sessions():
    # fetch data from sessions table
    sessions = db.sessions.find()
    return render_template("sessions.html", sessions=sessions)



################################################ API START ##########################################################
 
# ************ FOR CUSTOMERS/USERS SIGNUP ************
@app.route("/signup-api", methods=["POST"])
def signup_api():
    try:
        if request.method == "POST":
                email = request.form.get('email').lower()
                import re
                regex = '[^@]+@[a-zA-Z0-9]+[.][a-zA-Z]+'
                if not (re.search(regex, email)):
                    return jsonify({
                        "success": False,
                        "error": "invalid email"
                    })
                first_name = request.form.get('first_name')
                last_name = request.form.get('last_name')
                contact = request.form.get('contact')
                profile_pic = request.files.get('profile_pic')
                password = request.form.get('password')
                
                if not first_name or not last_name or not contact or not password:
                    return jsonify({"success": False, "error": "Missing details"})
                    
                if profile_pic and allowed_file(profile_pic.filename):
                    filename = secure_filename(profile_pic.filename)
                    profile_pic.save(
                        os.path.join(app.config['UPLOAD_FOLDER2'], filename))
                else:
                    return jsonify({
                        "success": False,
                        "error": "File not found or incorrect format"
                    })
                    
                query = {"email": email}
                user_data1 = db.customers.find_one(query)
                user_data2 = db.company.find_one(query)
                user_data3 = db.trainers.find_one(query)
                if user_data1 is None and user_data2 is None and user_data3 is None:
                    hash_password = generate_password_hash(password)
                    # Insert into db
                    newAccount = {
                        "email": email,
                        "first_name": first_name,
                        "last_name": last_name,
                        "phone": contact,
                        "password": password,
                        "hash": hash_password,
                        "profile_pic": filename
                    }
                    userid = db.customers.insert_one(newAccount).inserted_id
                    return jsonify({
                        "first_name": first_name,
                        "last_name": last_name,
                        "email": email,
                        "contact": contact,
                        "profile_pic": filename,
                        "success": True,
                    })
                else:
                    return jsonify({
                        "success":
                        False,
                        "error":
                        "User already exist with this email id."
                    })
            
        else:
            return jsonify({"success": False, "error": "Invalid request"})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})


# ************ FOR COMPANY SIGNUP ************
@app.route("/companysignup-api", methods=["POST"])
def companysignup_api():
    try:
        if request.method == "POST":
            organizational_number = request.form.get("organizational_number")
            company_name = request.form.get("company_name")
            contact_person = request.form.get("contact_person")
            region = request.form.get("region")
            company_profile_pic = request.files.get('company_profile_pic')
            email = request.form.get('email').lower()
            import re
            regex = '[^@]+@[a-zA-Z0-9]+[.][a-zA-Z]+'
            if not (re.search(regex, email)):
                return jsonify({
                    "success": False,
                    "error": "invalid email"
                })
            contact = request.form.get("contact")
            password = request.form.get("password")
            if company_profile_pic and allowed_file(company_profile_pic.filename):
                    filename = secure_filename(company_profile_pic.filename)
                    company_profile_pic.save(
                        os.path.join(app.config['UPLOAD_FOLDER3'], filename))
            else:
                return jsonify({
                    "success": False,
                    "error": "File not found or incorrect format"
                })
            confirm_password = request.form.get("confirm_password")
            if password != confirm_password:
                return jsonify({
                    "success": False,
                    "error": "password doesn't match"
                })
            
            if not organizational_number or not company_name or not contact_person or not region or not contact:
                    return jsonify({"success": False, "error": "Missing details"})
            query = {"email": email}
            user_data1 = db.company.find_one(query)
            user_data2 = db.trainers.find_one(query)
            user_data3 = db.customers.find_one(query)
            if user_data1 is None and user_data2 is None and user_data3 is None:
                hash_password = generate_password_hash(password)
                # Insert into db
                newAccount = {
                    "organizational_number": organizational_number,
                    "company_name": company_name,
                    "contact_person": contact_person,
                    "email": email,
                    "phone": contact,
                    "company_profile_pic": filename,
                    "password": password,
                    "hash": hash_password,
                    "region": region
                }
                db.company.insert_one(newAccount)
                return jsonify({
                    "organizaional_number": organizational_number,
                    "company_name": company_name,
                    "email": email,
                    "contact": contact,
                    "company_profile_pic": filename,
                    "success": True,
                })
            else:
                return jsonify({
                    "success":
                    False,
                    "error":
                    "User already exist with this email id."
                })
            
        else:
            return jsonify({"success": False, "error": "Invalid request"})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})


# ************ FOR PERSONAL TRAINERS SIGNUP ************
@app.route("/trainersignup-api", methods=["POST"])
def trainersignup_api():
    try:
        if request.method == "POST":
            # contact_person = request.form.get('contact_person')
            first_name = request.form.get('first_name')
            last_name = request.form.get('last_name')
            region = request.form.get('region')
            email = request.form.get('email').lower()
            certificates = request.files.getlist("certificate")
            filenames = []
            for certificate in certificates:
                if certificate and allowed_file(certificate.filename):
                    filename = secure_filename(certificate.filename)
                    print (filename)
                    certificate.save(
                        os.path.join(app.config['UPLOAD_FOLDER'], filename))
                    filename=filenames.append(filename)  
                else:
                    return jsonify({
                        "success": False,
                        "error": "Certificate not found or incorrect format"
                    })
            trainer_profile_pic = request.files.get('trainer_profile_pic')
            if trainer_profile_pic and allowed_file(trainer_profile_pic.filename):
                    filename2 = secure_filename(trainer_profile_pic.filename)
                    trainer_profile_pic.save(
                        os.path.join(app.config['UPLOAD_FOLDER4'], filename2))
            else:
                return jsonify({
                    "success": False,
                    "error": "Profile Picture not found or incorrect format"
                })
            regex = '[^@]+@[a-zA-Z0-9]+[.][a-zA-Z]+'
            if not (re.search(regex, email)):
                return jsonify({"success": False, "error": "invalid email"})
            contact = request.form.get('contact')
            password = request.form.get('password')
            confirm_password = request.form.get('confirm_password')
            if password != confirm_password:
                return jsonify({
                    "success": False,
                    "error": "password doesn't match"
                })
            
            
            if not first_name or not last_name or not region or not contact:
                    return jsonify({"success": False, "error": "Missing details"})
            query = {"email": email}
            user_data1 = db.trainers.find_one(query)
            user_data2 = db.company.find_one(query)
            user_data3 = db.customers.find_one(query)
            if user_data1 is None and user_data2 is None and user_data3 is None:
                hash_password = generate_password_hash(password)
                # Insert into db
                newAccount = {
                    # "contact_person": contact_person,
                    "first_name": first_name,
                    "last_name": last_name,
                    "email": email,
                    "phone": contact,
                    "password": password,
                    "hash": hash_password,
                    "region": region,                    
                    "profile_pic": filename2,
                    "certificate": filenames,
                }
                db.trainers.insert_one(newAccount)
                return jsonify({
                    "email": email,
                    "first_name": first_name,
                    "last_name": last_name,
                    # "contact_person": contact_person,
                    "contact": contact,
                    "success": True,
                })
            else:
                return jsonify({
                    "success":
                    False,
                    "error":
                    "User already exist with this email id."
                })
        else:
            return jsonify({"success": False, "error": "Invalid request"})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})


# ************ FOR ALL PERSONAL TRAINERS DETAILS ************
@app.route("/all-trainers-details-api", methods=["GET"])
def alltrainerdetails_api():
    try:
        if request.method == "GET":
            trainersdata = db.trainers.find({"status":"activated"}, {"password": 0, "hash": 0})
            lists = []
            for i in trainersdata:
                i.update({"_id": str(i["_id"])})
                lists.append(i)
                print(lists, "hello")
            return jsonify({"success": True, "trainersdata": lists})
        else:
            return jsonify({"success": False, "msg": "Invalid request method"})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

# ************ FOR ALL CUSTOMERS/USERS DETAILS ************
@app.route("/all-customers-details-api", methods=["GET"])
def all_customer_details():
    try:
        if request.method == "GET":
            customers_data = db.customers.find({}, {"password": 0, "hash": 0})
            lists = []
            for i in customers_data:
                i.update({"_id": str(i["_id"])})
                lists.append(i)
                print(lists)
            return jsonify({"success": True, "customers data": lists})
        else:
            return jsonify({"success": False, "msg": "Invalid request method"})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})


# ************ FOR UPDATE CUSTOMERS PROFILE************
@app.route("/update-customer-profile-api/<id>", methods=["POST"])
def update_customer_profile_api(id):
    try:
        if request.method == "POST":
            first_name = request.form.get('first_name')
            last_name = request.form.get('last_name')
            email = request.form.get('email')
            contact = request.form.get('contact')
            profile_pic = request.files.get('profile_pic')
            password = request.form.get('password')
            regex = '[^@]+@[a-zA-Z0-9]+[.][a-zA-Z]+'
            if not (re.search(regex, email)):
                return jsonify({"success": False, "error": "invalid email"})
            if profile_pic and allowed_file(profile_pic.filename):
                filename = secure_filename(profile_pic.filename)
                profile_pic.save(
                    os.path.join(app.config['UPLOAD_FOLDER2'], filename))
            else:
                return jsonify({
                    "success": False,
                    "error": "File not found or incorrect format"
                })
            if not first_name or not last_name or not contact or not password:
                    return jsonify({"success": False, "error": "Missing details"})

            query = {'_id': ObjectId(id)}
            user_data = db.customers.find_one(query)
            if user_data is not None:
                hash_password = generate_password_hash(password)
                # Insert into db #
                newData = {'$set':{"first_name":first_name,
                    "last_name": last_name,
                    "email": email,
                    "phone": contact,
                    "password": password,
                    "hash": hash_password,
                    "profile_pic": filename }}
                db.customers.update_one(user_data,newData)
                # db.trainers.insert_one(newAccount)
                return jsonify({
                    "id": str(user_data['_id']),
                    "first_name": first_name,
                    "last_name": last_name,
                    "email": email,
                    "contact": contact,
                    "profile_pic": filename,
                    "user_type": "customer",
                    "success": True,
                })
            else:
                return jsonify({
                    "success": False, "error": "Invalid User."
                })
        else:
            return jsonify({"success": False, "error": "Invalid request"})

    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

# ************ FOR UPDATE TRAINERS PROFILE************
@app.route("/update-trainer-profile-api/<id>", methods=["POST"])
def update_trainer_profile_api(id):
    try:
        if request.method == "POST":
            # contact_person = request.form.get('contact_person')
            first_name = request.form.get('first_name')
            last_name = request.form.get('last_name')
            email = request.form.get('email')
            contact = request.form.get('contact')
            profile_pic = request.files.get('profile_pic')
            password = request.form.get('password')
            bio = request.form.get('bio')
            regex = '[^@]+@[a-zA-Z0-9]+[.][a-zA-Z]+'
            if not (re.search(regex, email)):
                return jsonify({"success": False, "error": "invalid email"})
            if profile_pic and allowed_file(profile_pic.filename):
                filename = secure_filename(profile_pic.filename)
                profile_pic.save(
                    os.path.join(app.config['UPLOAD_FOLDER4'], filename))
            else:
                return jsonify({
                    "success": False,
                    "error": "File not found or incorrect format"
                })
            if not first_name or not last_name or not contact or not password or not bio:
                    return jsonify({"success": False, "error": "Missing details"})

            query = {'_id': ObjectId(id)}
            user_data = db.trainers.find_one(query)
            if user_data is not None:
                hash_password = generate_password_hash(password)
                # Insert into db #
                newData = {'$set':{
                    # "contact_person":contact_person,
                    "first_name": first_name,
                    "last_name": last_name,
                    "email": email,
                    "phone": contact,
                    "bio": bio,
                    "password": password,
                    "hash": hash_password,
                    "profile_pic": filename
                    }}
                db.trainers.update_one(user_data,newData)
                return jsonify({
                    "id": str(user_data['_id']),
                    # "contact_person":contact_person,
                    "first_name":first_name,
                    "last_name":last_name,
                    "email": email,
                    "contact": contact,
                    "profile_pic": filename,
                    "user_type": "trainer",
                    "success": True,
                })
            else:
                return jsonify({
                    "success": False, "error": "Invalid User."
                })
        else:
            return jsonify({"success": False, "error": "Invalid request"})

    except Exception as e:
        return jsonify({"success": False, "error": str(e)})


# ************ ALL IN ONE SIGNIN ************
@app.route("/signin-api", methods=["POST"])
def signin_api():
    try:
        if request.method == "POST":

            if request.is_json:
                data = request.get_json()
                email = data['email'].lower()
                password = data['password']

                query = {"email": email}
                customer = db.customers.find_one(query)
                company = db.company.find_one(query)
                trainer = db.trainers.find_one(query)

                if customer is not None:

                    hash_password = customer['hash']
                    if check_password_hash(hash_password, password):
                        return jsonify({
                            "id": str(customer['_id']),
                            "email": customer['email'],
                            "first_name": customer['first_name'],
                            "last_name": customer['last_name'],
                            "contact": customer['phone'],
                            "profile_pic" : customer['profile_pic'],
                            "profile_pic_path": "static/images/customers/profile-pics",
                            "user_type": "customer",
                            "mud_scheme": customer['mud_scheme'],
                            "mud_scheme_path": "static/images/customers/mud-schemes",
                            "today": customer['today'],
                            "goals": customer['goals'],
                            "active packages": customer['active packages'],
                            "inactive packages": customer['inactive packages'],
                            "notes": customer['notes'],

                            "success": True,

                        })
                    else:
                        return jsonify({
                            "success": False,
                            "error": "Invalid Credentials"
                        })
                elif company is not None:
                    hash_password = company['hash']
                    if check_password_hash(hash_password, password):
                        return jsonify({
                            "id": str(company['_id']),
                            "organizational number":company['organizational_number'],
                            "email": company['email'],
                            "company": company['company_name'],
                            "contact person": company['contact_person'],
                            "contact": company['phone'],
                            "company_profile_pic": company['company_profile_pic'],
                            "profile_pic_path": "static/images/company/company-profile-pics",
                            "region": company['region'],
                            "user_type": "company",
                            "success": True,
                        })
                    else:
                        return jsonify({
                            "success": False,
                            "error": "Invalid Credentials"
                        })
                elif trainer is not None:
                    hash_password = trainer['hash']
                    if check_password_hash(hash_password, password):
                        return jsonify({"id": str(trainer['_id']),
                                        "email": trainer['email'],
                                        # "contact person": trainer['contact_person'],
                                        "first_name": trainer['first_name'],
                                        "last_name": trainer['last_name'],
                                        "contact": trainer['phone'],
                                        "region": trainer['region'], 
                                        "certificate": trainer['certificate'],
                                        "trainer-profile-pic": trainer['profile_pic'],
                                        "profile_pic_path": "static/images/trainers/trainer-profile-pics",
                                        "certificate_path": "static/images/certificates",
                                        "user_type": "trainer", 
                                        "success": True })
                    else:
                        return jsonify({
                            "success": False,
                            "error": "Invalid Credentials"
                        })
                else:
                    return jsonify({
                        "success":
                        False,
                        "error":
                        "Invalid User or user doesn't exist."
                    })
            else:
                return jsonify({
                    "success": False,
                    "error": "Invalid request not json format."
                })
        else:
            return jsonify({"success": False, "error": "Invalid request"})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

# ************ TRAINER PRICING ************
@app.route("/trainer-package-api/<id>")
def trainer_package_api(id):
    try:
        if request.method == "GET":
            query = {'_id': ObjectId(id)}
            user_data = db.trainers.find_one(query)
            if user_data is not None:
                return jsonify({
                    "id": str(user_data['_id']),
                    "packages": user_data['packages'],
                    "success": True,
                })
            else:
                return jsonify({
                    "success": False, "error": "Invalid User."
                })
        else:
            return jsonify({"success": False, "error": "Invalid request"})

    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

# ************ BOOKINGS FOR CUSTOMER ************
@app.route("/customer-bookings-api/<string:id>")
def customer_bookings(id):
    try:
        if request.method == "GET":
            query = {'customer_id': id} 
            booking_data = db.bookings.find(query)
            lists = []
            for i in booking_data:
                i.update({"_id": str(i["_id"])})
                lists.append(i)
                print(lists)
            booking_data = db.bookings.find(query)
            if booking_data is not None:
                return jsonify({
                    "booking_data": lists,
                    "success": True,
                })
            else:
                return jsonify({
                    "success": False, "error": "Invalid Booking."
                })
        else:
            return jsonify({"success": False, "error": "Invalid request"})

    except Exception as e:
        return jsonify({"success": False, "error": str(e)})


# ************ BOOKINGS FOR TRAINERS ************
@app.route("/trainer-bookings-api/<string:id>")
def trainer_bookings(id):
    try:
        if request.method == "GET":
            query = {'trainer_id': id} 
            booking_data = db.bookings.find(query)
            lists = []
            for i in booking_data:
                i.update({"_id": str(i["_id"])})
                lists.append(i)
                print(lists)
            booking_data = db.bookings.find(query)
            if booking_data is not None:
                return jsonify({
                    "booking_data": lists,
                    "success": True,
                })
            else:
                return jsonify({
                    "success": False, "error": "Invalid Booking."
                })
        else:
            return jsonify({"success": False, "error": "Invalid request"})

    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

if __name__ == '__main__':
    app.run(debug=True)
