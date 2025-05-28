import re
import unicodedata
import tkinter as tk
from tkinter import scrolledtext, messagebox, filedialog
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import mm

# === Logic ===

invisible_patterns = {
    '\u200B': 'ZERO WIDTH SPACE',
    '\u200C': 'ZERO WIDTH NON-JOINER',
    '\u200D': 'ZERO WIDTH JOINER',
    '\u200E': 'LEFT-TO-RIGHT MARK',
    '\u200F': 'RIGHT-TO-LEFT MARK',
    '\uFEFF': 'ZERO WIDTH NO-BREAK SPACE (BOM)',
    '\u202F': 'NARROW NO-BREAK SPACE',
}

def visualize_invisible_chars(text, stats):
    visualization = []
    for ch in text:
        code = ord(ch)
        name = unicodedata.name(ch, 'UNKNOWN')
        category = unicodedata.category(ch)
        if category.startswith('C') or ch in invisible_patterns:
            stats[ch] = stats.get(ch, 0) + 1
            visualization.append(f"[U+{code:04X} {name}]")
        else:
            visualization.append(ch)
    return ''.join(visualization)

def remove_invisible_chars(text):
    cleaned = ''.join(
        ch for ch in text
        if unicodedata.category(ch) not in ('Cf', 'Cc', 'Cs', 'Co', 'Cn')
        or ch in '\n\r\t '
    )
    return re.sub(r'[\u200B-\u200F\uFEFF\u202F]', '', cleaned)

def process_text():
    raw_text = input_text.get("1.0", tk.END)
    stats = {}
    cleaned = remove_invisible_chars(raw_text)
    visualized = visualize_invisible_chars(raw_text, stats)

    output_cleaned.delete("1.0", tk.END)
    output_cleaned.insert(tk.END, cleaned.strip())

    output_visual.config(state="normal")
    output_visual.delete("1.0", tk.END)

    pattern = re.compile(r'\[U\+[0-9A-F]{4} [^\]]+\]')
    pos = 0
    for part in re.split(pattern, visualized):
        output_visual.insert(tk.END, part)
        match = pattern.search(visualized, pos)
        if match:
            output_visual.insert(tk.END, match.group(), "highlight")
            pos = match.end()

    output_visual.config(state="disabled")

    stats_lines = [f"{unicodedata.name(k, 'UNKNOWN')} (U+{ord(k):04X}): {v} pcs."
                   for k, v in stats.items()]
    stats_output.config(state="normal")
    stats_output.delete("1.0", tk.END)
    stats_output.insert(tk.END, "\n".join(stats_lines) if stats_lines else "No invisible characters found.")
    stats_output.config(state="disabled")

def save_to_file():
    text = output_cleaned.get("1.0", tk.END).strip()
    if not text:
        messagebox.showwarning("Save", "No text to save.")
        return
    file_path = filedialog.asksaveasfilename(defaultextension=".txt",
                                             filetypes=[("Text Files", "*.txt")],
                                             title="Save cleaned text")
    if file_path:
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(text)
        messagebox.showinfo("Saved", f"File saved: {file_path}")

def clear_all():
    input_text.delete("1.0", tk.END)
    output_cleaned.delete("1.0", tk.END)
    output_visual.config(state="normal")
    output_visual.delete("1.0", tk.END)
    output_visual.config(state="disabled")
    stats_output.config(state="normal")
    stats_output.delete("1.0", tk.END)
    stats_output.config(state="disabled")

def load_file(event=None):
    file_path = filedialog.askopenfilename(filetypes=[("Text files", "*.txt")])
    if file_path:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
            input_text.delete("1.0", tk.END)
            input_text.insert(tk.END, content)

