import tkinter as tk
import random
from PIL import Image, ImageTk
import io
import base64

# Main window setup must come first to ensure a valid Tkinter root
root = tk.Tk()
root.title("The Grand Mystic Fortune Teller 🔮")
root.geometry("500x400")
root.configure(bg="black")

# Function to create colored image placeholders instead of using invalid base64 strings
def create_placeholder_image(color, width=100, height=150):
    image = Image.new('RGB', (width, height), color=color)
    return ImageTk.PhotoImage(image)

# Create colored placeholder images
card_front_img = create_placeholder_image((70, 30, 100))  # Purple for front
card_back_img = create_placeholder_image((20, 20, 50))    # Dark blue for back

# Fortunes to choose from - philosophical, Lacanian style
fortunes = [
    "🌑 The symbolic order through which you perceive reality is about to shift fundamentally.",
    "🪞 Your mirror stage is complete; now confront the Real that lies beyond language.",
    "⛓️ The chains of desire that bind you are of your own making—recognize the lack driving you.",
    "🧩 The fragments of your identity seek coherence—understand that wholeness is an illusion.",
    "🔍 What you seek is precisely what creates the void you're trying to fill.",
    "🌌 That which you most fear to lose is already not yours.",
    "📜 The narrative you tell yourself obscures the truth of your desire.",
    "⏳ Time reveals itself not as linear progression but as repetition of structure.",
    "🕸️ You are caught in a web of signifiers that precedes and exceeds you.",
    "🎭 The persona you present is neither authentic nor false—it is the necessary fiction.",
    "🧠 The unconscious is structured like a language you cannot help but speak.",
    "🚪 The obstacle you perceive is actually the path itself.",
    "🧿 What appears as chance is the manifestation of your deepest determination.",
    "🔮 Your symptom is the truth of your being—embrace it rather than seek its cure.",
    "🗝️ The answer you seek exists in the space between what can and cannot be said.",
    "📱 The distance between you and your digital avatar grows smaller as your alienation increases.",
    "🌊 The Real erupts at precisely the moment you believe you've contained it.",
    "⚡ Your jouissance reveals itself in what you claim to hate most fervently.",
    "🌓 The missing half you seek has never existed—desire sustains itself through its own lack.",
    "🧭 You navigate by stars that were extinguished eons ago.",
    "🎲 The illusion of choice masks the determination of your unconscious.",
    "🏺 You are the vessel for desires that preceded your birth.",
    "🥀 The beauty you pursue is inseparable from its inevitable decay.",
    "🔄 The cycle you're trying to break is precisely what constitutes your identity.",
    "🖼️ The frame through which you view the world is invisible to you until now."
]

# Animation settings
flip_steps = 10
flip_delay = 30
card_width = 100
animation_in_progress = False

# Forward declaration of animate_unflip
def animate_unflip(step=0):
    pass

# Flip animation
def animate_flip(step=0):
    global animation_in_progress
    if step < flip_steps:
        scale = 1.0 - (step / flip_steps)
        scaled_width = int(card_width * scale)
        card_label.place(relx=0.5, rely=0.4, anchor='center', width=scaled_width)
        card_label.config(highlightthickness=2, highlightbackground="gold")
        root.after(flip_delay, lambda: animate_flip(step + 1))
    elif step == flip_steps:
        card_label.config(image=card_front_img)
        animate_unflip()

# Actual implementation of animate_unflip
def animate_unflip(step=0):
    global animation_in_progress
    if step < flip_steps:
        scale = (step + 1) / flip_steps
        scaled_width = int(card_width * scale)
        card_label.place(relx=0.5, rely=0.4, anchor='center', width=scaled_width)
        root.after(flip_delay, lambda: animate_unflip(step + 1))
    else:
        card_label.config(highlightthickness=0)
        result_label.config(text=random.choice(fortunes), fg="gold")
        fortune_btn.config(state="normal")
        animation_in_progress = False

# Trigger animation
def reveal_fortune():
    global animation_in_progress
    if animation_in_progress:
        return
    animation_in_progress = True
    fortune_btn.config(state="disabled")
    card_label.config(image=card_back_img)
    card_label.place(relx=0.5, rely=0.4, anchor='center', width=card_width)
    result_label.config(text="Shuffling the stars... 🔮", fg="white")
    root.after(500, lambda: animate_flip())

# UI Elements
title_label = tk.Label(root, text="✨ Ask the Fortune Teller ✨", font=("Papyrus", 18, "bold"), bg="black", fg="violet")
title_label.pack(pady=10)

card_label = tk.Label(root, image=card_back_img, bg="black", highlightthickness=0)
card_label.place(relx=0.5, rely=0.4, anchor='center', width=card_width)

fortune_btn = tk.Button(root, text="Reveal My Fortune", font=("Courier", 14, "bold"), bg="darkmagenta", fg="white", command=reveal_fortune)
fortune_btn.pack(pady=10)

result_label = tk.Label(root, text="", font=("Georgia", 14, "italic"), bg="black", fg="gold", wraplength=400, justify="center")
result_label.pack(pady=10)

root.mainloop()
