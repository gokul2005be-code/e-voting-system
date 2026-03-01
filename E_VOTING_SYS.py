import customtkinter as ctk
import tkinter.messagebox as messagebox
import cv2
import serial
import time
import mysql.connector  # Changed from oracledb
import qrcode
from PIL import Image
import os
import threading

# === CONFIGURATION (UPDATED FOR MYSQL) ===
DB_USER = "root"
DB_PASS = "GOKUL@12"
DB_HOST = "localhost"
DB_PORT = "3306"
DB_NAME = "secured_voting" # Ensure this database exists in MySQL Workbench

COM_PORT = "COM5"
BAUD_RATE = 9600

# === MAIN APPLICATION ===
class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("E-Voting System - Login")
        self.geometry("700x700")
        self.resizable(False, False)
        ctk.set_appearance_mode("DARK")
        ctk.set_default_color_theme("green")
        self.name_font = ctk.CTkFont(family="Helvetica", size=12)
        self.login_page()

    def get_connection(self):
        try:
            # MySQL connection structure
            return mysql.connector.connect(
                host=DB_HOST,
                user=DB_USER,
                password=DB_PASS,
                port=DB_PORT,
                database=DB_NAME
            )
        except mysql.connector.Error as e:
            messagebox.showerror("Database Error", str(e))
            return None

    def login_page(self):
        self.login_frame = ctk.CTkFrame(self)
        self.login_frame.place(relx=0.5, rely=0.5, anchor="center")

        ctk.CTkLabel(
            self.login_frame,
            text="LOGIN",
            font=ctk.CTkFont(family="Times New Roman", size=35, weight="bold")
        ).grid(row=0, column=0, columnspan=2, pady=30)

        ctk.CTkLabel(self.login_frame, text="Name:", font=self.name_font)\
            .grid(row=1, column=0, padx=10, pady=20, sticky="e")
        self.usernameEntry = ctk.CTkEntry(
            self.login_frame, width=250, placeholder_text="username"
        )
        self.usernameEntry.grid(row=1, column=1, padx=20, pady=10)

        ctk.CTkLabel(self.login_frame, text="Password:", font=self.name_font)\
            .grid(row=2, column=0, padx=10, pady=20, sticky="e")
        self.passwordEntry = ctk.CTkEntry(
            self.login_frame, show="*", width=250, placeholder_text="password"
        )
        self.passwordEntry.grid(row=2, column=1, padx=20, pady=10)

        ctk.CTkButton(
            self.login_frame,
            text="Login",
            width=150,
            command=self.login
        ).grid(row=3, column=0, columnspan=2, pady=25)

    def login(self):
        username = self.usernameEntry.get().strip()
        password = self.passwordEntry.get().strip()
        if not username or not password:
            messagebox.showerror("Error", "All fields are required")
            return

        conn = self.get_connection()
        if not conn:
            return
        cursor = conn.cursor()
        
        # MySQL uses %s as placeholder
        cursor.execute("""
            SELECT user_name FROM v_user_detail 
            WHERE user_name = %s AND password = %s
        """, (username, password))
        user = cursor.fetchone()

        if not user:
            cursor.execute("""
                SELECT user_name FROM v_admin_detail 
                WHERE user_name = %s AND password = %s
            """, (username, password))
            admin = cursor.fetchone()
        else:
            admin = None
        conn.close()

        if user:
            self.login_frame.destroy()
            messagebox.showinfo("Success", "Voter Login Successful")
            VoterStatusPage(self)
        elif admin:
            self.login_frame.destroy()
            messagebox.showinfo("Success", "Admin Login Successful")
            AdminPage(self)
        else:
            messagebox.showerror("Login Failed", "Invalid Username or Password")

