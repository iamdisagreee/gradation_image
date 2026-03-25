import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from PIL import Image, ImageTk
import numpy as np


class ImageProcessorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Градационные преобразования")
        self.root.geometry("1200x800")

        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)

        self.original_image = None
        self.original_np = None
        self.processed_image = None

        self.setup_ui()

    def setup_ui(self):
        self.canvas = tk.Canvas(self.root, highlightthickness=0)
        self.scrollbar = ttk.Scrollbar(self.root, orient="vertical", command=self.canvas.yview)
        self.scrollable_frame = ttk.Frame(self.canvas)

        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )

        self.canvas_window = self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        self.canvas.grid(row=0, column=0, sticky="nsew")
        self.scrollbar.grid(row=0, column=1, sticky="ns")

        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)

        self.canvas.bind("<Configure>", self._on_canvas_configure)

        self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)

        self._create_interface()

    def _on_canvas_configure(self, event):
        """Растягиваем содержимое на всю ширину Canvas при изменении размера окна"""
        self.canvas.itemconfig(self.canvas_window, width=event.width)

    def _on_mousewheel(self, event):
        """Обработка прокрутки колёсиком мыши"""
        self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    def _create_interface(self):
        """Создание всего интерфейса внутри прокручиваемого фрейма"""

        content_frame = ttk.Frame(self.scrollable_frame)
        content_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        content_frame.columnconfigure(0, weight=1)
        content_frame.columnconfigure(1, weight=1)

        self.img_frame = ttk.LabelFrame(content_frame, text="Изображения")
        self.img_frame.grid(row=0, column=0, columnspan=2, sticky="nsew", pady=(0, 10))
        self.img_frame.columnconfigure(0, weight=1)
        self.img_frame.columnconfigure(1, weight=1)
        self.img_frame.rowconfigure(0, weight=1)

        self.left_frame = ttk.LabelFrame(self.img_frame, text="Исходное изображение")
        self.left_frame.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
        self.lbl_original = ttk.Label(self.left_frame, text="Нет изображения")
        self.lbl_original.pack(padx=5, pady=5, expand=True)

        self.right_frame = ttk.LabelFrame(self.img_frame, text="Результат преобразования")
        self.right_frame.grid(row=0, column=1, sticky="nsew", padx=5, pady=5)
        self.lbl_result = ttk.Label(self.right_frame, text="Ожидание обработки")
        self.lbl_result.pack(padx=5, pady=5, expand=True)

        self.ctrl_frame = ttk.LabelFrame(content_frame, text="Панель управления")
        self.ctrl_frame.grid(row=1, column=0, columnspan=2, sticky="nsew", pady=(0, 10))
        self.ctrl_frame.columnconfigure(0, weight=1)
        self.ctrl_frame.columnconfigure(1, weight=1)
        self.ctrl_frame.columnconfigure(2, weight=1)
        self.ctrl_frame.columnconfigure(3, weight=1)

        btn_load = ttk.Button(self.ctrl_frame, text="📁 Загрузить изображение", command=self.load_image)
        btn_load.grid(row=0, column=0, padx=5, pady=5, sticky="ew")

        ttk.Label(self.ctrl_frame, text="Тип преобразования:").grid(row=0, column=1, padx=5, pady=5, sticky="e")

        self.transform_var = tk.StringVar(value="1. Цветное в полутоновое")
        self.combo_transform = ttk.Combobox(self.ctrl_frame, textvariable=self.transform_var, state="readonly",
                                            width=30)
        self.combo_transform['values'] = (
            "1. Цветное в полутоновое",
            "2. Полутоновое в бинарное",
            "3. Негатив",
            "4. Логарифмическое",
            "5. Степенное (Гамма)"
        )
        self.combo_transform.grid(row=0, column=2, padx=5, pady=5, sticky="ew")
        self.combo_transform.bind("<<ComboboxSelected>>", self.on_transform_change)

        self.param_frame = ttk.LabelFrame(self.ctrl_frame, text="Параметры преобразования")
        self.param_frame.grid(row=1, column=0, columnspan=4, sticky="nsew", padx=5, pady=5)
        self.param_frame.columnconfigure(0, weight=1)

        self.params_container = ttk.Frame(self.param_frame)
        self.params_container.pack(fill=tk.X, padx=5, pady=5)

        btn_apply = ttk.Button(self.ctrl_frame, text="▶ Применить преобразование", command=self.apply_transformation)
        btn_apply.grid(row=2, column=0, columnspan=4, padx=10, pady=10, sticky="ew")


        self.on_transform_change(None)

    def on_transform_change(self, event):
        """Обновление полей ввода параметров в зависимости от выбранного преобразования"""
        # Очистка старых параметров
        for widget in self.params_container.winfo_children():
            widget.destroy()

        # ИСПРАВЛЕНИЕ: используем lower() для надежного сравнения
        selection = self.transform_var.get().lower()
        self.param_entries = {}

        info = "Выберите преобразование из списка"

        if "цветное в полутоновое" in selection:
            self._create_param_entry("Вес R (Kr):", "0.299", 0, key="kr")
            self._create_param_entry("Вес G (Kg):", "0.587", 1, key="kg")
            self._create_param_entry("Вес B (Kb):", "0.114", 2, key="kb")
            info = "Формула: Y = Kr*R + Kg*G + Kb*B. Сумма весов должна быть ≈ 1.0"

        elif "бинарное" in selection:
            self._create_param_entry("Порог бинаризации (0-255):", "128", 0, key="threshold")
            info = "Пиксели > порога становятся 255 (белые), иначе 0 (черные)"

        elif "негатив" in selection:
            self._create_param_entry("Максимальное значение:", "255", 0, key="max_val")
            info = "Формула: S = Max - R. Обычно Max = 255"

        elif "логарифмическое" in selection:
            self._create_param_entry("Масштабирующий коэффициент (c):", "28.0", 0, key="c")
            self._create_param_entry("Смещение (для log(1+r)):", "1", 1, key="offset")
            info = "Формула: s = c * log(смещение + r). Рекомендуется c = 255/log(1+255) ≈ 28.0"

        elif "степенное" in selection:
            self._create_param_entry("Гамма (γ):", "1.5", 0, key="gamma")
            self._create_param_entry("Масштабирующий коэффициент (c):", "1.0", 1, key="c")
            info = "Формула: s = c * r^γ. γ < 1 осветляет, γ > 1 затемняет"

        info_label = ttk.Label(self.params_container, text=info, foreground="blue")
        info_label.grid(row=len(self.param_entries), column=0, columnspan=4, sticky=tk.W, padx=5, pady=5)

    def _create_param_entry(self, label_text, default_value, row, key=None):
        """Создание поля ввода параметра"""
        label = ttk.Label(self.params_container, text=label_text)
        label.grid(row=row, column=0, sticky=tk.W, padx=5, pady=3)

        entry = ttk.Entry(self.params_container, width=15)
        entry.insert(0, default_value)
        entry.grid(row=row, column=1, sticky=tk.W, padx=5, pady=3)

        if key is None:
            key = label_text.split("(")[0].strip().replace(" ", "_").lower()

        self.param_entries[key] = entry

    def load_image(self):
        file_path = filedialog.askopenfilename(
            title="Выберите изображение",
            filetypes=[
                ("BMP Files", "*.bmp"),
                ("PCX Files", "*.pcx"),
                ("PNG Files", "*.png"),
                ("All Files", "*.*")
            ]
        )

        if file_path:
            try:
                img = Image.open(file_path)
                if img.mode != 'RGB':
                    img = img.convert('RGB')

                self.original_image = img
                self.original_np = np.array(img)

                self.display_image(self.lbl_original, img)
                self.lbl_result.config(text="Ожидание обработки")

                if hasattr(self, 'tk_result'):
                    self.lbl_result.config(image='')
                    self.tk_result = None

            except Exception as e:
                messagebox.showerror("Ошибка", f"Не удалось загрузить изображение:\n{e}")

    def display_image(self, label, pil_image):
        """Масштабирует изображение для отображения в интерфейсе"""
        max_w, max_h = 500, 500
        img_copy = pil_image.copy()
        img_copy.thumbnail((max_w, max_h))

        tk_img = ImageTk.PhotoImage(img_copy)
        label.config(image=tk_img, text="")

        if label == self.lbl_original:
            self.tk_original = tk_img
        else:
            self.tk_result = tk_img

    def apply_transformation(self):
        if self.original_np is None:
            messagebox.showwarning("Внимание", "Сначала загрузите изображение!")
            return

        selection = self.transform_var.get().lower()
        img_np = self.original_np.copy()

        try:
            if "цветное в полутоновое" in selection:
                kr = float(self.param_entries["kr"].get())
                kg = float(self.param_entries["kg"].get())
                kb = float(self.param_entries["kb"].get())
                img_np = self.to_grayscale(img_np, kr, kg, kb)

            elif "бинарное" in selection:
                threshold = float(self.param_entries["threshold"].get())
                gray = self.to_grayscale(img_np, 0.299, 0.587, 0.114)
                img_np = self.to_binary(gray, threshold)

            elif "негатив" in selection:
                max_val = float(self.param_entries["max_val"].get())
                img_np = self.to_negative(img_np, max_val)

            elif "логарифмическое" in selection:
                c = float(self.param_entries["c"].get())
                offset = float(self.param_entries["offset"].get())
                gray = self.to_grayscale(img_np, 0.299, 0.587, 0.114)
                img_np = self.to_logarithmic(gray, c, offset)

            elif "степенное" in selection:
                gamma = float(self.param_entries["gamma"].get())
                c = float(self.param_entries["c"].get())
                gray = self.to_grayscale(img_np, 0.299, 0.587, 0.114)
                img_np = self.to_power_law(gray, gamma, c)

            if len(img_np.shape) == 2:
                result_pil = Image.fromarray(img_np.astype(np.uint8), mode='L')
            else:
                result_pil = Image.fromarray(img_np.astype(np.uint8), mode='RGB')

            self.processed_image = result_pil
            self.display_image(self.lbl_result, result_pil)

        except ValueError as e:
            messagebox.showerror("Ошибка параметров",
                                 f"Проверьте введенные числа (используйте точку для дробных):\n{e}")
        except KeyError as e:
            messagebox.showerror("Ошибка", f"Не найдено поле параметра: {e}")
        except Exception as e:
            messagebox.showerror("Ошибка обработки", f"{e}")

    def to_grayscale(self, img_np, kr=0.299, kg=0.587, kb=0.114):
        if len(img_np.shape) == 2:
            return img_np
        weights = np.array([kr, kg, kb])
        gray = np.dot(img_np[..., :3], weights)
        return np.clip(gray, 0, 255).astype(np.uint8)

    def to_binary(self, img_np, threshold):
        binary = np.where(img_np > threshold, 255, 0)
        return binary.astype(np.uint8)

    def to_negative(self, img_np, max_val=255):
        return np.clip(max_val - img_np, 0, 255).astype(np.uint8)

    def to_logarithmic(self, img_np, c=28.0, offset=1):
        log_img = c * np.log(offset + img_np.astype(np.float32))
        return np.clip(log_img, 0, 255).astype(np.uint8)

    def to_power_law(self, img_np, gamma=1.5, c=1.0):
        normalized = img_np.astype(np.float32) / 255.0
        powered = c * np.power(normalized, gamma)
        return np.clip(powered * 255, 0, 255).astype(np.uint8)


if __name__ == "__main__":
    root = tk.Tk()

    try:
        style = ttk.Style()
        style.theme_use('clam')
        style.configure('TLabel', font=('Arial', 10))
        style.configure('TButton', font=('Arial', 10, 'bold'))
        style.configure('TLabelframe', font=('Arial', 11, 'bold'))
    except:
        pass

    app = ImageProcessorApp(root)
    root.mainloop()