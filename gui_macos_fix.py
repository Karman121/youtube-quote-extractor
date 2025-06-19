"""
YouTube Quote Extractor - GUI for macOS (Visibility Fix)
A reliable GUI with forced light-mode and explicit, high-contrast styling 
to ensure perfect visibility on macOS.
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog
import threading
import sys

# Import our core functionality
from main import (
    process_youtube_url_only,
    process_timestamps,
    validate_url,
    validate_timestamps_format
)
from transcript_utils import parse_input
from config import DEFAULT_SETTINGS

class YouTubeExtractorGUI:
    def __init__(self):
        self.root = tk.Tk()

        # === MACOS COMPATIBILITY ===
        # Force window to front and ensure proper rendering
        if sys.platform == "darwin":
            self.root.lift()
            self.root.attributes('-topmost', True)
            self.root.after_idle(self.root.attributes, '-topmost', False)

        self.root.title("YouTube Quote Extractor")
        
        # Define a high-contrast, visible-everywhere color scheme
        self.theme = {
            "bg": "#F7F7F7",
            "fg": "#1F1F1F",
            "entry_bg": "#FFFFFF",
            "entry_fg": "#000000",
            "button_bg": "#E1E1E1",
            "button_fg": "#000000",
            "accent": "#007AFF", # A standard Apple blue
            "border": "#C1C1C1",
        }
        
        self.root.geometry("1000x850")
        self.root.configure(bg=self.theme["bg"])
        
        # State variables
        self.is_processing = False
        self.current_transcript = ""
        self.current_video_title = ""
        self.current_quotes = []
        self.processing_mode = tk.StringVar(value="both")
        self.context_before = tk.IntVar(value=DEFAULT_SETTINGS["default_context_before_seconds"])
        self.context_after = tk.IntVar(value=DEFAULT_SETTINGS["default_context_after_seconds"])
        self.status_var = tk.StringVar(value="Ready")
        
        self.create_widgets()
        
    def create_widgets(self):
        """Create all GUI widgets with explicit styling to guarantee visibility."""
        
        # Main container frame
        main_frame = tk.Frame(self.root, bg=self.theme["bg"])
        main_frame.pack(fill=tk.BOTH, expand=True, padx=25, pady=15)

        # 1. Title
        tk.Label(
            main_frame, 
            text="YouTube Quote Extractor", 
            font=("Helvetica Neue", 22, "bold"),
            bg=self.theme["bg"],
            fg=self.theme["fg"]
        ).pack(pady=(5, 20))
        
        # 2. URL Input
        url_frame = self.create_styled_labelframe(main_frame, "1. Enter YouTube URL")
        self.url_entry = self.create_styled_entry(url_frame)
        
        # 3. Processing Mode
        mode_frame = self.create_styled_labelframe(main_frame, "2. Select Mode")
        self.create_styled_radiobutton(mode_frame, "Generate Transcript Only", "transcript")
        self.create_styled_radiobutton(mode_frame, "Generate Transcript + Extract Quotes", "both")
        
        # 4. Frame for Toggling Quote-related settings
        self.quote_settings_frame = tk.Frame(main_frame, bg=self.theme["bg"])
        self.quote_settings_frame.pack(fill=tk.BOTH, expand=True, pady=5)

        # 5. Context Settings
        context_frame = self.create_styled_labelframe(self.quote_settings_frame, "3. Set Quote Context (Optional)")
        context_inner = tk.Frame(context_frame, bg=self.theme["bg"])
        context_inner.pack(pady=5)
        
        tk.Label(context_inner, text="Before:", font=("Helvetica Neue", 12), bg=self.theme["bg"]).grid(row=0, column=0, padx=10, pady=5)
        self.create_styled_spinbox(context_inner, from_=0, to=300, textvariable=self.context_before).grid(row=0, column=1, padx=10, pady=5)
        
        tk.Label(context_inner, text="After:", font=("Helvetica Neue", 12), bg=self.theme["bg"]).grid(row=0, column=2, padx=20, pady=5)
        self.create_styled_spinbox(context_inner, from_=0, to=600, textvariable=self.context_after).grid(row=0, column=3, padx=10, pady=5)
        
        # 6. Timestamps Input
        timestamps_frame = self.create_styled_labelframe(self.quote_settings_frame, "4. Enter Timestamps")
        tk.Label(timestamps_frame, text="Enter timestamps (e.g., MM:SS or HH:MM:SS) one per line.", font=("Helvetica Neue", 10), bg=self.theme["bg"], fg='gray').pack(anchor=tk.W, padx=5, pady=(0,5))
        self.timestamps_text = self.create_styled_scrolledtext(timestamps_frame)
        
        # 7. Control Buttons
        btn_frame = tk.Frame(main_frame, bg=self.theme["bg"])
        btn_frame.pack(fill=tk.X, pady=(20, 10))
        
        self.process_btn = self.create_styled_button(btn_frame, "🚀 Start Processing", self.start_processing, bg=self.theme["accent"])
        self.process_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        self.stop_btn = self.create_styled_button(btn_frame, "⏹ Stop", self.stop_processing, bg="#D32F2F", state=tk.DISABLED)
        self.stop_btn.pack(side=tk.LEFT, padx=10)
        
        self.create_styled_button(btn_frame, "🗑 Clear All", self.clear_all, bg="#F57C00").pack(side=tk.LEFT, padx=10)
        self.create_styled_button(btn_frame, "📝 View Results", self.show_results, bg="#757575").pack(side=tk.LEFT, padx=10)
        
        # 8. Status Bar
        status_frame = tk.Frame(self.root, bg='#E0E0E0')
        status_frame.pack(fill=tk.X, side=tk.BOTTOM, ipady=3)
        tk.Label(status_frame, textvariable=self.status_var, font=("Helvetica Neue", 10), bg='#E0E0E0', fg='#333').pack(side=tk.LEFT, padx=10)
        
        self.toggle_quote_settings() # Initial setup

    # --- Helper methods for creating styled widgets ---
    def create_styled_labelframe(self, parent, text):
        frame = tk.LabelFrame(parent, text=text, font=("Helvetica Neue", 13, "bold"), bg=self.theme["bg"], fg=self.theme["fg"], padx=15, pady=10, relief=tk.GROOVE, borderwidth=1)
        frame.pack(fill=tk.X, pady=8)
        return frame

    def create_styled_entry(self, parent):
        entry = tk.Entry(parent, font=("Menlo", 12), bg=self.theme["entry_bg"], fg=self.theme["entry_fg"], insertbackground=self.theme["entry_fg"], relief=tk.SOLID, borderwidth=1, highlightthickness=1, highlightcolor=self.theme["accent"], highlightbackground=self.theme["border"])
        entry.pack(padx=5, pady=5, fill=tk.X)
        return entry

    def create_styled_radiobutton(self, parent, text, value):
        rb = tk.Radiobutton(parent, text=text, variable=self.processing_mode, value=value, font=("Helvetica Neue", 12), bg=self.theme["bg"], fg=self.theme["fg"], command=self.toggle_quote_settings, activebackground=self.theme["bg"], activeforeground=self.theme["fg"], selectcolor=self.theme["entry_bg"], highlightthickness=0)
        rb.pack(anchor=tk.W, padx=5, pady=2)
        return rb

    def create_styled_spinbox(self, parent, from_, to, textvariable):
        return tk.Spinbox(parent, from_=from_, to=to, textvariable=textvariable, width=8, font=("Helvetica Neue", 12), bg=self.theme["entry_bg"], fg=self.theme["entry_fg"], relief=tk.SOLID, borderwidth=1, buttonbackground=self.theme["button_bg"])

    def create_styled_scrolledtext(self, parent):
        st = scrolledtext.ScrolledText(parent, height=6, font=("Menlo", 11), wrap=tk.WORD, bg=self.theme["entry_bg"], fg=self.theme["entry_fg"], insertbackground=self.theme["entry_fg"], relief=tk.SOLID, borderwidth=1, highlightthickness=1, highlightcolor=self.theme["accent"], highlightbackground=self.theme["border"])
        st.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        return st

    def create_styled_button(self, parent, text, command, bg, state=tk.NORMAL):
        return tk.Button(parent, text=text, command=command, font=("Helvetica Neue", 12, "bold"), bg=bg, fg='white', relief=tk.FLAT, state=state, padx=12, pady=8)

    # --- End of styled widget helpers ---

    def toggle_quote_settings(self):
        """Show/hide quote-related settings based on mode."""
        if self.processing_mode.get() == "transcript":
            self.quote_settings_frame.pack_forget()
        else:
            self.quote_settings_frame.pack(fill=tk.BOTH, expand=True, pady=5)
    
    def clear_all(self):
        self.url_entry.delete(0, tk.END)
        self.timestamps_text.delete('1.0', tk.END)
        self.current_transcript = ""
        self.current_video_title = ""
        self.current_quotes = []
        self.status_var.set("Cleared all fields")
    
    def start_processing(self):
        if self.is_processing: return
        url = self.url_entry.get().strip()
        if not url or not validate_url(url):
            messagebox.showerror("Error", "Please enter a valid YouTube URL!")
            return
        if self.processing_mode.get() == "both" and not self.timestamps_text.get('1.0', tk.END).strip():
            messagebox.showerror("Error", "Please enter timestamps for quote extraction!")
            return
        
        self.is_processing = True
        self.process_btn.config(state=tk.DISABLED, text="Processing...")
        self.stop_btn.config(state=tk.NORMAL)
        
        thread = threading.Thread(target=self.process_video, args=(url, self.processing_mode.get()))
        thread.daemon = True
        thread.start()
    
    def process_video(self, url, mode):
        try:
            self.update_status("Starting... Downloading audio...")
            result = process_youtube_url_only(url, progress_callback=self.update_status)
            if not result:
                raise Exception("Failed to process video.")
                
            self.current_transcript, _, self.current_video_title = result
            
            if mode == "both":
                timestamps_text = self.timestamps_text.get('1.0', tk.END).strip()
                _, timestamps_to_process = parse_input(f"{url}\n{timestamps_text}")
                
                if not timestamps_to_process or not validate_timestamps_format(timestamps_to_process):
                    raise Exception("Invalid timestamp format found.")
                
                self.update_status("Extracting quotes...")
                self.current_quotes = process_timestamps(timestamps_to_process, self.current_transcript, self.context_after.get(), self.context_before.get(), "")
                
            self.update_status("Processing completed successfully!")
            self.root.after(0, lambda: messagebox.showinfo("Success", "Processing complete! Click 'View Results' to see the output."))
        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror("Error", f"An error occurred: {str(e)}"))
        finally:
            self.root.after(0, self.processing_complete)
    
    def processing_complete(self):
        self.is_processing = False
        self.process_btn.config(state=tk.NORMAL, text="🚀 Start Processing")
        self.stop_btn.config(state=tk.DISABLED)
    
    def stop_processing(self):
        self.is_processing = False
        self.update_status("Processing stopped by user.")
    
    def update_status(self, message):
        self.status_var.set(message)
    
    def show_results(self):
        if not self.current_transcript:
            messagebox.showwarning("No Results", "There are no results to display. Please process a video first.")
            return
        
        results_window = tk.Toplevel(self.root)
        results_window.title(f"Results: {self.current_video_title or 'Untitled'}")
        results_window.geometry("900x600")
        results_window.configure(bg=self.theme["bg"])

        style = ttk.Style()
        style.theme_use('clam') # A good, cross-platform theme
        style.configure("TNotebook.Tab", font=('Helvetica Neue', 12), padding=[10, 5])
        
        notebook = ttk.Notebook(results_window)
        notebook.pack(fill=tk.BOTH, expand=True, padx=15, pady=10)

        # Transcript Tab
        transcript_frame = tk.Frame(notebook, bg=self.theme["entry_bg"])
        notebook.add(transcript_frame, text="📝 Transcript")
        transcript_text = self.create_styled_scrolledtext(transcript_frame)
        transcript_text.insert('1.0', self.current_transcript)
        transcript_text.config(state=tk.DISABLED)

        # Quotes Tab
        if self.current_quotes:
            quotes_frame = tk.Frame(notebook, bg=self.theme["entry_bg"])
            notebook.add(quotes_frame, text="💬 Quotes")
            quotes_widget = self.create_styled_scrolledtext(quotes_frame)
            quotes_widget.insert('1.0', '\n\n'.join(self.current_quotes))
            quotes_widget.config(state=tk.DISABLED)

        # Export buttons
        export_frame = tk.Frame(results_window, bg=self.theme["bg"])
        export_frame.pack(fill=tk.X, padx=15, pady=(0, 10), anchor="e")
        self.create_styled_button(export_frame, "💾 Save Transcript", self.save_transcript, bg=self.theme["accent"]).pack(side=tk.RIGHT, padx=5)
        if self.current_quotes:
            self.create_styled_button(export_frame, "💾 Save Quotes", self.save_quotes, bg=self.theme["accent"]).pack(side=tk.RIGHT)

    def save_file(self, content, extension, file_type):
        if not content:
            messagebox.showwarning("Nothing to Save", f"There are no {file_type} to save.")
            return
        initial_name = f"{self.current_video_title}_{file_type}.{extension}" if self.current_video_title else f"{file_type}.{extension}"
        filename = filedialog.asksaveasfilename(defaultextension=f".{extension}", filetypes=[(f"{file_type.title()} files", f"*.{extension}")], initialname=initial_name)
        if filename:
            try:
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(content)
                messagebox.showinfo("Success", f"{file_type.title()} saved successfully!")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save file: {e}")

    def save_transcript(self):
        self.save_file(self.current_transcript, "txt", "transcript")
    
    def save_quotes(self):
        self.save_file('\n\n'.join(self.current_quotes), "txt", "quotes")
    
    def run(self):
        self.root.mainloop()

def main():
    app = YouTubeExtractorGUI()
    app.run()

if __name__ == "__main__":
    main() 