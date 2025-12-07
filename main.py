
import cv2
import os
import pandas as pd
from collections import Counter
from deepface import DeepFace
from datetime import datetime


STUDENTS_CSV_PATH = "students.csv"
CLASS_REPORT_PATH = "class_report.csv"


FACE_MATCH_THRESHOLD = 0.6       # relaxed a bit
FACE_MODEL_NAME = "VGG-Face"     # DeepFace model to use
DEBUG_MATCH = False              # set True to see distances in console


FRAME_TARGET_WIDTH = 640         # resize camera frame width
PROCESS_EVERY_N_FRAMES = 3       # do heavy DeepFace work every Nth frame




def load_students(csv_path):
    """
    Load students.csv, fix spaces in column names AND cell values.
    """

    if not os.path.exists(csv_path):
        raise FileNotFoundError(f"{csv_path} not found. Use register_student.py or web app first.")

    df = pd.read_csv(csv_path)

   
    original_cols = list(df.columns)
    print("Original columns in students.csv:", original_cols)

    clean_map = {col: col.strip() for col in df.columns}
    df = df.rename(columns=clean_map)

   
    for col in ["roll_no", "name", "department", "section", "image_path", "email", "phone"]:
        if col in df.columns:
            df[col] = df[col].astype(str).str.strip()

  
    print("Cleaned columns:", list(df.columns))
    print("First row after cleaning (if any):")
    if not df.empty:
        print(df.iloc[0])

 
    required = {"roll_no", "name", "department", "section", "image_path"}
    if not required.issubset(df.columns):
        raise ValueError(
            f"{csv_path} is missing required columns {required}. "
            f"Current columns after cleaning: {list(df.columns)}"
        )

    return df


def init_attendance_dict(students_df):
    """
    Initialize an attendance dictionary for the current session.
    """
    attendance = {}
    for _, row in students_df.iterrows():
        roll_no = str(row["roll_no"])

        attendance[roll_no] = {
            "name": row["name"],
            "department": row["department"],
            "section": row["section"],
            "email": row.get("email", ""),
            "phone": row.get("phone", ""),
            "present": False,
            "frames_present": 0,
            "frames_attentive": 0,
            "dominant_emotions": [],
        }
    return attendance




def identify_student(face_roi, students_df):
    """
    Identify which registered student this face belongs to
    using DeepFace.verify against each student's image.
    Uses a fixed model and skips internal detection (face_roi is already cropped).
    """
    best_match_roll_no = None
    best_distance = None

    for _, row in students_df.iterrows():
        roll_no = str(row["roll_no"])
        img_path = row["image_path"]

        if not os.path.exists(img_path):
            if DEBUG_MATCH:
                print(f"[WARN] Image not found for {roll_no} at '{img_path}'")
            continue

        try:
            result = DeepFace.verify(
                face_roi,
                img_path,
                model_name=FACE_MODEL_NAME,
                detector_backend="skip",  # we already cropped the face
                enforce_detection=False
            )
            distance = result.get("distance", None)
            if distance is None:
                continue

            if best_distance is None or distance < best_distance:
                best_distance = distance
                best_match_roll_no = roll_no
        except Exception as e:
            if DEBUG_MATCH:
                print(f"[ERROR] verify failed for {roll_no}: {e}")
            continue

    if DEBUG_MATCH and best_distance is not None:
        print(f"[MATCH-DEBUG] best roll: {best_match_roll_no}, distance: {best_distance}")

    if best_distance is not None and best_distance < FACE_MATCH_THRESHOLD:
        return best_match_roll_no
    return None


def get_dominant_emotion(face_roi):
    """
    Detect dominant emotion from a face ROI using DeepFace.analyze.
    """
    try:
        analysis = DeepFace.analyze(
            face_roi,
            actions=["emotion"],
            enforce_detection=False
        )

        if isinstance(analysis, list):
            analysis = analysis[0]

        return analysis.get("dominant_emotion", "unknown")
    except Exception:
        return "unknown"


def estimate_attention_status(x, y, w, h, frame_width, frame_height):
    """
    Simple attention heuristic:
    - If face is near center of frame => Attentive
    - Else => Not attentive
    """
    frame_center_x = frame_width // 2
    frame_center_y = frame_height // 2

    face_center_x = x + w // 2
    face_center_y = y + h // 2

    tolerance_x = frame_width * 0.25
    tolerance_y = frame_height * 0.25

    if (
        abs(face_center_x - frame_center_x) < tolerance_x
        and abs(face_center_y - frame_center_y) < tolerance_y
    ):
        return "Attentive", (0, 255, 0)
    else:
        return "Not attentive", (0, 0, 255)


