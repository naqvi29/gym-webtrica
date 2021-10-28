import re
import os, sys
from os.path import join, dirname, realpath
from sys import meta_path
from pymongo.message import query
from werkzeug.utils import secure_filename
from bson import objectid
from flask import Flask, render_template, request, url_for, jsonify, json, send_file, send_from_directory,session
import json
import pymongo
from bson.objectid import ObjectId
from bson.json_util import dumps
from werkzeug.utils import redirect
from werkzeug.security import generate_password_hash, check_password_hash
from PIL import Image
from flask_socketio import SocketIO, join_room, leave_room,emit
import datetime
from datetime import datetime
import random
import string
import stripe
from flask_mail import Mail, Message
import time


app = Flask(__name__)

# MONGOGB DATABASE CONNECTION
connection_url = "mongodb://77.68.126.35:27017/"
client = pymongo.MongoClient(connection_url)
client.list_database_names()
database_name = "fitness-app"
db = client[database_name]

# configure stripe
stripe_keys = {
    'secret_key': 'sk_test_51JkZF0BqpCv5jaX1oSPqLeBjHdku2lgrClgkVpttodmhaeDcdzpmDm5GWi8yNnX1bI8ZGtb2kXTAosO4ppiy5jlV00Fi9ITk4p',
    'publishable_key': 'pk_test_51JkZF0BqpCv5jaX1lRNB6p9ysHvt7VRndrZ0uKIy19RNkMinlKEqBrUXcMs3fLR2ZuJqHGCMOCMI4QPXsOVdkmnK00Zs2fBYeY'
}
stripe.api_key = stripe_keys['secret_key']

# USER IMAGES UPLOAD FOLDER
UPLOAD_FOLDER = join(dirname(realpath(__file__)), 'static/images/certificates')
UPLOAD_FOLDER2 = join(dirname(realpath(__file__)), 'static/images/customers/profile-pics')
UPLOAD_FOLDER3 = join(dirname(realpath(__file__)), 'static/images/company/company-profile-pics')
UPLOAD_FOLDER4 = join(dirname(realpath(__file__)), 'static/images/trainers/trainer-profile-pics')
UPLOAD_FOLDER5 = join(dirname(realpath(__file__)), 'static/images/customers/mud-schemes')
UPLOAD_FOLDER6 = join(dirname(realpath(__file__)), 'static/images/gyms/gym-profile-pics')
ALLOWED_EXTENSIONS = {'pdf', 'png', 'jpg', 'jpeg',}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['UPLOAD_FOLDER2'] = UPLOAD_FOLDER2
app.config['UPLOAD_FOLDER3'] = UPLOAD_FOLDER3
app.config['UPLOAD_FOLDER4'] = UPLOAD_FOLDER4
app.config['UPLOAD_FOLDER5'] = UPLOAD_FOLDER5
app.config['UPLOAD_FOLDER6'] = UPLOAD_FOLDER6

# configure socketio 
socketio = SocketIO(app)


def id_generator(size=8, chars=string.ascii_uppercase + string.digits + string.ascii_lowercase):
    return ''.join(random.choice(chars) for _ in range(size))
def id_generator2(size=4, chars=string.ascii_uppercase + string.digits + string.ascii_lowercase):
    return ''.join(random.choice(chars) for _ in range(size))

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


# configure secret key for session
app.secret_key = '_5#y2L"F4Q8z\n\xec]/'

# Mail server config.

app.config['MAIL_DEBUG'] = True
app.config['MAIL_SERVER'] = 'smtp.ionos.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USE_SSL'] = False
app.config['MAIL_USERNAME'] = 'testing@web-designpakistan.com'
app.config['MAIL_PASSWORD'] = 'Lawrence1234**'
app.config['MAIL_DEFAULT_SENDER'] = ('testing@web-designpakistan.com')

mail = Mail(app)


# Homepage route
@app.route("/")
def index():
    if 'loggedin' in session:
        totalcustomers = db.customers.count()
        totaltrainers = db.trainers.count()
        totalcompany = db.company.count()
        totalgyms = db.gyms.count()        
        I_one_training = db.bookings.count({'package_type': 'Training-1','completed':False})
        I_five_training = db.bookings.count({'package_type': 'Training-5','completed':False})
        I_ten_training = db.bookings.count({'package_type': 'Training-10','completed':False})
        I_mud_scheme = db.bookings.count({'package_type': 'Mud-Scheme','completed':False})
        I_training_scheme = db.bookings.count({'package_type': 'Training-Scheme','completed':False})
        C_one_training = db.bookings.count({'package_type': 'Training-1','completed':True})
        C_five_training = db.bookings.count({'package_type': 'Training-5','completed':True})
        C_ten_training = db.bookings.count({'package_type': 'Training-10','completed':True})
        C_mud_scheme = db.bookings.count({'package_type': 'Mud-Scheme','completed':True})
        C_training_scheme = db.bookings.count({'package_type': 'Training-Scheme','completed':True})
        current_year = datetime.now().year

        # return render_template("home.html")
        return render_template("index.html",totalcustomers = totalcustomers,totaltrainers=totaltrainers,totalcompany=totalcompany,totalgyms=totalgyms,I_one_training=I_one_training,I_five_training=I_five_training,I_ten_training=I_ten_training,I_mud_scheme=I_mud_scheme,I_training_scheme=I_training_scheme,C_one_training=C_one_training,C_five_training=C_five_training,C_ten_training=C_ten_training,C_mud_scheme=C_mud_scheme,C_training_scheme=C_training_scheme, current_year=current_year)
    else:
        # Admin is not loggedin show them the login page
        return redirect(url_for('signin'))

@app.route("/signin", methods=['GET', 'POST'])
def signin():
    if request.method == 'POST' and 'username' in request.form and 'password' in request.form:
        username = request.form['username']
        password = request.form['password']
        query = {'username': username}
        admin = db.admin.find_one(query)
        if admin:
            matched = admin['password'] == password
            if matched is True:
                # Create session data, we can access this data in other routes                
                session['loggedin'] = True
                session['id'] =  str(admin['_id'])
                session['username'] = admin['username']
                # Redirect to index page
                return redirect(url_for('index'))
            else:
                return jsonify({"status":False,"error":"Invalid Password"})
        else:
            return jsonify({"success":False, "error":"Invalid username"})
    else:  
        return render_template("adminlogin.html")

# configure signout route
@app.route('/signout')
def signout():
        # Remove session data, this will log the user out 
        session.pop('loggedin', None)
        session.pop('id', None)
        session.pop('username', None)
        # Redirect to index page
        return redirect(url_for('index'))


# Dashboard route
@app.route("/dashboard")
def dashboard():
    return render_template("dashboard.html")

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

# View bookings route
@app.route('/bookings')
def bookings():
    # fetch data from trainers table
    bookings = db.bookings.find()
    return render_template("bookings.html", bookings=bookings)

# View Superadmin setting route
@app.route('/settings')
def settings():
    # fetch data from admin table
    admin = db.admin.find()
    return render_template("settings.html", admin=admin)

# edit admin account 
@app.route('/edit/admin/<id>', methods=['GET', 'POST'])
def edit_admin(id):
    if request.method == 'GET':
        # fetch data from admin table 
        query = {'_id': ObjectId(id)}
        admin = db.admin.find_one(query)
        return render_template("edit-admin.html",admin=admin)
    else:
        username = request.form.get("username")
        password = request.form.get("password")
        cpassword = request.form.get("cpassword")
        if cpassword != password:
            return jsonify({"success":False, "error":"Password didn't match"})
        newvalues = {
            "$set": {
                'username': username,
                'password': password,
            }
        }
        filter = {'_id': ObjectId(id)}
        db.admin.update_one(filter, newvalues)
        return redirect(url_for('settings')) 

# add new admin 
@app.route("/addnew/admin", methods=['GET', 'POST'])
def add_admin():
    if request.method == 'GET':
        return render_template("add-admin.html")
    else:
        username = request.form.get("username")
        password = request.form.get("password")
        cpassword = request.form.get("cpassword")
        if cpassword != password:
            return jsonify({"success":False, "error":"Password didn't match"})
        newvalues = {
                'username': username,
                'password': password,
        }
        db.admin.insert_one(newvalues)
        return redirect(url_for('settings')) 
# delete admin 
@app.route("/delete/admin/<id>",)
def delete_admin(id):
    if request.method == 'GET':
        query = {'_id': ObjectId(id)}
        admin = db.admin.find_one(query)
        if admin is None:
            return jsonify({"success":False, "error":"Invalid Admin"})
        db.admin.delete_one(query)
        return redirect(url_for('settings'))
    else:
        return jsonify({"success":False,"error":"Invalid Request"})
            


# certificates route
@app.route('/certificates')
def certificates():
    # fetch data from trainers table
    trainers = db.trainers.find()
    # fetch data from certificates table
    certificates = db.certificates.find()
    return render_template("certificates.html", trainers=trainers,certificates=certificates)

# View certificates route
@app.route('/view-certificates/<email>')
def view_certificates(email):
    # fetch data from certificates table
    query = {'trainer_email':email}
    certificates = db.certificates.find(query)
    return render_template("viewcertificates.html",certificates=certificates)

