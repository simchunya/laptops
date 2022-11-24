from flask import Flask, render_template, url_for, request, redirect, session
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, PasswordField, EmailField, IntegerField, TextAreaField
from wtforms.validators import ValidationError, DataRequired, Length, EqualTo, Email

from werkzeug.security import check_password_hash, generate_password_hash
import sqlite3
from helpers import *





app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///test.db'
db = SQLAlchemy(app)
app.config['SECRET_KEY']='LongAndRandomSecretKeyandalaptop'
app.secret_key='LongAndRandomSecretKey'
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"



#form when user gets the default registration page
class RegistrationForm(FlaskForm):
    email = EmailField(label=('Email'),
        validators=[DataRequired(), Email(), Length(min=3, max=64)]) 
    password = PasswordField(label=('Password'), 
        validators=[DataRequired(), 
        Length(min=8, message='Password should be at least %(min)d characters long')])
    confirm_password = PasswordField(
        label=('Confirm Password'), 
        validators=[DataRequired(message='*Required'),
        EqualTo('password', message='Both password fields must be equal!')]) 
    name = StringField(label=('Name'),
        validators=[DataRequired(), 
        Length(min=3, max=64, message='Name length must be between %(min)d and %(max)dcharacters')])
    contact_number = StringField(label=('Contact Number'), 
        validators=[DataRequired(), Length(max=120)])
    company_name= StringField(label=('Company Name'), 
        validators=[Length(max=30)])
    uen_number= StringField(label=('Company UEN'), 
        validators=[Length(max=30)])
    address1 = StringField(label=('Address'), 
        validators=[DataRequired(), Length(max=120)])
    address2 = StringField(label=('Floor and Unit'), 
        validators=[Length(max=120)])
    address3 = StringField(label=('Postal'), 
        validators=[Length(min=6),Length(max=6)])
    submit = SubmitField(label=('Submit'))

class AddproductForm(FlaskForm):
    name = StringField(label=('Name'),
        validators=[DataRequired()])
    description = TextAreaField(label=('Description'),
        validators=[DataRequired()])
    price = IntegerField(label=('Price'),
        validators=[DataRequired()])
    submit = SubmitField(label=('Submit'))

#class for database
class Profile(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(64))
    password = db.Column(db.String(64))
    name = db.Column(db.String(64))
    contact_number = db.Column(db.String(64))
    company_name = db.Column(db.String(64), nullable=True)
    uen_number = db.Column(db.String(64), nullable=True)
    address1 = db.Column(db.String(64), nullable=True)
    address2 = db.Column(db.String(64), nullable=True)
    address3 = db.Column(db.String(6), nullable=True)

    def __repr__(self):
        return '<profile %r>' % self.id

class Products(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64))
    description = db.Column(db.String(2000))
    price = db.Column(db.Integer)

    def __repr__(self):
        return '<products %r>' % self.id