# === VOTER STATUS PAGE ===
class VoterStatusPage:
    def __init__(self, parent):
        self.parent = parent
        self.qr_path = None

        self.status_frame = ctk.CTkFrame(parent)
        self.status_frame.place(relx=0.5, rely=0.5, anchor="center")

        ctk.CTkLabel(
            self.status_frame,
            text="VOTER STATUS",
            font=ctk.CTkFont(family="Times New Roman", size=30, weight="bold")
        ).grid(row=0, column=0, columnspan=2, pady=20)

        ctk.CTkLabel(self.status_frame, text="Enter Voter ID:")\
            .grid(row=1, column=0, padx=10, pady=10, sticky="e")
        self.voterid_Entry = ctk.CTkEntry(self.status_frame, width=250)
        self.voterid_Entry.grid(row=1, column=1, padx=20, pady=10)

        ctk.CTkButton(
            self.status_frame, text="Search", command=self.user_search
        ).grid(row=2, column=0, pady=15)
        ctk.CTkButton(
            self.status_frame, text="Reset", fg_color="gray",
            command=self.reset_fields
        ).grid(row=2, column=1, pady=15)

        self.result_label = ctk.CTkLabel(self.status_frame, text="")
        self.result_label.grid(row=3, column=0, columnspan=2, pady=10)

        self.qr_label = ctk.CTkLabel(
            self.status_frame, text="QR Code Area",
            width=200, height=200, fg_color="gray20"
        )
        self.qr_label.grid(row=4, column=0, columnspan=2, pady=15)

        self.Gqr_btn = ctk.CTkButton(
            self.status_frame, text="Generate QR",
            state="disabled", command=self.generate_qr
        )
        self.Gqr_btn.grid(row=5, column=0, columnspan=2, pady=10)

        self.print_btn = ctk.CTkButton(
            self.status_frame, text="Print QR",
            state="disabled", command=self.print_qr
        )
        self.print_btn.grid(row=6, column=0, columnspan=2, pady=15)

    def reset_fields(self):
        self.voterid_Entry.delete(0, "end")
        self.result_label.configure(text="", text_color="white")
        self.qr_label.configure(image="", text="QR Code Area")
        self.Gqr_btn.configure(state="disabled")
        self.print_btn.configure(state="disabled")
        self.qr_path = None

    def user_search(self):
        voter_id = self.voterid_Entry.get().strip().upper()
        if not voter_id:
            messagebox.showerror("Error", "Please enter a Voter ID")
            return

        connection = self.parent.get_connection()
        if not connection:
            return
        cursor = connection.cursor()
        cursor.execute("""
            SELECT voter_name, booth_name 
            FROM v_voterid_prestored_data 
            WHERE UPPER(voter_id) = %s
        """, (voter_id,))
        result = cursor.fetchone()
        connection.close()

        if result:
            self.result_label.configure(
                text=f"NAME: {result[0]}\nBOOTH: {result[1]}\nSTATUS: ELIGIBLE",
                text_color="#2ECC71"
            )
            self.Gqr_btn.configure(state="normal")
        else:
            self.result_label.configure(
                text="Voter Not Found",
                text_color="#E74C3C"
            )
            self.Gqr_btn.configure(state="disabled")

    def generate_qr(self):
        voter_id = self.voterid_Entry.get().strip().upper()
        os.makedirs("qr_codes", exist_ok=True)
        self.qr_path = os.path.abspath(f"qr_codes/{voter_id}.png")

        qr_img = qrcode.make(voter_id)
        qr_img.save(self.qr_path)

        img = ctk.CTkImage(Image.open(self.qr_path), size=(200, 200))
        self.qr_label.configure(image=img, text="")
        self.qr_label.image = img

        self.print_btn.configure(state="normal")
        messagebox.showinfo("Success", f"QR saved to:\n{self.qr_path}")

    def print_qr(self):
        if not self.qr_path or not os.path.exists(self.qr_path):
            messagebox.showerror("Error", "Generate QR before printing")
            return
        try:
            os.startfile(self.qr_path, "print")
            messagebox.showinfo("Print", "QR sent to printer successfully")
            self.open_scan_window()
        except Exception as e:
            messagebox.showerror("Print Error", str(e))

    def open_scan_window(self):
        QRScanPage(self.parent)

