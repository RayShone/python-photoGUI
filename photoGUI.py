import tkinter as tk
from tkinter import filedialog
from PIL import Image, ImageDraw, ImageFont
import numpy as np
import time
import threading
import os
import sys


# ---------------------------------------------------------------------------
# helper: find a usable truetype font across platforms
# ---------------------------------------------------------------------------
def _find_font():
    """Return path to an available CJK-capable truetype font, or '' if none."""
    candidates = []
    if sys.platform == 'win32':
        candidates = [
            os.path.join(os.environ.get('WINDIR', 'C:\\Windows'), 'Fonts', 'simsun.ttc'),
            os.path.join(os.environ.get('WINDIR', 'C:\\Windows'), 'Fonts', 'msyh.ttc'),
            os.path.join(os.environ.get('WINDIR', 'C:\\Windows'), 'Fonts', 'msyhbd.ttc'),
            os.path.join(os.environ.get('WINDIR', 'C:\\Windows'), 'Fonts', 'simhei.ttf'),
            os.path.join(os.environ.get('WINDIR', 'C:\\Windows'), 'Fonts', 'arial.ttf'),
        ]
    elif sys.platform == 'darwin':
        candidates = [
            '/System/Library/Fonts/PingFang.ttc',
            '/System/Library/Fonts/STHeiti Light.ttc',
            '/System/Library/Fonts/Helvetica.ttc',
            '/Library/Fonts/Arial.ttf',
        ]
    else:  # linux / others
        candidates = [
            '/usr/share/fonts/truetype/droid/DroidSansFallbackFull.ttf',
            '/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc',
            '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',
            '/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf',
            '/usr/share/fonts/noto/NotoSansCJK-Regular.ttc',
            '/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc',
        ]

    for p in candidates:
        if os.path.isfile(p):
            return p
    return ''


# default character sets
DEFAULT_CN_CHARS = (
    "我爱你中国我爱你中国我爱你中国"
    "山川河流花草树木天地日月"
    "风雨雷电春夏秋冬东西南北"
    "人生如梦岁月如歌心之所向行之所往"
)
DEFAULT_EN_CHARS = "@%#*+=-:. "


