# Assignment: An Online Shop
"""
An eCommerce website with payment processing.
"""
import sqlite3

import sqlalchemy.exc

"""
Using what you have learnt by building the blog website using Flask, you're now going to build your own eCommerce website. 
Your website needs to have a working cart and checkout.

It should be able to display items for sale and take real payment from users.
It should have login/registration authentication features.

Here is an example website:
https://store.waitbutwhy.com/
You should consider using the Stripe API:
https://stripe.com/docs/payments/checkout
"""

"""
Y/1. Login/Register + Authenticating User + Loading Cart (create cart for user once registered; how?)
Y/1.1. After register/login, create cart and tag to current user id using foreign key
Y/2. Shop + Item interface (Bootstrap) -- Create random fake shop with random items
Y/2.1. Add items to cart 
    Y--- query item id and tag cart id to it 
    Y--- show notification once added to cart;
    Y--- display total # of items in cart
Y/3. Cart: Display added items + Total Price 
Y/3.1. Checkout + Address + Delivery
Y/3.2. Clear cart once sign out/purchase complete
4. Payment methods - Add payment details + Save payment details in database
5. Make Payment through API

#Database foreign key -foreign key SQLAlchemy
https://docs.sqlalchemy.org/en/14/orm/basic_relationships.html

E-commerce template (with cart)
https://startbootstrap.com/template/shop-homepage

How to push footer to bottom of page
Center form css
HTML form prefill

How to print number with 2 decimal places in python
How to check if last decimal is 0

Flask flash message for certain duration
Flask flash message set timer/ fade out
"""

from flask import Flask, render_template, request, url_for, redirect, flash, send_from_directory
from werkzeug.security import generate_password_hash, check_password_hash
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin, login_user, LoginManager, login_required, current_user, logout_user
from sqlalchemy import Column, ForeignKey, Integer, Table
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy import insert

import stripe
import os

stripe.api_key = "sk_test_51LL3eDI6b7ZbumIjMlffZoiacfhKc3qopcq6CQ582i7Sr4YjBtrQ951j1tXVpckrnofVAK3J8sVMoWGp0IXbZuXw00xdVayDam"
# stripe.api_key = "pk_test_51LL3eDI6b7ZbumIj3lxRq9oVOPuHSmCDynRN8pyXlF9XRS1AjBgNRRq7HSrT1BX6ZaDFEh3FvSYbqJd6wNDLkvyf001KXsxKWq"
app = Flask(__name__)

app.config['SECRET_KEY'] = 'any-secret-key-you-choose'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
Base = declarative_base()

user_cart_items = []


# --------------------------------------------STORE DATABASE------------------------------------------------------#

# One User to One Address
# Need foreign key to reference to User Table
class User(UserMixin, db.Model):
    __tablename__ = "user"
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(100))
    first_name = db.Column(db.String(1000))
    last_name = db.Column(db.String(1000))
    user_address = relationship("User_Address_Payment", back_populates="user", uselist=False)
    user_cart = relationship("Cart", back_populates="user", uselist=False)


class User_Address_Payment(db.Model):
    __tablename__ = "user_address"
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(1000))
    last_name = db.Column(db.String(1000))
    email = db.Column(db.String(100), unique=True)
    address = db.Column(db.String(1000))
    postal_code = db.Column(db.String(20))
    phone_num = db.Column(db.String(20))
    user_id = Column(Integer, ForeignKey("user.id"), unique=True)
    user = relationship("User", back_populates="user_address")


# LINK Shop_Items & Cart (for particular user : One User to One Cart)
# -- Want to be able to add multiple items to cart & different carts
# MANY - MANY RELATIONSHIP... HOW TO IMPLEMENT?
# https://docs.sqlalchemy.org/en/14/orm/basic_relationships.html#many-to-many
# Association Object instead of Association Table (cant insert or access values)
# One Cart to Many Shop Item ; One Shop Item to Many Cart
# eg. Stores Various Items with id = 1/2/3 etc...

