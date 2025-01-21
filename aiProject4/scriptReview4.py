import tkinter as tk
from openai import OpenAI  # Using the new library approach
import requests
import io
from PIL import Image, ImageTk

# ----------------------------------------------------------
# 1. Hardcode your OpenAI API Key
#    (Keep in mind this is not recommended for production
#     or public repos—use environment variables instead.)
# ----------------------------------------------------------
api_key = "OPENAIKEY"
client = OpenAI(api_key=api_key)

# ----------------------------------------------------------
# GUI Setup
# ----------------------------------------------------------
root = tk.Tk()
root.title("Movie Script Commentary & Set Design Generator")
# Enough space to show 512x512 images plus some UI
root.geometry("900x800")

# Create frames for layout
main_frame = tk.Frame(root)
main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

# Script Section (Left side)
script_label = tk.Label(main_frame, text="Paste Your Movie Script Here:")
script_label.pack(anchor="nw")
script_textbox = tk.Text(main_frame, wrap=tk.WORD, width=50, height=20)
script_textbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

# Commentary Section (Right side)
commentary_label = tk.Label(main_frame, text="AI Commentary:")
commentary_label.pack(anchor="ne")
commentary_textbox = tk.Text(
    main_frame, wrap=tk.WORD, width=50, height=20,
    fg="#FF1493", bg="black", state=tk.DISABLED
)
commentary_textbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

# Frame for buttons
button_frame = tk.Frame(root)
button_frame.pack(pady=5)

# Loading indicator label
loading_label = tk.Label(root, text="", fg="red")
loading_label.pack()

# Frame for image navigation
nav_frame = tk.Frame(root)
nav_frame.pack(pady=10)

image_label = tk.Label(nav_frame, bg="grey")
image_label.pack(side=tk.LEFT)

prev_button = tk.Button(nav_frame, text="⟨ Previous")
prev_button.pack(side=tk.LEFT, padx=10)

next_button = tk.Button(nav_frame, text="Next ⟩")
next_button.pack(side=tk.LEFT, padx=10)

# ----------------------------------------------------------
# Global Variables
# ----------------------------------------------------------
current_image_index = 0
generated_images = []

