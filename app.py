from flask import Flask, render_template, request, redirect, url_for, session, flash
import mysql.connector
from mysql.connector import Error

app = Flask(__name__)
app.secret_key = "change-this-secret-key"

# -----------------------
# DATABASE CONFIG
# -----------------------
DB_CONFIG = {
    "host": "127.0.0.1",
    "user": "root",          # <-- change to your MySQL username
    "password": "",          # <-- change to your MySQL password
    "database": "satisbank_new"
}


def get_db_connection():
    """Create and return a new MySQL connection."""
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        return conn
    except Error as e:
        print(f"Database connection error: {e}")
        return None


# -----------------------
# ROOT
# -----------------------
@app.route("/")
def index():
    if "user" in session:
        return redirect(url_for("dashboard"))
    return redirect(url_for("login"))


# -----------------------
# LOGIN
# -----------------------
@app.route("/login", methods=["GET", "POST"])
def login():
    # Prevent logged-in users from returning to the login page
    if "user" in session:
        return redirect(url_for("dashboard"))

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        selected_role = request.form.get("role", "user").strip()

        conn = get_db_connection()
        if conn is None:
            flash("Unable to connect to the database. Please try again later.", "error")
            return render_template("auth/login.html")

        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute(
                "SELECT id, username, password, role FROM users WHERE username = %s",
                (username,)
            )
            user = cursor.fetchone()
        finally:
            cursor.close()
            conn.close()

        # NOTE: passwords in the current dump are stored in plain text.
        # For production use, store hashed passwords (e.g. with werkzeug.security
        # generate_password_hash / check_password_hash) instead of comparing directly.
        if user is None or password != user["password"]:
            flash("Invalid username or password.", "error")
        elif user["role"] != selected_role:
            # Credentials are correct, but they don't hold the role they selected
            # on the login screen (e.g. a regular user picking "Admin").
            flash("This account does not have access to the selected role.", "error")
        else:
            session["user"] = user["username"]
            session["role"] = user["role"]
            flash("Login successful!", "success")
            return redirect(url_for("dashboard"))

    return render_template("auth/login.html")


# -----------------------
# DASHBOARD
# -----------------------
@app.route("/dashboard")
def dashboard():
    if "user" not in session:
        flash("Please log in first.", "error")
        return redirect(url_for("login"))

    return render_template(
        "1-dashboard/dashboard.html",
        username=session["user"],
        page_title="Dashboard",
        page_description="View product risks, insights, and recommendations."
    )
    

# -----------------------
# COMPARISON
# -----------------------
@app.route("/comparison")
def comparison():
    if "user" not in session:
        flash("Please log in first.", "error")
        return redirect(url_for("login"))

    return render_template(
        "2-comparison/comparison.html",
        username=session["user"],
        page_title="Comparison",
        page_description="Compare different products and their features."
    )
    
# -----------------------
# ANALYTICS
# -----------------------
@app.route("/analytics")
def analytics():
    if "user" not in session:
        flash("Please log in first.", "error")
        return redirect(url_for("login"))

    return render_template(
        "3-analytics/analytics.html",
        username=session["user"],
        page_title="Analytics",
        page_description="View analytics and insights."
    )
    
# -----------------------
# Recommendations
# -----------------------
@app.route("/recommendations")
def recommendations():
    if "user" not in session:
        flash("Please log in first.", "error")
        return redirect(url_for("login"))

    return render_template(
        "4-recommendations/recommendations.html",
        username=session["user"],
        page_title="Recommendations",
        page_description="Get personalized product recommendations based on your preferences."
    )
    
    
# # -----------------------
# # BANK INFORMATION
# # -----------------------
# @app.route("/bank-profile")
# def bankProfile():
#     if "user" not in session:
#         flash("Please log in first.", "error")
#         return redirect(url_for("login"))

#     return render_template(
#         "5-bankInfo/bankProfile.html",
#         username=session["user"],
#         page_title="Bank Profile",
#         page_description="View all bank information."
#     )

# -----------------------
# BANK INFORMATION
# -----------------------
# Paste this into app.py, replacing your current bankProfile route.
# Needs: from flask import request  (add it to your existing flask import)

