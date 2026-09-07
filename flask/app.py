from flask import Flask, render_template, request, redirect, url_for
import mysql.connector
from mysql.connector import Error
from datetime import datetime, date, time


# =========================================================
# FLASK APPLICATION
# =========================================================

app = Flask(__name__)


# =========================================================
# DATABASE CONFIGURATION
# =========================================================

DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "212226",
    "database": "college_visitor_system"
}


# =========================================================
# DATABASE CONNECTION
# =========================================================

def get_db_connection():

    try:

        conn = mysql.connector.connect(
            host=DB_CONFIG["host"],
            user=DB_CONFIG["user"],
            password=DB_CONFIG["password"],
            database=DB_CONFIG["database"]
        )

        return conn

    except Error as e:

        print("Database connection error:", e)

        return None


# =========================================================
# INITIALIZE DATABASE
# =========================================================

def init_db():

    conn = None
    cursor = None

    try:

        # Connect to MySQL server
        conn = mysql.connector.connect(
            host=DB_CONFIG["host"],
            user=DB_CONFIG["user"],
            password=DB_CONFIG["password"]
        )

        cursor = conn.cursor()

        # Create database
        cursor.execute(
            f"CREATE DATABASE IF NOT EXISTS `{DB_CONFIG['database']}`"
        )

        print("Database is ready.")

        cursor.close()
        conn.close()

        # Connect to database
        conn = get_db_connection()

        if conn is None:

            print("Could not connect to database.")

            return

        cursor = conn.cursor()

        # Create table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS gate_log (

                id INT AUTO_INCREMENT PRIMARY KEY,

                visitor_name VARCHAR(100) NOT NULL,

                contact_number VARCHAR(15) NOT NULL,

                email VARCHAR(255) NOT NULL,

                purpose VARCHAR(255) NOT NULL,

                whom_to_meet VARCHAR(100) NOT NULL,

                check_in_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

                check_out_time TIMESTAMP NULL DEFAULT NULL,

                status VARCHAR(20) DEFAULT 'Inside'

            )
        """)

        conn.commit()

        print("Table gate_log is ready.")

        cursor.close()
        conn.close()

    except Error as e:

        print("Database initialization error:", e)

        if cursor:
            cursor.close()

        if conn and conn.is_connected():
            conn.close()


# =========================================================
# HOME / DASHBOARD
# =========================================================

@app.route("/")
def index():

    conn = get_db_connection()

    if conn is None:

        return "Database connection failed!", 500

    cursor = None

    try:

        cursor = conn.cursor(dictionary=True)

        # =====================================================
        # GET TODAY'S DATE FROM PYTHON
        # =====================================================

        today = date.today()

        # Start of today
        start_of_day = datetime.combine(
            today,
            time.min
        )

        # Start of tomorrow
        end_of_day = datetime.combine(
            today,
            time.max
        )

        print("---------------------------------------")
        print("TODAY:", today)
        print("START:", start_of_day)
        print("END:", end_of_day)
        print("---------------------------------------")

        # =====================================================
        # SHOW ONLY TODAY'S RECORDS
        #
        # IMPORTANT:
        # There is NO LIMIT.
        #
        # Old records remain safely stored in MySQL.
        # =====================================================

        cursor.execute("""
            SELECT *
            FROM gate_log
            WHERE check_in_time >= %s
              AND check_in_time <= %s
            ORDER BY
                CASE
                    WHEN status = 'Inside' THEN 0
                    ELSE 1
                END,
                check_in_time DESC
        """, (
            start_of_day,
            end_of_day
        ))

        logs = cursor.fetchall()

        print("Today's visitor records:", len(logs))

        # Print records for debugging
        for log in logs:
            print(
                log["id"],
                log["visitor_name"],
                log["check_in_time"],
                log["status"]
            )

        print("---------------------------------------")

        return render_template(
            "guard_dashboard.html",
            logs=logs,
            today=today
        )

    except Error as e:

        print("Error loading dashboard:", e)

        return "Error loading dashboard.", 500

    finally:

        if cursor:
            cursor.close()

        if conn and conn.is_connected():
            conn.close()


# =========================================================
# CHECK-IN
# =========================================================

@app.route("/check-in", methods=["POST"])
def check_in():

    # Get form values
    name = request.form.get(
        "visitor_name",
        ""
    ).strip()

    contact = request.form.get(
        "contact_number",
        ""
    ).strip()

    email = request.form.get(
        "email",
        ""
    ).strip()

    purpose = request.form.get(
        "purpose",
        ""
    ).strip()

    whom = request.form.get(
        "whom_to_meet",
        ""
    ).strip()


    # =====================================================
    # REQUIRED FIELD VALIDATION
    # =====================================================

    if not name:
        return "Visitor name is required!", 400

    if not contact:
        return "Contact number is required!", 400

    if not email:
        return "Email is required!", 400

    if not whom:
        return "Person to meet is required!", 400


    # =====================================================
    # DATABASE CONNECTION
    # =====================================================

    conn = get_db_connection()

    if conn is None:

        return "Database connection failed!", 500

    cursor = None

    try:

        cursor = conn.cursor()

        # =================================================
        # INSERT NEW VISITOR
        # =================================================

        sql = """
            INSERT INTO gate_log
            (
                visitor_name,
                contact_number,
                email,
                purpose,
                whom_to_meet,
                status
            )

            VALUES
            (
                %s,
                %s,
                %s,
                %s,
                %s,
                'Inside'
            )
        """

        cursor.execute(
            sql,
            (
                name,
                contact,
                email,
                purpose,
                whom
            )
        )

        conn.commit()

        print("---------------------------------------")
        print("Visitor checked in successfully.")
        print("Visitor:", name)
        print("Database time:", datetime.now())
        print("---------------------------------------")

        return redirect(url_for("index"))

    except Error as e:

        print("Check-in error:", e)

        return "Error while checking in visitor.", 500

    finally:

        if cursor:
            cursor.close()

        if conn and conn.is_connected():
            conn.close()


# =========================================================
# CHECK-OUT
# =========================================================

@app.route("/check-out/<int:log_id>", methods=["POST"])
def check_out(log_id):

    conn = get_db_connection()

    if conn is None:

        return "Database connection failed!", 500

    cursor = None

    try:

        cursor = conn.cursor()

        cursor.execute("""
            UPDATE gate_log

            SET
                check_out_time = CURRENT_TIMESTAMP,
                status = 'Checked Out'

            WHERE id = %s

            AND status = 'Inside'
        """, (log_id,))

        conn.commit()

        print("---------------------------------------")
        print(
            f"Visitor ID {log_id} checked out successfully."
        )
        print("---------------------------------------")

        return redirect(url_for("index"))

    except Error as e:

        print("Check-out error:", e)

        return "Error while checking out visitor.", 500

    finally:

        if cursor:
            cursor.close()

        if conn and conn.is_connected():
            conn.close()


# =========================================================
# RUN APPLICATION
# =========================================================

if __name__ == "__main__":

    print("---------------------------------------")
    print("College Visitor Management System")
    print("---------------------------------------")

    # Initialize database
    init_db()

    print("")
    print("Starting Flask server...")
    print("")
    print("Open on this PC:")
    print("http://127.0.0.1:5000")

    print("")
    print("Network access:")
    print("http://YOUR-PC-IP:5000")

    print("---------------------------------------")

    app.run(
        debug=True,
        host="0.0.0.0",
        port=5000
    )

