import os
import csv
from flask import Flask, render_template, request, redirect, url_for, flash

# ---------------- CONFIG ----------------

UPLOAD_FOLDER = "students"       # where profile images are saved
STUDENTS_CSV = "students.csv"   # same file used by your main.py

CSV_HEADER = ["roll_no", "name", "department", "section", "image_path", "email", "phone"]

app = Flask(__name__)
app.secret_key = "some_secret_key_for_flask"  # needed for flash messages
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

# Make sure upload folder exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


def ensure_students_csv():
    """Create students.csv with header if it doesn't exist."""
    if not os.path.exists(STUDENTS_CSV):
        with open(STUDENTS_CSV, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=CSV_HEADER)
            writer.writeheader()


def check_existing(roll_no=None, email=None, phone=None):
    """
    Check if roll_no OR email OR phone already exists.
    Returns (exists: bool, field: 'roll' | 'email' | 'phone' | None)
    Safely handles old CSV files that may not have email/phone columns.
    """
    if not os.path.exists(STUDENTS_CSV):
        return False, None

    with open(STUDENTS_CSV, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)

        for row in reader:
            # roll_no will exist in your old file
            row_roll = row.get("roll_no", "").strip()

            # email/phone might NOT exist in old header → use .get()
            row_email = row.get("email", "").strip().lower()
            row_phone = row.get("phone", "").strip()

            if roll_no and row_roll == roll_no:
                return True, "roll"

            if email and row_email and row_email == email.lower():
                return True, "email"

            if phone and row_phone and row_phone == phone:
                return True, "phone"

    return False, None



# ---------------- ROUTES ----------------

@app.route("/", methods=["GET", "POST"])
def register():
    ensure_students_csv()

    if request.method == "POST":
        roll_no = request.form.get("roll_no", "").strip()
        name = request.form.get("name", "").strip()
        department = request.form.get("department", "").strip()
        section = request.form.get("section", "").strip()
        email = request.form.get("email", "").strip()
        phone = request.form.get("phone", "").strip()
        file = request.files.get("photo")

        # ---------- Basic required fields ----------
        if not roll_no or not name or not department or not section:
            flash("Roll No, Name, Department, and Section are required.", "error")
            return redirect(url_for("register"))

        if not email:
            flash("Email is required.", "error")
            return redirect(url_for("register"))

        if not phone:
            flash("Phone number is required.", "error")
            return redirect(url_for("register"))

        # ---------- Phone validation: exactly 10 digits ----------
        if not phone.isdigit() or len(phone) != 10:
            flash("Phone number must contain exactly 10 digits.", "error")
            return redirect(url_for("register"))

        # ---------- Uniqueness checks ----------
        exists, field = check_existing(roll_no=roll_no, email=email, phone=phone)
        if exists:
            if field == "roll":
                flash(f"Roll No {roll_no} is already registered.", "error")
            elif field == "email":
                flash(f"Email {email} is already registered.", "error")
            elif field == "phone":
                flash(f"Phone {phone} is already registered.", "error")
            return redirect(url_for("register"))

        # ---------- Photo required ----------
        if not file or file.filename == "":
            flash("Please upload a profile photo.", "error")
            return redirect(url_for("register"))

        # ---------- Save image file ----------
        ext = os.path.splitext(file.filename)[1].lower() or ".jpg"
        filename = f"{roll_no}{ext}"
        save_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
        file.save(save_path)

        image_path = save_path.replace("\\", "/")

        # ---------- Append to students.csv ----------
        with open(STUDENTS_CSV, "a", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=CSV_HEADER)
            writer.writerow({
                "roll_no": roll_no,
                "name": name,
                "department": department,
                "section": section,
                "image_path": image_path,
                "email": email,
                "phone": phone
            })

        flash("Registration successful! You are now registered.", "success")
        return redirect(url_for("register"))

    # GET request → show registration form
    return render_template("register.html")


if __name__ == "__main__":
    app.run(debug=True)