def compute_session_report(attendance, total_frames, session_date, session_time):
    """
    Convert attendance dict into a pandas DataFrame for CSV export.
    """
    rows = []

    for roll_no, info in attendance.items():
        frames_present = info["frames_present"]
        frames_attentive = info["frames_attentive"]
        emotions_list = info["dominant_emotions"]

        if frames_present == 0:
            status = "Absent"
            present_pct = 0.0
            attention_pct = 0.0
            dominant_emotion_final = "N/A"
        else:
            status = "Present"
            present_pct = (frames_present / max(total_frames, 1)) * 100.0
            attention_pct = (frames_attentive / frames_present) * 100.0

            if emotions_list:
                dominant_emotion_final = Counter(emotions_list).most_common(1)[0][0]
            else:
                dominant_emotion_final = "unknown"

        rows.append({
            "Roll No": roll_no,
            "Name": info["name"],
            "Department": info["department"],
            "Section": info["section"],
            "Session Date": session_date,
            "Session Time": session_time,
            "Status": status,
            "% Time Present (approx)": round(present_pct, 2),
            "% Time Attentive": round(attention_pct, 2),
            "Dominant Emotion": dominant_emotion_final,
        })

    return pd.DataFrame(rows)


def open_camera():
    """
    Try camera indexes 0,1,2 using DirectShow backend (Windows).
    """
    for index in range(3):
        print(f"Trying camera index {index}...")
        cap = cv2.VideoCapture(index, cv2.CAP_DSHOW)
        if cap.isOpened():
            print(f"✅ Using camera index {index}")
            return cap
        cap.release()
    return None




def main():
   
    now = datetime.now()
    session_date = now.date().isoformat()
    session_time = now.strftime("%H:%M:%S")

    
    try:
        print("Loading students database...")
        students_df = load_students(STUDENTS_CSV_PATH)
        print(students_df)
    except Exception as e:
        print(f"❌ Error loading students: {e}")
        return

    attendance = init_attendance_dict(students_df)

    print("Initializing face detector...")
    cascade_path = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
    print("Using Haar cascade:", cascade_path)
    face_cascade = cv2.CascadeClassifier(cascade_path)

    if face_cascade.empty():
        print("❌ Failed to load Haar cascade. Check OpenCV installation / path.")
        return

    print("Opening webcam...")
    cap = open_camera()
    if cap is None:
        print("❌ Could not open any camera.")
        return

    total_frames = 0
    print("Press 'q' to end session and generate report.")

    while True:
        ret, frame = cap.read()
        if not ret:
            print("❌ Failed to read frame from camera.")
            break

        total_frames += 1

       
        h, w = frame.shape[:2]
        if w > FRAME_TARGET_WIDTH:
            scale = FRAME_TARGET_WIDTH / float(w)
            frame = cv2.resize(
                frame,
                (FRAME_TARGET_WIDTH, int(h * scale)),
                interpolation=cv2.INTER_LINEAR
            )
            h, w = frame.shape[:2]

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

      
        do_heavy = (total_frames % PROCESS_EVERY_N_FRAMES == 0)

        faces = face_cascade.detectMultiScale(
            gray,
            scaleFactor=1.1,
            minNeighbors=5,
            minSize=(30, 30),
            flags=cv2.CASCADE_SCALE_IMAGE
        )

    
        cv2.putText(
            frame,
            f"Faces: {len(faces)}",
            (10, 25),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.8,
            (0, 255, 255),
            2
        )

        for (x, y, w_box, h_box) in faces:
            face_roi = frame[y:y + h_box, x:x + w_box]

            if do_heavy:
               
                dominant_emotion = get_dominant_emotion(face_roi)
                attention_status, color = estimate_attention_status(
                    x, y, w_box, h_box, w, h
                )
                roll_no = identify_student(face_roi, students_df)

                if roll_no is not None and roll_no in attendance:
                    info = attendance[roll_no]
                    info["present"] = True
                    info["frames_present"] += 1

                    if attention_status == "Attentive":
                        info["frames_attentive"] += 1

                    if dominant_emotion != "unknown":
                        info["dominant_emotions"].append(dominant_emotion)

                    name = info["name"]
                    id_label = f"{roll_no} | {name}"
                else:
                    id_label = "Unknown"

                cv2.rectangle(frame, (x, y), (x + w_box, y + h_box), color, 2)
                cv2.putText(
                    frame,
                    id_label,
                    (x, y - 30),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.6,
                    (255, 255, 0),
                    2
                )
                cv2.putText(
                    frame,
                    f"Emotion: {dominant_emotion}",
                    (x, y - 10),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.5,
                    (0, 255, 255),
                    2
                )
                cv2.putText(
                    frame,
                    attention_status,
                    (x, y + h_box + 20),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.6,
                    color,
                    2
                )
            else:
               
                _, color = "Detecting...", (0, 255, 255)
                cv2.rectangle(frame, (x, y), (x + w_box, y + h_box), color, 1)

        cv2.imshow("Emotion-Aware Classroom Monitor", frame)

      
        if cv2.waitKey(1) & 0xFF == ord("q"):
            print("👋 Ending session...")
            break

    cap.release()
    cv2.destroyAllWindows()

    print("Generating session report...")
    report_df = compute_session_report(attendance, total_frames, session_date, session_time)

    file_exists = os.path.exists(CLASS_REPORT_PATH)

    report_df.to_csv(
        CLASS_REPORT_PATH,
        mode="a" if file_exists else "w",
        header=not file_exists,
        index=False
    )

    print(f"✅ Appended session report to: {CLASS_REPORT_PATH}")
    print("Done.")


if __name__ == "__main__":
    main()

