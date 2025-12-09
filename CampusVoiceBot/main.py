import tkinter as tk
import pyttsx3
import speech_recognition as sr
import mysql.connector
import cv2
from PIL import Image, ImageTk, ImageSequence

# Initialize Text-to-Speech Engine
engine = pyttsx3.init()

# Tkinter Window setup
root = tk.Tk()
root.title("Campus Voice Assistant")
root.geometry("700x600")

# Theme state and palettes
IS_DARK = False
LIGHT_THEME = {
    "root_bg": "#ececec",
    "content_bg": "white",
    "text_fg": "#333333",
    "button_bg": "#4CAF50",
    "button_active": "#45a049",
    "button_fg": "white",
    "video_bg": "white",
    "frame_bd": "solid",
}
DARK_THEME = {
    "root_bg": "#212121",
    "content_bg": "#303030",
    "text_fg": "#E0E0E0",
    "button_bg": "#66BB6A",
    "button_active": "#81C784",
    "button_fg": "white",
    "video_bg": "#303030",
    "frame_bd": "solid",
}

def apply_theme():
    theme = DARK_THEME if IS_DARK else LIGHT_THEME
    root.config(bg=theme["root_bg"])
    try:
        background_label.config(bg=theme["root_bg"])
    except Exception:
        pass
    content_frame.config(bg=theme["content_bg"])
    label_text.config(bg=theme["content_bg"], fg=theme["text_fg"])
    label_video.config(bg=theme["video_bg"])
    # Update Ask Me button colors
    button.config(bg=theme["button_bg"], fg=theme["button_fg"], activebackground=theme["button_active"])
    # Update Toggle button colors
    toggle_btn.config(bg=theme["button_bg"], fg=theme["button_fg"], activebackground=theme["button_active"])
    # Update any animated GIF label background if exists
    try:
        if hasattr(animator, "label") and animator.label:
            animator.label.config(bg=theme["content_bg"])
    except Exception:
        pass

def toggle_theme():
    global IS_DARK
    IS_DARK = not IS_DARK
    apply_theme()

# Background Image (Optional, you can remove if not needed)
try:
    bg_image = tk.PhotoImage(file="background_image.png")
    background_label = tk.Label(root, image=bg_image)
    background_label.place(relwidth=1, relheight=1)
except Exception:
    background_label = tk.Label(root, bg=LIGHT_THEME["root_bg"])
    background_label.place(relwidth=1, relheight=1)

# Frame for content
content_frame = tk.Frame(root, bg="white", bd=10, relief="solid", padx=20, pady=20)
content_frame.place(relx=0.5, rely=0.5, anchor="center", relwidth=0.9, relheight=0.7)

# Welcoming text
label_text = tk.Label(content_frame, text="Loading...", font=("Helvetica", 16, "bold"), fg="#333", bg="white")
label_text.pack(pady=10)

# Create a Text-to-Speech function
def speak(text):
    engine.say(text)
    engine.runAndWait()

# Function to recognize speech input
def listen():
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        print("Listening...")
        try:
            audio = recognizer.listen(source, timeout=5)
            command = recognizer.recognize_google(audio)
            print(f"You said: {command}")
            label_text.config(text=f"You said: {command}")
            return command.lower()
        except sr.UnknownValueError:
            speak("Sorry, I didn't understand that.")
            label_text.config(text="Sorry, I didn't understand that.")
            return None
        except sr.WaitTimeoutError:
            speak("No input detected.")
            label_text.config(text="No input detected.")
            return None

# Fetch answer from the database
def fetch_answer(question):
    try:
        connection = mysql.connector.connect(
            host="localhost",
            user="root",
            password="",
            database="campus_bot"
        )
        cursor = connection.cursor()
        query = "SELECT answer FROM faq WHERE question LIKE %s"
        cursor.execute(query, (f"%{question}%",))
        result = cursor.fetchone()
        connection.close()
        return result[0] if result else "Sorry, I don't have an answer for that."
    except mysql.connector.Error as err:
        return f"Database error: {err}"