class Cart_Items(db.Model):
    __tablename__ = "cart_items"
    cart_id = db.Column(db.Integer(), db.ForeignKey("cart.id"), primary_key=True)
    item_id = db.Column(db.Integer(), db.ForeignKey("shopree.id"), primary_key=True)
    quantity = db.Column(db.Integer())
    shop_item = relationship("Shop_Items", back_populates="cart_s")
    cart = relationship("Cart", back_populates="shop_items")


class Cart(db.Model):
    __tablename__ = "cart"
    # __abstract__ = True
    id = db.Column(db.Integer, primary_key=True)
    cart_desc = db.Column(db.String(1000))
    user_id = Column(Integer, ForeignKey("user.id"))
    user = relationship("User", back_populates="user_cart")
    shop_items = relationship("Cart_Items", back_populates="cart")


class Shop_Items(db.Model):
    __tablename__ = "shopree"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(1000), unique=True)
    img_url = db.Column(db.String)
    description = db.Column(db.String(1000))
    price = db.Column(db.Float)
    quantity = db.Column(db.Integer)
    stripe_id = db.Column(db.String)
    stripe_id_price = db.Column(db.String)
    # cart_id = Column(Integer, ForeignKey("cart.id"))
    cart_s = relationship("Cart_Items", back_populates="shop_item")


# #How to reference database item from another database using foreign/primary key?
"""Create seperate table for payment & cart and reference to relevant user using foreign/primary key"""
# #Set default values for payment & cart as None
# #Save payment details as JSON; name, card name, card #, card CVV etc?
# payment = db.Column()
# # Save cart details as foreign key to items database?
# cart = db.Column()
db.create_all()

item_0 = Shop_Items(
    name="Squirtle",
    img_url="https://images-wixmp-ed30a86b8c4ca887773594c2.wixmp.com/f/67f84de8-d494-455a-8a98-bf116e96d1f7/dcwjuhc-82806ad4-a7ad-4f1c-9770-35f559db6fbf.png/v1/fill/w_1024,h_1191,strp/cute_squirtle_by_oukokudesign_dcwjuhc-fullview.png?token=eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJzdWIiOiJ1cm46YXBwOjdlMGQxODg5ODIyNjQzNzNhNWYwZDQxNWVhMGQyNmUwIiwiaXNzIjoidXJuOmFwcDo3ZTBkMTg4OTgyMjY0MzczYTVmMGQ0MTVlYTBkMjZlMCIsIm9iaiI6W1t7ImhlaWdodCI6Ijw9MTE5MSIsInBhdGgiOiJcL2ZcLzY3Zjg0ZGU4LWQ0OTQtNDU1YS04YTk4LWJmMTE2ZTk2ZDFmN1wvZGN3anVoYy04MjgwNmFkNC1hN2FkLTRmMWMtOTc3MC0zNWY1NTlkYjZmYmYucG5nIiwid2lkdGgiOiI8PTEwMjQifV1dLCJhdWQiOlsidXJuOnNlcnZpY2U6aW1hZ2Uub3BlcmF0aW9ucyJdfQ.XLg3YPmjoahRtHKrgvbVU5UeUL6b7zeZ4V8uSeMHgqA"
    ,
    description="Fun is best in little squirts",
    price=9.60,
    quantity=99,
    stripe_id="prod_M3AuLoHHrJGIud",
    stripe_id_price="price_1LL4YiI6b7ZbumIjCrClKa6z"
)

item_1 = Shop_Items(
    name="Charbulsaur",
    img_url="https://cdn.vox-cdn.com/thumbor/Dx9mZyycmNANH418EfmctIEB2aQ=/800x0/filters:no_upscale()/cdn.vox-cdn.com/uploads/chorus_asset/file/6828695/unnamed__1_.0.jpg",
    description="Charbulsaur Toy; A inter-breed of charmander & bulbasaur",
    price=10.00,
    quantity=55,
    stripe_id="prod_M3AvrJAW9tgQK8",
    stripe_id_price="price_1LL4ZII6b7ZbumIjZ7JxLRwF"
)