# Placeholder data that matches the design.
# Replace the numbers with your survey results / real interest rates later.
BANKS = {
    "bdo": {
        "code": "bdo",
        "short_name": "BDO",
        "full_name": "Banco de Oro Unibank",
        "logo": "images/banks/bdo.png",
        "description": "One of the oldest banks in the Philippines, known for excellent customer service and innovation.",
        "satisfaction": 8.7,
        "service_quality": 8.8,
        "safety": 9.3,
        "savings_rate": "0.3%",
        "loan_rate": "11.8%",
        "card_rate": "3.25%",
        "features": ["Mobile Banking App", "Wealth management", "Premium Services", "Corporate Banking"],
        # bars in the "Services Ratings" chart (0-60); blank label = no text under that bar
        "service_ratings": [
            {"label": "",             "value": 57},
            {"label": "Credit Cards", "value": 58},
            {"label": "",             "value": 56},
            {"label": "Savings",      "value": 56},
            {"label": "",             "value": 54},
            {"label": "Fees",         "value": 55},
            {"label": "",             "value": 56},
            {"label": "Rates",        "value": 53},
            {"label": "",             "value": 53},
            {"label": "Loans",        "value": 54},
        ],
        # points of the pentagon chart (0-10)
        "breakdown": {
            "security": 8.0,
            "transparency": 8.6,
            "fee_honesty": 8.1,
            "data_privacy": 8.4,
            "stability": 8.7,
        },
        "reviews": [
            {
                "name": "King Jamcent Casupang",
                "avatar": "images/avatars/user-1.png",
                "text": "I couldn’t send Instapay Transfers … even BPI-to-BPI doesn’t work on their app … ‘Sending Money In Progress’ … but it never pushes through.",
            },
        ],
    },

    # Add more banks with the same keys, e.g.:
    # "bpi": { "code": "bpi", "short_name": "BPI", "full_name": "Bank of the Philippine Islands", ... },
}


@app.route("/bank-profile")
def bankProfile():
    if "user" not in session:
        flash("Please log in first.", "error")
        return redirect(url_for("login"))

    # /bank-profile          -> no bank selected (empty state)
    # /bank-profile?bank=bdo -> show BDO's profile
    selected_code = request.args.get("bank", "").lower()
    selected_bank = BANKS.get(selected_code)  # None if missing or unknown

    return render_template(
        "5-bankInfo/bankProfile.html",
        username=session["user"],
        page_title="Bank Profile",
        page_description="View all bank information.",
        banks=list(BANKS.values()),
        bank=selected_bank,
    )

@app.route("/nearby-banks")
def nearbyBanks():
    if "user" not in session:
        flash("Please log in first.", "error")
        return redirect(url_for("login"))

    return render_template(
        "5-bankInfo/nearbyBanks.html",
        username=session["user"],
        page_title="Nearby Banks",
        page_description="Find banks near your location."
    )
    

# -----------------------
# GENERAL
# -----------------------
@app.route("/save-banks")
def saveBanks():
    if "user" not in session:
        flash("Please log in first.", "error")
        return redirect(url_for("login"))

    return render_template(
        "6-general/saveBanks.html",
        username=session["user"],
        page_title="Save Banks",
        page_description="Save your favorite banks for quick access."
    )


@app.route("/profile")
def profile():
    if "user" not in session:
        return redirect(url_for("login"))

    return render_template(
        "6-general/profile.html",
        username=session["user"]
    )
    
@app.route("/how-it-works")
def howItWorks():
    if "user" not in session:
        return redirect(url_for("login"))

    return render_template(
        "6-general/how_it_works.html",
        username=session["user"]
    )
    




    









# -----------------------
# SUPPORT - HELP & SUPPORT
# -----------------------
@app.route("/help-support")
def helpSupport():
    if "user" not in session:
        return redirect(url_for("login"))

    return render_template(
        "support/help_center.html",
        username=session["user"]
    )


# -----------------------
# LOGOUT
# -----------------------
@app.route("/logout")
def logout():
    session.pop("user", None)
    session.pop("role", None)
    flash("You have been logged out.", "success")
    return redirect(url_for("login"))


if __name__ == "__main__":
    app.run(debug=True)