# ----------------------------------------------------------
# Functions
# ----------------------------------------------------------
def get_commentary():
    """
    Get the movie script from the script Text widget, send it to OpenAI,
    and display the commentary in the commentary Text widget.
    Logs any errors or messages in the terminal.
    """
    # Grab the user's script
    script_text = script_textbox.get("1.0", tk.END).strip()
    
    if not script_text:
        print("[INFO] No script text found. Prompting user to enter a movie script.")
        commentary_textbox.config(state=tk.NORMAL)
        commentary_textbox.delete("1.0", tk.END)
        commentary_textbox.insert(tk.END, "Please enter a movie script first.")
        commentary_textbox.config(state=tk.DISABLED)
        return
    
    print("[INFO] Sending request to OpenAI for commentary...")
    loading_label.config(text="Loading commentary, please wait...")
    root.update_idletasks()  # Force update of the label on-screen
    
    # Clear the commentary box
    commentary_textbox.config(state=tk.NORMAL)
    commentary_textbox.delete("1.0", tk.END)
    commentary_textbox.insert(tk.END, "Fetching commentary...")
    commentary_textbox.config(state=tk.DISABLED)
    
    try:
        # Build the prompt
        prompt = (
            "You are a helpful assistant specialized in analyzing movie scripts. "
            "Given the following movie script:\n\n"
            f"{script_text}\n\n"
            "Provide commentary on the script that includes:\n"
            "- The specific feel of the scene\n"
            "- The colors associated with it\n"
            "- Suggestions for how to act\n"
            "- Which specific emotions to capture\n"
        )
        
        print(f"[DEBUG] Prompt for commentary:\n{prompt}\n")

        # Call OpenAI's chat API
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",  # or "gpt-4" if you have access
            messages=[
                {"role": "system", "content": "You are an expert in film analysis."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=1000
        )
        
        # Extract commentary
        commentary = response.choices[0].message.content.strip()
        
        print("[INFO] Commentary successfully received from OpenAI.")
        
        # Display commentary in the box
        commentary_textbox.config(state=tk.NORMAL)
        commentary_textbox.delete("1.0", tk.END)
        commentary_textbox.insert(tk.END, commentary)
        commentary_textbox.config(state=tk.DISABLED)
        
    except Exception as e:
        # Print error to terminal
        print("[ERROR] An error occurred while generating commentary:", e)
        
        # Display error in GUI
        commentary_textbox.config(state=tk.NORMAL)
        commentary_textbox.delete("1.0", tk.END)
        commentary_textbox.insert(
            tk.END, 
            f"An error occurred while generating commentary:\n\n{e}"
        )
        commentary_textbox.config(state=tk.DISABLED)
    
    finally:
        loading_label.config(text="")

def clear_commentary():
    """
    Clear the commentary text box.
    """
    commentary_textbox.config(state=tk.NORMAL)
    commentary_textbox.delete("1.0", tk.END)
    commentary_textbox.config(state=tk.DISABLED)

def show_image(index):
    """
    Display the smaller (resized) image from generated_images at the given index.
    """
    if not generated_images:
        return
    index = max(0, min(index, len(generated_images) - 1))
    image_label.config(image=generated_images[index])
    # Keep a reference to avoid garbage collection
    image_label.image = generated_images[index]

def show_previous_image():
    global current_image_index
    if generated_images:
        current_image_index -= 1
        if current_image_index < 0:
            current_image_index = 0
        show_image(current_image_index)

def show_next_image():
    global current_image_index
    if generated_images:
        current_image_index += 1
        if current_image_index >= len(generated_images):
            current_image_index = len(generated_images) - 1
        show_image(current_image_index)

def generate_images():
    """
    Generate 3 AI-created still images representing the beginning,
    middle, and end of the movie script. Each image is generated
    at 1024x1024, then resized to 512x512 for displaying.
    """
    global generated_images, current_image_index
    generated_images = []
    current_image_index = 0
    
    script_text = script_textbox.get("1.0", tk.END).strip()
    if not script_text:
        print("[INFO] No script text for images. Prompting user to enter a movie script.")
        commentary_textbox.config(state=tk.NORMAL)
        commentary_textbox.delete("1.0", tk.END)
        commentary_textbox.insert(tk.END, "Please enter a movie script first.")
        commentary_textbox.config(state=tk.DISABLED)
        return
    
    print("[INFO] Sending request to OpenAI for image generation...")
    loading_label.config(text="Generating images, please wait...")
    root.update_idletasks()
    
    try:
        # Shorten (or summarize) the script to avoid prompt length issues
        shortened_script = script_text[:500] + "..." if len(script_text) > 500 else script_text

        # We'll define 3 segments: beginning, middle, end
        segments = ["beginning", "middle", "end"]

        for i, segment in enumerate(segments):
            # Create a unique prompt for each stage
            image_prompt = (
                f"Create a photo-like still image that represents the {segment} of this movie script. "
                "Focus on capturing a cinematic moment with relevant characters, setting, and mood. "
                f"The script:\n\n{shortened_script}\n\n"
                "Generate a visually striking scene that embodies the key elements at this stage of the story."
            )

            # Debug info
            print(f"\n[DEBUG] Prompt for the {segment} (Image {i+1}):\n{image_prompt}\n")
            print(f"[DEBUG] Prompt length: {len(image_prompt)} characters")

            # Call DALL·E 3 (n=1 each time)
            response = client.images.generate(
                model="dall-e-3",
                prompt=image_prompt,
                size="1024x1024",  # Must be 1024x1024 for DALL-E 3
                quality="standard",
                n=1
            )
            url = response.data[0].url
            print(f"[INFO] {segment.capitalize()} Image URL: {url}")
            
            # Fetch the image bytes via a GET request
            img_response = requests.get(url)
            pil_image = Image.open(io.BytesIO(img_response.content))
            
            # Resize the image for display (1024 -> 512)
            resized_pil = pil_image.resize((512, 512), Image.Resampling.LANCZOS)
            tk_image = ImageTk.PhotoImage(resized_pil)
            generated_images.append(tk_image)
        
        if generated_images:
            print("[INFO] All images have been downloaded and resized.")
            show_image(current_image_index)
        
    except Exception as e:
        print("[ERROR] An error occurred while generating images:", e)
        
        commentary_textbox.config(state=tk.NORMAL)
        commentary_textbox.delete("1.0", tk.END)
        commentary_textbox.insert(
            tk.END, 
            f"An error occurred while generating images:\n\n{e}"
        )
        commentary_textbox.config(state=tk.DISABLED)
    finally:
        loading_label.config(text="")

# ----------------------------------------------------------
# Button Configurations
# ----------------------------------------------------------
submit_button = tk.Button(button_frame, text="Get Commentary", command=get_commentary)
submit_button.pack(side=tk.LEFT, padx=5)

clear_button = tk.Button(button_frame, text="Clear Commentary", command=clear_commentary)
clear_button.pack(side=tk.LEFT, padx=5)

images_button = tk.Button(button_frame, text="Generate Images", command=generate_images)
images_button.pack(side=tk.LEFT, padx=5)

prev_button.config(command=show_previous_image)
next_button.config(command=show_next_image)

# ----------------------------------------------------------
# Start the GUI event loop
# ----------------------------------------------------------
root.mainloop()
