from flask import Flask, request, render_template, session, redirect, url_for
from database import get_db_connection

app = Flask(__name__)

app.secret_key = "hospital123"


# ---------------- HOME ----------------

@app.route("/")
def home():
    connection = get_db_connection()

    if connection.is_connected():
        connection.close()
        return "Flask connected to MySQL successfully"

    return "Database connection failed"


# ---------------- REGISTER ----------------

@app.route("/register", methods=["POST"])
def register():

    name = request.form["name"]
    age = request.form["age"]
    gender = request.form["gender"]
    email = request.form["email"]
    phone = request.form["phone"]
    address = request.form["address"]

    connection = get_db_connection()
    cursor = connection.cursor()

    query = """
        INSERT INTO patient_details
        (Name, Age, Gender, Email, Phone, Address)
        VALUES (%s, %s, %s, %s, %s, %s)
    """

    values = (
        name,
        age,
        gender,
        email,
        phone,
        address
    )

    cursor.execute(query, values)
    connection.commit()

    cursor.close()
    connection.close()

    return """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Registration Successful</title>
            <link rel="stylesheet" href="http://127.0.0.1:5500/static/style.css">
        </head>
        <body>

            <header>
                <h1>Cloud Hospital Appointment System</h1>
            </header>

            <main>
                <h2>Registration successful!</h2>
                <p>Your account has been created. You can now log in.</p>

                <a href="http://127.0.0.1:5500/login.html">
                    <button>Go to Login</button>
                </a>
            </main>

            <footer>
                <p>Cloud-Based Hospital Appointment System</p>
            </footer>

        </body>
        </html>
    """


# ---------------- LOGIN ----------------

@app.route("/login", methods=["POST"])
def login():

    email = request.form["email"]
    phone = request.form["phone"]

    connection = get_db_connection()
    cursor = connection.cursor()

    query = """
        SELECT Patient_ID, Name
        FROM patient_details
        WHERE Email = %s AND Phone = %s
    """

    cursor.execute(query, (email, phone))

    patient = cursor.fetchone()

    cursor.close()
    connection.close()

    if patient is None:
        return """
            <h2>Invalid Email or Mobile Number.</h2>
            <br>
            <a href="http://127.0.0.1:5500/login.html">
                Try Again
            </a>
        """

    session["patient_id"] = patient[0]
    session["patient_name"] = patient[1]

    return """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Login Successful</title>
            <link rel="stylesheet" href="http://127.0.0.1:5500/static/style.css">
        </head>
        <body>

            <header>
                <h1>Cloud Hospital Appointment System</h1>
            </header>

            <main>
                <h2>Login successful!</h2>
                <p>Welcome! You are now logged in.</p>

                <a href="http://127.0.0.1:5500/index.html">
                    <button>Go to Home Page</button>
                </a>
                <a href="http://127.0.0.1:5000/my_appointments">
                    <button>View My Appointments</button>
                </a>
            </main>

            <footer>
                <p>Cloud-Based Hospital Appointment System</p>
            </footer>

        </body>
        </html>
    """


# ---------------- BOOK APPOINTMENT ----------------

@app.route("/book_appointment", methods=["POST"])
def book_appointment():

    patient_name = request.form["patient_name"]
    doctor_name = request.form["doctor_name"]
    appointment_date = request.form["appointment_date"]
    appointment_time = request.form["appointment_time"]
    reason = request.form["reason"]

    connection = get_db_connection()
    cursor = connection.cursor()

    # Use logged-in patient if available
    patient_id = session.get("patient_id")

    if patient_id is None:

        # Find patient from database
        patient_query = """
            SELECT Patient_ID
            FROM patient_details
            WHERE LOWER(TRIM(Name)) = LOWER(TRIM(%s))
        """

        cursor.execute(patient_query, (patient_name,))
        patient = cursor.fetchone()

        if patient is None:

            cursor.close()
            connection.close()

            return "Patient not found. Please register first."

        patient_id = patient[0]

        # Store patient in session
        session["patient_id"] = patient_id
        session["patient_name"] = patient_name

    # Find doctor from database
    doctor_query = """
        SELECT Doctor_ID
        FROM doctor
        WHERE LOWER(TRIM(Name)) = LOWER(TRIM(%s))
    """

    cursor.execute(doctor_query, (doctor_name,))
    doctor = cursor.fetchone()

    if doctor is None:

        cursor.close()
        connection.close()

        return "Doctor not found."

    doctor_id = doctor[0]

    # Store appointment in database
    appointment_query = """
        INSERT INTO appointment
        (
            Patient_ID,
            Doctor_ID,
            Appointment_Date,
            Appointment_Time,
            Reason,
            Status
        )
        VALUES (%s, %s, %s, %s, %s, %s)
    """

    values = (
        patient_id,
        doctor_id,
        appointment_date,
        appointment_time,
        reason,
        "Pending"
    )

    cursor.execute(appointment_query, values)

    connection.commit()

    cursor.close()
    connection.close()

    return redirect(url_for("my_appointments"))