item_2 = Shop_Items(
    name="Snorlax",
    img_url="https://assets.pokemon.com/assets/cms2/img/pokedex/full/143_f2.png",
    description="The perfect cuddle buddy",
    price=69.69,
    quantity=69,
    stripe_id="prod_M3Av7anonsnhUh",
    stripe_id_price="price_1LLKteI6b7ZbumIjI2wxX2h9"
)
new_cart = Cart(
    cart_desc="Guest",
    user_id=0,
)
try:
    db.session.add(new_cart)
    db.session.add(item_0)
    db.session.add(item_1)
    db.session.add(item_2)
    db.session.commit()
except:
    pass

# --------------------------------------------USER AUTHENTICATION------------------------------------------------------#
login_manager = LoginManager()
login_manager.init_app(app)


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


@app.route('/login', methods=["GET", "POST"])
def login():
    global user_cart_items
    if request.method == "POST":
        print(request.form.get("email"))
        user = User.query.filter_by(email=request.form.get("email")).first()
        print(user)
        # print(user.password)
        if not user:
            flash("That email is not in our collection, please try again.")
            return redirect(url_for('login'))
        elif check_password_hash(user.password, request.form.get("password")):
            login_user(user)
            print("LOGGED IN")
            # is_authenticated = True
            return redirect(url_for("cart", user_first=user.first_name, user_last=user.last_name,
                                    logged_in=current_user.is_authenticated, user_cart_items=user_cart_items))
        else:
            flash("WRONG EMAIL OR PASSWORD!")
            print("WRONG EMAIL OR PASSWORD!")
            return redirect(url_for("login"))

    return render_template("login.html", user_cart_items=user_cart_items)


@app.route('/logout')
def logout():
    if current_user.is_authenticated:
        clear_cart = db.session.query(Cart_Items).all()
        print("CLEAR CART BEFORE LOGOUT")
        print(clear_cart)
        for item in clear_cart:
            if current_user.id == item.cart_id:
                db.session.delete(item)
                db.session.commit()
    logout_user()

    return redirect(url_for('home'))


@app.route('/register', methods=["GET", "POST"])
def register():
    global user_cart_items
    if request.method == "POST":
        try:
            user = User.query.filter_by(email=request.form.get("email")).first()
            if request.form.get("email") == user.email:
                flash("PLEASE LOGIN!!! You have already registered an account with our premium service!")
                return redirect(url_for("login"))
            else:
                flash("New User available for registering.")
        except AttributeError:

            hash_and_salted_password = generate_password_hash(
                request.form.get('password'),
                method='pbkdf2:sha256',
                salt_length=8
            )

            new_user = User(
                email=request.form.get("email"),
                first_name=request.form.get("first_name"),
                last_name=request.form.get("last_name"),
                password=hash_and_salted_password,
            )
            db.session.add(new_user)
            db.session.commit()
            print(new_user.first_name)
            print(new_user.last_name)

            # Log in and authenticate user after adding details to database.
            login_user(new_user)

            new_cart = Cart(
                cart_desc=current_user.first_name,
                user_id=current_user.id,
            )
            db.session.add(new_cart)
            db.session.commit()

            return redirect(url_for("cart", user_first=current_user.first_name, user_last=current_user.last_name,
                                    logged_in=current_user.is_authenticated, user_cart_items=user_cart_items))
    return render_template("register.html", logged_in=current_user.is_authenticated, user_cart_items=user_cart_items)


# -----------------------------------------SHOP MECHANICS: ITEMS + CART--------------------------------------------------#

# Displays all shop items on home page
# Allow user to add specific shop items to cart
@app.route('/')
def home():
    global user_cart_items
    user_cart_items = []
    all_items = db.session.query(Shop_Items).all()
    print(all_items[0].name)
    all_user_cart_items = db.session.query(Cart_Items).all()
    print(all_user_cart_items)

    if current_user.is_authenticated:

        for item in all_user_cart_items:
            if current_user.id == item.cart_id:
                if str(item) not in user_cart_items:
                    user_cart_items.append(str(item))
        print(user_cart_items)

        return render_template("index.html", user_first=current_user.first_name, user_last=current_user.last_name,
                               logged_in=current_user.is_authenticated, all_items=all_items,
                               user_cart_items=user_cart_items)
    else:
        for item in all_user_cart_items:
            if item.cart_id == 0:
                if str(item) not in user_cart_items:
                    user_cart_items.append(str(item))
        print(user_cart_items)
        # Bug check bcos item keep getting added to cart even when already inside
        # try:
        #     print(user_cart_items[0])
        #     print(user_cart_items[3])
        #     print(str(user_cart_items[0])==str(user_cart_items[3]))
        # except:
        #     pass

        return render_template("index.html", logged_in=current_user.is_authenticated, all_items=all_items,
                               user_cart_items=user_cart_items)