# Mark certified route
@app.route('/mark-certified/<id>')
def mark_certified(id):
    # fetch data from certificates table
    query = {'_id': ObjectId(id)}
    newvalues = {
            "$set": {
                'trainer_certified': 'True',
            }
        }
    db.trainers.update_one(query, newvalues)
    return redirect(url_for('certificates')) 

# add new certificate to trainer 
@app.route("/add-certificate", methods = ['GET','POST'])
def add_certificate():
    try:
        if request.method == 'POST':
            traineremail = request.form.get("trainer-email")
            certificate = request.files["certificate"]
            query = {'email': traineremail}
            trainerdata = db.trainers.find_one(query)
            if trainerdata is None:
                return jsonify({"success":False , "error":"Invalid Email or trainer didn't exist"})

            if certificate and allowed_file(certificate.filename):
                filename = secure_filename(certificate.filename)
                certificate.save(
                    os.path.join(app.config['UPLOAD_FOLDER'], filename))
                # compress image
                newimage = Image.open(os.path.join(app.config['UPLOAD_FOLDER'], str(filename)))
                newimage.thumbnail((400, 400))
                newimage.save(os.path.join(UPLOAD_FOLDER, str(filename)), quality=95)
            else:
                return jsonify({
                    "success": False,
                    "error": "File not found or incorrect format"
                })
            
            newvalues = {
                'trainer_email': traineremail,
                'certificate': filename
            }
            db.certificates.insert_one(newvalues)
            return redirect(url_for('certificates')) 
        else:
            return render_template("add-certificate.html")
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})


# Edit accounts route **not using**
# @app.route('/edit/<cat>-<id>', methods=['GET', 'POST'])
# def edit(cat, id):
#     if request.method == 'GET':
#         # fetch data which will edit
#         query = {'_id': ObjectId(id)}
#         edit = db[cat].find_one(query)
#         return render_template("edit.html", edit=edit, cat=cat, id=id)
#     else:
#         email = request.form.get("email")
#         phone = request.form.get("phone")
#         password = request.form.get("password")
#         newvalues = {
#             "$set": {
#                 'email': email,
#                 'phone': phone,
#                 'password': password
#             }
#         }
#         filter = {'_id': ObjectId(id)}
#         db[cat].update_one(filter, newvalues)
#         return redirect(url_for(cat))

# Edit booking accounts route
@app.route('/edit/booking/<id>', methods=['GET', 'POST'])
def editbooking(id):
    if request.method == 'GET':
        # fetch booking data which will edit
        query = {'_id': ObjectId(id)}
        edit = db.bookings.find_one(query)
        return render_template("editbookings.html", edit=edit, id=id)
    else:
        first_name = request.form.get("customer_name")
        last_name = request.form.get("trainer_name")
        booking_month = request.form.get("booking_month")
        booking_date = request.form.get("booking_date")
        booking_time = request.form.get("booking_time")
        location = request.form.get("location")
        package = request.form.get("package")
        # Replace Updated data in database
        newvalues = {
            "$set": {
                'first_name': first_name,
                'last_name': last_name,
                'booking_month': booking_month,
                'booking_date': booking_date,
                'booking_time': booking_time,
                'location': location,
                'package_type': package,
            }
        }
        filter = {'_id': ObjectId(id)}
        db.bookings.update_one(filter, newvalues)
        return redirect(url_for('bookings')) 

# Edit customer accounts route
@app.route('/edit/customers/<id>', methods=['GET', 'POST'])
def editcustomers(id):
    if request.method == 'GET':
        # fetch customer data which will edit
        query = {'_id': ObjectId(id)}
        edit = db.customers.find_one(query)
        return render_template("editcustomers.html", edit=edit, id=id)
    else:
        first_name = request.form.get("first_name")
        last_name = request.form.get("last_name")
        email = request.form.get("email")
        phone = request.form.get("phone")
        goals = request.form.get("goals")
        today = request.form.get("today")
        good_to_know = request.form.get("good_to_know")
        notes = request.form.get("notes")
        password = request.form.get("password")
        # Replace Updated data in database
        newvalues = {
            "$set": {
                'email': email,
                'first_name': first_name,
                'last_name': last_name,
                'phone': phone,
                'goals': goals,
                'today': today,
                'good_to_know': good_to_know,
                'notes': notes,
                'password': password
            }
        }
        filter = {'_id': ObjectId(id)}
        db.customers.update_one(filter, newvalues)
        return redirect(url_for('customers')) 

# Edit company accounts route
@app.route('/edit/company/<id>', methods=['GET', 'POST'])
def editcompany(id):
    if request.method == 'GET':
        # fetch customer data which will edit
        query = {'_id': ObjectId(id)}
        edit = db.company.find_one(query)
        return render_template("editcompany.html", edit=edit, id=id)
    else:
        organizational_number = request.form.get("organizational_number")
        company_name = request.form.get("company_name")
        contact_person = request.form.get("contact_person")
        email = request.form.get("email")
        phone = request.form.get("phone")
        region = request.form.get("region")
        password = request.form.get("password")
        # Replace Updated data in database
        newvalues = {
            "$set": {
                'organizational_number': organizational_number,
                'company_name': company_name,
                'contact_person': contact_person,
                'email': email,
                'phone': phone,
                'region': region,
                'password': password
            }
        }
        filter = {'_id': ObjectId(id)}
        db.company.update_one(filter, newvalues)
        return redirect(url_for('company'))

# Edit trainers accounts route
@app.route('/edit/trainer/<id>', methods=['GET', 'POST'])
def edittrainer(id):
    if request.method == 'GET':
        # fetch trainer data which will edit
        query = {'_id': ObjectId(id)}
        edit = db.trainers.find_one(query)
        return render_template("edittrainer.html", edit=edit, id=id)
    else:
        first_name = request.form.get("first_name")
        last_name = request.form.get("last_name")
        email = request.form.get("email")
        phone = request.form.get("phone")
        region = request.form.get("region")
        password = request.form.get("password")
        today = request.form.get("today")
        goals = request.form.get("goals")
        notes = request.form.get("notes")
        bio = request.form.get("bio")
        link = request.form.get("link")
        desc = request.form.get("desc")
        level = request.form.get("level")
        availability = request.form.get("availability")
        # Replace Updated data in database
        newvalues = {
            "$set": {
                'first_name': first_name,
                'last_name': last_name,
                'email': email,
                'phone': phone,
                'region': region,
                'password': password,
                'today': today,
                'goals': goals,
                'notes': notes,
                'bio': bio,
                'link': link,
                'desc': desc,
                'level': level,
                'availability':availability,
            }
        }
        filter = {'_id': ObjectId(id)}
        db.trainer.update_one(filter, newvalues)
        return redirect(url_for('company')) 


# All in one Delete accounts route
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
    customers = db.customers.find().sort('_id', -1).limit(4)
    # fetch recent 2 documents from company collection
    company = db.company.find().sort('_id', -1).limit(4)
    # fetch recent 2 documents from trainers collection
    trainers = db.trainers.find().sort('_id', -1).limit(4)
    return render_template("newaccounts.html",
                           customers=customers,
                           company=company,
                           trainers=trainers)





# route for view trainer's certificate
@app.route('/certificate/<certificatename>')
def viewcertificate(certificatename):
    return render_template('certificate.html', certificatename=certificatename)


# Add new account route **unused**
# @app.route('/addnew/<cat>', methods=['GET', 'POST'])
# def addnew(cat):
#     if request.method == 'POST':
#         name = request.form.get("name")
#         email = request.form.get("email")
#         phone = request.form.get("phone")
#         password = request.form.get("password")
#         hash_password = generate_password_hash(password)
#         address = request.form.get("address")
#         newAccount = {
#             "name": name,
#             "email": email,
#             "phone": phone,
#             "password": password,
#             "hash": hash_password,
#             "address": address
#         }
#         db[cat].insert_one(newAccount)
#         return redirect(url_for(cat))
#     else:
#         return render_template('addnew.html', cat=cat)

# Add new customer account route
@app.route('/addnew/customer', methods=['GET', 'POST'])
def addnewcustomer():
    if request.method == 'POST':
        first_name = request.form.get("first_name")
        last_name = request.form.get("last_name")
        email = request.form.get("email")
        phone = request.form.get("phone")        
        password = request.form.get("password")
        hash_password = generate_password_hash(password)
        profile_pic = request.files["profile_pic"]

        if profile_pic and allowed_file(profile_pic.filename):
            filename = secure_filename(profile_pic.filename)
            profile_pic.save(
                os.path.join(app.config['UPLOAD_FOLDER2'], filename))
            # compress image
            newimage = Image.open(os.path.join(app.config['UPLOAD_FOLDER2'], str(filename)))
            newimage.thumbnail((400, 400))
            newimage.save(os.path.join(UPLOAD_FOLDER2, str(filename)), quality=95)
        else:
            return jsonify({
                "success": False,
                "error": "File not found or incorrect format"
            })
        # Insert into db
        newAccount = {
            "first_name": first_name,
            "last_name": last_name,
            "email": email,
            "phone": phone,
            "profile_pic": filename,
            "password": password,
            "hash": hash_password
        }
        db.customers.insert_one(newAccount)
        return redirect(url_for('customers'))
    else:
        return render_template('addnewcustomer.html')

