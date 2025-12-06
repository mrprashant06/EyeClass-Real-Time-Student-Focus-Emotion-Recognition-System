import tkinter as tk
from tkinter import messagebox
from tkinter import ttk
import subprocess
import os

# Path to your virtualenv python
PYTHON_EXE = r".\venv\Scripts\python.exe"

# Script names
REGISTER_SCRIPT = "register_student.py"
MAIN_SCRIPT = "main.py"
REPORT_FILE = "class_report.csv"
STUDENTS_FILE = "students.csv"


def run_register_student():
    """Run the register_student.py script."""
    try:
        subprocess.run([PYTHON_EXE, REGISTER_SCRIPT], check=True)
    except Exception as e:
        messagebox.showerror("Error", f"Failed to run {REGISTER_SCRIPT}\n{e}")


def run_main_class():
    """Run main.py (class session monitoring)."""
    try:
        subprocess.run([PYTHON_EXE, MAIN_SCRIPT], check=True)
        messagebox.showinfo("Done", "Class session finished.\nReport updated.")
    except Exception as e:
        messagebox.showerror("Error", f"Failed to run {MAIN_SCRIPT}\n{e}")


def open_report():
    """Open class_report.csv."""
    if not os.path.exists(REPORT_FILE):
        messagebox.showwarning("Not Found", "No class_report.csv found.\nRun a class first.")
        return
    os.startfile(REPORT_FILE)


def open_students_csv():
    """Open students.csv file."""
    if not os.path.exists(STUDENTS_FILE):
        messagebox.showwarning("Not Found", "students.csv does not exist.\nRegister at least one student.")
        return
    os.startfile(STUDENTS_FILE)


def build_modern_styles(root):
    """Configure modern dark theme styles using ttk."""
    style = ttk.Style(root)

    try:
        style.theme_use("clam")
    except Exception:
        pass

    bg_main = "#161622"
    bg_card = "#1f1f2e"
    fg_text = "#f5f5f5"
    accent = "#4c8bf5"
    accent_hover = "#3a6fd1"

    root.configure(bg=bg_main)

    style.configure(
        "Card.TFrame",
        background=bg_card,
        borderwidth=0,
        relief="flat"
    )

    style.configure(
        "Title.TLabel",
        background=bg_card,
        foreground=fg_text,
        font=("Segoe UI", 18, "bold")
    )
    style.configure(
        "Subtitle.TLabel",
        background=bg_card,
        foreground="#a0a0b8",
        font=("Segoe UI", 10)
    )

    style.configure(
        "Menu.TButton",
        font=("Segoe UI", 10, "bold"),
        padding=8,
        foreground=fg_text,
        background="#2b2b3c",
        borderwidth=0
    )
    style.map(
        "Menu.TButton",
        background=[
            ("active", "#34344a"),
            ("pressed", "#2b2b3c")
        ]
    )

    style.configure(
        "Accent.TButton",
        font=("Segoe UI", 10, "bold"),
        padding=8,
        foreground="white",
        background=accent,
        borderwidth=0
    )
    style.map(
        "Accent.TButton",
        background=[
            ("active", accent_hover),
            ("pressed", accent)
        ]
    )

    return {
        "bg_main": bg_main,
        "bg_card": bg_card,
        "fg_text": fg_text,
    }


def main():
    root = tk.Tk()
    root.title("Teacher Portal - Emotion Aware Classroom")

    # Center window
    window_width = 480
    window_height = 360
    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()
    x_cord = int((screen_width / 2) - (window_width / 2))
    y_cord = int((screen_height / 2) - (window_height / 2))
    root.geometry(f"{window_width}x{window_height}+{x_cord}+{y_cord}")
    root.resizable(False, False)

    build_modern_styles(root)

    # Outer frame (card)
    outer = ttk.Frame(root, style="Card.TFrame", padding=20)
    outer.place(relx=0.5, rely=0.5, anchor="center")

    # Title
    title_label = ttk.Label(outer, text="Teacher Portal", style="Title.TLabel")
    title_label.grid(row=0, column=0, sticky="w")

    subtitle_label = ttk.Label(
        outer,
        text="Emotion-Aware Virtual Classroom Monitoring System",
        style="Subtitle.TLabel"
    )
    subtitle_label.grid(row=1, column=0, pady=(0, 15), sticky="w")

    # Buttons container
    buttons_frame = ttk.Frame(outer, style="Card.TFrame")
    buttons_frame.grid(row=2, column=0, sticky="nsew")

    ttk.Button(
        buttons_frame,
        text="➕  Register Student",
        style="Menu.TButton",
        command=run_register_student,
        width=30
    ).grid(row=0, column=0, pady=4, sticky="ew")

    ttk.Button(
        buttons_frame,
        text="▶  Start Class Session",
        style="Accent.TButton",
        command=run_main_class,
        width=30
    ).grid(row=1, column=0, pady=4, sticky="ew")

    ttk.Button(
        buttons_frame,
        text="📊  Open Master Report (class_report.csv)",
        style="Menu.TButton",
        command=open_report,
        width=30
    ).grid(row=2, column=0, pady=4, sticky="ew")

    ttk.Button(
        buttons_frame,
        text="👥  Open Students CSV",
        style="Menu.TButton",
        command=open_students_csv,
        width=30
    ).grid(row=3, column=0, pady=4, sticky="ew")

    ttk.Button(
        buttons_frame,
        text="⏹  Exit",
        style="Menu.TButton",
        command=root.destroy,
        width=30
    ).grid(row=4, column=0, pady=(10, 0), sticky="ew")

    buttons_frame.columnconfigure(0, weight=1)

    root.mainloop()


if __name__ == "__main__":
    main()