@app.route('/add/<item_id>', methods=["GET", "POST", "PATCH"])
def add_cart(item_id):
    cart_item = Shop_Items.query.get(item_id)
    print("Adding item to cart...")
    print(cart_item.name)

    # More than one except in try block?; just if else using condition

    # Filter by multiple properties SQLAlchemy?
    if current_user.is_authenticated:
        if Cart_Items.query.filter_by(item_id=item_id).filter_by(cart_id=current_user.id).first() == None:
            add_item = Cart_Items(
                cart_id=current_user.id,
                item_id=item_id,
                quantity=1
            )
            db.session.add(add_item)
            db.session.commit()
            flash(f"{cart_item.name} added to cart!")
        else:
            item_quantity = Cart_Items.query.filter_by(item_id=item_id).filter_by(cart_id=current_user.id).first()
            print("QUANTITY/user")
            print(item_quantity.item_id)
            print(item_quantity.cart_id)
            print(item_quantity.quantity)
            item_quantity.quantity += 1
            db.session.commit()
            flash(f"{cart_item.name} +1")
    else:
        if Cart_Items.query.filter_by(item_id=item_id).filter_by(cart_id=0).first() == None:
            add_item = Cart_Items(
                cart_id=0,
                item_id=item_id,
                quantity=1
            )
            db.session.add(add_item)
            db.session.commit()
            flash(f"{cart_item.name} added to cart!")
        else:
            item_quantity = Cart_Items.query.filter_by(item_id=item_id).filter_by(cart_id=0).first()
            print("QUANTITY/guest")
            print(item_quantity.item_id)
            print(item_quantity.cart_id)
            print(item_quantity.quantity)
            item_quantity.quantity += 1
            db.session.commit()
            flash(f"{cart_item.name} +1")

    # cart_item.cart_id = current_user.id
    # cart_item.quantity = 1
    return redirect(url_for('home'))


@app.route('/cart/<user_first>/<user_last>', methods=["GET", "POST", "PATCH"])
# css not showing for url with custom parameters
def cart(user_first, user_last):
    global user_cart_items
    user_cart_items = []
    cart_total_price = 0
    all_user_cart_items = db.session.query(Cart_Items).all()

    if current_user.is_authenticated:
        print(f"current_user.id: {current_user.id}")
        user_cart = Cart.query.filter_by(user_id=int(current_user.id)).first()
        print(f"user_cart.user_id: {user_cart.user_id}")

        for item in all_user_cart_items:
            if current_user.id == item.cart_id:
                if item not in user_cart_items:
                    user_cart_items.append(item)
        print(user_cart_items)
        for item in user_cart_items:
            print(item.item_id)
            item_price = Shop_Items.query.get(item.item_id)
            cart_total_price += (item_price.price * item.quantity)
            print(round(cart_total_price, 2))
        cart_shop_items = []
        for item in user_cart_items:
            item_name = Shop_Items.query.get(item.item_id)
            cart_shop_items.append(item_name)
            print(cart_shop_items)

        return render_template("cart.html", user_first=user_first, user_last=user_last, user_cart=user_cart,
                               logged_in=True, user_cart_items=user_cart_items,
                               cart_total_price=round(cart_total_price, 2), cart_shop_items=cart_shop_items)
    else:
        user_cart = Cart.query.filter_by(user_id=0).first()

        for item in all_user_cart_items:
            if item.cart_id == 0:
                if item not in user_cart_items:
                    user_cart_items.append(item)
        print(user_cart_items)
        for item in user_cart_items:
            print(item.item_id)
            item_price = Shop_Items.query.get(item.item_id)
            cart_total_price += (item_price.price * item.quantity)
            print(round(cart_total_price, 2))
        cart_shop_items = []
        for item in user_cart_items:
            item_name = Shop_Items.query.get(item.item_id)
            cart_shop_items.append(item_name)
            print(cart_shop_items)

        return render_template("cart.html", user_first=user_first, user_last=user_last, user_cart=user_cart,
                               logged_in=False, user_cart_items=user_cart_items,
                               cart_total_price=round(cart_total_price, 2), cart_shop_items=cart_shop_items)
    # <p>{{user_cart.user_id}}</p>
    # <p>{{user_cart.cart_desc}}</p>