# Add new company account route
@app.route('/addnew/company', methods=['GET', 'POST'])
def addnewcompany():
    if request.method == 'POST':
        organizational_number = request.form.get("organizational_number")
        company_name = request.form.get("company_name")
        contact_person = request.form.get("contact_person")
        email = request.form.get("email")
        phone = request.form.get("phone")        
        region = request.form.get("region")        
        password = request.form.get("password")
        hash_password = generate_password_hash(password)
        profile_pic = request.files["profile_pic"]

        if profile_pic and allowed_file(profile_pic.filename):
            filename = secure_filename(profile_pic.filename)
            profile_pic.save(
                os.path.join(app.config['UPLOAD_FOLDER3'], filename))
            # compress image
            newimage = Image.open(os.path.join(app.config['UPLOAD_FOLDER3'], str(filename)))
            newimage.thumbnail((400, 400))
            newimage.save(os.path.join(UPLOAD_FOLDER3, str(filename)), quality=95)
        else:
            return jsonify({
                "success": False,
                "error": "File not found or incorrect format"
            })
        # Insert into db
        newAccount = {
            "organizational_number": organizational_number,
            "company_name": company_name,
            "contact_person": contact_person,
            "email": email,
            "phone": phone,
            "region": region,
            "company_profile_pic": filename,
            "password": password,
            "hash": hash_password
        }
        db.company.insert_one(newAccount)
        return redirect(url_for('company'))
    else:
        return render_template('addnewcompany.html')

# Add new trainer account route
@app.route('/addnew/trainer', methods=['GET', 'POST'])
def addnewtrainer():
    if request.method == 'POST':
        first_name = request.form.get("first_name")
        last_name = request.form.get("last_name")
        email = request.form.get("email")
        contact = request.form.get("phone")        
        region = request.form.get("region")        
        password = request.form.get("password")
        confirmpassword = request.form.get("cpassword")
        trainer_profile_pic = request.files["profile_pic"]
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
        if trainer_profile_pic and allowed_file(trainer_profile_pic.filename):
                filename2 = secure_filename(trainer_profile_pic.filename)
                trainer_profile_pic.save(
                    os.path.join(app.config['UPLOAD_FOLDER4'], filename2))
                # compress image
                newimage = Image.open(os.path.join(app.config['UPLOAD_FOLDER4'], str(filename2)))
                newimage.thumbnail((400, 400))
                newimage.save(os.path.join(UPLOAD_FOLDER4, str(filename2)), quality=95)
        else:
            return jsonify({
                "success": False,
                "error": "Profile Picture not found or incorrect format"
            })
        regex = '[^@]+@[a-zA-Z0-9]+[.][a-zA-Z]+'
        if not (re.search(regex, email)):
            return jsonify({"success": False, "error": "invalid email"})
        if password != confirmpassword:
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
                "first_name": first_name,
                "last_name": last_name,
                "email": email,
                "phone": contact,
                "password": password,
                "hash": hash_password,
                "region": region,                    
                "profile_pic": filename2,
                "status": True,
                "gyms": [],
                "today": "0",
                "notes": "Lorem",
                "goals": "0",
                "bio": "lorem",
                "trainer_certified": "False",
                "link": "https://www.youtube.com/watch?v=vlXRyUn9feI",
                "desc": "lorem",
                "available_dates": [],
                "rating": "0",
                "level": "0",
                "availability": "0"
            }

            db.trainers.insert_one(newAccount)
            for filename in filenames:
                newCertificates = {
                    "certificate": filename,
                    "trainer_email": email  
                }
                db.certificates.insert_one(newCertificates)
            # insert empty ratings
            query = {"trainer_email": email}
            ratings= db.ratings.find_one(query)
            if ratings is None:
                newRatings = {
                    "trainer_email":email,
                    "1-star": 0,
                    "2-star": 0,
                    "3-star": 0,
                    "4-star": 0,
                    "5-star": 0,
                    "totalRatings":0
                }
                db.ratings.insert_one(newRatings)

            # insert default packages
            query = {"trainer_email": email}
            packages = db.trainer_packages.find_one(query)
            if packages is None:
                def1 = {
                    "name":"1-training",
                    "price": "500",
                    "desc": "lorem",
                    "trainer_email":email 
                }
                def2 = {
                    "name":"5-training",
                    "price": "2500",
                    "desc": "lorem",
                    "trainer_email":email 
                }
                def3 = {
                    "name":"10-training",
                    "price": "5000",
                    "desc": "lorem",
                    "trainer_email":email 
                }
                def4 = {
                    "name":"Mud scheme",
                    "price": "500",
                    "desc": "lorem",
                    "trainer_email":email 
                }
                def5 = {
                    "name":"training scheme",
                    "price": "500",
                    "desc": "lorem",
                    "trainer_email":email 
                }
                db.trainer_packages.insert_one(def1)
                db.trainer_packages.insert_one(def2)
                db.trainer_packages.insert_one(def3)
                db.trainer_packages.insert_one(def4)
                db.trainer_packages.insert_one(def5)
            
            return redirect(url_for('trainers'))
        else:
            return jsonify({"success":False,"error":"User already exist with this email"})
    else:
        return render_template('addnewtrainer.html')


# View completed sessions route
@app.route('/completed-sessions')
def completed_sessions():
    # fetch data from sessions table
    query = {"completed":True}
    sessions = db.sessions.find(query)
    return render_template("sessions.html", sessions=sessions)

# Contact Us messages customers
@app.route("/messages/customers")
def messages_customers():
    # fetch data from contactus table 
    query = {"account":"customer"}
    messages = db.contact_us.find(query)
    return render_template("/messages_customer.html", messages=messages)

# Contact Us messages trainers
@app.route("/messages/trainers")
def messages_trainers():
    # fetch data from contactus table 
    query = {"account":"trainer"}
    messages = db.contact_us.find(query)
    return render_template("/messages_trainer.html", messages=messages)

# Delete Contact Us messages 
@app.route("/delete/messages/<id>")
def delete_messages(id):
    try:
        # fetch data from contactus table 
        query = {"_id": ObjectId(id)}
        data = db.contact_us.find_one(query)
        db.contact_us.delete_one(query)
        if data['account'] == 'customer':
            return redirect("/messages/customers")        
        elif data['account'] == 'trainer':
            return redirect("/messages/trainers")
        return "Success"
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

#Gyms route
@app.route("/gyms")
def gyms():
    try:
        # fetch data from gyms table 
        gyms = db.gyms.find()
        return render_template("gyms.html", gyms=gyms)
    except Exception as e:
        return jsonify({"success":False, "error": str(e)})

# Edit gyms accounts route
@app.route('/edit/gyms/<id>', methods=['GET', 'POST'])
def editgyms(id):
    try:
        if request.method == 'GET':
            # fetch booking data which will edit
            query = {'_id': ObjectId(id)}
            edit = db.gyms.find_one(query)
            return render_template("editgyms.html", edit=edit, id=id)
        else:
            name = request.form.get("name")
            heading = request.form.get("heading")
            desc = request.form.get("desc")
            peoples = request.form.get("peoples")
            links = request.form.get("links")
            latitude = request.form.get("latitude")
            longitude = request.form.get("longitude")
            # profile_pic = request.files["profile_pic"]

            # if profile_pic and allowed_file(profile_pic.filename):
            #     filename = secure_filename(profile_pic.filename)
            #     profile_pic.save(
            #         os.path.join(app.config['UPLOAD_FOLDER6'], filename))
            #     # compress image
            #     newimage = Image.open(os.path.join(app.config['UPLOAD_FOLDER6'], str(filename)))
            #     newimage.thumbnail((400, 400))
            #     newimage.save(os.path.join(UPLOAD_FOLDER6, str(filename)), quality=95)
            # else:
            #     return jsonify({
            #         "success": False,
            #         "error": "File not found or incorrect format"
            #     })
            # Replace Updated data in database
            newvalues = {
                "$set": {
                    'name': name,
                    'heading': heading,
                    'desc': desc,
                    'peoples': peoples,
                    'links': links,
                    'latitude': float(latitude),
                    'longitude': float(longitude),
                }
            }
            filter = {'_id': ObjectId(id)}
            db.gyms.update_one(filter, newvalues)
            return redirect(url_for('gyms'))
    except Exception as e:
        return jsonify({"success":False, "error": str(e)})

#payments route
@app.route("/payments")
def payments():
    try:
        # fetch data from payments table 
        payments = db.payments.find()
        return render_template("payments.html", payments=payments)
    except Exception as e:
        return jsonify({"success":False, "error": str(e)})

#promo codes route
@app.route("/promocodes")
def promocodes():
    try:
        # fetch data from promocodes table 
        promo = db.promo_codes.find()
        return render_template("promocodes.html", promo=promo)
    except Exception as e:
        return jsonify({"success":False, "error": str(e)})

# edit promo codes route
@app.route("/edit/promo/<id>", methods=['GET', 'POST'])
def edit_promo(id):
    try:
        if request.method == 'GET':
            # fetch promo data which will edit
            query = {'_id': ObjectId(id)}
            edit = db.promo_codes.find_one(query)
            return render_template("editpromo.html", edit=edit, id=id)
        else:
            name = request.form.get("name")
            discount = request.form.get("discount")
            type = request.form.get("type")
            # Replace Updated data in database
            newvalues = {
                "$set": {
                    'name': name,
                    'discount': int(discount),
                    'type':type
                }
            }
            filter = {'_id': ObjectId(id)}
            db.promo_codes.update_one(filter, newvalues)
            return redirect(url_for('promocodes'))
    except Exception as e:
        return jsonify({"success":False, "error": str(e)})