# === QR SCAN WINDOW ===
class QRScanPage(ctk.CTkToplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title("E-Voting System - QR Scan")
        self.geometry("600x600")
        self.resizable(False, False)
        self.locked = False

        ctk.CTkLabel(self, text="QR SCAN & VERIFY",
                     font=ctk.CTkFont(size=32, weight="bold")
        ).pack(pady=30)

        self.status_label = ctk.CTkLabel(
            self, text="Click START to scan QR",
            font=ctk.CTkFont(size=16)
        )
        self.status_label.pack(pady=20)

        self.start_btn = ctk.CTkButton(
            self, text="START SCAN", width=200,
            command=self.start_scan
        )
        self.start_btn.pack(pady=15)

        self.reset_btn = ctk.CTkButton(
            self, text="RESET", width=200,
            fg_color="gray",
            command=self.reset_app
        )
        self.reset_btn.pack(pady=10)

    def get_connection(self):
        try:
            return mysql.connector.connect(
                host=DB_HOST,
                user=DB_USER,
                password=DB_PASS,
                port=DB_PORT,
                database=DB_NAME
            )
        except mysql.connector.Error as e:
            messagebox.showerror("Database Error", str(e))
            return None

    def send_to_arduino(self, payload):
        try:
            arduino = serial.Serial(COM_PORT, BAUD_RATE, timeout=1)
            time.sleep(2)
            arduino.write((payload + "\n").encode())
            arduino.close()
        except Exception as e:
            messagebox.showerror("Serial Error", str(e))

    def start_scan(self):
        if self.locked:
            return
        self.status_label.configure(text="Scanning QR...")
        self.update()
        qr_data = self.scan_qr_opencv()
        if qr_data:
            self.process_qr(qr_data)
        else:
            self.status_label.configure(text="Scan cancelled")

    def scan_qr_opencv(self):
        cap = cv2.VideoCapture(0)
        detector = cv2.QRCodeDetector()
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            data, bbox, _ = detector.detectAndDecode(frame)
            if data:
                cap.release()
                cv2.destroyAllWindows()
                return data.strip()
            cv2.imshow("QR Scanner - Press Q to Exit", frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
        cap.release()
        cv2.destroyAllWindows()
        return None

    def process_qr(self, voter_id):
        try:
            conn = self.get_connection()
            if not conn:
                return
            cursor = conn.cursor()
            cursor.execute("""
                SELECT voter_name FROM v_voterid_prestored_data 
                WHERE UPPER(voter_id) = %s
            """, (voter_id.upper(),))
            result = cursor.fetchone()
            if result:
                voter_name = result[0]
                cursor.execute("""
                    INSERT INTO v_voterid_details (voter_id, voter_name, polling_status) 
                    VALUES (%s, %s, 'NOT_POLLED')
                """, (voter_id, voter_name))
                conn.commit()
                payload = f"VID:{voter_id};NAME:{voter_name}"
                self.send_to_arduino(payload)
                self.status_label.configure(
                    text=f"✔ VERIFIED\nSent to Arduino\n{payload}"
                )
                self.locked = True
                self.start_btn.configure(state="disabled")
            else:
                messagebox.showerror("Invalid Voter", "Voter not found in database")
                self.status_label.configure(text="Scan failed")
            conn.close()
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def reset_app(self):
        self.locked = False
        self.status_label.configure(text="Click START to scan QR")
        self.start_btn.configure(state="normal")

# === ADMIN PAGE ===
class AdminPage:
    def __init__(self, parent):
        self.parent = parent
        self.admin_frame = ctk.CTkFrame(parent, width=850, height=850)
        self.admin_frame.place(relx=0.5, rely=0.5, anchor="center")
        parent.name_font = ctk.CTkFont(family="Helvetica", size=12)

        self.admin_frame.columnconfigure((0, 1), weight=1)
        ctk.CTkLabel(self.admin_frame, text="Party 1:", font=parent.name_font)\
            .grid(row=0, column=0, padx=20, pady=10, sticky="e")
        self.count_1 = ctk.CTkLabel(self.admin_frame, text="0", fg_color="gray30", width=300)
        self.count_1.grid(row=0, column=1, pady=10)

        ctk.CTkLabel(self.admin_frame, text="Party 2:", font=parent.name_font)\
            .grid(row=1, column=0, padx=20, pady=10, sticky="e")
        self.count_2 = ctk.CTkLabel(self.admin_frame, text="0", fg_color="gray30", width=300)
        self.count_2.grid(row=1, column=1, pady=10)

        ctk.CTkLabel(self.admin_frame, text="Party 3:", font=parent.name_font)\
            .grid(row=2, column=0, padx=20, pady=10, sticky="e")
        self.count_3 = ctk.CTkLabel(self.admin_frame, text="0", fg_color="gray30", width=300)
        self.count_3.grid(row=2, column=1, pady=10)

        self.result_btn = ctk.CTkButton(
            self.admin_frame, text="RESULT", fg_color="green", hover_color="darkgreen",
            command=self.update_counts
        )
        self.result_btn.grid(row=3, column=0, columnspan=2, pady=50)

        back_btn = ctk.CTkButton(
            self.admin_frame, text="Back", command=self.go_back
        )
        back_btn.grid(row=4, column=0, padx=20, pady=20, sticky="w")

        self.listening = True
        threading.Thread(target=self.listen_serial, daemon=True).start()

    def update_counts(self):
        conn = self.parent.get_connection()
        if conn:
            cursor = conn.cursor()
            cursor.execute("SELECT party_name, COUNT(*) FROM vote_result GROUP BY party_name")
            results = dict(cursor.fetchall())
            self.count_1.configure(text=str(results.get("Party 1", 0)))
            self.count_2.configure(text=str(results.get("Party 2", 0)))
            self.count_3.configure(text=str(results.get("Party 3", 0)))
            conn.close()

    def listen_serial(self):
        # We need to establish its own connection for the thread
        try:
            conn = self.parent.get_connection()
            cursor = conn.cursor()
            arduino = serial.Serial(COM_PORT, BAUD_RATE, timeout=1)
            while self.listening:
                line = arduino.readline().decode().strip()
                if line:
                    try:
                        letter = line.split('_')[-1]
                        party_idx = ord(letter) - ord('A') + 1
                        party_name = f"Party {party_idx}"
                        cursor.execute("INSERT INTO votes (party_name) VALUES (%s)", (party_name,))
                        conn.commit()
                        self.parent.after(0, self.update_counts)
                    except Exception:
                        pass
                time.sleep(0.1)
            arduino.close()
            conn.close()
        except Exception:
            pass

    def go_back(self):
        self.listening = False
        self.admin_frame.destroy()
        self.parent.login_page()

# === RUN APPLICATION ===
if __name__ == "__main__":
    app = App()
    app.mainloop()
