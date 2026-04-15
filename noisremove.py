import os
import numpy as np
import noisereduce as nr
from scipy.io import wavfile
import customtkinter as ctk
from tkinter import filedialog, messagebox

# -----------------------------
# Utility: Load WAV as mono float32
# -----------------------------
def load_wav_mono(path):
    rate, data = wavfile.read(path)

    if data.dtype != np.float32:
        data = data.astype(np.float32) / 32767

    if data.ndim > 1:
        data = np.mean(data, axis=1)

    return rate, data


# -----------------------------
# Normalization Methods
# -----------------------------
def normalize_peak(audio):
    peak = np.max(np.abs(audio))
    if peak == 0:
        return (audio * 32767).astype(np.int16)
    return (audio / peak * 32767).astype(np.int16)


def normalize_rms(audio, target_rms=0.1):
    rms = np.sqrt(np.mean(audio ** 2))
    if rms == 0:
        return (audio * 32767).astype(np.int16)

    scaled = audio * (target_rms / rms)
    scaled = np.clip(scaled, -1.0, 1.0)
    return (scaled * 32767).astype(np.int16)


NORMALIZERS = {
    "peak": normalize_peak,
    "rms": normalize_rms
}


# -----------------------------
# Noise Reduction
# -----------------------------
def reduce_noise(audio, rate, noise_sample=None):
    if noise_sample is not None:
        return nr.reduce_noise(y=audio, sr=rate, y_noise=noise_sample)
    return nr.reduce_noise(y=audio, sr=rate)


# -----------------------------
# Main Processing Function
# -----------------------------
def process_files(input_dir, output_dir, normalization="peak", noise_profile_path=""):
    os.makedirs(output_dir, exist_ok=True)
    log_items = []

    noise_sample = None
    if noise_profile_path:
        _, noise_sample = load_wav_mono(noise_profile_path)

    normalizer = NORMALIZERS.get(normalization, normalize_peak)

    for entry in os.scandir(input_dir):
        if not entry.name.lower().endswith(".wav"):
            continue

        rate, audio = load_wav_mono(entry.path)

        backup_path = os.path.join(output_dir, f"backup_{entry.name}")
        wavfile.write(backup_path, rate, (audio * 32767).astype(np.int16))

        cleaned = reduce_noise(audio, rate, noise_sample)
        final_audio = normalizer(cleaned)

        output_path = os.path.join(output_dir, entry.name)
        wavfile.write(output_path, rate, final_audio)

        log_items.append(
            f"✔ {entry.name} | {rate} Hz | Normalized: {normalization} | Backup saved"
        )

    show_log(log_items)
    messagebox.showinfo("Done", "🎉 All files processed successfully!")


# -----------------------------
# Log Window (CustomTkinter)
# -----------------------------
def show_log(log_items):
    win = ctk.CTkToplevel()
    win.title("Processing Log")
    win.geometry("700x400")

    textbox = ctk.CTkTextbox(win, width=680, height=360, corner_radius=10)
    textbox.pack(padx=10, pady=10, fill="both", expand=True)

    for line in log_items:
        textbox.insert("end", line + "\n")


# -----------------------------
# GUI Callbacks
# -----------------------------
def browse_input():
    input_dir.set(filedialog.askdirectory())

def browse_output():
    output_dir.set(filedialog.askdirectory())

def browse_noise_profile():
    noise_profile_path.set(
        filedialog.askopenfilename(filetypes=[("WAV files", "*.wav")])
    )

def run_processing():
    if not input_dir.get() or not output_dir.get():
        messagebox.showerror("Error", "Please select both input and output folders.")
        return

    process_files(
        input_dir.get(),
        output_dir.get(),
        normalization=normalization_method.get(),
        noise_profile_path=noise_profile_path.get()
    )


# -----------------------------
# CustomTkinter Modern UI
# -----------------------------
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("dark-blue")  # will override with lavender below

# Lavender accent override
LAVENDER = "#caa0ff"

root = ctk.CTk()
root.title("NoisRemover")
root.geometry("600x350")

# Variables
input_dir = ctk.StringVar()
output_dir = ctk.StringVar()
noise_profile_path = ctk.StringVar()
normalization_method = ctk.StringVar(value="peak")

# Layout Frame
frame = ctk.CTkFrame(root, corner_radius=15)
frame.pack(padx=20, pady=20, fill="both", expand=True)

# Widgets
def add_label(text, row):
    lbl = ctk.CTkLabel(frame, text=text, text_color=LAVENDER)
    lbl.grid(row=row, column=0, padx=10, pady=10, sticky="w")

def add_entry(var, row):
    entry = ctk.CTkEntry(frame, textvariable=var, width=300)
    entry.grid(row=row, column=1, padx=10, pady=10)

def add_button(text, cmd, row, col):
    btn = ctk.CTkButton(frame, text=text, command=cmd, fg_color=LAVENDER, text_color="black")
    btn.grid(row=row, column=col, padx=10, pady=10)

# Input Folder
add_label("Input Folder", 0)
add_entry(input_dir, 0)
add_button("Browse", browse_input, 0, 2)

# Output Folder
add_label("Output Folder", 1)
add_entry(output_dir, 1)
add_button("Browse", browse_output, 1, 2)

# Normalization
add_label("Normalization", 2)
opt = ctk.CTkOptionMenu(frame, variable=normalization_method, values=["peak", "rms"],
                        fg_color="#1f1f1f", button_color=LAVENDER, button_hover_color="#d8b8ff")
opt.grid(row=2, column=1, padx=10, pady=10)

# Noise Profile
add_label("Custom Noise Profile", 3)
add_entry(noise_profile_path, 3)
add_button("Browse", browse_noise_profile, 3, 2)

# Start Button
start_btn = ctk.CTkButton(
    frame, text="Start Processing", command=run_processing,
    fg_color=LAVENDER, text_color="black", height=40, corner_radius=12
)
start_btn.grid(row=4, column=1, pady=20)

root.mainloop()