# delete promo codes route
@app.route("/delete/promo/<id>")
def delete_promo(id):
    try:
        query = {'_id': ObjectId(id)}
        db.promo_codes.delete_one(query)
        return redirect(url_for('promocodes'))
    except Exception as e:
        return jsonify({"success":False, "error": str(e)})

# add new promo codes route
@app.route("/addnewpromo", methods = ['GET', 'POST'])
def add_promo():
    try:
        if request.method == 'GET':
            return render_template("addpromo.html")
        else:
            name = request.form.get("name")
            discount = request.form.get("discount")
            if int(discount) >= 1:                
                # Replace Updated data in database
                newvalues = {
                        'name': name,
                        'discount': int(discount),
                        'type': "%"                
                }
                db.promo_codes.insert_one(newvalues)
                return redirect(url_for('promocodes'))
            else:
                return jsonify ({"success":False, "error":"Invalid discount number"})
    except Exception as e:
        return jsonify({"success":False, "error": str(e)})



################################################ MOBILE API'S START ##########################################################
 
# ************ FOR CUSTOMERS/USERS SIGNUP ************
@app.route("/signup-api", methods=["POST"])
def signup_api():
    try:
        if request.method == "POST":
                email = request.form.get('email').lower()
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
                    # compress image
                    newimage = Image.open(os.path.join(app.config['UPLOAD_FOLDER2'], str(filename)))
                    newimage.thumbnail((400, 400))
                    newimage.save(os.path.join(UPLOAD_FOLDER2, str(filename)), quality=95)
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
                        "profile_pic": filename,
                        # defaults 
                        "mud_scheme": "",
                        "today": "0",
                        "goals": "0",
                        "active packages":[],
                        "inactive packages":[],
                        "notes":"Here you can add your notes..",
                        "wallet_cards": [],
                        "good_to_know":"Lorem ipsum dolor sit amet consectetur adipisicing elit. Molestiae aperiam consectetur deserunt officiis quos soluta autem placeat labore fuga, pariatur voluptatem odit similique quibusdam natus, hic exercitationem quisquam velit delectus.",
                    }
                    db.customers.insert_one(newAccount)
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
                    # compress image
                    newimage = Image.open(os.path.join(app.config['UPLOAD_FOLDER3'], str(filename)))
                    newimage.thumbnail((400, 400))
                    newimage.save(os.path.join(UPLOAD_FOLDER3, str(filename)), quality=95)
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
                    # compress image
                    newimage = Image.open(os.path.join(app.config['UPLOAD_FOLDER4'], str(filename2)))
                    newimage.thumbnail((400, 400))
                    newimage.save(os.path.join(UPLOAD_FOLDER4, str(filename2)), quality=95)
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
                    "first_name": first_name,
                    "last_name": last_name,
                    "email": email,
                    "phone": contact,
                    "password": password,
                    "hash": hash_password,
                    "region": region,                    
                    "profile_pic": filename2,
                    "status": True,
                    "gyms": [],
                    "today": "0",
                    "notes": "Lorem",
                    "goals": "0",
                    "bio": "lorem",
                    "trainer_certified": "False",
                    "link": "https://www.youtube.com/watch?v=vlXRyUn9feI",
                    "desc": "lorem",
                    "available_dates": [],
                    "rating": "0",
                    "level": "0",
                    "availability": "0"
                    
                }
                db.trainers.insert_one(newAccount)
                for filename in filenames:
                    newCertificates = {
                        "certificate": filename,
                        "trainer_email": email  
                    }
                    db.certificates.insert_one(newCertificates)
                # insert empty ratings
                query = {"trainer_email": email}
                ratings= db.ratings.find_one(query)
                if ratings is None:
                    newRatings = {
                        "trainer_email":email,
                        "1-star": 0,
                        "2-star": 0,
                        "3-star": 0,
                        "4-star": 0,
                        "5-star": 0,
                        "totalRatings":0
                    }
                    db.ratings.insert_one(newRatings)

                # insert default packages
                query = {"trainer_email": email}
                packages = db.trainer_packages.find_one(query)
                if packages is None:
                    def1 = {
                        "name":"1-training",
                        "price": "500",
                        "desc": "lorem",
                        "trainer_email":email 
                    }
                    def2 = {
                        "name":"5-training",
                        "price": "2500",
                        "desc": "lorem",
                        "trainer_email":email 
                    }
                    def3 = {
                        "name":"10-training",
                        "price": "5000",
                        "desc": "lorem",
                        "trainer_email":email 
                    }
                    def4 = {
                        "name":"Mud scheme",
                        "price": "500",
                        "desc": "lorem",
                        "trainer_email":email 
                    }
                    def5 = {
                        "name":"training scheme",
                        "price": "500",
                        "desc": "lorem",
                        "trainer_email":email 
                    }
                    db.trainer_packages.insert_one(def1)
                    db.trainer_packages.insert_one(def2)
                    db.trainer_packages.insert_one(def3)
                    db.trainer_packages.insert_one(def4)
                    db.trainer_packages.insert_one(def5)
                
                return jsonify({
                    "email": email,
                    "first_name": first_name,
                    "last_name": last_name,
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
            trainersdata = db.trainers.find({"status":True}, {"password": 0, "hash": 0})
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
            if not first_name or not last_name or not contact or not password:
                    return jsonify({"success": False, "error": "Missing details"})
            if profile_pic:
                if allowed_file(profile_pic.filename):
                    filename = secure_filename(profile_pic.filename)
                    profile_pic.save(
                        os.path.join(app.config['UPLOAD_FOLDER2'], filename))
                    # compress image
                    newimage = Image.open(os.path.join(app.config['UPLOAD_FOLDER2'], str(filename)))
                    newimage.thumbnail((400, 400))
                    newimage.save(os.path.join(UPLOAD_FOLDER2, str(filename)), quality=95)
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
                    return jsonify({
                        "success": False, "error":"Invalid Profile picture format"
                    })
            else:
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
                        "hash": hash_password, }}
                    db.customers.update_one(user_data,newData)
                    # db.trainers.insert_one(newAccount)
                    return jsonify({
                        "id": str(user_data['_id']),
                        "first_name": first_name,
                        "last_name": last_name,
                        "email": email,
                        "contact": contact,
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
            if not first_name or not last_name or not contact or not password or not bio:
                    return jsonify({"success": False, "error": "Missing details"})
            if profile_pic:
                if allowed_file(profile_pic.filename):
                    filename = secure_filename(profile_pic.filename)
                    profile_pic.save(
                        os.path.join(app.config['UPLOAD_FOLDER4'], filename))
                    # compress image
                    newimage = Image.open(os.path.join(app.config['UPLOAD_FOLDER4'], str(filename)))
                    newimage.thumbnail((400, 400))
                    newimage.save(os.path.join(UPLOAD_FOLDER4, str(filename)), quality=95)
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
                    return jsonify({
                        "success": False, "error": "invalid profile picture format"
                    })
            else:
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
                        "hash": hash_password
                        }}
                    db.trainers.update_one(user_data,newData)
                    return jsonify({
                        "id": str(user_data['_id']),
                        "first_name":first_name,
                        "last_name":last_name,
                        "email": email,
                        "contact": contact,
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

# ************ FOR UPDATE CUSTOMERS STATS************
@app.route("/update-customer-stats-api/<id>", methods=["POST"])
def update_customer_stats_api(id):
    try:
        if request.method == 'POST':      
            if request.is_json:            
                data = request.get_json()
                today = data["today"]
                goals = data["goals"]
                notes = data["notes"]
                if not today or not goals or not notes:
                        return jsonify({"success": False, "error": "Missing details"})

                query = {'_id': ObjectId(id)}
                user_data = db.customers.find_one(query)
                if user_data is not None:
                    # Insert into db #
                    newData = {'$set':{"today":today,
                        "goals": goals,
                        "notes": notes }}
                    db.customers.update_one(user_data,newData)
                    return jsonify({    
                        "id": str(user_data['_id']),
                        "success": True,
                    })
                else:
                    return jsonify({
                        "success": False, "error": "Invalid User."
                    })
            else:
                return jsonify({"success": False, "msg": "Invalid data format"})
        else:
            return jsonify({"success": False, "msg": "Invalid request"})

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
                            "wallet_cards": customer['wallet_cards'],
                            "good_to_know": customer['good_to_know'],
                            "key": stripe_keys['publishable_key'],
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
                            "good_to_know":"Lorem ipsum dolor sit amet consectetur adipisicing elit. Molestiae aperiam consectetur deserunt officiis quos soluta autem placeat labore fuga, pariatur voluptatem odit similique quibusdam natus, hic exercitationem quisquam velit delectus.",
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
                                        "first_name": trainer['first_name'],
                                        "last_name": trainer['last_name'],
                                        "contact": trainer['phone'],
                                        "region": trainer['region'],
                                        "trainer-profile-pic": trainer['profile_pic'],
                                        "status": trainer['status'],
                                        "bio": trainer['bio'],
                                        "today": trainer['today'],
                                        "goals": trainer['goals'],
                                        "notes": trainer['notes'],
                                        "available_dates": trainer['available_dates'],
                                        "profile_pic_path": "static/images/trainers/trainer-profile-pics",
                                        "user_type": "trainer",
                                        "good_to_know":"Lorem ipsum dolor sit amet consectetur adipisicing elit. Molestiae aperiam consectetur deserunt officiis quos soluta autem placeat labore fuga, pariatur voluptatem odit similique quibusdam natus, hic exercitationem quisquam velit delectus.", 
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


# ************ TRAINER PRICING ************note:changed
@app.route("/trainer-package-api/<id>")
def trainer_package_api(id):
    try:
        if request.method == "GET":
            query = {'_id': ObjectId(id)}
            user_data = db.trainers.find_one(query)
            if user_data is not None:
                email = user_data['email']
                query = {'trainer_email': email}
                packagedata = db.trainer_packages.find(query)
                lists = []
                for i in packagedata:
                    i.update({"_id": str(i["_id"])})
                    lists.append(i)
                return jsonify({
                    "id": str(user_data['_id']),
                    "email": str(email),
                    "packages": lists,
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
            # trainersdata = db.trainers.find({"status":True}, {"password": 0, "hash": 0})
            query = {'customer_id': id,'accepted':True} 
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
            # today = time.strftime("%d/%m/%Y")
            # today_format = datetime.strptime(today, "%d/%m/%Y")
            # exp_date = str(today_format + datetime.timedelta(days=365)).split(" ")
            # exp = exp_date[0]
            # return jsonify({"date":exp})
            # query = {'trainer_id': id,"completed":False, "date": {"$gt": today_format } }
            query = {'trainer_id': id,"completed":False,}
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

# ************ GYMS DETAILS ************
@app.route("/all-gym-details-api", methods=["GET"])
def all_gym_details():
    try:
        if request.method == "GET":
            gym_data = db.gyms.find()
            lists = []
            for i in gym_data:
                i.update({"_id": str(i["_id"])})
                lists.append(i)
                print(lists)
            return jsonify({"success": True, "gyms data": lists})
        else:
            return jsonify({"success": False, "msg": "Invalid request method"})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})


# ************ GET TRAINER CERTIFICATES ************
@app.route("/get-trainer-certificates-api/<id>", methods=["GET"])
def get_trainer_certificates(id):
    try:
        if request.method == "GET":
            # fetch trainer email from trainers table
            query = {'_id': ObjectId(id)}
            user_data = db.trainers.find_one(query)
            if user_data is not None:
                # fetch all certificates registered with trainer email 
                query = {'trainer_email': user_data['email']}
                certificate_data = db.certificates.find(query)
                lists = []
                # for loop
                for i in certificate_data:
                    i.update({"_id": str(i["_id"])})
                    lists.append(i)
                    print(lists, "hello")
                return jsonify({"success": True, "certificates": lists, "certificate_path": "static/images/certificates"})
                # end forloop
            else:
                return jsonify({
                    "success": False, "error": "Invalid User."
                })
        else:
            return jsonify({"success": False, "error": "Invalid request"})

    except Exception as e:
        return jsonify({"success": False, "error": str(e)})


# ************ ADD NEW TRAINER CERTIFICATE ************
@app.route("/add-new-trainer-certificate-api/<id>", methods=["POST"])
def add_new_trainer_certificate(id):
    try:
        if request.method == "POST":
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
            query = {'_id': ObjectId(id)}
            user_data = db.trainers.find_one(query)
            if user_data is not None:
                # get trainer's email from trainers table 
                query = {'trainer_email': user_data['email']}
                for filename in filenames:
                    newCertificates = {
                        "certificate": filename,
                        "trainer_email": user_data['email']  
                    }
                    db.certificates.insert_one(newCertificates)        

                return jsonify({
                    "id": str(user_data['_id']),
                    "certificates added": filenames,
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

# ************ DELETE TRAINER CERTIFICATE ************
@app.route("/delete-trainer-certificate-api/<id>")
def delete_trainer_certificate(id):
    try:
        if request.method == "GET":
            query = {'_id': ObjectId(id)}
            certificate_data = db.certificates.find_one(query)
            if certificate_data:
                db.certificates.delete_one(query)
                return jsonify({"success": True,})
            else:
                return jsonify({"success": False, "error": "Certificate doesn't exist"})
        else:
            return jsonify({"success": False, "error": "Invalid request"})

    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

# ************ FOR UPDATE TRAINER STATS************
@app.route("/update-trainer-stats-api/<id>", methods=["POST"])
def update_trainer_stats_api(id):
    try:
        if request.method == 'POST':      
            if request.is_json:            
                data = request.get_json()
                today = data["today"]
                goals = data["goals"]
                notes = data["notes"]
                if not today or not goals or not notes:
                        return jsonify({"success": False, "error": "Missing details"})

                query = {'_id': ObjectId(id)}
                user_data = db.trainers.find_one(query)
                if user_data is not None:
                    # Insert into db #
                    newData = {'$set':{"today":today,
                        "goals": goals,
                        "notes": notes }}
                    db.trainers.update_one(user_data,newData)
                    return jsonify({    
                        "id": str(user_data['_id']),
                        "success": True,
                    })
                else:
                    return jsonify({
                        "success": False, "error": "Invalid User."
                    })
            else:
                return jsonify({"success": False, "msg": "Invalid data format"})
        else:
            return jsonify({"success": False, "msg": "Invalid request"})

    except Exception as e:
        return jsonify({"success": False, "error": str(e)})


# ************ ADD TRAINER AVAILABILITY************
@app.route("/add-trainer-availability-api/<id>", methods=["POST"])
def add_trainer_availability_api(id):
    try:
        if request.method == 'POST':      
            if request.is_json: 
                data = request.get_json()
                session = data["session"]
                date = data["date"]
                starttime = data["start-time"]
                endtime = data["end-time"]
                if not session or not date or not starttime or not endtime:
                        return jsonify({"success": False, "error": "Missing details"})
                query = {'_id': ObjectId(id)}
                user_data = db.trainers.find_one(query)
                if user_data is not None:
                    available_dates = user_data["available_dates"]
                    # output
                    # [{'session': 'boxing', 'date': '17 OCT', 'time': '04-05'}, {'session': 'indoor', 'date': '18 OCT', 'time': '05-06'},
                    # {'session': 'outdoor', 'date': '19 OCT', 'time': '06-07'}, {'session': 'indoor', 'date': '22 OCT', 'time': '07-08'},
                    # {'session': 'boxing', 'date': '24 OCT', 'time': '08-09'}]
                    
                    # Modify old data to updated data 
                    newtime = {"session":session,"date":date,"start-time":starttime, "end-time":endtime, "select-date":False}
                    available_dates.append(newtime)
                    # output
                    # [{'session': 'boxing', 'date': '17 OCT', 'time': '04-05'}, {'session': 'indoor', 'date': '18 OCT', 'time': '05-06'},
                    # {'session': 'outdoor', 'date': '19 OCT', 'time': '06-07'}, {'session': 'indoor', 'date': '22 OCT', 'time': '07-08'},
                    # {'session': 'boxing', 'date': '24 OCT', 'time': '08-09'}, {'session': 'mysession', 'date': '04 Oct', 'time': '04-05'}]

                    # replace old data with new data into db 
                    newData = {'$set':{"available_dates":available_dates }}
                    db.trainers.update_one(query,newData)
                    return jsonify({    
                        "id": str(user_data['_id']),
                        # "available_dates": str(available_dates),
                        "success": True,
                    })
                else:
                    return jsonify({
                        "success": False, "error": "Invalid User."
                    })
            else:
                return jsonify({"success": False, "msg": "Invalid data format"})
        else:
            return jsonify({"success": False, "msg": "Invalid request"})

    except Exception as e:
        return jsonify({"success": False, "error": str(e)})   


# ************ UPDATE TRAINER PACKAGES************
# note:yahan py id mai trainer id ayegi or package mai sirf ["1-training","5-training","10-training","Mud-scheme","training scheme"] in mai se koi 1 value aegi    
@app.route("/update-trainer-packages-api/<id>/<package>", methods=["POST"])
def update_trainer_packages_api(id,package):
    try:
        if request.method == 'POST':      
            if request.is_json:
                data = request.get_json()
                price = data["price"]
                if not price:
                    return jsonify({"success": False, "error": "Missing Price"})
                query = {'_id': ObjectId(id)}
                user_data = db.trainers.find_one(query)
                if user_data is not None:
                    email = user_data["email"]
                    query = {'trainer_email': email ,'name':package}
                    packagedata = db.trainer_packages.find_one(query)
                    if not packagedata:
                        return jsonify ({"success": False, "error":"invalid package name in API"})
                    newData = {'$set':{"price": price }}
                    db.trainer_packages.update_one(packagedata,newData)
                    return jsonify ({"success": True, "newprice":price})
            else:
                return jsonify({"success": False, "msg": "Invalid data format"})
        else:
            return jsonify({"success": False, "msg": "Invalid request"})

    except Exception as e:
        return jsonify({"success": False, "error": str(e)})
    
# ************ GET TRAINER's COMPLETED SESSIONS ************
@app.route("/get-trainer-completed-sessions-api/<id>", methods=["GET"])
def get_trainer_complete_sessions_api(id):
    try:
        if request.method == "GET":
            query = {'trainer_id': id,}
            user_data = db.sessions.find(query)
            if user_data is not None:
                lists = []
                # for loop
                for i in user_data:
                    i.update({"_id": str(i["_id"])})
                    lists.append(i)
                # end forloop
                return jsonify({"success": True, "sessions": lists})                
            else:
                return jsonify({
                    "success": False, "error": "Invalid User."
                })
        else:
            return jsonify({"success": False, "error": "Invalid request"})

    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

# ************ TOGGLE ACTIVATE/DEACTIVATE TRAINER PROFILE ************
@app.route("/toggle-trainer-status-api/<id>", methods=["POST"])
def toggle_trainer_status_api(id):
    try:
        if request.method == "POST":
            if request.is_json:            
                    data = request.get_json()
                    status = data["status"]            
                    query = {'_id': ObjectId(id)}
                    trainer_data = db.trainers.find_one(query)
                    if trainer_data is not None:
                        newStatus = {'$set':{"status":status}}
                        db.trainers.update_one(trainer_data,newStatus)
                        return jsonify({
                            "success": True, "status": status
                        })
                    else:
                        return jsonify({
                            "success": False, "error": "Trainer doesn't exist."
                        })
            else:
                return jsonify({"success": False, "msg": "Invalid data format"})
        else:
            return jsonify({"success": False, "error": "Invalid request"})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

# ************ UPDATE TRAINER RATING API ************
@app.route("/trainer-rating-api/<id>/<sessionid>", methods=["POST"])
def trainer_rating_api(id, sessionid):
    try:
        if request.method == "POST":
            if request.is_json:            
                    data = request.get_json()
                    # Fetch rating from customer 
                    rating = data["rating"]
                    # fetch trainer id             
                    query = {'_id': ObjectId(id)}
                    trainer_data = db.trainers.find_one(query)
                    if trainer_data is not None:
                        # fetch trainer email from trainer id for rating tables 
                        query = {'trainer_email': trainer_data["email"]}
                        # fetch all ratings of that trainer 
                        rating_data = db.ratings.find_one(query)
                        current_rating = rating_data[rating]
                        updated_rating = current_rating + 1
                        # increment 1 rating 
                        newData = {'$set':{rating:updated_rating,}}
                        db.ratings.update_one(rating_data,newData)
                        
                        # now update total ratings
                        query = {'trainer_email': trainer_data["email"]}
                        # fetch all ratings of that trainer 
                        rating_data2 = db.ratings.find_one(query)
                       
                        total_rating = rating_data2["totalRatings"]
                        
                        # formula 
                        score_total = rating_data2["5-star"]*(5) + rating_data2["4-star"]*(4) + rating_data2["3-star"]*(3) + rating_data2["2-star"]*(2) + rating_data2["1-star"]*(1)
                        response_total = rating_data2["5-star"] + rating_data2["4-star"] + rating_data2["3-star"] + rating_data2["2-star"] + rating_data2["1-star"]
                        total_rating = float(round(score_total / response_total, 1))
                        # 3.8  OUTPUT

                        newData = {'$set':{"totalRatings":total_rating}}
                        db.ratings.update_one(rating_data2, newData)

                        # now update ratings into trainers table 
                        query = {'_id': ObjectId(id)}
                        trainer_data = db.trainers.find_one(query)
                        newData = {'$set':{"rating":str(total_rating)}}
                        db.trainers.update_one(trainer_data, newData)

                        # now update ratings into sessions table 
                        query = {'_id': ObjectId(sessionid)}
                        newvalue = {'$set':{"rating":str(rating)}} 
                        db.sessions.update_one(query,newvalue)

                        return jsonify({
                            "success": True, "status": "Ratings Updated.","total Rating":total_rating
                        })
                    else:
                        return jsonify({
                            "success": False, "error": "Trainer doesn't exist."
                        })
            else:
                return jsonify({"success": False, "msg": "Invalid data format"})
        else:
            return jsonify({"success": False, "error": "Invalid request"})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})


# ************ FETCH TRAINER AVAILABLE DATES FOR CUSTOMER API ************
@app.route("/fetch-trainer-available-dates-api/<id>", methods=["GET"])
def fetch_trainer_available_dates_api(id):
    try:
        if request.method == "GET":
            query = {'_id': ObjectId(id)}
            trainer_data = db.trainers.find_one(query)
            if trainer_data is not None:
                return jsonify({
                    "success": True, "availability":trainer_data["available_dates"]
                })
        else:
            return jsonify({"success": False, "error": "Invalid request"})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})


