import os
import numpy as np
import noisereduce as nr
from scipy.io import wavfile
import tkinter as tk
from tkinter import filedialog, messagebox

# --- Normalization Methods ---
def normalize_peak(audio_data):
    max_val = np.max(np.abs(audio_data))
    if max_val == 0:
        return audio_data
    normalized = audio_data / max_val
    return (normalized * 32767).astype(np.int16)

def normalize_rms(audio_data, target_rms=0.1):
    rms = np.sqrt(np.mean(audio_data**2))
    if rms == 0:
        return audio_data
    normalized = audio_data * (target_rms / rms)
    normalized = np.clip(normalized, -1.0, 1.0)
    return (normalized * 32767).astype(np.int16)

# --- Noise Reduction with Optional Custom Profile ---
def apply_custom_noise_profile(data, sample_noise, rate):
    return nr.reduce_noise(y=data, sr=rate, y_noise=sample_noise)

# --- Processing Function ---
def process_files(input_dir, output_dir, normalization="peak", noise_profile_path=""):
    os.makedirs(output_dir, exist_ok=True)
    log_items = []

    # Load custom noise profile if provided
    if noise_profile_path:
        noise_rate, noise_sample = wavfile.read(noise_profile_path)
        noise_sample = noise_sample.astype(np.float32) / 32767
    else:
        noise_sample = None

    for filename in os.listdir(input_dir):
        if filename.endswith(".wav"):
            file_path = os.path.join(input_dir, filename)
            rate, data = wavfile.read(file_path)

            # Backup original
            backup_path = os.path.join(output_dir, f"backup_{filename}")
            wavfile.write(backup_path, rate, data.astype(np.int16))

            # Mono + float32
            if len(data.shape) > 1:
                data = np.mean(data, axis=1)
            data = data.astype(np.float32) / 32767

            # Noise reduction
            if noise_sample is not None:
                reduced_noise = apply_custom_noise_profile(data, noise_sample, rate)
            else:
                reduced_noise = nr.reduce_noise(y=data, sr=rate)

            # Normalization
            if normalization == "rms":
                final_audio = normalize_rms(reduced_noise)
            else:
                final_audio = normalize_peak(reduced_noise)

            output_path = os.path.join(output_dir, filename)
            wavfile.write(output_path, rate, final_audio)

            log_items.append(f"✅ {filename} | Rate: {rate} Hz | Normalized: {normalization} | Backup saved")

    show_log(log_items)
    messagebox.showinfo("Done", "🎉 All files processed successfully!")

# --- Log Window ---
def show_log(log_items):
    log_window = tk.Toplevel()
    log_window.title("Processing Log")
    text = tk.Text(log_window, wrap="word", width=80, height=20)
    text.pack()
    for line in log_items:
        text.insert(tk.END, line + "\n")

# --- Folder & File Browsing ---
def browse_input():
    input_dir.set(filedialog.askdirectory())

def browse_output():
    output_dir.set(filedialog.askdirectory())

def browse_noise_profile():
    noise_profile_path.set(filedialog.askopenfilename(filetypes=[("WAV files", "*.wav")]))

# --- Run Processing ---
def run_processing():
    if not input_dir.get() or not output_dir.get():
        messagebox.showerror("Error", "Please select both input and output folders.")
        return
    process_files(input_dir.get(), output_dir.get(), normalization=normalization_method.get(), noise_profile_path=noise_profile_path.get())

# --- GUI Setup ---
root = tk.Tk()
root.title("NoisRemover")

input_dir = tk.StringVar()
output_dir = tk.StringVar()
noise_profile_path = tk.StringVar()
normalization_method = tk.StringVar(value="peak")

tk.Label(root, text="Input Folder").grid(row=0, column=0, padx=5, pady=5)
tk.Entry(root, textvariable=input_dir, width=40).grid(row=0, column=1)
tk.Button(root, text="Browse", command=browse_input).grid(row=0, column=2)

tk.Label(root, text="Output Folder").grid(row=1, column=0, padx=5, pady=5)
tk.Entry(root, textvariable=output_dir, width=40).grid(row=1, column=1)
tk.Button(root, text="Browse", command=browse_output).grid(row=1, column=2)

tk.Label(root, text="Normalization").grid(row=2, column=0, padx=5, pady=5)
tk.OptionMenu(root, normalization_method, "peak", "rms").grid(row=2, column=1)

tk.Label(root, text="Custom Noise Profile").grid(row=3, column=0, padx=5, pady=5)
tk.Entry(root, textvariable=noise_profile_path, width=40).grid(row=3, column=1)
tk.Button(root, text="Browse", command=browse_noise_profile).grid(row=3, column=2)

tk.Button(root, text="Start Processing", command=run_processing, bg="green", fg="white").grid(row=4, column=1, pady=20)

root.mainloop()
