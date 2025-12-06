import cv2
import os
import csv

STUDENTS_DIR = "students"
STUDENTS_CSV = "students.csv"
CSV_HEADER = ["roll_no", "name", "department", "section", "image_path", "email", "phone"]


def ensure_students_dir():
    if not os.path.exists(STUDENTS_DIR):
        os.makedirs(STUDENTS_DIR)
        print(f"Created folder: {STUDENTS_DIR}")


def ensure_students_csv():
    """Create students.csv with proper header if it doesn't exist."""
    if not os.path.exists(STUDENTS_CSV):
        with open(STUDENTS_CSV, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=CSV_HEADER)
            writer.writeheader()
        print(f"Created file: {STUDENTS_CSV}")


def student_exists_roll(roll_no: str) -> bool:
    """Check if this roll number is already registered."""
    if not os.path.exists(STUDENTS_CSV):
        return False

    with open(STUDENTS_CSV, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row.get("roll_no", "").strip() == roll_no:
                return True
    return False


def open_camera():
    """Try multiple camera indexes using DirectShow backend."""
    for index in range(3):
        print(f"Trying camera index {index}...")
        cap = cv2.VideoCapture(index, cv2.CAP_DSHOW)
        if cap.isOpened():
            print(f"✅ Using camera index {index}")
            return cap
        cap.release()
    return None


def main():
    ensure_students_dir()
    ensure_students_csv()

    roll_no = input("Enter Roll Number: ").strip()
    name = input("Enter Name: ").strip()
    department = input("Enter Department: ").strip()
    section = input("Enter Section: ").strip()
    email = input("Enter Email: ").strip()
    phone = input("Enter Phone (10 digits): ").strip()

    if not roll_no or not name or not department or not section:
        print("❌ Roll No, Name, Department, and Section are required.")
        return

    if not email:
        print("❌ Email is required.")
        return

    if not phone.isdigit() or len(phone) != 10:
        print("❌ Phone number must contain exactly 10 digits.")
        return

    if student_exists_roll(roll_no):
        print(f"❌ Roll number {roll_no} is already registered. Aborting.")
        return

    img_filename = f"{roll_no}.jpg"
    img_path = os.path.join(STUDENTS_DIR, img_filename)

    cap = open_camera()
    if cap is None:
        print("❌ Could not open camera.")
        return

    print("✅ Camera opened.")
    print("Look at the camera. Press SPACE to capture, 'q' to cancel.")

    while True:
        ret, frame = cap.read()
        if not ret:
            print("❌ Failed to grab frame from camera.")
            break

        display = frame.copy()
        cv2.putText(
            display,
            f"{roll_no} | {name}",
            (20, 40),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.8,
            (0, 255, 255),
            2
        )

        cv2.imshow("Capture Student Face", display)
        key = cv2.waitKey(1) & 0xFF

        if key == 32:  # SPACE
            cv2.imwrite(img_path, frame)
            print(f"✅ Saved image: {img_path}")

            # Append to CSV
            with open(STUDENTS_CSV, "a", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=CSV_HEADER)
                writer.writerow({
                    "roll_no": roll_no,
                    "name": name,
                    "department": department,
                    "section": section,
                    "image_path": img_path.replace("\\", "/"),
                    "email": email,
                    "phone": phone
                })

            print("✅ Student added to students.csv")
            break

        if key == ord("q"):
            print("❌ Cancelled without saving.")
            break

    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