# ************ ADD NEW WALLET CARD FOR CUSTOMER ************
@app.route("/add-walletcard-customer-api/<id>", methods=["POST"])
def add_walletcard_customer_api(id):
    try:
        if request.method == "POST":
            number = request.form.get('number')
            expiryDate = request.form.get('expirydate')
            cvv = request.form.get('cvv')
            cardHolder = request.form.get('cardholder')
            query = {'_id': ObjectId(id)}
            customer_data = db.customers.find_one(query)
            if customer_data is not None:
                db.customers.update({"_id": ObjectId(id)},
                         {"$addToSet": {"wallet_cards": [number,expiryDate,cvv,cardHolder,"#0D135C",False]}})
                customer_data = db.customers.find_one(query)
                return jsonify({
                    "success": True,"wallet_cards":customer_data['wallet_cards'],
                })
        else:
            return jsonify({"success": False, "error": "Invalid request"})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

# ************ ACTIVATE ONE WALLET CARD FOR CUSTOMER ************
# @app.route("/activate-walletcard-customer-api/<id>", methods=["GET"])
# def activate_walletcard_customer_api(id):
#     try:
#         if request.method == "POST":
#             number = request.form.get('number')
#             query = {'_id': ObjectId(id)}
#             customer_data = db.customers.find_one(query)
#             if customer_data is not None:
#                 db.customers.update({"_id": ObjectId(id)},
#                          {"$Set": {"wallet_cards": [number,expiryDate,cvv,cardHolder,"#0D135C",False]}})
#                 customer_data = db.customers.find_one(query)
#                 return jsonify({
#                     "success": True,"wallet_cards":customer_data['wallet_cards'],
#                 })
#         else:
#             return jsonify({"success": False, "error": "Invalid request"})
#     except Exception as e:
#         return jsonify({"success": False, "error": str(e)})


