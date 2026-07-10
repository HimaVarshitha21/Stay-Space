from flask import Flask, render_template, request, redirect, session
import os
from werkzeug.utils import secure_filename
import uuid
from flask_sqlalchemy import SQLAlchemy
from flask import flash
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash 
from flask_mail import Mail, Message
import secrets
from datetime import datetime, timedelta

ADMIN_USERNAME = "chennareddy_hima_varshitha"

app = Flask(__name__)
app.secret_key = "secret123"

UPLOAD_FOLDER = "static/uploads"
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

# ================================
# DATABASE CONFIG
# ================================
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///database.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)

from flask_migrate import Migrate
migrate = Migrate(app, db)


def time_ago(time):
    now = datetime.now()
    diff = now - time

    seconds = diff.total_seconds()

    if seconds < 60:
        return "Just now"
    elif seconds < 3600:
        return f"{int(seconds // 60)} min ago"
    elif seconds < 86400:
        return f"{int(seconds // 3600)} hours ago"
    else:
        return f"{int(seconds // 86400)} days ago"
    
# ================================
# USER TABLE
# ================================
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    firstName = db.Column(db.String(100))
    lastName = db.Column(db.String(100))
    mobile = db.Column(db.String(20), unique=True)
    email = db.Column(db.String(120))
    password = db.Column(db.String(200))
    username = db.Column(db.String(100), unique=True)
    likes = db.Column(db.Integer, default=0)
    is_admin = db.Column(db.Boolean, default=False)
    profile_image = db.Column(db.String(200))
    location = db.Column(db.String(150))
    about = db.Column(db.Text)