# ---------------- MY APPOINTMENTS ----------------

@app.route("/my_appointments")
def my_appointments():

    patient_id = session.get("patient_id")

    if patient_id is None:
        return """
            <h2>Please login first.</h2>
            <br>
            <a href="http://127.0.0.1:5500/login.html">
                Go to Login
            </a>
        """

    connection = get_db_connection()
    cursor = connection.cursor()

    query = """
        SELECT
            doctor.Name,
            appointment.Appointment_Date,
            appointment.Appointment_Time,
            appointment.Status
        FROM appointment
        JOIN doctor
        ON appointment.Doctor_ID = doctor.Doctor_ID
        WHERE appointment.Patient_ID = %s
    """

    cursor.execute(query, (patient_id,))

    appointments = cursor.fetchall()

    patient_name = session.get("patient_name")

    cursor.close()
    connection.close()

    return render_template(
        "my_appointments.html",
        appointments=appointments,
        patient_name=patient_name
    )


# ---------------- DOCTOR DASHBOARD ----------------

@app.route("/doctor_dashboard")
def doctor_dashboard():

    connection = get_db_connection()
    cursor = connection.cursor()

    query = """
        SELECT
            appointment.Appointment_ID,
            patient_details.Name,
            doctor.Name,
            appointment.Appointment_Date,
            appointment.Appointment_Time,
            appointment.Status
        FROM appointment
        JOIN patient_details
        ON appointment.Patient_ID = patient_details.Patient_ID
        JOIN doctor
        ON appointment.Doctor_ID = doctor.Doctor_ID
        ORDER BY appointment.Appointment_ID
    """

    cursor.execute(query)

    # Gets only appointments stored in MySQL
    appointments = cursor.fetchall()

    cursor.close()
    connection.close()

    return render_template(
        "dashboard.html",
        appointments=appointments
    )


# ---------------- CONFIRM / REJECT ----------------

@app.route("/update_appointment/<int:appointment_id>/<status>")
def update_appointment(appointment_id, status):

    if status not in ["Confirmed", "Rejected"]:
        return "Invalid status."

    connection = get_db_connection()
    cursor = connection.cursor()

    query = """
        UPDATE appointment
        SET Status = %s
        WHERE Appointment_ID = %s
    """

    cursor.execute(
        query,
        (status, appointment_id)
    )

    connection.commit()

    cursor.close()
    connection.close()

    return redirect(url_for("doctor_dashboard"))


# ---------------- LOGOUT ----------------

@app.route("/logout")
def logout():

    session.clear()

    return """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Logout Successful</title>
            <link rel="stylesheet" href="http://127.0.0.1:5500/static/style.css">
        </head>
        <body>

            <header>
                <h1>Cloud Hospital Appointment System</h1>
            </header>

            <main>
                <h2>Logout successful!</h2>
                <p>You have been logged out safely.</p>

                <a href="http://127.0.0.1:5500/index.html">
                    <button>Go to Home Page</button>
                </a>
            </main>

            <footer>
                <p>Cloud-Based Hospital Appointment System</p>
            </footer>

        </body>
        </html>
    """


# ---------------- ADMIN LOGIN PAGE ----------------

@app.route("/admin_login_page")
def admin_login_page():
    return render_template("admin_login.html")


# ---------------- ADMIN LOGIN ----------------

@app.route("/admin_login", methods=["POST"])
def admin_login():

    username = request.form["username"]
    password = request.form["password"]

    if username == "admin" and password == "admin123":

        session["admin"] = True

        return redirect(url_for("doctor_dashboard"))

    return """
        <h2>Invalid Admin Username or Password.</h2>
        <br>
        <a href="http://127.0.0.1:5000/admin_login_page">
            Try Again
        </a>
    """


# ---------------- RUN APPLICATION ----------------

if __name__ == "__main__":
    app.run(debug=True)