# ************ADD PROMO CODES FOR CUSTOMER ************
@app.route("/add-promo-codes-customer-api/", methods=["POST"])
def add_promo_codes_customer_api():
    try:
        if request.method == "POST":
            name = request.form.get('name')
            discount = request.form.get('discount')
            type = request.form.get('type')
            
            newAccount = {
            "name": name,
            "discount": int(discount),
            "type": type
            }
            query = {'name': name}
            promo = db.promo_codes.find_one(query)
            if promo is None:
                db.promo_codes.insert_one(newAccount)
                return jsonify({
                    "success": True,
                })
            else:
                return jsonify({"success":False, "error":"Promocode already exist."})  
        else:
            return jsonify({"success": False, "error": "Invalid request"})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})


# ************DELETE PROMO CODES FOR CUSTOMER ************
@app.route("/delete-promo-codes-customer-api/<name>", methods=["GET"])
def delete_promo_codes_customer_api(name):
    try:
        if request.method == "GET":
            query = {'name':name}
            promo = db.promo_codes.find_one(query)
            if promo is not None:
                db.promo_codes.delete_one(query)
                return jsonify({"success":True})
            else:
                return jsonify({"success":False,"error":"Promocode doesn't exist"})
              
        else:
            return jsonify({"success": False, "error": "Invalid request"})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})


# ************ADD MUDSCHEME FOR CUSTOMER ************
@app.route("/add-mudscheme-for-customer-api/<id>", methods=["POST"])
def add_mudscheme_for_customer_api(id):
    try:
        if request.method == "POST":
            mudscheme = request.files['mudscheme']

            if mudscheme and allowed_file(mudscheme.filename):
                filename = secure_filename(mudscheme.filename)
                mudscheme.save(os.path.join(app.config['UPLOAD_FOLDER5'], filename))
            else:
                return jsonify({
                    "success": False,
                    "error": "File not found or incorrect format"
                })
            query = {'_id': ObjectId(id)}
            customerdata = db.customers.find_one(query)
            if customerdata is not None:
                newvalues = {"$set": {
                    'mud_scheme': str(filename) }}                
                db.customers.update_one(query, newvalues)
                return jsonify({"success":True,"mudscheme":filename})
            else:
                return jsonify({"success":False, "error":"Invalid customer"})               
        else:
            return jsonify({"success": False, "error": "Invalid request"})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})
    
    # ************CONTACT US FOR TRAINER ************
@app.route("/contact-us-for-trainer-api/<id>", methods=["POST"])
def contact_us_for_trainer_api(id):
    try:
        if request.method == "POST":            
            message = request.form.get("message")
            query= {'_id': ObjectId(id)}
            trainerData = db.trainers.find_one(query)
            if trainerData is not None:
                trainerEmail= trainerData['email']
                newContact = {"message": message, "account": "trainer","trainerid": ObjectId(id),"trainer_email":trainerEmail,"time":datetime.now()}
                db.contact_us.insert_one(newContact)
                return jsonify({"success": True,"status":"message sent successfully"})
            else:
                return jsonify({"success":False, "error":"Invalid trainer"})              
        else:
            return jsonify({"success": False, "error": "Invalid request"})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

    # ************CONTACT US FOR CUSTOMER ************
