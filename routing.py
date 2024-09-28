import sqlite3, os, starlink_grpc
import time
from flask import flash, jsonify, redirect, render_template, request, send_file, url_for
from flask_login import login_required, login_user, logout_user
from werkzeug.security import check_password_hash, generate_password_hash

from database import get_db
from starlink import generate_obstruction_map_svg, get_starlink_model
from user import User


def routing(app, database):
    @app.route("/")
    def index():
        return redirect(url_for("login"))

    @app.route("/get_inital_data")
    def get_inital_data():
        starlink_model = get_starlink_model()
        return jsonify(starlink_model)

    @app.route("/dashboard")
    @login_required
    def dashboard():
        return render_template("dashboard.html")

    @app.route("/logout")
    @login_required
    def logout():
        logout_user()
        return redirect(url_for("login"))

    @app.route("/obstruction_map_image")
    def obstruction_map_image():
        generate_obstruction_map_svg(starlink_grpc.obstruction_map())
        image_path = os.path.join("obstruction_map.svg")
        return send_file(image_path, mimetype="image/svg+xml")

    @app.route("/login", methods=["GET", "POST"])
    def login():
        if request.method == "POST":
            username = request.form["username"]
            password = request.form["password"]
            db = get_db(database)
            user = db.execute(
                "SELECT * FROM users WHERE username = ?", (username,)
            ).fetchone()

            if user and check_password_hash(user["password"], password):
                login_user(User(user["id"], user["username"], user["password"]))
                return redirect(url_for("dashboard"))
            else:
                flash("Invalid username or password", "danger")
        return render_template("login.html")

    @app.route("/register", methods=["GET", "POST"])
    def register():
        if request.method == "POST":
            username = request.form["username"]
            password = generate_password_hash(request.form["password"])

            db = get_db(database)
            try:
                db.execute(
                    "INSERT INTO users (username, password) VALUES (?, ?)",
                    (username, password),
                )
                db.commit()
                flash("User registered successfully", "success")
                return redirect(url_for("login"))
            except sqlite3.IntegrityError:
                flash("Username already exists", "danger")
        return render_template("register.html")
