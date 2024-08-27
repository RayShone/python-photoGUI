import tkinter as tk
from tkinter import filedialog
from PIL import Image, ImageDraw, ImageFont
import numpy as np
import time

class ImageConverter:
    def __init__(self, root):
        self.root = root
        self.root.title("图片转换器")
        self.setup_input_layout()

        self.console_output = tk.Text(self.root, height=10, width=50)
        self.console_output.pack(pady=10)
        credits_label = tk.Label(self.root,
                                 text="本项目由RayShone制作，完全开源且免费，项目涉及所有资源皆来源于网络，如有雷同，不甚荣幸！",
                                 bg="lightgray")
        credits_label.pack(side=tk.BOTTOM, fill=tk.X)

    def setup_input_layout(self):
        input_frame = tk.Frame(self.root)
        input_frame.pack(pady=10)

        custom_text_label = tk.Label(input_frame, text="输入自定义字符串:")
        custom_text_label.grid(row=0, column=0, padx=5, pady=5)
        self.custom_text_entry = tk.Entry(input_frame)
        self.custom_text_entry.grid(row=0, column=1, padx=5, pady=5)

        custom_text_size_label = tk.Label(input_frame, text="输入自定义字符串大小（默认为10）:")
        custom_text_size_label.grid(row=1, column=0, padx=5, pady=5)
        self.custom_text_size_entry = tk.Entry(input_frame)
        self.custom_text_size_entry.insert(0, "10")
        self.custom_text_size_entry.grid(row=1, column=1, padx=5, pady=5)

        self.convert_button = tk.Button(input_frame, text="开始转换！", command=self.convert_image)
        self.convert_button.grid(row=2, columnspan=2, pady=10)

        mode_frame = tk.Frame(self.root)
        mode_frame.pack()

        self.cn_mode_button = tk.Button(mode_frame, text="中文模式", command=lambda: self.set_text_mode("CN"))
        self.cn_mode_button.grid(row=0, column=0, padx=5, pady=5)

        self.en_mode_button = tk.Button(mode_frame, text="英文模式", command=lambda: self.set_text_mode("EN"))
        self.en_mode_button.grid(row=0, column=1, padx=5, pady=5)

    def set_text_mode(self, mode):
        if mode == "CN":
            self.current_text_mode = "CN"
            self.cn_mode_button.configure(relief=tk.SUNKEN)
            self.en_mode_button.configure(relief=tk.RAISED)
        elif mode == "EN":
            self.current_text_mode = "EN"
            self.en_mode_button.configure(relief=tk.SUNKEN)
            self.cn_mode_button.configure(relief=tk.RAISED)

    def convert_image(self):
        file_path = filedialog.askopenfilename()
        if file_path:
            custom_text = self.custom_text_entry.get()
            text_size = int(self.custom_text_size_entry.get() or 10)
            self.generate_image(file_path, "converted_image.jpg", scale=2, sample_step=3, text=custom_text, text_size=text_size, console_output=self.console_output)

    def generate_image(self, srd_img_file_path, dst_img_file_path=None, scale=2, sample_step=3, text="", text_size=20, console_output=None):
        start_time = int(time.time())
        old_img = Image.open(srd_img_file_path)
        pix = old_img.load()
        width = old_img.size[0]
        height = old_img.size[1]

        canvas = np.ndarray((height * scale, width * scale, 3), np.uint8)
        canvas[:, :, :] = 255
        new_image = Image.fromarray(canvas)
        draw = ImageDraw.Draw(new_image)

        font_path = "simsun.ttc" if text else ImageFont.load_default()

        font = ImageFont.truetype(font_path, text_size)

        char_table = list(text)

        pix_count = 0
        table_len = len(char_table)
        for y in range(height):
            for x in range(width):
                if x % sample_step == 0 and y % sample_step == 0:
                    draw.text((x * scale, y * scale), char_table[pix_count % table_len], pix[x, y], font)
                    pix_count += 1

        if dst_img_file_path is not None:
            new_image.save(dst_img_file_path)

        used_time = int(time.time()) - start_time
        result_message = f"耗时: {used_time} 秒, 像素数: {pix_count}\n"
        console_output.insert(tk.END, result_message)
        console_output.insert(tk.END, f"{pix_count} 转换像素\n")
        new_image.show()

if __name__ == "__main__":
    root = tk.Tk()
    root.geometry("600x600")
    image_converter = ImageConverter(root)
    root.mainloop()