@app.route('/remove/<item_id>', methods=["GET", "POST", "PATCH"])
def remove_cart(item_id):
    global user_cart_items
    user_cart_items = []
    cart_item = Shop_Items.query.get(item_id)
    print("Removing item to cart...")
    print(cart_item.name)

    if current_user.is_authenticated:
        if Cart_Items.query.filter_by(item_id=item_id).filter_by(cart_id=current_user.id).first().quantity > 1:
            item_quantity = Cart_Items.query.filter_by(item_id=item_id).filter_by(cart_id=current_user.id).first()
            item_quantity.quantity -= 1
            db.session.commit()
        else:
            item_quantity_0 = Cart_Items.query.filter_by(item_id=item_id).filter_by(cart_id=current_user.id).first()
            db.session.delete(item_quantity_0)
            db.session.commit()
    else:
        if Cart_Items.query.filter_by(item_id=item_id).filter_by(cart_id=0).first().quantity > 1:
            item_quantity = Cart_Items.query.filter_by(item_id=item_id).filter_by(cart_id=0).first()
            item_quantity.quantity -= 1
            db.session.commit()
        else:
            item_quantity_0 = Cart_Items.query.filter_by(item_id=item_id).filter_by(cart_id=0).first()
            db.session.delete(item_quantity_0)
            db.session.commit()

    # cart_item.cart_id = current_user.id
    # cart_item.quantity = 1
    if current_user.is_authenticated:
        return redirect(url_for('cart', user_first=current_user.first_name, user_last=current_user.last_name))
    else:
        return redirect(url_for('cart', user_first="GUEST", user_last="XYZ"))


@app.route('/checkout', methods=["GET", "POST", "PATCH"])
def checkout():
    #STRIPE CART CHECKOUT; payment link limited to only 1 item purchase
    # Get stripe product link from cart items
    user_cart_items = []
    all_items = db.session.query(Shop_Items).all()
    all_user_cart_items = db.session.query(Cart_Items).all()
    if current_user.is_authenticated:
        user_cart = Cart.query.filter_by(user_id=int(current_user.id)).first()
        for item in all_user_cart_items:
            if current_user.id == item.cart_id:
                if item not in user_cart_items:
                    user_cart_items.append(item)
        stripe_parameters = ""
        stripe_line_items = []
        for item in user_cart_items:
            print(item.item_id)
            stripe_item = Shop_Items.query.get(item.item_id)
            stripe_product_ID = stripe_item.stripe_id
            stripe_price_ID = stripe_item.stripe_id_price
            stripe_quantity = item.quantity
            LINE_ITEM = {
                "price": stripe_price_ID,
                "quantity": int(stripe_quantity)
            }
            stripe_line_items.append(LINE_ITEM)
            print(stripe_line_items)

        try:
            checkout_session = stripe.checkout.Session.create(
                # line_items = [{"price":"price_1LL4ZII6b7ZbumIjZ7JxLRwF","quantity":5},{'price': 'price_1LL4YiI6b7ZbumIjCrClKa6z', 'quantity': 10}],
                line_items=stripe_line_items,
                mode='payment',
                success_url="http://127.0.0.1:5000/",
                cancel_url="http://127.0.0.1:5000/",
            )
        except Exception as e:
            return str(e)
        print("URL?")
        print(checkout_session.url)
        return redirect(checkout_session.url, code=303)

        # stripe_session= stripe.checkout.Session.list(limit=3)
        # print(stripe_session)

        # return render_template("delivery.html", user_first=current_user.first_name, user_last=current_user.last_name,
        #                        email=current_user.email)

        # STRIPE PAYMENT LINK LIMITATION; ONLY 1 PRODUCT PER LINK
        #     line_parameter = f'"price": {stripe_price_ID}, "quantity": {int(stripe_quantity)}'
        #     line_parameter = {line_parameter}
        #     stripe_parameters+= f'line_items = [{line_parameter}]'
        #
        # stripe.Price.create(
        #     currency="sgd",
        #     unit_amount=1000,
        #     product=stripe_product_ID,
        # )
        # stripe.PaymentLink.create(stripe_parameters)


    else:
        return redirect(url_for('login'))