class ImageConverter:
    def __init__(self, root):
        self.root = root
        self.root.title("图片转换器")

        # ── state ──────────────────────────────────────────────────
        self.current_text_mode = "CN"       # "CN" or "EN"
        self.converting = False

        # ── UI ─────────────────────────────────────────────────────
        self._build_input_area()
        self._build_mode_buttons()
        self._build_console()
        self._build_footer()

    # ==================================================================
    # UI construction
    # ==================================================================

    def _build_input_area(self):
        frame = tk.Frame(self.root)
        frame.pack(pady=10)

        tk.Label(frame, text="输入自定义字符串:").grid(row=0, column=0, padx=5, pady=5, sticky='e')
        self.custom_text_entry = tk.Entry(frame, width=40)
        self.custom_text_entry.grid(row=0, column=1, padx=5, pady=5, sticky='w')

        tk.Label(frame, text="字体大小 (默认10):").grid(row=1, column=0, padx=5, pady=5, sticky='e')
        self.text_size_entry = tk.Entry(frame, width=8)
        self.text_size_entry.insert(0, "10")
        self.text_size_entry.grid(row=1, column=1, padx=5, pady=5, sticky='w')

        tk.Label(frame, text="采样步长 (默认3, 越大越快):").grid(row=2, column=0, padx=5, pady=5, sticky='e')
        self.sample_step_entry = tk.Entry(frame, width=8)
        self.sample_step_entry.insert(0, "3")
        self.sample_step_entry.grid(row=2, column=1, padx=5, pady=5, sticky='w')

        self.convert_btn = tk.Button(frame, text="选择图片并开始转换！", command=self.convert_image)
        self.convert_btn.grid(row=3, columnspan=2, pady=10)

    def _build_mode_buttons(self):
        frame = tk.Frame(self.root)
        frame.pack()

        self.cn_btn = tk.Button(frame, text="中文模式", command=lambda: self.set_text_mode("CN"))
        self.cn_btn.grid(row=0, column=0, padx=5, pady=5)

        self.en_btn = tk.Button(frame, text="英文模式", command=lambda: self.set_text_mode("EN"))
        self.en_btn.grid(row=0, column=1, padx=5, pady=5)

        # initial visual state
        self.cn_btn.configure(relief=tk.SUNKEN)
        self.en_btn.configure(relief=tk.RAISED)

    def _build_console(self):
        self.console_output = tk.Text(self.root, height=10, width=60, state=tk.DISABLED)
        self.console_output.pack(pady=10, padx=10, fill=tk.BOTH, expand=True)

    def _build_footer(self):
        credits = tk.Label(
            self.root,
            text="本项目由RayShone制作，完全开源且免费。修复版：修复空字符串崩溃、字体路径、颜色模式等bug。",
            bg="lightgray",
        )
        credits.pack(side=tk.BOTTOM, fill=tk.X)

    # ==================================================================
    # helpers
    # ==================================================================

    def _log(self, msg):
        self.console_output.configure(state=tk.NORMAL)
        self.console_output.insert(tk.END, msg + "\n")
        self.console_output.see(tk.END)
        self.console_output.configure(state=tk.DISABLED)
        self.root.update_idletasks()

    def _safe_int(self, val, default):
        """Parse int with fallback on ValueError."""
        try:
            return int(val)
        except (ValueError, TypeError):
            return default

    # ==================================================================
    # mode toggle (now actually functional)
    # ==================================================================

    def set_text_mode(self, mode):
        self.current_text_mode = mode
        if mode == "CN":
            self.cn_btn.configure(relief=tk.SUNKEN)
            self.en_btn.configure(relief=tk.RAISED)
        else:
            self.en_btn.configure(relief=tk.SUNKEN)
            self.cn_btn.configure(relief=tk.RAISED)

    # ==================================================================
    # convert entry point
    # ==================================================================

    def convert_image(self):
        if self.converting:
            self._log("⚠️ 正在转换中，请等待...")
            return

        file_path = filedialog.askopenfilename(
            title="选择图片",
            filetypes=[
                ("图片文件", "*.jpg *.jpeg *.png *.bmp *.gif *.tiff *.webp"),
                ("所有文件", "*.*"),
            ],
        )
        if not file_path:
            return

        custom_text = self.custom_text_entry.get().strip()
        text_size = self._safe_int(self.text_size_entry.get(), 10)
        sample_step = self._safe_int(self.sample_step_entry.get(), 3)

        # clamp reasonable bounds
        text_size = max(4, min(text_size, 200))
        sample_step = max(1, min(sample_step, 50))

        self.convert_btn.configure(state=tk.DISABLED, text="转换中...")
        self.converting = True

        def _run():
            try:
                self.generate_image(
                    file_path,
                    dst_img_file_path="converted_image.jpg",
                    scale=2,
                    sample_step=sample_step,
                    text=custom_text,
                    text_size=text_size,
                )
            except Exception as e:
                self._log(f"❌ 转换失败: {e}")
            finally:
                self.converting = False
                self.convert_btn.configure(state=tk.NORMAL, text="选择图片并开始转换！")

        threading.Thread(target=_run, daemon=True).start()

    # ==================================================================
    # core conversion logic
    # ==================================================================

    def generate_image(self, src_path, dst_img_file_path=None, scale=2,
                       sample_step=3, text="", text_size=20):
        start_time = time.time()

        # ── 1. open & normalize to RGB ──────────────────────────
        old_img = Image.open(src_path)
        if old_img.mode not in ('RGB', 'RGBA'):
            old_img = old_img.convert('RGB')
        # Use RGBA for paste if alpha present, else RGB
        if old_img.mode == 'RGBA':
            old_img = old_img.convert('RGBA')
        else:
            old_img = old_img.convert('RGB')

        pix = old_img.load()
        width, height = old_img.size

        # ── 2. determine character table ────────────────────────
        if text:
            char_table = list(text)
        elif self.current_text_mode == "CN":
            char_table = list(DEFAULT_CN_CHARS)
        else:
            char_table = list(DEFAULT_EN_CHARS)

        table_len = len(char_table)
        if table_len == 0:
            raise ValueError("字符表为空，请输入自定义字符串。")

        # ── 3. font ─────────────────────────────────────────────
        font = None
        font_path = _find_font()
        if font_path:
            try:
                font = ImageFont.truetype(font_path, text_size)
            except Exception:
                font = None

        if font is None:
            # fallback to default bitmap font (works everywhere)
            font = ImageFont.load_default()

        # ── 4. canvas ───────────────────────────────────────────
        canvas = np.full((height * scale, width * scale, 3), 255, dtype=np.uint8)
        new_image = Image.fromarray(canvas, mode='RGB')
        draw = ImageDraw.Draw(new_image)

        # ── 5. render characters ────────────────────────────────
        pix_count = 0
        for y in range(height):
            for x in range(width):
                if x % sample_step == 0 and y % sample_step == 0:
                    ch = char_table[pix_count % table_len]
                    color = pix[x, y]

                    # Normalise colour to a valid PIL colour.
                    # PIL.ImageDraw.text accepts:
                    #   (R,G,B) / (R,G,B,A) / '#rrggbb' / named string
                    # For greyscale or palette images we already converted
                    # to RGB/RGBA above, so pix[x,y] is a tuple.
                    if old_img.mode == 'RGBA' and isinstance(color, tuple) and len(color) == 4:
                        # RGBA → RGB by blending on white background
                        r, g, b, a = color
                        if a < 255:
                            alpha = a / 255.0
                            r = int(r * alpha + 255 * (1 - alpha))
                            g = int(g * alpha + 255 * (1 - alpha))
                            b = int(b * alpha + 255 * (1 - alpha))
                        color = (r, g, b)

                    elif not isinstance(color, tuple) or len(color) < 3:
                        # safety fallback (should not happen after convert)
                        color = (0, 0, 0)

                    try:
                        draw.text((x * scale, y * scale), ch, fill=color, font=font)
                    except Exception:
                        # if fill is malformed for any reason, use black
                        draw.text((x * scale, y * scale), ch, fill=(0, 0, 0), font=font)

                    pix_count += 1

        # ── 6. save & show ──────────────────────────────────────
        if dst_img_file_path:
            new_image.save(dst_img_file_path)
            self._log(f"✅ 已保存: {dst_img_file_path}")

        elapsed = round(time.time() - start_time, 2)
        self._log(f"⏱ 耗时: {elapsed} 秒  |  绘制字符数: {pix_count}")

        # show in a separate thread so it doesn't block GUI
        new_image.show()


# ======================================================================
if __name__ == "__main__":
    root = tk.Tk()
    root.geometry("650x650")
    app = ImageConverter(root)
    root.mainloop()
