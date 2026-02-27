import customtkinter as ctk
import tkinter.messagebox as messagebox
import cv2
import serial
import time
import oracledb

# ================= SERIAL CONFIG =================
COM_PORT = "COM5"      # 🔴 CHANGE to your Arduino COM port
BAUD_RATE = 9600

# ================= DATABASE CONFIG =================
DB_USER = "voting_schema"
DB_PASS = "voting123"
DSN = "localhost:1521/XEPDB1"

# ==================================================

ctk.set_appearance_mode("DARK")
ctk.set_default_color_theme("green")


# ================= QR SCAN FUNCTION (OpenCV) =================
def scan_qr_opencv():
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


# ================= MAIN APPLICATION =================
class QRScanApp(ctk.CTk):

    def __init__(self):
        super().__init__()

        self.title("E-Voting System - QR Scan")
        self.geometry("600x600")
        self.resizable(False, False)

        self.locked = False

        ctk.CTkLabel(
            self, text="QR SCAN & VERIFY",
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

    # ---------------- DATABASE CONNECTION ----------------
    def get_connection(self):
        return oracledb.connect(
            user=DB_USER,
            password=DB_PASS,
            dsn=DSN
        )

    # ---------------- SERIAL SEND ----------------
    def send_to_arduino(self, payload):
        try:
            arduino = serial.Serial(COM_PORT, BAUD_RATE, timeout=1)
            time.sleep(2)  # wait for Arduino reset
            arduino.write((payload + "\n").encode())
            arduino.close()
        except Exception as e:
            messagebox.showerror("Serial Error", str(e))

    # ---------------- START SCAN ----------------
    def start_scan(self):
        if self.locked:
            return

        self.status_label.configure(text="Scanning QR...")
        self.update()

        qr_data = scan_qr_opencv()

        if qr_data:
            self.process_qr(qr_data)
        else:
            self.status_label.configure(text="Scan cancelled")

    # ---------------- PROCESS QR ----------------
    def process_qr(self, voter_id):
        try:
            conn = self.get_connection()
            cursor = conn.cursor()

            cursor.execute("""
                SELECT voter_name
                FROM v_voterid_prestored_data
                WHERE UPPER(voter_id) = :vid
            """, {"vid": voter_id.upper()})

            result = cursor.fetchone()
            conn.close()

            if result:
                voter_name = result[0]

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

        except Exception as e:
            messagebox.showerror("Error", str(e))

    # ---------------- RESET ----------------
    def reset_app(self):
        self.locked = False
        self.status_label.configure(text="Click START to scan QR")
        self.start_btn.configure(state="normal")


# ================= RUN APP =================
if __name__ == "__main__":
    app = QRScanApp()
    app.mainloop()