@app.route("/contact-us-for-customer-api/<id>", methods=["POST"])
def contact_us_for_customer_api(id):
    try:
        if request.method == "POST":            
            message = request.form.get("message")
            query= {'_id': ObjectId(id)}
            customerData = db.customers.find_one(query)
            if customerData is not None:
                customerEmail= customerData['email']
                newContact = {"message": message, "account": "customer","customerid": ObjectId(id),"customer_email":customerEmail,"time":datetime.now()}
                db.contact_us.insert_one(newContact)
                return jsonify({"success": True,"status":"message sent successfully"})
            else:
                return jsonify({"success":False, "error":"Invalid trainer"})              
        else:
            return jsonify({"success": False, "error": "Invalid request"})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

# ************ PROMO CODES VALIDATION ************
@app.route("/validate-promocode-api", methods=["POST"])
def validate_promocode_api():
    try:
        if request.method == "POST":
                code = request.form.get("code")
                price = request.form.get("price")
                query= {'name': code}
                promo_codes = db.promo_codes.find_one(query)
                if promo_codes is not None:
                    discount = promo_codes['discount']
                    discount_percent = int(price) * discount / 100
                    afterdiscount = int(price) - int(discount_percent)
                    if afterdiscount is not None:
                        newPrice = afterdiscount
                        return jsonify({
                            "success": True, "newPrice": newPrice
                        })
                    else:
                        return jsonify({"success":False, "error":"calculation error"}) 
                else:
                    return jsonify({"success":False, "error":"Invalid Promo Code"})
        else:
            return jsonify({"success": False, "error": "Invalid request"})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

# ************ MARK COMPLETE SESSION ************
@app.route("/mark-complete-session/<string:bookingid>")
def mark_complete_session(bookingid):
    try:
        query = {"_id": ObjectId(bookingid)}
        booking = db.bookings.find_one(query)
        db.bookings.update(
                query,
                {"$set": {"completed": True}}
            )

        newValues = {
                'customer_id': booking['customer_id'],
                'trainer_id': booking['trainer_id'],
                'dateAdded': booking['dateAdded'],
                'trainer_name': booking['trainer_name'],
                'customer_name': booking['customer_name'],
                'location': booking['location'],
                'package': booking['package_type'],
                'customer_profile_pic': booking['customer_profile_pic'],
                'customer_profile_pic_path': "static/images/customers/profile-pics",
                'trainer_profile_pic': booking['trainer_profile_pic'],
                'trainer_profile_pic_path': "static/images/trainers/trainer-profile-pics",
                'booking_time': booking['booking_time'],
                'date': booking['date'],
                'rating':"pending",
                'completed': True,

        }
        db.sessions.insert_one(newValues)
        return jsonify({"success": True,})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

# ************ GET CUSTOMER's COMPLETED SESSIONS ************
@app.route("/get-customer-completed-sessions-api/<id>", methods=["GET"])
def get_customer_complete_sessions_api(id):
    try:
        if request.method == "GET":
            query = {'customer_id': id, 'completed':True}
            user_data = db.sessions.find(query)
            if user_data is not None:
                lists = []
                # for loop
                for i in user_data:
                    i.update({"_id": str(i["_id"])})
                    lists.append(i)
                # end forloop
                return jsonify({"success": True, "sessions": lists})                
            else:
                return jsonify({
                    "success": False, "error": "Invalid User."
                })
        else:
            return jsonify({"success": False, "error": "Invalid request"})

    except Exception as e:
        return jsonify({"success": False, "error": str(e)})


# ************ FORGOT PASSWORD API ************
@app.route("/forgot-password-api", methods=["POST", "GET"])
def forgot_password_api():
    try:
        if request.is_json:
            if request.method == "POST":
                data = request.get_json()
                email = data["email"]
                query = {"email": email}
                customer_data = db.customers.find_one(query)
                company_data = db.company.find_one(query)
                trainer_data = db.trainers.find_one(query)
                if customer_data is None and company_data is None and trainer_data is None:
                    return jsonify({"success":False, "error":"User didn't exist with this email"})
                if customer_data is not None:
                    code = id_generator2()
                    msg = Message("Gym! Forgot Password Code", recipients=[email])
                    msg.html = str("To update password of your account use the following code "
                                    "as confirmation code " + str(code))
                    mail.send(msg)
                    newvalues = {"userid": customer_data['_id'], "code":code, "user_account":"customer", "status":True, "time":datetime.now()}
                    db.change_password.insert_one(newvalues)
                    return jsonify(
                        {"msg": "Please check your email to update your password.",
                            "name": customer_data["first_name"], "email": customer_data['email'], 'userid':str(customer_data['_id']),
                            "success": True})
                if company_data is not None:
                    # if email == user_data1['email']:
                    code = id_generator2()
                    msg = Message("Gym! Forgot Password Code", recipients=[email])
                    msg.html = str("To update password of your account use the following code "
                                    "as confirmation code " + str(code))
                    mail.send(msg)
                    newvalues = {"userid": company_data['_id'], "code":code, "user_account":"company", "status":True, "time":datetime.now()}
                    db.change_password.insert_one(newvalues)
                    # cursor.execute('''insert into change_password (user_id, code) 
                    # values (%s, %s);''', [user_data[0], code])
                    return jsonify(
                        {"msg": "Please check your email to update your password.",
                            "name": company_data["company_name"], "email": company_data['email'], 'userid':str(company_data['_id']),
                            "success": True})
                    # else:
                    #     return jsonify({"success": False, "error": "Invalid contact number of user."})
                if trainer_data is not None:
                    # if email == user_data1['email']:
                    code = id_generator2()
                    msg = Message("Gym! Forgot Password Code", recipients=[email])
                    msg.html = str("To update password of your account use the following code "
                                    "as confirmation code " + str(code))
                    mail.send(msg)
                    newvalues = {"userid": trainer_data['_id'], "code":code, "user_account":"trainer", "status":True, "time":datetime.now()}
                    db.change_password.insert_one(newvalues)
                    # cursor.execute('''insert into change_password (user_id, code) 
                    # values (%s, %s);''', [user_data[0], code])
                    return jsonify(
                        {"msg": "Please check your email to update your password.",
                            "name": trainer_data["first_name"], "email": trainer_data['email'], 'userid':str(trainer_data['_id']),
                            "success": True})
                    # else:
                    #     return jsonify({"success": False, "error": "Invalid contact number of user."})
                else:
                    return jsonify({"success": False, "error": "Invalid User or user doesn't exist."})
            else:
                return jsonify({"success": False, "error": "Invalid request"})
        else:
            return jsonify({"success": False, "error": "Invalid request not json format"})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

# ************ UPATE PASSWORD FROM EMAIL CODE ************
@app.route("/update-password-api", methods=["POST", "GET"])
def update_password_api():
    try:
        if request.is_json:
            if request.method == "POST":
                data = request.get_json()
                user_id = data["user_id"]
                email = data["email"]
                password = data["newpassword"]
                code = data["code"]
                query = {"email": email}
                customer_data = db.customers.find_one(query)
                company_data = db.company.find_one(query)
                trainer_data = db.trainers.find_one(query)
                if customer_data is None and company_data is None and trainer_data is None:
                    return jsonify({"success":False, "error":"User didn't exist with this email"})
                if customer_data is not None:
                    query = {"userid":ObjectId(user_id), "status":True}
                    user_code = db.change_password.find_one(query)
                    if user_code is not None:
                        if code == user_code['code']:
                            if user_code['status'] is not False:
                                hash_password = generate_password_hash(password)
                                newvalues = {
                                            "$set": {
                                                'password': password,
                                                'hash': hash_password
                                            }
                                        }
                                query = {'_id': ObjectId(user_id)}
                                db.customers.update_one(query,newvalues)
                                newvalues = {
                                            "$set": {
                                                'status': False,
                                            }
                                        }
                                query = {'_id': user_code['_id']}
                                db.change_password.update_one(query,newvalues)
                                return jsonify({"success": True, "message": "Password Updated "
                                                                            "successfully."})
                            else:
                                return jsonify({"success": False, "error": "Code is already used."})
                        else:
                            return jsonify({"success": False, "error": "Invalid Code."})
                    else:
                        return jsonify({"success": False, "error": "No change password request "
                                                                "received."})
                if company_data is not None:
                    # cursor.execute('''select user_id, code, status from change_password where 
                    # user_id=%s and status="notused" order by timestamp desc limit 1;''', [user_id])
                    # user_code = cursor.fetchone()
                    query = {"userid":ObjectId(user_id), "status":True}
                    user_code = db.change_password.find_one(query)
                    if user_code is not None:
                        if code == user_code['code']:
                            if user_code['status'] is not False:
                                # cursor.execute('''Update users set password=%s
                                # where user_id=%s  and email=%s;''', [password,
                                #                                      user_id, email])
                                hash_password = generate_password_hash(password)
                                newvalues = {
                                            "$set": {
                                                'password': password,
                                                'hash': hash_password
                                            }
                                        }
                                query = {'_id': ObjectId(user_id)}
                                db.company.update_one(query,newvalues)
                                newvalues = {
                                            "$set": {
                                                'status': False,
                                            }
                                        }
                                query = {'_id': user_code['_id']}
                                db.change_password.update_one(query,newvalues)
                                return jsonify({"success": True, "message": "Password Updated "
                                                                            "successfully."})
                            else:
                                return jsonify({"success": False, "error": "Code is already used."})
                        else:
                            return jsonify({"success": False, "error": "Invalid Code."})
                    else:
                        return jsonify({"success": False, "error": "No change password request "
                                                                "received."})
                if trainer_data is not None:
                    # cursor.execute('''select user_id, code, status from change_password where 
                    # user_id=%s and status="notused" order by timestamp desc limit 1;''', [user_id])
                    # user_code = cursor.fetchone()
                    query = {"userid":ObjectId(user_id), "status":True}
                    user_code = db.change_password.find_one(query)
                    if user_code is not None:
                        if code == user_code['code']:
                            if user_code['status'] is not False:
                                # cursor.execute('''Update users set password=%s
                                # where user_id=%s  and email=%s;''', [password,
                                #                                      user_id, email])
                                hash_password = generate_password_hash(password)
                                newvalues = {
                                            "$set": {
                                                'password': password,
                                                'hash': hash_password
                                            }
                                        }
                                query = {'_id': ObjectId(user_id)}
                                db.trainers.update_one(query,newvalues)
                                newvalues = {
                                            "$set": {
                                                'status': False,
                                            }
                                        }
                                query = {'_id': user_code['_id']}
                                db.change_password.update_one(query,newvalues)
                                return jsonify({"success": True, "message": "Password Updated "
                                                                            "successfully."})
                            else:
                                return jsonify({"success": False, "error": "Code is already used."})
                        else:
                            return jsonify({"success": False, "error": "Invalid Code."})
                    else:
                        return jsonify({"success": False, "error": "No change password request "
                                                                "received."})
            else:
                return jsonify({"success": False, "error": "Invalid request"})
        else:
            return jsonify({"success": False, "error": "Invalid request not a json type data."})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})