def export_to_pdf():
    text = output_cleaned.get("1.0", tk.END).strip()
    stats = stats_output.get("1.0", tk.END).strip()

    if not text:
        messagebox.showwarning("Export to PDF", "No text to export.")
        return

    file_path = filedialog.asksaveasfilename(defaultextension=".pdf",
                                             filetypes=[("PDF files", "*.pdf")],
                                             title="Save as PDF")
    if not file_path:
        return

    c = canvas.Canvas(file_path, pagesize=A4)
    width, height = A4
    margin = 20 * mm
    max_width = width - 2 * margin
    y = height - margin
    line_height = 14

    c.setFont("Helvetica-Bold", 12)
    c.drawString(margin, y, "Cleaned Text")
    y -= 20

    c.setFont("Helvetica", 10)

    def draw_wrapped_text(content):
        nonlocal y
        for line in content.splitlines():
            wrapped = []
            while line:
                for i in range(len(line), 0, -1):
                    if c.stringWidth(line[:i]) <= max_width:
                        wrapped.append(line[:i])
                        line = line[i:]
                        break
                else:
                    wrapped.append(line)
                    break

            for wrap_line in wrapped:
                if y < margin + 50:
                    c.showPage()
                    c.setFont("Helvetica", 10)
                    y = height - margin
                c.drawString(margin, y, wrap_line)
                y -= line_height

    # Cleaned text
    draw_wrapped_text(text)

    # Space before stats
    y -= 20
    if y < margin + 50:
        c.showPage()
        c.setFont("Helvetica", 10)
        y = height - margin

    # Statistics
    if stats:
        c.setFont("Helvetica-Bold", 12)
        c.drawString(margin, y, "Removed Characters Statistics")
        y -= 20
        c.setFont("Helvetica", 10)
        draw_wrapped_text(stats)

    c.save()
    messagebox.showinfo("Done", f"PDF successfully saved: {file_path}")

# === GUI ===

root = tk.Tk()
root.title("Invisible Characters Remover")

# — Description —
description = (
    "🔍 This app removes invisible and control characters from text.\n"
    "It finds and deletes symbols like:\n"
    "– ZERO WIDTH SPACE (U+200B), BOM (U+FEFF), NARROW NO-BREAK SPACE (U+202F), etc.\n\n"
    "🛠 Features:\n"
    "– Clean text\n"
    "– Highlight removed characters\n"
    "– Statistics by character type\n"
    "– Save results\n"
    "– Drag-and-drop / load text files"
)
desc_label = tk.Label(root, text=description, justify="left", wraplength=700, fg="#333", bg="#f0f0f0", padx=10, pady=10, anchor="w")
desc_label.pack(fill="both", padx=10, pady=(10, 0))

# — Input text —
tk.Label(root, text="Paste text here (or drag-and-drop a .txt file):").pack(anchor="w", padx=10)
input_text = scrolledtext.ScrolledText(root, height=5)
input_text.pack(fill="both", padx=10, pady=5, expand=True)
input_text.bind("<Control-o>", load_file)
input_text.bind("<Button-3>", load_file)  # Right-click — open file

# — Buttons —
frame = tk.Frame(root)
frame.pack(pady=5)
tk.Button(frame, text="Clean Text", command=process_text).pack(side="left", padx=5)
tk.Button(frame, text="Save", command=save_to_file).pack(side="left", padx=5)
tk.Button(frame, text="Export to PDF", command=export_to_pdf).pack(side="left", padx=5)
tk.Button(frame, text="Clear All", command=clear_all).pack(side="left", padx=5)

# — Cleaned text output —
tk.Label(root, text="Cleaned Text:").pack(anchor="w", padx=10)
output_cleaned = scrolledtext.ScrolledText(root, height=4, bg="#e8ffe8")
output_cleaned.pack(fill="both", padx=10, pady=5, expand=True)

# — Visualization —
tk.Label(root, text="Visualization of removed characters:").pack(anchor="w", padx=10)
output_visual = scrolledtext.ScrolledText(root, height=6, bg="#fff3e6")
output_visual.tag_config("highlight", background="#ffcccc", foreground="black")
output_visual.config(state="disabled")
output_visual.pack(fill="both", padx=10, pady=5, expand=True)

# — Statistics —
tk.Label(root, text="Removed Characters Statistics:").pack(anchor="w", padx=10)
stats_output = scrolledtext.ScrolledText(root, height=4, bg="#f5f5f5")
stats_output.config(state="disabled")
stats_output.pack(fill="both", padx=10, pady=5, expand=True)

# — FAQ —
faq_text = (
    "🧪 How to use:\n\n"
    "🔽 Drag and drop a .txt file here or right-click → select file\n\n"
    "🧼 Press \"Clean Text\" — text will be cleaned, visualized, and counted\n\n"
    "💾 Press \"Save\" to export the result to a file\n\n"
    "🧹 \"Clear All\" resets the entire interface\n"
)
tk.Label(root, text="📖 FAQ / How to use:", font=("Segoe UI", 10, "bold")).pack(anchor="w", padx=10, pady=(10, 0))
faq_box = scrolledtext.ScrolledText(root, height=7, bg="#f0f8ff", fg="#333333", font=("Segoe UI", 10), wrap="word")
faq_box.insert(tk.END, faq_text)
faq_box.config(state="disabled")
faq_box.pack(fill="both", padx=10, pady=(0, 10), expand=False)

# — Run app —
root.mainloop()
