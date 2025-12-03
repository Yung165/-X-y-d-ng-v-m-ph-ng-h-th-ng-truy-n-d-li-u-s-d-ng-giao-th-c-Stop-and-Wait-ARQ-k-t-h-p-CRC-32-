import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import time
import threading
import zlib
import base64
import random

# --- CẤU HÌNH GIAO DIỆN ---
FONT_NAME = "Times New Roman"
FONT_SIZE = 12

class DataTransmissionSim:
    def __init__(self, root):
        self.root = root
        self.root.title("Mô phỏng Stop-and-Wait ARQ & CRC32")
        self.root.geometry("1100x750")
        
        # Biến trạng thái hệ thống
        self.is_transmitting = False
        self.scenario = tk.StringVar(value="normal") # Giá trị: normal, error, loss
        
        # Khởi tạo giao diện
        self.setup_ui()

    def setup_ui(self):
        """Thiết lập các thành phần giao diện đồ họa"""
        
        # 1. Phần Tiêu đề (Header)
        header_frame = tk.Frame(self.root, bg="#2c3e50", pady=15)
        header_frame.pack(fill="x")
        tk.Label(header_frame, text="MÔ PHỎNG HỆ THỐNG TRUYỀN DỮ LIỆU SỐ ", 
                 font=(FONT_NAME, 18, "bold"), fg="white", bg="#2c3e50").pack()
        tk.Label(header_frame, text="Giao thức: Stop-and-Wait ARQ | Kiểm soát lỗi: CRC32 | Mã hóa: Base64", 
                 font=(FONT_NAME, 11, "italic"), fg="#ecf0f1", bg="#2c3e50").pack()

        # 2. Phần Nội dung chính (Main Content)
        main_frame = tk.Frame(self.root, padx=10, pady=10)
        main_frame.pack(fill="both", expand=True)

        # --- CỘT TRÁI: SENDER (MÁY GỬI) ---
        left_frame = tk.LabelFrame(main_frame, text="SENDER (MÁY GỬI)", 
                                   font=(FONT_NAME, 12, "bold"), fg="blue", bg="#e8f4f8")
        left_frame.pack(side="left", fill="both", expand=True, padx=5)

        tk.Label(left_frame, text="Nhập dữ liệu:", bg="#e8f4f8").pack(anchor="w", padx=5)
        self.txt_input = tk.Entry(left_frame, font=(FONT_NAME, 11))
        self.txt_input.pack(fill="x", padx=5, pady=5)
        self.txt_input.insert(0, "Hello Network") # Giá trị mặc định

        tk.Label(left_frame, text="Nhật ký gửi (Log):", bg="#e8f4f8").pack(anchor="w", padx=5)
        self.log_sender = scrolledtext.ScrolledText(left_frame, height=20, font=("Consolas", 9))
        self.log_sender.pack(fill="both", expand=True, padx=5, pady=5)

        # --- CỘT GIỮA: CHANNEL (KÊNH TRUYỀN & ĐIỀU KHIỂN) ---
        mid_frame = tk.Frame(main_frame, width=250)
        mid_frame.pack(side="left", fill="y", padx=10)

        # Khu vực chọn kịch bản
        tk.Label(mid_frame, text="CHỌN KỊCH BẢN (SCENARIOS)", font=(FONT_NAME, 11, "bold")).pack(pady=(10, 5))
        
        rb1 = tk.Radiobutton(mid_frame, text="1. Truyền bình thường", variable=self.scenario, 
                             value="normal", font=(FONT_NAME, 10))
        rb1.pack(anchor="w")
        rb2 = tk.Radiobutton(mid_frame, text="2. Lỗi dữ liệu (Nhiễu)", variable=self.scenario, 
                             value="error", font=(FONT_NAME, 10))
        rb2.pack(anchor="w")
        rb3 = tk.Radiobutton(mid_frame, text="3. Mất gói tin (Loss)", variable=self.scenario, 
                             value="loss", font=(FONT_NAME, 10))
        rb3.pack(anchor="w")

        # Nút Bắt đầu
        self.btn_send = tk.Button(mid_frame, text="BẮT ĐẦU TRUYỀN", bg="#27ae60", fg="white", 
                                  font=(FONT_NAME, 11, "bold"), command=self.start_transmission_thread)
        self.btn_send.pack(pady=(20, 5), fill="x", ipady=5)

        # Nút Reset (MỚI THÊM)
        self.btn_reset = tk.Button(mid_frame, text="LÀM MỚI (RESET)", bg="#e67e22", fg="white", 
                                  font=(FONT_NAME, 10, "bold"), command=self.reset_app)
        self.btn_reset.pack(pady=5, fill="x", ipady=2)

        # Trạng thái và Hoạt họa
        self.lbl_status = tk.Label(mid_frame, text="Trạng thái: Sẵn sàng", fg="gray", wraplength=200)
        self.lbl_status.pack(pady=10)

        self.canvas_visual = tk.Canvas(mid_frame, height=150, bg="#ecf0f1", relief="sunken", bd=1)
        self.canvas_visual.pack(fill="x", pady=10)
        
        # Vẽ các nút mạng trên Canvas
        self.canvas_visual.create_oval(10, 55, 50, 95, fill="blue", outline="") # Sender Node
        self.canvas_visual.create_text(30, 110, text="Sender")
        
        self.canvas_visual.create_oval(190, 55, 230, 95, fill="red", outline="") # Receiver Node
        self.canvas_visual.create_text(210, 110, text="Receiver")
        
        # Tạo đối tượng gói tin (ẩn ban đầu)
        self.packet_node = self.canvas_visual.create_rectangle(60, 65, 90, 85, fill="orange", state="hidden")

        # --- CỘT PHẢI: RECEIVER (MÁY NHẬN) ---
        right_frame = tk.LabelFrame(main_frame, text="RECEIVER (MÁY NHẬN)", 
                                    font=(FONT_NAME, 12, "bold"), fg="red", bg="#fce4ec")
        right_frame.pack(side="right", fill="both", expand=True, padx=5)

        tk.Label(right_frame, text="Dữ liệu giải mã:", bg="#fce4ec").pack(anchor="w", padx=5)
        self.txt_output = tk.Entry(right_frame, font=(FONT_NAME, 11), state="readonly")
        self.txt_output.pack(fill="x", padx=5, pady=5)

        tk.Label(right_frame, text="Nhật ký nhận (Log):", bg="#fce4ec").pack(anchor="w", padx=5)
        self.log_receiver = scrolledtext.ScrolledText(right_frame, height=20, font=("Consolas", 9))
        self.log_receiver.pack(fill="both", expand=True, padx=5, pady=5)

        # 3. Footer
        footer_frame = tk.Frame(self.root, pady=5)
        footer_frame.pack(fill="x")
        tk.Label(footer_frame, text="ĐỀ TÀI: XÂY DỰNG VÀ MÔ PHỎNG HỆ THỐNG TRUYỀN DỮ LIỆU SỬ DỤNG GIAO THỨC STOP-AND-WAIT ARQ VÀ MÃ HÓA CRC", 
                 font=(FONT_NAME, 9, "italic")).pack()

    # --- CÁC HÀM XỬ LÝ LOGIC ---

    def log(self, widget, message):
        """Hàm ghi log vào khung text"""
        timestamp = time.strftime("%H:%M:%S")
        widget.insert(tk.END, f"[{timestamp}] {message}\n")
        widget.see(tk.END) # Tự động cuộn xuống cuối

    def encode_base64(self, text):
        """Mã hóa chuỗi văn bản sang Base64"""
        data_bytes = text.encode('utf-8')
        encoded_bytes = base64.b64encode(data_bytes)
        return encoded_bytes # Trả về dạng bytes

    def calculate_crc(self, data_bytes):
        """Tính toán mã CRC-32"""
        return zlib.crc32(data_bytes)

    def reset_app(self):
        """Hàm Reset để xóa dữ liệu cũ, chuẩn bị cho kịch bản mới"""
        if self.is_transmitting:
            messagebox.showwarning("Cảnh báo", "Hệ thống đang truyền tin. Vui lòng đợi hoàn tất!")
            return

        # Xóa log Sender
        self.log_sender.delete(1.0, tk.END)
        # Xóa log Receiver
        self.log_receiver.delete(1.0, tk.END)
        # Xóa output
        self.txt_output.config(state="normal")
        self.txt_output.delete(0, tk.END)
        self.txt_output.config(state="readonly")
        # Đặt lại Input mặc định
        self.txt_input.delete(0, tk.END)
        self.txt_input.insert(0, "Hello Network")
        # Reset trạng thái
        self.lbl_status.config(text="Trạng thái: Đã làm mới. Sẵn sàng.", fg="black")
        self.canvas_visual.itemconfig(self.packet_node, state="hidden")
        
        # Đặt lại kịch bản về mặc định (tuỳ chọn)
        self.scenario.set("normal")

    def start_transmission_thread(self):
        """Bắt đầu luồng chạy mô phỏng để không treo giao diện"""
        if self.is_transmitting: return
        
        raw_data = self.txt_input.get()
        if not raw_data:
            messagebox.showwarning("Cảnh báo", "Vui lòng nhập dữ liệu để truyền!")
            return

        # Khóa giao diện
        self.is_transmitting = True
        self.btn_send.config(state="disabled", text="ĐANG XỬ LÝ...")
        self.btn_reset.config(state="disabled") # Khóa nút Reset khi đang chạy
        self.txt_output.config(state="normal")
        self.txt_output.delete(0, tk.END)
        self.txt_output.config(state="readonly")
        
        # Chỉ xóa log nếu người dùng muốn (ở đây ta giữ lại log cũ nếu không bấm Reset)
        # Để tự động xóa mỗi lần chạy, bỏ comment 2 dòng dưới:
        # self.log_sender.delete(1.0, tk.END)
        # self.log_receiver.delete(1.0, tk.END)

        # Chạy logic trong luồng riêng
        threading.Thread(target=self.transmission_process, args=(raw_data,), daemon=True).start()

    def animate_packet(self, start_x, end_x, color="orange", speed=0.03):
        """Hàm tạo hoạt họa gói tin di chuyển"""
        self.canvas_visual.itemconfig(self.packet_node, state="normal", fill=color)
        self.canvas_visual.coords(self.packet_node, start_x, 65, start_x + 30, 85)
        
        current_x = start_x
        step = 5 if end_x > start_x else -5
        
        while (step > 0 and current_x < end_x) or (step < 0 and current_x > end_x):
            self.canvas_visual.move(self.packet_node, step, 0)
            self.root.update()
            time.sleep(speed)
            current_x += step
            
        self.canvas_visual.itemconfig(self.packet_node, state="hidden")

    def transmission_process(self, raw_data):
        """Logic chính của giao thức Stop-and-Wait ARQ"""
        scenario = self.scenario.get()
        success = False
        retry_count = 0
        MAX_RETRIES = 3 

        # --- BƯỚC 1: SENDER ---
        self.log(self.log_sender, f"--- BẮT ĐẦU PHIÊN MỚI ---")
        self.log(self.log_sender, f"Dữ liệu gốc: '{raw_data}'")
        
        payload = self.encode_base64(raw_data)
        self.log(self.log_sender, f"Mã hóa Base64: {payload}")
        
        crc_value = self.calculate_crc(payload)
        self.log(self.log_sender, f"Tính CRC-32: {crc_value}")
        
        frame = {
            "payload": payload,
            "crc": crc_value,
            "seq_num": 1
        }
        self.log(self.log_sender, f"Đóng gói Frame: [Seq:1 | Data | CRC]")
        time.sleep(1)

        # --- BƯỚC 2: VÒNG LẶP TRUYỀN TIN ---
        while not success and retry_count < MAX_RETRIES:
            if retry_count > 0:
                self.log(self.log_sender, f"--- THỬ LẠI LẦN {retry_count} ---")
            
            self.lbl_status.config(text="Sender: Đang gửi gói tin...", fg="blue")
            self.log(self.log_sender, "Đang gửi Frame qua kênh truyền...")
            self.animate_packet(50, 190, color="orange") 
            
            received_frame = frame.copy() 
            
            # Kịch bản 3: Mất gói tin (Loss)
            if scenario == "loss" and retry_count == 0:
                self.log(self.log_sender, "!!! SỰ CỐ: Gói tin bị mất.")
                self.lbl_status.config(text="SỰ CỐ: Mất kết nối...", fg="red")
                time.sleep(2) 
                self.log(self.log_sender, "TIMEOUT: Không có phản hồi.")
                self.log(self.log_sender, "-> Kích hoạt gửi lại.")
                retry_count += 1
                continue 

            # Kịch bản 2: Lỗi dữ liệu (Error)
            if scenario == "error" and retry_count == 0:
                self.log(self.log_sender, "!!! SỰ CỐ: Nhiễu kênh truyền.")
                received_frame["payload"] = b"CorruptedBytes==" 
                self.lbl_status.config(text="SỰ CỐ: Dữ liệu bị nhiễu!", fg="orange")

            # --- BƯỚC 3: RECEIVER ---
            self.lbl_status.config(text="Receiver: Đang xử lý...", fg="purple")
            self.log(self.log_receiver, f"Nhận Frame [Seq:{received_frame['seq_num']}]")
            
            crc_check = self.calculate_crc(received_frame["payload"])
            self.log(self.log_receiver, f"CRC tính lại: {crc_check}")

            if crc_check == received_frame["crc"]:
                # THÀNH CÔNG
                self.log(self.log_receiver, "CRC OK. Chấp nhận gói tin.")
                try:
                    decoded_bytes = base64.b64decode(received_frame["payload"])
                    decoded_text = decoded_bytes.decode('utf-8')
                    
                    self.txt_output.config(state="normal")
                    self.txt_output.insert(0, decoded_text)
                    self.txt_output.config(state="readonly")
                    
                    self.log(self.log_receiver, f"Kết quả: '{decoded_text}'")
                    
                    # Gửi ACK
                    self.log(self.log_receiver, "-> Gửi ACK (Xanh).")
                    self.animate_packet(190, 50, color="#2ecc71") # Xanh lá
                    self.log(self.log_sender, "Nhận ACK. Hoàn tất.")
                    self.lbl_status.config(text="HOÀN THÀNH: Thành công.", fg="green")
                    success = True
                except Exception as e:
                    self.log(self.log_receiver, f"Lỗi giải mã: {str(e)}")
            else:
                # LỖI CRC
                self.log(self.log_receiver, "CRC FAIL! Hủy gói tin.")
                self.log(self.log_receiver, "-> Gửi NAK (Đỏ).")
                
                # Gửi NAK
                self.animate_packet(190, 50, color="#e74c3c") # Đỏ
                self.log(self.log_sender, "Nhận NAK. Chuẩn bị gửi lại...")
                self.lbl_status.config(text="CẢNH BÁO: Đang gửi lại...", fg="orange")
                
                time.sleep(1)
                retry_count += 1
                if retry_count == 1: 
                    scenario = "normal" 

        self.is_transmitting = False
        self.btn_send.config(state="normal", text="BẮT ĐẦU TRUYỀN")
        self.btn_reset.config(state="normal") # Mở lại nút Reset
        if not success:
            self.lbl_status.config(text="THẤT BẠI: Quá số lần thử lại.", fg="red")

if __name__ == "__main__":
    root = tk.Tk()
    app = DataTransmissionSim(root)
    root.mainloop()