@app.route('/address', methods=["GET", "POST", "PATCH"])
def address():
    try:
        user_address = User_Address_Payment(
            first_name=request.form.get("first_name"),
            last_name=request.form.get("last_name"),
            email=request.form.get("email"),
            address=request.form.get("address"),
            postal_code=request.form.get("postal_code"),
            phone_num=request.form.get("phone_num"),
            user_id=current_user.id
        )
        db.session.add(user_address)
        db.session.commit()
    except:
        db.session.rollback()
        edit_address = User_Address_Payment.query.filter_by(user_id=current_user.id).first()
        edit_address.first_name = request.form.get("first_name")
        edit_address.last_name = request.form.get("last_name")
        edit_address.email = request.form.get("email")
        edit_address.address = request.form.get("address")
        edit_address.postal_code = request.form.get("postal_code")
        edit_address.phone_num = request.form.get("phone_num")
        db.session.commit()

    return redirect(url_for('home'))


# --------------------------------------------PAYMENT LINK----------------------------------------------------------#
# import stripe
# stripe.api_key = "sk_test_51LL3eDI6b7ZbumIjMlffZoiacfhKc3qopcq6CQ582i7Sr4YjBtrQ951j1tXVpckrnofVAK3J8sVMoWGp0IXbZuXw00xdVayDam"


# db.session.rollback()
# all_items = db.session.query(Shop_Items).all()
# for i in range(len(all_items)):
#     print(all_items[i].name)
#     print(all_items[i].description)
#     print(all_items[i].price)
#     stripe.Product.create(name=f"{all_items[i].name}",description=f"{all_items[i].description}",default_price_data=f"{all_items[i].price}")

# stripe.Price.create(
#   currency="usd",
#   unit_amount=1000,
#   product='{{PRODUCT_ID}}',
# )
#
# payment_link = stripe.PaymentLink.create(
#   line_items=[{"price": '{{PRICE_ID}}', "quantity": 1}],
# )
# print(payment_link["url"])

# --------------------------------------------SHOP DESCRIPTION------------------------------------------------------#

@app.route('/about')
def about():
    global user_cart_items
    if current_user.is_authenticated:
        return render_template("about.html", user_first=current_user.first_name, user_last=current_user.last_name,
                               logged_in=current_user.is_authenticated, user_cart_items=user_cart_items)
    else:
        return render_template("about.html", logged_in=current_user.is_authenticated, user_cart_items=user_cart_items)


# ----------------------------------------------SHOP CATEGORIES-----------------------------------------------------#
@app.route('/popular')
def popular():
    global user_cart_items
    all_items = db.session.query(Shop_Items).all()
    if current_user.is_authenticated:
        return render_template("popular_items.html", user_first=current_user.first_name,
                               user_last=current_user.last_name, logged_in=current_user.is_authenticated,
                               all_items=all_items, user_cart_items=user_cart_items)
    else:
        return render_template("popular_items.html", logged_in=current_user.is_authenticated, all_items=all_items,
                               user_cart_items=user_cart_items)


@app.route('/new')
def new():
    global user_cart_items
    if current_user.is_authenticated:
        return render_template("new_items.html", user_first=current_user.first_name, user_last=current_user.last_name,
                               logged_in=current_user.is_authenticated, user_cart_items=user_cart_items)
    else:
        return render_template("new_items.html", logged_in=current_user.is_authenticated,
                               user_cart_items=user_cart_items)


if __name__ == "__main__":
    app.run(debug=True)