# ================================
# PROPERTY TABLE
# ================================
class Property(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    # location
    state = db.Column(db.String(100))
    city = db.Column(db.String(100))
    area = db.Column(db.String(100))

    # details
    propertyType = db.Column(db.String(50))
    listingType = db.Column(db.String(50))

    price = db.Column(db.String(50))
    rent = db.Column(db.String(50))
    deposit = db.Column(db.String(50))

    bhk = db.Column(db.String(10))
    size = db.Column(db.String(50))
    facing = db.Column(db.String(50))

    # images (store as comma separated)
    images = db.Column(db.Text)
    image = db.Column(db.String(200))

    # owner
    owner_name = db.Column(db.String(100))
    owner_mobile = db.Column(db.String(20))

# ================================
# SAVED PROPERTY TABLE
# ================================
class SavedProperty(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    user_mobile = db.Column(db.String(20))
    property_id = db.Column(db.Integer)

# ================================
# NOTIFICATION TABLE
# ================================
class Notification(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    user_mobile = db.Column(db.String(20))   # receiver
    message = db.Column(db.String(200))

    type = db.Column(db.String(50))          # like, message, visit, etc
    property_id = db.Column(db.Integer)
    is_read = db.Column(db.Boolean, default=False)

# ================================
# VISIT REQUEST TABLE
# ================================
class VisitRequest(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    property_id = db.Column(db.Integer)

    user_mobile = db.Column(db.String(20))
    owner_mobile = db.Column(db.String(20))

    date = db.Column(db.String(20))
    time = db.Column(db.String(20))
    message = db.Column(db.String(200))

    status = db.Column(db.String(20), default="pending")  
    # pending / accepted / rejected / cancelled

    created_at = db.Column(db.DateTime, default=datetime.now)

# ================================
# MESSAGE TABLE
# ================================

class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    sender = db.Column(db.String(20))
    receiver = db.Column(db.String(20))

    text = db.Column(db.String(500))
    
    time = db.Column(db.DateTime, default=datetime.now)

    status =  db.Column(db.String(20), default="sent")

    read_time = db.Column(db.DateTime)

    property_id = db.Column(db.Integer)

    reply_to = db.Column(db.Integer, nullable=True)

# ================================
# USER ACTIONS
# ================================

class UserAction(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    owner_mobile = db.Column(db.String(20))
    target_mobile = db.Column(db.String(20))

    is_blocked = db.Column(db.Boolean, default=False)
    is_restricted = db.Column(db.Boolean, default=False)
    
    cleared_at = db.Column(db.DateTime, nullable=True)

# ================================
# LIKE TABLE
# ================================
class ProfileLike(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    liked_user = db.Column(db.String(20))   # username
    liked_by = db.Column(db.String(20))     # username

# ================================
# REPORT TABLE
# ================================

from datetime import datetime

class Report(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user = db.Column(db.String(100))   # username
    issue = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    seen = db.Column(db.Boolean, default=False)

# ================================
# SUPPORT MESSAGE TABLE
# ================================

class SupportMessage(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    user_mobile = db.Column(db.String(20))   # who sent
    message = db.Column(db.Text)
    sender = db.Column(db.String(10))

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

# ================================
# UPLOAD CONFIG
# ================================
UPLOAD_FOLDER = "static/uploads"
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)


def is_admin_user():
    return "username" in session and session["username"] == ADMIN_USERNAME
# ================================
# INDEX
# ================================
@app.route("/")
def index():
    return render_template("index.html")

# ================================
# SIGNUP
# ================================
@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":

        first = request.form.get("firstName")
        last = request.form.get("lastName")
        username = (first + "_" + last).lower().replace(" ", "_")
        mobile = request.form.get("mobile")
        email = request.form.get("email")
        password = request.form.get("password")
        confirm = request.form.get("confirmPassword")

        if not all([first, last, mobile, email, password]):
            return render_template("signup.html", error="Fill all fields")

        if password != confirm:
            return render_template("signup.html", error="Passwords do not match")

        # check if user exists
        existing_user = User.query.filter_by(mobile=mobile).first()

        if existing_user:
            return render_template("signup.html", error="Mobile already registered")
        
        existing_username = User.query.filter_by(username=username).first()

        if existing_username:
            return render_template("signup.html", error="username already taken")
        # create new user
        new_user = User(
             firstName=first,
             lastName=last,
             mobile=mobile,
             email=email,
             password=generate_password_hash(password),
             username=username
             )
        
        db.session.add(new_user)
        db.session.commit()

        flash("Account created successfully! Please login to continue.", "success")

        return redirect("/login")

    return render_template("signup.html")

# ================================
# LOGIN
# ================================
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":

        loginId = request.form.get("loginId", "").strip()
        password = request.form.get("password", "").strip()

        if not loginId or not password:
            return render_template("login.html", error="Enter Email/Mobile and Password")

        # find user in database
        user = User.query.filter(
            (User.email == loginId) | (User.mobile == loginId)
            ).first()
        
        if not user:
            return render_template("login.html", error="User not found")
        
        if not check_password_hash(user.password, password):
            return render_template("login.html", error="Invalid password")
        
        session["user"] = user.mobile

# ✅ ADD THIS (IMPORTANT)
        admin_mobile = "7396362701"

        if str(user.mobile).strip() == admin_mobile:
            session["is_admin"] = True
        else:
            session["is_admin"] = False

        session["username"] = user.username

        return redirect("/home")

    return render_template("login.html")

# ================================
# ADMIN
# ================================

@app.route("/admin")
def admin():

    if not is_admin_user():
        return "Access denied"

    users = User.query.all()
    properties = Property.query.all()

    all_reports = Report.query.order_by(Report.id.desc()).limit(5).all()

    reports = []

    for r in all_reports:

        user = User.query.filter_by(mobile=r.user).first()

        reports.append({
        "username": user.username if user else r.user,
        "issue": r.issue,
        "created_at": r.created_at,
        "id": r.id
        })

    import pytz
    ist = pytz.timezone("Asia/Kolkata")

    for r in reports:
        if r["created_at"]:
            r["created_at"] = r["created_at"].replace(tzinfo=pytz.utc).astimezone(ist)

    unseen_count = Report.query.filter_by(seen=False).count()
    support_messages = SupportMessage.query.order_by(SupportMessage.id.desc()).all()

    return render_template("admin.html", users=users, properties=properties, reports=reports, unseen_count=unseen_count,
                            support_messages=support_messages)

# ================================
# ADMIN DELETE USER
# ================================

@app.route("/delete_user/<int:id>")
def delete_user(id):

    if not is_admin_user():
        return "Access denied"

    user = User.query.get(id)

    if user:
        db.session.delete(user)
        db.session.commit()

    return redirect("/admin")

# ================================
# ADMIN DELETE PROPERTY
# ================================

@app.route("/admin/delete_property/<int:id>")
def admin_delete_property(id):

    if not is_admin_user():
        return "Access denied"

    property = Property.query.get(id)

    if property:
        db.session.delete(property)
        db.session.commit()

    return redirect("/admin")

# ================================
# ADMIN VIEW REPORTS
# ================================

@app.route("/admin/reports")
def view_reports():

    print("SESSION:", session)   # 👈 ADD THIS

    if "user" not in session:
        return redirect("/login")

    if not session.get("is_admin"):
        return "Access Denied"

    reports = Report.query.order_by(Report.id.desc()).all()
    
    final_reports = []
  
    for r in reports:
        user = User.query.filter_by(mobile=r.user).first()

        final_reports.append({
        "id": r.id,
        "issue": r.issue,
        "created_at": r.created_at,
        "username": user.username if user else "Unknown"
        })

    return render_template("admin_reports.html", reports=final_reports)

# ================================
# ADMIN DELETE REPORTS
# ================================

@app.route("/admin/delete_report/<int:id>", methods=["POST"])
def delete_report(id):

    if not session.get("is_admin"):
        return "Access Denied"

    report = Report.query.get(id)

    if report:
        db.session.delete(report)
        db.session.commit()

    return redirect("/admin")

# ================================
# SUPPORT
# ================================

@app.route("/support")
def support():

    if "user" not in session:
        return redirect("/login")

    user_mobile = request.args.get("user") or session["user"]

    messages = SupportMessage.query.filter_by(
        user_mobile=user_mobile
    ).order_by(SupportMessage.id.asc()).all()

    return render_template("support.html", messages=messages)

# ================================
# ADMIN SUPPORT
# ================================

@app.route("/admin_support")
def admin_support():

    if not is_admin_user():
        return "Access denied"

    messages = SupportMessage.query.order_by(SupportMessage.id.desc()).all()

    return render_template("admin_support.html", messages=messages)

# ================================
# HOME
# ================================

@app.route("/home")
def home():
    if "user" not in session:
        return redirect("/login")

    properties = Property.query.all()

    unread_notifications = Notification.query.filter_by(
        user_mobile=session['user'],
        is_read=False
        ).count()

    unread_messages = Message.query.filter(
        Message.receiver == session['user'],
        Message.status != "read"
        ).count()

    search = request.args.get("search", "")

    has_new_requests = VisitRequest.query.filter_by(
    owner_mobile=session["user"],
    status="pending"
).count() > 0


    return render_template(
    "home.html",
    properties=properties,
    unread_notifications=unread_notifications,
    unread_messages=unread_messages,
    search=search,
    has_new_requests=has_new_requests   # ✅ ADD THIS
)

# ================================
# USER PROFILE
# ================================

@app.route("/user_profile/<username>")
def user_profile(username):

    if "user" not in session:
        return redirect("/login")

    # 🔍 get user by username
    user = User.query.filter_by(username=username).first()

    if not user:
        return "User not found"

    # 🏠 get properties of that user
    properties = Property.query.filter_by(
        owner_mobile=user.mobile
    ).all()

    likes_count = ProfileLike.query.filter_by(
        liked_user=username
        ).count()
    
    is_liked = ProfileLike.query.filter_by(
        liked_user=username,
        liked_by=session["username"]
    ).first() is not None

    return render_template(
        "user_profile.html",
        user=user,
        properties=properties,
        likes_count=likes_count,
        is_liked=is_liked
    )

# ================================
# LIKE PROFILE
# ================================
@app.route("/like_profile/<username>")
def like_profile(username):

    if "username" not in session:
        return redirect("/login")

    current_user_mobile = session["user"]
    current_username = session["username"]

    user = User.query.filter_by(username=username).first()

    if not user:
        return "User not found"

    # ❌ prevent self-like
    if current_username == username:
        return redirect(f"/user_profile/{username}")

    # check existing like
    existing = ProfileLike.query.filter_by(
        liked_user=user.mobile,
        liked_by=current_user_mobile
    ).first()

    if existing:
        # 🔁 UNLIKE
        db.session.delete(existing)
        user.likes = max((user.likes or 1) - 1, 0)

    else:
        # ❤️ LIKE
        like = ProfileLike(
            liked_user=user.mobile,
            liked_by=current_user_mobile
        )
        db.session.add(like)

        user.likes = (user.likes or 0) + 1

        # 🔔 notification
        notification = Notification(
            user_mobile=user.mobile,   # keep internal
            message=f"{current_username} liked your profile",
            type="like"
        )
        db.session.add(notification)

    db.session.commit()

    return redirect(f"/user_profile/{username}")

# ================================
# SEARCH
# ================================

from flask import jsonify   # 🔥 add this import

@app.route("/search")
def search():
    query = request.args.get("q")

    users = User.query.filter(User.username.ilike(f"%{query}%")).all()

    properties = Property.query.filter(
        Property.area.ilike(f"%{query}%")
    ).all()

    return jsonify({
        "users": [{"username": u.username} for u in users],
        "properties": [{"id": p.id, "title": p.area} for p in properties]
    })

# ================================
# SEARCH PAGE
# ================================

@app.route("/search_page")
def search_page():
    if "user" not in session:
        return redirect("/login")
    return render_template("search.html")

# ================================
# SEND MESSAGE
# ================================

@app.route("/send_message/<int:property_id>", methods=["POST"])
def send_message(property_id):


    if "user" not in session:
        return redirect("/login")

    sender = session["user"]          # mobile
    sender_username = session["username"]

    text = request.form.get("message")

    reply_to = request.form.get("reply_to")
    reply_to = int(reply_to) if reply_to else None

    # 🔥 receiver username from hidden input
    receiver_username = request.form.get("receiver")

    receiver_user = User.query.filter_by(username=receiver_username).first()

    if not receiver_user:
        return "Receiver not found"

    receiver = receiver_user.mobile

    blocked = UserAction.query.filter(
    (
        (UserAction.owner_mobile == session["user"]) &
        (UserAction.target_mobile == receiver) &
        (UserAction.is_blocked == True)
    )
    |
    (
        (UserAction.owner_mobile == receiver) &
        (UserAction.target_mobile == session["user"]) &
        (UserAction.is_blocked == True)
    )
    ).first()

    if blocked:
        return redirect(request.referrer)

    # OPTIONAL PROPERTY
    property = None

    if property_id != 0:
        property = Property.query.get(property_id)

    # EMPT
    # 
    # MESSAGE CHECK
    if not text:
        return redirect(f"/chat/{receiver_user.username}/{property_id}")

    # SAVE MESSAGE
    msg = Message(
        sender=sender,
        receiver=receiver,
        text=text,
        property_id=property_id,
        reply_to=reply_to,
        status="sent"
    )

    db.session.add(msg)

    # NOTIFICATION
    existing_notification = Notification.query.filter_by(
        user_mobile=receiver,
        type="message",
        is_read=False
    ).first()

    if not existing_notification:

        notification = Notification(
            user_mobile=receiver,
            message=f"{sender_username} sent you a message",
            type="message",
            is_read=False
        )

        db.session.add(notification)

    db.session.commit()

    return redirect(f"/chat/{receiver_user.username}/{property_id}")

# ================================
# INBOX
# ================================

@app.route("/inbox")
def inbox():

    if "user" not in session:
        return redirect("/login")

    user = session["user"]

    messages = Message.query.filter(
    (Message.sender == user) |
    (Message.receiver == user)
).order_by(
    Message.time.desc(),
    Message.id.desc()
).all()

    conversations = {}

    for msg in messages:
        other = msg.receiver if msg.sender == user else msg.sender
        
        print("OTHER =", other)

         # 🔥 try finding user
        user_obj = User.query.filter(
            (User.mobile == other) |
            (User.username == other)
            ).first()

            # ✅ FIX: always ensure username exists
        if user_obj:
            name = user_obj.username
        else:
            print("⚠️ Missing user for mobile:", other)  # debug
            name = other   # fallback

        conversation_key = name

        if conversation_key not in conversations:

            conversations[conversation_key] = {
                "message": msg,
                "name": name
            }

    return render_template("inbox.html", conversations=conversations)

# ================================
# CHAT
# ================================

@app.route("/chat/<username>/<int:property_id>")
def chat(username, property_id):

    if "user" not in session:
        return redirect("/login")

    sender = session["user"]

    # ================================
    # FIND RECEIVER
    # ================================

    receiver_user = User.query.filter_by(username=username).first()

    if not receiver_user:
        receiver_user = User.query.filter_by(mobile=username).first()

    if not receiver_user:
        return "User not found"

    receiver = receiver_user.mobile
    receiver_username = receiver_user.username

    user_action = UserAction.query.filter_by(
    owner_mobile=sender,
    target_mobile=receiver
    ).first()

    cleared_at = None

    if user_action:
        cleared_at = user_action.cleared_at

    # ================================
    # BLOCK / RESTRICT STATUS
    # ================================

    user_action = UserAction.query.filter_by(
        owner_mobile=sender,
        target_mobile=receiver
    ).first()

    is_blocked = user_action.is_blocked if user_action else False
    is_restricted = user_action.is_restricted if user_action else False

    # Did receiver block me?

    blocked_by_other = UserAction.query.filter_by(
        owner_mobile=receiver,
        target_mobile=sender,
        is_blocked=True
    ).first()

    blocked_by_other = True if blocked_by_other else False

    # ================================
    # FETCH CHAT
    # ================================

    query = Message.query.filter(
    (
        (Message.sender == sender) &
        (Message.receiver == receiver)
    )
    |
    (
        (Message.sender == receiver) &
        (Message.receiver == sender)
    )
    ).filter(
    Message.property_id == property_id
    )

    if cleared_at:
        query = query.filter(
            Message.time > cleared_at
    )

    messages = query.order_by(
        Message.id.asc()
    ).all()

    # ================================
    # UPDATE STATUS
    # ================================

    restricted_by_other = UserAction.query.filter_by(
        owner_mobile=receiver,
        target_mobile=sender,
        is_restricted=True
    ).first()

    for msg in messages:

        if msg.receiver == sender and msg.status == "sent":
            msg.status = "delivered"

        if not restricted_by_other:

            if msg.receiver == sender and msg.status != "read":

               msg.status = "read"
               msg.read_time = datetime.now()

    db.session.commit()

    # ================================
    # REPLY MAP
    # ================================

    message_map = {
        msg.id: msg
        for msg in messages
    }

    # ================================
    # DEBUG
    # ================================

    print("Blocked:", is_blocked)
    print("Restricted:", is_restricted)

    # ================================
    # TEMPLATE
    # ================================

    return render_template(
        "chat.html",
        messages=messages,
        message_map=message_map,
        receiver=receiver_username,
        receiver_name=receiver_user.username,
        receiver_user=receiver_user,
        property_id=property_id,
        time_ago=time_ago,
        is_blocked=is_blocked,
        is_restricted=is_restricted,
        blocked_by_other=blocked_by_other
    )
# ================================
# BLOCK USER
# ================================

@app.route("/block_user/<username>")
def block_user(username):

    if "user" not in session:
        return redirect("/login")

    target = User.query.filter_by(username=username).first()

    if not target:
        return "User not found"

    existing = UserAction.query.filter_by(
        owner_mobile=session["user"],
        target_mobile=target.mobile
    ).first()

    if existing:
        existing.is_blocked = True
    else:
        action = UserAction(
            owner_mobile=session["user"],
            target_mobile=target.mobile,
            is_blocked=True
        )
        db.session.add(action)

    db.session.commit()

    return redirect(request.referrer or "/inbox")

# ================================
# UNBLOCK USER
# ================================

@app.route("/unblock_user/<username>")
def unblock_user(username):

    if "user" not in session:
        return redirect("/login")

    target = User.query.filter_by(username=username).first()

    if not target:
        return "User not found"

    action = UserAction.query.filter_by(
        owner_mobile=session["user"],
        target_mobile=target.mobile
    ).first()

    if action:
        action.is_blocked = False
        db.session.commit()

    return redirect(request.referrer or "/inbox")

# ================================
# RESTRICT USER
# ================================

@app.route("/restrict_user/<username>")
def restrict_user(username):

    if "user" not in session:
        return redirect("/login")

    target = User.query.filter_by(username=username).first()

    if not target:
        return "User not found"

    existing = UserAction.query.filter_by(
        owner_mobile=session["user"],
        target_mobile=target.mobile
    ).first()

    if existing:
        existing.is_restricted = True
    else:
        action = UserAction(
            owner_mobile=session["user"],
            target_mobile=target.mobile,
            is_restricted=True
        )
        db.session.add(action)

    db.session.commit()

    return redirect(request.referrer or "/inbox")

# ================================
# UNRESTRICT USER
# ================================

@app.route("/unrestrict_user/<username>")
def unrestrict_user(username):

    if "user" not in session:
        return redirect("/login")

    target = User.query.filter_by(username=username).first()

    if not target:
        return "User not found"

    action = UserAction.query.filter_by(
        owner_mobile=session["user"],
        target_mobile=target.mobile
    ).first()

    if action:
        action.is_restricted = False
        db.session.commit()

    return redirect(request.referrer or "/inbox")

# ================================
# REPORT USER
# ================================

@app.route("/report_user/<username>", methods=["POST"])
def report_user(username):

    if "user" not in session:
        return jsonify({"message":"Login required"})

    target = User.query.filter_by(username=username).first()

    if not target:
        return jsonify({"message":"User not found"})

    data = request.get_json()

    reason = data.get("reason")

    new_report = Report(
        user=session["user"],
        issue=f"Reported user {username}: {reason}"
    )

    db.session.add(new_report)
    db.session.commit()

    return jsonify({"message":"User reported successfully"})

# ================================
# CLEAR CHAT
# ================================

@app.route("/clear_chat/<username>")
def clear_chat(username):

    if "user" not in session:
        return redirect("/login")

    receiver_user = User.query.filter_by(username=username).first()

    if not receiver_user:
        return "User not found"

    receiver = receiver_user.mobile

    action = UserAction.query.filter_by(
        owner_mobile=session["user"],
        target_mobile=receiver
    ).first()

    if not action:

        action = UserAction(
            owner_mobile=session["user"],
            target_mobile=receiver
        )

        db.session.add(action)

    action.cleared_at = datetime.now()

    db.session.commit()

    return redirect("/chat/" + username + "/0")

# ================================
# LISTING STEP
# ================================
@app.route("/listing", methods=["GET", "POST"])
def listing():
    if "user" not in session:
        return redirect("/login")

    if request.method == "POST":
        session["listingType"] = request.form.get("listingType")
        session["propertyType"] = request.form.get("propertyType")
        return redirect("/details")

    return render_template("listing.html")

# ================================
# DETAILS STEP
# ================================
@app.route("/details", methods=["GET", "POST"])
def details():
    if "user" not in session:
        return redirect("/login")

    if "propertyType" not in session:
        return redirect("/listing")

    if request.method == "POST":
        session["new_property"] = dict(request.form)
        return redirect("/image")

    return render_template(
        "details.html",
        propertyType=session.get("propertyType"),
        listingType=session.get("listingType"),
        data=session.get("new_property", {})
    )

# ================================
# IMAGE + CONTACT STEP (FINAL SAVE)
# ================================
@app.route("/image", methods=["GET", "POST"])
def image():
    if "user" not in session:
        return redirect("/login")

    if "new_property" not in session:
        return redirect("/details")

    if request.method == "POST":

        files = request.files.getlist("images")

        image_urls = []

        for file in files:
            if file and file.filename != "":
                print("Uploading:", file.filename)
                filename = str(uuid.uuid4()) + "_" + secure_filename(file.filename)

                filepath = os.path.join(app.config["UPLOAD_FOLDER"], filename)
                file.save(filepath)

                # ✅ FIXED PATH (NO starting slash)
                image_urls.append("static/uploads/" + filename)

        print("Final images:", image_urls)

        data = session["new_property"]

        owner_name = request.form.get("owner_name")

        # ✅ CREATE PROPERTY
        new_property = Property(
            state=data.get("state"),
            city=data.get("city"),
            area=data.get("area"),

            propertyType=session.get("propertyType"),
            listingType=session.get("listingType"),

            price=data.get("price"),
            rent=data.get("rent"),
            deposit=data.get("deposit"),

            bhk=data.get("bhk"),
            size=data.get("size"),
            facing=data.get("facing"),

            images=",".join(image_urls),
            image=image_urls[0] if image_urls else "",

            owner_name=owner_name,

            # ✅ ALWAYS FROM SESSION
            owner_mobile=session["user"]
        )

        db.session.add(new_property)
        db.session.commit()


        # ✅ NOTIFICATION
        notification = Notification(
            user_mobile=session["user"],
            message="Your property has been posted successfully",
            type="post"
        )

        db.session.add(notification)
        db.session.commit()

        session.pop("new_property", None)

        flash("Property posted successfully!", "success")

        return redirect("/home")

    return render_template(
        "image.html",
        propertyType=session.get("propertyType")
    )

# ================================
# NOTIFICATIONS PAGE
# ================================
@app.route("/notifications")
def notifications():

    if "user" not in session:
        return redirect("/login")

    user_mobile = session["user"]

    notifications = Notification.query.filter_by(
        user_mobile=user_mobile
    ).order_by(Notification.id.desc()).all()

    Notification.query.filter_by(
        user_mobile=user_mobile,
        is_read=False
    ).update({"is_read": True})

    db.session.commit()

    return render_template("notifications.html", notifications=notifications)

@app.route("/read_notification/<int:id>")
def read_notification(id):

    if "user" not in session:
        return "", 401

    n = Notification.query.get(id)

    if n:
        n.is_read = True
        db.session.commit()

    return "", 204

# ================================
# DELETE SINGLE NOTIFICATION
# ================================
@app.route("/delete_notification/<int:id>")
def delete_notification(id):

    if "user" not in session:
        return "", 401

    n = Notification.query.get(id)

    if n:
        db.session.delete(n)
        db.session.commit()

    return "", 204

# ================================
# CLEAR ALL NOTIFICATIONS
# ================================
@app.route("/clear_notifications")
def clear_notifications():

    if "user" not in session:
        return redirect("/login")

    user_mobile = session["user"]

    Notification.query.filter_by(user_mobile=user_mobile).delete()
    db.session.commit()

    return redirect("/notifications")

# ================================
# VIEW PROPERTY
# ================================
@app.route("/view/<int:id>")
def view_property(id):

    if "user" not in session:
        return redirect("/login")

    user = session["user"]
    username = session["username"]

    property = Property.query.get(id)

    # 🔥 GET OWNER USER (IMPORTANT FIX)
    owner_user = User.query.filter_by(mobile=property.owner_mobile).first()
    owner_username = owner_user.username if owner_user else property.owner_mobile

    # ================================
    # NOTIFICATION LOGIC (UNCHANGED)
    # ================================
    if user != property.owner_mobile:

        existing = Notification.query.filter_by(
            user_mobile=property.owner_mobile,
            type="view"
        ).filter(
            Notification.message.like(f"{username}%")
        ).first()

        if not existing:
            notification = Notification(
                user_mobile=property.owner_mobile,
                message=f"{username} viewed your property ",
                type="view",
                is_read=False
            )
            db.session.add(notification)
            db.session.commit()

    # ================================
    # VISIT REQUEST
    # ================================
    visit = VisitRequest.query.filter_by(
        property_id=id,
        user_mobile=session["user"]
    ).order_by(VisitRequest.id.desc()).first()

    # ================================
    # RETURN TEMPLATE
    # ================================
    return render_template(
        "view.html",
        property=property,
        visit=visit,
        owner_username=owner_username   # ✅ VERY IMPORTANT
    )

# ================================
# SAVE PROPERTY
# ================================

@app.route("/save/<int:property_id>")
def save(property_id):

    if "user" not in session:
        return redirect("/login")

    user = session["user"]
    username = session["username"]

    print("👉 Saving property:", property_id)
    print("👉 User:", user)

    existing = SavedProperty.query.filter_by(
        user_mobile=user,
        property_id=property_id
    ).first()

    if existing:
        print("⚠️ Already saved")
        flash("Already saved", "info")
    else:
        new_save = SavedProperty(
            user_mobile=user,
            property_id=property_id
            )
        db.session.add(new_save)

    # 🔥 GET PROPERTY OWNER
    property = Property.query.get(property_id)

    # 🔔 CREATE NOTIFICATION
    notification = Notification(
        user_mobile=property.owner_mobile,   # 👈 OWNER
        message=f"{username} saved your property",
        type="property",
        is_read=False
    )
    db.session.add(notification)

    db.session.commit()

    print("✅ SAVED SUCCESSFULLY")
    flash("Property saved!", "success")

    return redirect(f"/view/{property_id}")

# ================================
# CREATE VISIT REQUEST
# ================================
@app.route("/request_visit/<int:property_id>", methods=["POST"])
def request_visit(property_id):

    if "user" not in session:
        return redirect("/login")

    user = session["user"]
    username = session["username"]

    property = Property.query.get(property_id)

    date = request.form.get("date")
    time = request.form.get("time")
    message = request.form.get("message")

    # 🔒 CHECK EXISTING ACTIVE REQUEST
    existing = VisitRequest.query.filter_by(
        property_id=property_id,
        user_mobile=user
    ).filter(
        VisitRequest.status.in_(["pending", "accepted"])
    ).first()

    if existing:
        return redirect(f"/view/{property_id}")

    # ✅ CREATE REQUEST
    visit = VisitRequest(
        property_id=property_id,
        user_mobile=user,
        owner_mobile=property.owner_mobile,
        date=date,
        time=time,
        message=message,
        status="pending"
    )

    db.session.add(visit)

    # 🔔 NOTIFY OWNER
    notification = Notification(
        user_mobile=property.owner_mobile,
        message=f"{username} requested a visit on {date} at {time}",
        type="visit"
    )
    db.session.add(notification)

    db.session.commit()

    return redirect(f"/view/{property_id}")

# ================================
# CANCEL VISIT REQUEST
# ================================
@app.route("/cancel_visit/<int:id>")
def cancel_visit(id):

    if "user" not in session:
        return redirect("/login")

    visit = VisitRequest.query.get(id)

    if visit and visit.user_mobile == session["user"]:
        visit.status = "cancelled"

        # 🔔 notify owner
        notification = Notification(
            user_mobile=visit.owner_mobile,
            message=f"{session['username']} cancelled the visit",
            type="visit"
        )
        db.session.add(notification)

        db.session.commit()

    return redirect(f"/view/{visit.property_id}")

# ================================
# ACCEPT VISIT
# ================================

@app.route("/accept_visit/<int:id>")
def accept_visit(id):

    v = VisitRequest.query.get(id)

    if v:
        v.status = "accepted"
        db.session.commit()

        # notification to buyer
        notification = Notification(
            user_mobile=v.user_mobile,
            message="Your visit request was accepted",
            type="visit"
        )
        db.session.add(notification)
        db.session.commit()

    return redirect("/visit_requests")

# ================================
# REJECT VISIT
# ================================

@app.route("/reject_visit/<int:id>")
def reject_visit(id):

    v = VisitRequest.query.get(id)

    if v:
        v.status = "rejected"
        db.session.commit()

        notification = Notification(
            user_mobile=v.user_mobile,
            message="Your visit request was rejected",
            type="visit"
        )
        db.session.add(notification)
        db.session.commit()

    return redirect("/visit_requests")

# ================================
# OWNER VIEW REQUESTS
# ================================

@app.route("/visit_requests")
def visit_requests():

    if "user" not in session:
        return redirect("/login")

    owner = session["user"]

    visits = VisitRequest.query.filter_by(
        owner_mobile=owner
    ).order_by(VisitRequest.id.desc()).all()

    # 🔥 ADD THIS BLOCK
    for v in visits:
        user = User.query.filter_by(mobile=v.user_mobile).first()
        v.username = user.username if user else "Unknown"

    return render_template("visit_requests.html", visits=visits)

# ================================
# SCHEDULE VISIT
# ================================

@app.route("/schedule_visit/<int:property_id>", methods=["POST"])
def schedule_visit(property_id):

    if "user" not in session:
        return redirect("/login")

    user = session["user"]

    date = request.form.get("date")
    time = request.form.get("time")
    message = request.form.get("message")

    property = Property.query.get(property_id)

    if not property:
        return "Property not found"

    # ❌ prevent duplicate pending request
    existing = VisitRequest.query.filter_by(
        user_mobile=user,
        property_id=property_id,
        status="pending"
    ).first()

    if existing:
        return redirect(f"/view/{property_id}")

    # ✅ create new request
    visit = VisitRequest(
        user_mobile=user,
        owner_mobile=property.owner_mobile,
        property_id=property_id,
        date=date,
        time=time,
        message=message,
        status="pending"
    )

    db.session.add(visit)

    # 🔔 notification to owner
    notification = Notification(
        user_mobile=property.owner_mobile,
        message=f"{session['username']} requested a visit on {date} at {time}",
        type="visit"
    )

    db.session.add(notification)
    db.session.commit()

    return redirect(f"/view/{property_id}")

# ================================
# UNSAVE PROPERTY
# ================================

@app.route("/unsave/<int:property_id>")
def unsave(property_id):

    if "user" not in session:
        return redirect("/login")

    user = session["user"]

    saved = SavedProperty.query.filter_by(
        user_mobile=user,
        property_id=property_id
    ).first()

    if saved:
        db.session.delete(saved)
        db.session.commit()
        flash("Removed from saved", "success")

    return redirect("/profile")

# ================================
# PROFILE
# ================================

@app.route("/profile")
def profile():

    # ✅ Check login
    if "user" not in session:
        return redirect("/login")

    mobile = session["user"]


    # ✅ Get user from DB
    user = User.query.filter_by(mobile=mobile).first()

    if not user:
        return "User not found", 404

    # ✅ Get only this user's properties
    my_properties = Property.query.filter_by(owner_mobile=mobile).all()

    # 🔥 GET SAVED PROPERTIES
    saved = SavedProperty.query.filter_by(user_mobile=mobile).all()

    saved_properties = []
    for s in saved:
        prop = Property.query.get(s.property_id)
        if prop:
            saved_properties.append(prop)
    is_admin = session.get("username") == "chennareddy_hima_varshitha"
    # ✅ Send to template
    return render_template(
        "profile.html",
        user=user,
        is_admin=is_admin,
        my_properties=my_properties,
        saved_properties=saved_properties   # 👈 ADD THIS
)

# ================================
# ACCOUNT
# ================================

@app.route("/account")
def account():

    if "user" not in session:
        return redirect("/login")

    user = User.query.filter_by(mobile=session["user"]).first()

    return render_template("account.html", user=user)

# ================================
# CHANGE PASSWORD
# ================================

@app.route("/verify_old_password", methods=["POST"])
def verify_old_password():

    if "user" not in session:
        return jsonify({"status": "not_logged_in"})

    data = request.get_json()
    old = data.get("old_password")

    user = User.query.filter_by(mobile=session["user"]).first()

    if not user:
        return jsonify({"status": "error"})

    if not check_password_hash(user.password, old):
        return jsonify({"status": "wrong_old"})

    return jsonify({"status": "correct"})

from flask import request, jsonify, session
from werkzeug.security import generate_password_hash, check_password_hash

@app.route("/change_password", methods=["POST"])
def change_password():

    if "user" not in session:
        return jsonify({"status": "not_logged_in"})

    try:
        data = request.get_json(force=True)   # ✅ FIX HERE

        old = data.get("old_password")
        new = data.get("new_password")

        if not old or not new:
            return jsonify({"status": "empty_fields"})

        user = User.query.filter_by(mobile=session["user"]).first()

        if not user:
            return jsonify({"status": "error"})

        if not check_password_hash(user.password, old):
            return jsonify({"status": "wrong_old"})   # ✅ THIS WILL WORK NOW

        user.password = generate_password_hash(new)
        db.session.commit()

        return jsonify({"status": "success"})

    except Exception as e:
        print("❌ ERROR:", e)
        return jsonify({"status": "error"})
  
# ================================
# HELP AND PRIVACY
# ================================
@app.route("/help")
def help_page():
    return render_template("help.html")

@app.route("/privacy")
def privacy():
    return render_template("privacy.html")


# ================================
# REPORT ISSUE
# ================================
from flask import request, jsonify, session

@app.route("/report_issue", methods=["POST"])
def report_issue():

    if "user" not in session:
        return jsonify({"status": "error", "message": "Not logged in"})
    data = request.get_json()
    message = data.get("issue")

    if not message:
        return jsonify({"status": "error", "message": "Empty message"})

    current_user = User.query.filter_by(mobile=session["user"]).first()

    if not current_user:
        return jsonify({"status": "error", "message": "User not found"})

    new_report = Report(
        user=current_user.mobile,
        issue=message
    )
    db.session.add(new_report)

    admin_user = User.query.filter_by(is_admin=True).first()

    if admin_user:
        new_notification = Notification(
            user_mobile=admin_user.mobile,   # receiver = admin
            message=f"New issue reported by {current_user.username}",
            type="report",                  # 🔥 IMPORTANT
            property_id=None
        )
        db.session.add(new_notification)

    db.session.commit()

    return jsonify({"status": "success"})

# ================================
# ACCOUNT DELETION
# ================================


from werkzeug.security import check_password_hash

@app.route("/delete_account", methods=["POST"])
def delete_account():

    if "user" not in session:
        return redirect("/login")

    password = request.form.get("password")
    reason = request.form.get("reason")

    user = User.query.filter_by(mobile=session["user"]).first()

    if not check_password_hash(user.password, password):
        return "Wrong password!"

    print("Delete reason:", reason)  # you can store later

    Report.query.filter_by(user=user.mobile).delete()
    SupportMessage.query.filter_by(user_mobile=user.mobile).delete()

    db.session.delete(user)
    db.session.commit()

    session.clear()

    return "Deleted"
# ================================
# DELETE PROPERTY
# ================================

@app.route("/delete_property/<int:id>")
def delete_property(id):

    if "user" not in session:
        return redirect("/login")

    property = Property.query.get(id)

    if not property:
        return "Property not found"

    # SECURITY: only owner can delete
    if property.owner_mobile != session["user"]:
        return "Unauthorized"

    db.session.delete(property)
    db.session.commit()

    flash("Property deleted successfully", "success")

    return redirect("/profile")

# ================================
# UPDATE PROPERTY
# ================================

@app.route("/edit_property/<int:id>", methods=["GET", "POST"])
def edit_property(id):

    if "user" not in session:
        return redirect("/login")

    property = Property.query.get(id)

    if not property:
        return "Property not found"

    if property.owner_mobile != session["user"]:
        return "Unauthorized"

    if request.method == "POST":
        property.price = request.form.get("price")
        property.area = request.form.get("area")
        property.city = request.form.get("city")
        property.size = request.form.get("size")

        db.session.commit()

        flash("Property updated successfully", "success")

        return redirect("/profile")

    return render_template("edit_property.html", property=property)

# ================================
# EDIT PROFILE PICTURE
# ================================

from sqlalchemy import or_

@app.route("/edit_profile", methods=["GET", "POST"])
def edit_profile():

    if "user" not in session:
        return redirect("/login")

    user = User.query.filter_by(mobile=session["user"]).first()

    if request.method == "POST":

        username = request.form.get("username").strip()
        mobile = request.form.get("mobile").strip()
        email = request.form.get("email").strip()

        first_name = request.form.get("first_name")
        last_name = request.form.get("last_name")
        location = request.form.get("location")
        about = request.form.get("about")

        # =========================
        # 🔥 VALIDATIONS
        # =========================

        # 1. Username uniqueness
        existing_user = User.query.filter(
            User.username == username,
            User.id != user.id
        ).first()

        if existing_user:
            flash("Username already taken", "error")
            return redirect("/edit_profile")

        # 2. Mobile uniqueness
        existing_mobile = User.query.filter(
            User.mobile == mobile,
            User.id != user.id
        ).first()

        if existing_mobile:
            flash("Mobile number already in use", "error")
            return redirect("/edit_profile")

        # 3. Email uniqueness (optional but good)
        existing_email = User.query.filter(
            User.email == email,
            User.id != user.id
        ).first()

        if existing_email:
            flash("Email already in use", "error")
            return redirect("/edit_profile")

        # =========================
        # ✅ UPDATE DATA
        # =========================

        user.username = username
        user.mobile = mobile
        user.email = email
        user.firstName = first_name
        user.lastName = last_name
        user.location = location
        user.about = about

        # 🔥 session update
        session["user"] = mobile

        # =========================
        # IMAGE UPLOAD
        # =========================

        profile = request.files.get("profile_image")
        
        if profile and profile.filename != "":
            
            filename = secure_filename(profile.filename)
            
            filepath = os.path.join(
                app.config["UPLOAD_FOLDER"],
                filename
                )
            
            profile.save(filepath)
            
            user.profile_image = filename

        db.session.commit()

        flash("Profile updated successfully", "success")

        return redirect("/profile")

    return render_template("edit_profile.html", user=user)


# ================================
# LOGOUT
# ================================
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

# ================================
# DELETE FOR ME
# ================================

@app.route("/delete_for_me/<int:id>")
def delete_for_me(id):

    if "user" not in session:
        return "Unauthorized"

    msg = Message.query.get(id)

    if not msg:
        return "Not found"

    user = session["user"]

    # 🔥 Hide message only for current user
    if msg.sender == user:
        msg.sender = None
    elif msg.receiver == user:
        msg.receiver = None

    db.session.commit()

    return "Deleted for me"

# ================================
# DELETE FOR EVERYONE
# ================================

@app.route("/delete_for_everyone/<int:id>")
def delete_for_everyone(id):

    if "user" not in session:
        return "Unauthorized"

    msg = Message.query.get(id)

    if not msg:
        return "Not found"

    # 🔥 Only sender can delete for everyone
    if msg.sender != session["user"]:
        return "Not allowed"

    db.session.delete(msg)
    db.session.commit()

    return "Deleted for everyone"

# ================================
# RUN
# ================================
if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)