# ************************************* CHATING START ***********************************************

@app.route('/chat-api', methods=["GET", "POST"])
def chatapi():
        try:
            if request.method == "POST":
                return redirect("/chat")
            else:
                username = ""
                # if session.get("username"):
                #     username = session.get("username")
                if request.args.get("username"):
                    username = request.args.get("username")
                customerid = ""
                # if session.get("userid"):
                #     userid = session.get("userid")
                if request.args.get("customerid"):
                    customerid = request.args.get("customerid")
                # chatTable = mydb["chating"]
                chatTable = db.chating
                # userTable = mydb["customers"]
                userTable = db.customers
                # trainerTable = mydb["trainers"]
                trainerTable = db.trainers
                trainerid = "NULL"
                if request.args.get("trainerid"):
                    trainerid = request.args.get('trainerid')
                if request.args.get("userType"):
                    userType = request.args.get("userType")
                # if customers wants to start a chat with trainer
                if trainerid != "NULL" and userType == "customer":
                    chatdata = chatTable.find_one({"customerid" :ObjectId(customerid), "trainerid": ObjectId(trainerid)})
                    trainerdata = trainerTable.find_one({"_id": ObjectId(trainerid)})
                    if chatdata == None:
                        roomname = id_generator()
                        chatTable.insert_one({"customerid": ObjectId(customerid), "customerName": username, "trainerid":
                            ObjectId(trainerid), "user2name": trainerdata["first_name"], "lastmessagecount": 0,
                                              "roomname": roomname,"accepted": False,
                                              "lastmessagetime": datetime.now(), "messages": []})
                # if trainer wants to start a chat with customer 
                elif customerid != "NULL" and userType == "trainer":
                    chatdata = chatTable.find_one({"customerid" :ObjectId(customerid), "trainerid": ObjectId(trainerid)})
                    customerdata = userTable.find_one({"_id": ObjectId(customerid)})
                    trainerdata = trainerTable.find_one({"_id": ObjectId(trainerid)})
                    if chatdata == None:
                        roomname = id_generator()
                        chatTable.insert_one({"customerid": ObjectId(customerid), "customerName": customerdata["first_name"], "trainerid":
                            ObjectId(trainerid), "user2name": trainerdata["first_name"], "lastmessagecount": 0,
                                            "roomname": roomname,"accepted": True,
                                            "lastmessagetime": datetime.now(), "messages": []})

                

                if userType == "trainer":
                    data = chatTable.find({"trainerid": ObjectId(trainerid)})
                elif userType == "customer":
                    data = chatTable.find({"customerid": ObjectId(customerid)})

                newdata = []
                for chats in data:
                    chats.update({"_id": str(chats["_id"]), "trainerid": str(chats["trainerid"]), "customerid": str(chats["customerid"])})
                    newdata.append(chats)
                return jsonify({"data":newdata, "username":username, "userid":customerid, "trainerid":trainerid,
                })
        except Exception as e:
            return jsonify({"status": str(e)})


@socketio.on('app event')
def handle_my_custom_event(json, methods=['GET', 'POST']):
    print('received app event: ' + str(json))

    username = ""
    if "user_name" in json:
        username = json["user_name"]
    
    curuser = json["userid"]
    print(curuser)
    roomname = ""
    if "roomname" in json:
        roomname = json["roomname"]
        join_room(roomname)
    # userid = session.get("status")
    chatTable = db.chating

    print(json["message"])
    if json["message"] != "connected":
        chatTable.update(
            {"roomname": roomname},
            {"$set": {"lastmessagetime": datetime.now().time().strftime("%H:%M:%S:%f")}}
        )
        chatTable.update({"roomname": roomname},
                         {"$addToSet": {"messages": {"status": curuser, "message": json["message"], "type": "text",
                                                     "timeStamp": datetime.now().time().strftime("%H:%M:%S:%f"),
                                                     "time": datetime.now().time().strftime("%H:%M")}}})

    # if status == "userlogin":
    socketio.emit('my response', json, room=roomname, callback=json)
    # socketio.send(json, to=roomname)
    # else:
    #     socketio.emit('doctor response', json, room=roomname, callback=json, usernamess=str(username),
    #                   username22=str(curuser))


# extra 
@app.route("/getmessages", methods=["GET"])   #notused yet
def getmessages():
    trainerid = request.args.get("trainerid")
    # sellerid = request.args.get("sellerid")
    # print(userid, sellerid)
    chatTable = db.chating
    # status = session.get("status")
    # print(status)
    messages = chatTable.find_one({"trainerid": ObjectId(trainerid)}, {"messages": 1,"user2name": 1})
    # print(messages)
    if messages is not None:
        messages = messages["messages"]    
    # print(messages)
    return jsonify({"messages": messages})
# extra 
# @app.route("/getmessages", methods=["GET"])
# def getmessages():
#     userid = request.args.get("id")
#     sellerid = request.args.get("sellerid")
#     print(userid, sellerid)
#     chatTable = db.chating
#     status = session.get("status")
#     print(status)
#     messages = chatTable.find_one({"user1": ObjectId(userid), "user2": ObjectId(sellerid)}, {"messages": 1,
#                                       "user1name": 1})
#     print(messages)
#     if messages is not None:
#         messages = messages["messages"]    
#     print(messages)
#     return jsonify({"messages": messages})

# ************************************* CHATING END ***********************************************


# ************************************* STRIPE START ***********************************************
@app.route("/payment-api", methods=["POST"])
def payment_api():
    # try:
    if request.method == "POST":
        if request.is_json:
            data = request.get_json()
            email = data['email'].lower()
            customerid = data['customerid']
            customername = data['customername']
            token = data['token']
            package = data['package']
            amount = data['amount']
            time = datetime.now()
            apiammount = float(amount) * 100                    
                        
            customer = stripe.Customer.create(
                        payment_method=token,
                        invoice_settings={
                        'default_payment_method': token,
                        },
            )
            
            # charge = stripe.Charge.create(
            #               customer=customer.id,
            #               amount=amount,
            #               currency="sek",
            #               source= token,
            #             )
            charge = stripe.PaymentIntent.create(
                customer=customer.id,
                amount=int(apiammount),
                currency='sek',
                payment_method_types=['card']
                )
            confirmpaymentmethod = stripe.PaymentIntent.confirm(
  charge.id,
  payment_method=token,
)
            # paymentrec = stripe.PaymentIntent.capture(
            #                     confirmpaymentmethod.id,
            #             )
            print(charge)
            if confirmpaymentmethod is not None:
                newPayment = {
                    "customerid": ObjectId(customerid),
                    "customername": customername,
                    "email": email,
                    "package": package,
                    "amount": amount,
                    "transaction_time": time,
                }
                db.payments.insert_one(newPayment)
                return jsonify ({"success":True, "status":"Transaction complete successfuly"})
        else:
            return jsonify({"success": False, "error": "Invalid json format."})
    else:
        return jsonify({"success": False, "error": "Invalid request"})
    # except Exception as e:
    #     return jsonify({"success": False, "error": str(e)})

# ************************************* STRIPE END ***********************************************


if __name__ == '__main__':
    socketio.run(app)