# Function to interact with voice commands
def process_voice_command():
    query = listen()
    if query:
        if "thanks" in query or "exit" in query:
            speak("Goodbye! See you soon!")
            label_text.config(text="Goodbye! See you soon!")
            root.quit()
        else:
            answer = fetch_answer(query)
            speak(answer)
            label_text.config(text=f"Answer: {answer}")
            play_video("robot_video.mp4")  # Play video when an answer is given

# Create a button to start the voice command process
def on_enter(e):
    theme = DARK_THEME if IS_DARK else LIGHT_THEME
    button.config(bg=theme["button_active"])

def on_leave(e):
    theme = DARK_THEME if IS_DARK else LIGHT_THEME
    button.config(bg=theme["button_bg"])

button = tk.Button(content_frame, text="Ask Me", font=("Helvetica", 14, "bold"),
                   bg=LIGHT_THEME["button_bg"], fg=LIGHT_THEME["button_fg"],
                   relief="raised", bd=5, command=process_voice_command)
button.pack(pady=20)
button.bind("<Enter>", on_enter)
button.bind("<Leave>", on_leave)

# Toggle Theme button (placed next to Ask Me)
toggle_frame = tk.Frame(content_frame, bg="white")
toggle_frame.pack(pady=5)
toggle_btn = tk.Button(toggle_frame, text="Toggle Theme", font=("Helvetica", 12, "bold"),
                       bg=LIGHT_THEME["button_bg"], fg=LIGHT_THEME["button_fg"],
                       relief="raised", bd=4, command=toggle_theme)
toggle_btn.pack(side="left", padx=8)

# Play video function
def play_video(video_path):
    # OpenCV to play video
    cap = cv2.VideoCapture(video_path)
    while(cap.isOpened()):
        ret, frame = cap.read()
        if not ret:
            break

        # Resize the video to fit the screen (adjust to fit the Tkinter window size)
        frame = cv2.resize(frame, (root.winfo_width(), root.winfo_height()))
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        # Convert the frame into an image for tkinter
        frame_image = Image.fromarray(frame)
        frame_image = ImageTk.PhotoImage(frame_image)
        
        # Display the video frame on the Tkinter window
        label_video.config(image=frame_image)
        label_video.image = frame_image
        
        root.update()

    cap.release()

# Create a label to display the video frame
label_video = tk.Label(content_frame, bg="white")
label_video.pack(pady=10)

# Animated GIF helper to replace static robot image
class AnimatedGIFLabel:
    def __init__(self, parent, gif_path):
        self.parent = parent
        self.gif_path = gif_path
        self.frames = []
        self.frame_index = 0
        self.label = tk.Label(parent, bg="white")
        self.label.pack(pady=20)
        self._load_frames()

    def _load_frames(self):
        try:
            gif = Image.open(self.gif_path)
            for frame in ImageSequence.Iterator(gif):
                # Convert each frame to RGBA and then to PhotoImage
                frame_rgba = frame.convert("RGBA")
                photo = ImageTk.PhotoImage(frame_rgba)
                self.frames.append(photo)
        except Exception as e:
            # If GIF fails to load, keep frames empty and optionally log
            print(f"Failed to load GIF: {e}")
            self.frames = []

    def _animate(self):
        if not self.frames:
            return
        frame = self.frames[self.frame_index]
        self.label.config(image=frame)
        # keep reference to avoid garbage collection
        self.label.image = frame
        self.frame_index = (self.frame_index + 1) % len(self.frames)
        # schedule next frame
        self.label.after(100, self._animate)

    def start(self):
        if self.frames:
            self._animate()

# Function to show robot face and greeting message after loading
def initial_greeting():
    speak("Hello! I am your campus assistant. Ask me anything!")
    label_text.config(text="Hello! I am your campus assistant. Ask me anything!")
    
    # Replace static robot image with animated GIF
    # This will create an AnimatedGIFLabel that packs itself into the content_frame
    global animator
    animator = AnimatedGIFLabel(content_frame, "robot_face.gif")
    animator.start()
    # Ensure animator label follows current theme
    apply_theme()

# Apply initial theme settings
apply_theme()

# Call the initial greeting function after a brief delay
root.after(2000, initial_greeting)  # Delay of 2 seconds before showing greeting and face

# Start the Tkinter event loop
root.mainloop()