class Invoice(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    customer_id = db.Column(db.Integer)

    def __repr__(self):
        return '<invoice %r>' % self.id


#first page upon going to the website       
@app.route('/', methods=['POST', 'GET'])
def index():
        return render_template('index.html')

@app.route('/addproducts', methods=['POST', 'GET']) 
@login_required
def addproducts():
    form = AddproductForm()
    if request.method == 'POST':
        name = request.form["name"]
        description = request.form["description"] 
        price = request.form["price"]

        new_product = Products(name=name, description=description, price=price)
        
        try:
            db.session.add(new_product)
            db.session.commit()
            return redirect('/addproducts')
        except:
            return "There was an error adding your product"

    elif request.method == 'GET':
        products = Products.query.order_by(Products.id).all()
        return render_template('addproducts.html', products=products, form=form)

@app.route('/products', methods=['POST', 'GET']) 
@login_required
def products():

    if request.method == "POST":
        
        if request.form.get("qty1") != None: 
            try:
                session["cart1"] += int(request.form.get("qty1"))
            except:
                session["cart1"] = 0
                session["cart1"] += int(request.form.get("qty1"))
        if request.form.get("qty2") != None:
            try:
                session["cart2"] += int(request.form.get("qty2"))
            except:
                session["cart2"] = 0
                session["cart2"] += int(request.form.get("qty2"))
        return redirect('/cart')

    elif request.method == 'GET':
        product1 = Products.query.get_or_404(1)
        name1 = product1.name
        description1 = product1.description
        price1 = product1.price

        product2 = Products.query.get_or_404(2)
        name2 = product2.name
        description2 = product2.description
        price2 = product2.price

        return render_template('products.html', name1=name1, description1=description1, price1=price1, name2=name2, description2=description2, price2=price2)

@app.route('/cart', methods=['POST', 'GET']) 
@login_required
def cart():
    products = Products.query.order_by(Products.id).all()
    product1 = Products.query.get_or_404(1)
    product2 = Products.query.get_or_404(2)
    total = product1.price * session["cart1"] + product2.price * session["cart2"]
    return render_template('cart.html',total=total, products=products, cart1=session["cart1"], cart2=session["cart2"])

@app.route('/removecart/<int:id>', methods=['POST', 'GET']) 
@login_required
def removecart(id):
    session[f"cart{id}"] = 0
    return redirect('/cart')

@app.route('/checkout', methods=['POST', 'GET']) 
@login_required
def checkout():

    class Product_in_cart():
        def __init__(self,id,name,price,qty,total):
            self.id = id
            self.name = name
            self.price = price
            self.qty = qty
            self.total = total

    #populate products in invoice
    product1 = Products.query.get_or_404(1)
    product2 = Products.query.get_or_404(2)
    
    list_of_items= []
    
    if session["cart1"] > 0:
        total = session["cart1"] * product1.price
        producta = Product_in_cart(product1.id,product1.name, product1.price, session["cart1"], total)
        list_of_items.append(producta)

    if session["cart2"] > 0:
        total = session["cart2"] * product2.price
        productb = Product_in_cart(product2.id,product2.name, product2.price, session["cart2"], total)
        list_of_items.append(productb)

    #get customer details
    profile = Profile.query.get_or_404(session["user_id"])

    #get last invoice number
    try:
        #getting the row object
        row = db.session.execute(db.select(Invoice.id).order_by(Invoice.id.desc())).first()
        #taking the value from row object
        for invoice in row:
            last_invoice = row.id
    
    #in case this is the first invoice
    except:
        print("This is the first invoice")
        last_invoice_number = 0

    invoice_number = int(last_invoice) + 1

    makepdf(invoice_number, profile.name,profile.contact_number, (profile.address1 + " " + profile.address2 + " " + profile.address3), profile.company_name, profile.uen_number, list_of_items)
    
    new_invoice = Invoice(customer_id=profile.id)
        
    try:
        db.session.add(new_invoice)
        db.session.commit()
        
    except:
        return "There was an error adding the invoice to our database. Please contact customer service"

    # send the invoice to the customer
    send_email(profile.email, profile.name, invoice_number)
    session["cart1"] = 0
    session["cart2"] = 0
    return redirect('/')

@app.route('/profile', methods=['POST', 'GET'])
@login_required
def profile():
    profile = Profile.query.get_or_404(session["user_id"])
    
    form = RegistrationForm()

    form['email'].data = profile.email
    form['name'].data = profile.name
    form['contact_number'].data = profile.contact_number
    form['company_name'].data= profile.company_name
    form['uen_number'].data = profile.uen_number
    form['address1'].data = profile.address1
    form['address2'].data = profile.address2
    form['address3'].data = profile.address3

    if request.method == "POST":
        profile.email = request.form.get("email")
        profile.name = request.form.get("name")
        profile.contact_number = request.form.get("contact_number")
        profile.uen_number = request.form.get("uen_number")
        profile.company_name = request.form.get("company_name")
        profile.address1 = request.form.get("address1")
        profile.address2 = request.form.get("address2")
        profile.address3 = request.form.get("address3")

        try:
            db.session.commit()
            return redirect('/')
        except:
            return 'there was a problem updating your profile'
    elif request.method == 'GET':
        return render_template('profile.html', form=form)

@app.route('/login', methods=['POST', 'GET'])
def login():
    #Log user in

    # Forget any user_id
    session.clear()
    

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("email"):
            return apology("must provide email", 403)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 403)

        # Query database for username
        try:
            # executing SQL syntax
            # connecting to the database
            connection = sqlite3.connect("test.db")
            # cursor
            crsr = connection.cursor() 
            # execute the SQL command
            crsr.execute("SELECT * FROM profile WHERE email = ?", (request.form.get("email"),))
            # store all the fetched data in the ans variable
            ans = list(crsr.fetchall()[0])
            
            # close the connection
            connection.close()
            #End of SQL  
        except:
            return apology("invalid username", 403)
        # Ensure username exists and password is correct
        if not check_password_hash(ans[2], request.form.get("password")):
            return apology("invalid password", 403)

        # Remember which user has logged in
        session["user_id"] = ans[0]
        session["email"] = request.form.get("email")
        session["name"] = ans[3]
        session["cart1"] = 0
        session["cart2"] = 0
        # Redirect user to home page
        return redirect("/products")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")

@app.route('/register', methods=['POST', 'GET']) 
def register():
    form = RegistrationForm()
    
    if request.method == 'POST':
            
            hash = generate_password_hash(request.form['password'])
            new_profile = Profile(email=request.form['email'], password=hash, name=request.form['name'], contact_number=request.form['contact_number'], company_name=request.form['company_name'], uen_number=request.form['uen_number'], address1=request.form['address1'], address2=request.form['address2'], address3=request.form['address3'])

            try:
                db.session.add(new_profile)
                db.session.commit()
                return redirect('/registerationsuccess')
            except:
                return "There was an error registering"
                
    elif request.method == 'GET':
        
        return render_template('register.html', form=form)

@app.route('/registerationsuccess', methods=['GET']) 
def registrationsuccess():
    return render_template('registrationsuccess.html')

@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")

@app.route('/delete/<int:id>')
def delete(id):
    
    product_to_delete = Products.query.get_or_404(id)
    
    try:
        db.session.delete(product_to_delete)
        db.session.commit()
        return redirect('/addproducts')
    except:
        return 'there was a problem deleting the product'

#update product
@app.route('/update/<int:id>', methods=['POST', 'GET'])
def update(id):
    products = Products.query.get_or_404(id)
    form = AddproductForm()
    if request.method == 'POST':
        products.name = request.form["name"]
        products.description = request.form["description"]
        products.price = request.form["price"]
        
        try:
            db.session.commit()
            return redirect('/addproducts')
        except:
            return 'there was a problem updating the product'

    elif request.method == 'GET':
        form.name.data = products.name
        form.price.data = products.price
        form.description.data = products.description
        return render_template('update.html', products = products, form = form)


if __name__ == "__main__":
    app.run(debug=True,use_debugger=True,use_reloader=True)