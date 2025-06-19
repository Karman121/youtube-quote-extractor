"""
YouTube Quote Extractor - Minimal GUI (macOS Visibility Fix)
A simple, reliable GUI with explicit styling to ensure visibility on macOS.
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog
import threading
import sys
import os

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
        self.root.title("YouTube Quote Extractor")
        
        # Consistent background color
        self.theme = {
            "bg": "#F0F0F0",
            "fg": "#000000",
            "entry_bg": "#FFFFFF",
            "button_bg": "#E1E1E1",
            "button_fg": "#000000",
            "accent": "#4A90E2",
        }
        
        self.root.geometry("1100x900")
        self.root.configure(bg=self.theme["bg"])
        
        # Force window to front on macOS
        if sys.platform == "darwin":
            self.root.lift()
            self.root.call('wm', 'attributes', '.', '-topmost', True)
            self.root.after_idle(self.root.attributes, '-topmost', False)
        
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
        """Create all GUI widgets with explicit styling for macOS."""
        
        # Main frame
        main_frame = tk.Frame(self.root, bg=self.theme["bg"])
        main_frame.pack(fill=tk.BOTH, expand=True, padx=30, pady=10)

        # Title
        title = tk.Label(
            main_frame, 
            text="🎬 YouTube Quote Extractor", 
            font=("Arial", 24, "bold"),
            bg=self.theme["bg"],
            fg='#333'
        )
        title.pack(pady=20)
        
        # --- URL Input ---
        url_frame = tk.LabelFrame(main_frame, text="1. YouTube URL", font=("Arial", 14), bg=self.theme["bg"], fg=self.theme["fg"], padx=15, pady=10)
        url_frame.pack(fill=tk.X, pady=5)
        
        self.url_entry = tk.Entry(url_frame, font=("Arial", 12), width=80, bg=self.theme["entry_bg"], fg=self.theme["fg"], insertbackground=self.theme["fg"], relief=tk.FLAT, highlightthickness=1, highlightbackground="#CCCCCC")
        self.url_entry.pack(padx=5, pady=10, fill=tk.X)
        
        # --- Processing Mode ---
        mode_frame = tk.LabelFrame(main_frame, text="2. Processing Mode", font=("Arial", 14), bg=self.theme["bg"], fg=self.theme["fg"], padx=15, pady=10)
        mode_frame.pack(fill=tk.X, pady=5)
        
        tk.Radiobutton(mode_frame, text="Generate Transcript Only", variable=self.processing_mode, value="transcript", font=("Arial", 12), bg=self.theme["bg"], command=self.toggle_timestamps, activebackground=self.theme["bg"], selectcolor=self.theme["entry_bg"]).pack(anchor=tk.W, padx=5, pady=2)
        tk.Radiobutton(mode_frame, text="Generate Transcript + Extract Quotes", variable=self.processing_mode, value="both", font=("Arial", 12), bg=self.theme["bg"], command=self.toggle_timestamps, activebackground=self.theme["bg"], selectcolor=self.theme["entry_bg"]).pack(anchor=tk.W, padx=5, pady=2)
        
        # --- Timestamps and Context Frame (to be toggled) ---
        self.timestamps_and_context_frame = tk.Frame(main_frame, bg=self.theme["bg"])
        self.timestamps_and_context_frame.pack(fill=tk.BOTH, expand=True, pady=5)

        # --- Context Settings ---
        context_frame = tk.LabelFrame(self.timestamps_and_context_frame, text="3. Context Settings (for Quotes)", font=("Arial", 14), bg=self.theme["bg"], fg=self.theme["fg"], padx=15, pady=10)
        context_frame.pack(fill=tk.X)
        
        context_inner = tk.Frame(context_frame, bg=self.theme["bg"])
        context_inner.pack(pady=5)
        
        tk.Label(context_inner, text="Before:", font=("Arial", 12), bg=self.theme["bg"]).grid(row=0, column=0, padx=10)
        tk.Spinbox(context_inner, from_=0, to=300, textvariable=self.context_before, width=10, font=("Arial", 12), bg=self.theme["entry_bg"], fg=self.theme["fg"], relief=tk.FLAT).grid(row=0, column=1, padx=10)
        
        tk.Label(context_inner, text="After:", font=("Arial", 12), bg=self.theme["bg"]).grid(row=0, column=2, padx=10)
        tk.Spinbox(context_inner, from_=0, to=600, textvariable=self.context_after, width=10, font=("Arial", 12), bg=self.theme["entry_bg"], fg=self.theme["fg"], relief=tk.FLAT).grid(row=0, column=3, padx=10)
        
        # --- Timestamps Input ---
        self.timestamps_frame = tk.LabelFrame(self.timestamps_and_context_frame, text="4. Timestamps & Descriptions", font=("Arial", 14), bg=self.theme["bg"], fg=self.theme["fg"], padx=15, pady=10)
        self.timestamps_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        tk.Label(self.timestamps_frame, text="Enter timestamps (MM:SS or HH:MM:SS) one per line.", font=("Arial", 10), bg=self.theme["bg"], fg='gray', justify=tk.LEFT).pack(anchor=tk.W, padx=5, pady=5)
        
        self.timestamps_text = scrolledtext.ScrolledText(self.timestamps_frame, height=8, font=("Consolas", 11), wrap=tk.WORD, bg=self.theme["entry_bg"], fg=self.theme["fg"], insertbackground=self.theme["fg"], relief=tk.FLAT, highlightthickness=1, highlightbackground="#CCCCCC")
        self.timestamps_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # --- Control Buttons ---
        btn_frame = tk.Frame(main_frame, bg=self.theme["bg"])
        btn_frame.pack(fill=tk.X, pady=15)
        
        self.process_btn = tk.Button(btn_frame, text="🚀 Start Processing", command=self.start_processing, font=("Arial", 14, "bold"), bg=self.theme["accent"], fg='white', relief=tk.FLAT, padx=15, pady=10)
        self.process_btn.pack(side=tk.LEFT, padx=10)
        
        self.stop_btn = tk.Button(btn_frame, text="⏹ Stop", command=self.stop_processing, font=("Arial", 12), bg="#D32F2F", fg='white', relief=tk.FLAT, state=tk.DISABLED, padx=15, pady=10)
        self.stop_btn.pack(side=tk.LEFT, padx=10)
        
        tk.Button(btn_frame, text="🗑 Clear All", command=self.clear_all, font=("Arial", 12), bg="#F57C00", fg='white', relief=tk.FLAT, padx=15, pady=10).pack(side=tk.LEFT, padx=10)
        tk.Button(btn_frame, text="📝 View Results", command=self.show_results, font=("Arial", 12), bg="#757575", fg='white', relief=tk.FLAT, padx=15, pady=10).pack(side=tk.LEFT, padx=10)
        
        # Status Bar
        status_frame = tk.Frame(self.root, bg='#E0E0E0', height=30)
        status_frame.pack(fill=tk.X, side=tk.BOTTOM)
        status_frame.pack_propagate(False)
        
        tk.Label(status_frame, textvariable=self.status_var, font=("Arial", 10), bg='#E0E0E0', fg='#333').pack(side=tk.LEFT, padx=10)
        
        # Initially hide timestamps if transcript only
        self.toggle_timestamps()
        
    def toggle_timestamps(self):
        """Show/hide timestamps and context section based on mode."""
        if self.processing_mode.get() == "transcript":
            self.timestamps_and_context_frame.pack_forget()
        else:
            self.timestamps_and_context_frame.pack(fill=tk.BOTH, expand=True, pady=5)

    def validate_url(self):
        """Validate the YouTube URL."""
        url = self.url_entry.get().strip()
        if validate_url(url):
            messagebox.showinfo("Success", "✅ Valid YouTube URL!")
        else:
            messagebox.showerror("Error", "❌ Invalid YouTube URL!")
    
    def clear_all(self):
        """Clear all fields."""
        self.url_entry.delete(0, tk.END)
        self.timestamps_text.delete('1.0', tk.END)
        self.current_transcript = ""
        self.current_video_title = ""
        self.current_quotes = []
        self.status_var.set("Cleared all fields")
    
    def start_processing(self):
        """Start processing in background thread."""
        if self.is_processing:
            return
            
        url = self.url_entry.get().strip()
        if not url:
            messagebox.showerror("Error", "Please enter a YouTube URL!")
            return
            
        mode = self.processing_mode.get()
        if mode == "both":
            timestamps = self.timestamps_text.get('1.0', tk.END).strip()
            if not timestamps:
                messagebox.showerror("Error", "Please enter timestamps for quote extraction!")
                return
        
        self.is_processing = True
        self.process_btn.config(state=tk.DISABLED, text="Processing...")
        self.stop_btn.config(state=tk.NORMAL)
        
        thread = threading.Thread(target=self.process_video, args=(url, mode))
        thread.daemon = True
        thread.start()
    
    def process_video(self, url, mode):
        """Process video in background."""
        try:
            self.update_status("Starting processing...")
            
            if mode == "transcript":
                result = process_youtube_url_only(url, progress_callback=self.update_status)
                if result:
                    transcript, filename, title = result
                    self.current_transcript = transcript
                    self.current_video_title = title
                    self.update_status("Transcript generated successfully!")
                    self.root.after(0, lambda: messagebox.showinfo("Success", "Transcript generated! Click 'View Results' to see it."))
            else:
                result = process_youtube_url_only(url, progress_callback=self.update_status)
                if not result:
                    self.root.after(0, self.processing_complete)
                    return
                    
                transcript, filename, title = result
                self.current_transcript = transcript
                self.current_video_title = title
                
                timestamps_text = self.timestamps_text.get('1.0', tk.END).strip()
                _, timestamps_to_process = parse_input(f"{url}\n{timestamps_text}")
                
                if not timestamps_to_process:
                    self.root.after(0, lambda: messagebox.showerror("Error", "No valid timestamps found!"))
                    self.root.after(0, self.processing_complete)
                    return
                
                if not validate_timestamps_format(timestamps_to_process):
                    self.root.after(0, lambda: messagebox.showerror("Error", "Invalid timestamp format!"))
                    self.root.after(0, self.processing_complete)
                    return
                
                self.update_status("Extracting quotes...")
                quotes = process_timestamps(timestamps_to_process, transcript, self.context_after.get(), self.context_before.get(), "")
                
                self.current_quotes = quotes
                self.update_status("Processing completed successfully!")
                self.root.after(0, lambda: messagebox.showinfo("Success", "Processing complete! Click 'View Results' to see transcript and quotes."))
                
        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror("Error", f"Processing failed: {str(e)}"))
        finally:
            self.root.after(0, self.processing_complete)
    
    def processing_complete(self):
        """Reset UI after processing."""
        self.is_processing = False
        self.process_btn.config(state=tk.NORMAL, text="🚀 Start Processing")
        self.stop_btn.config(state=tk.DISABLED)
    
    def stop_processing(self):
        """Stop processing."""
        self.is_processing = False
        self.processing_complete()
        self.update_status("Processing stopped")
    
    def update_status(self, message):
        """Update status message."""
        self.status_var.set(message)
        self.root.update_idletasks()
    
    def show_results(self):
        """Show results in a new window."""
        if not self.current_transcript:
            messagebox.showwarning("Warning", "No results to show! Process a video first.")
            return
        
        results_window = tk.Toplevel(self.root)
        results_window.title("Results - " + (self.current_video_title or "YouTube Video"))
        results_window.geometry("1000x700")
        results_window.configure(bg=self.theme["bg"])
        
        # Tabs for results
        notebook = ttk.Notebook(results_window)
        notebook.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)

        # Transcript Tab
        transcript_frame = tk.Frame(notebook, bg=self.theme["entry_bg"])
        notebook.add(transcript_frame, text="📝 Transcript")
        
        transcript_text = scrolledtext.ScrolledText(transcript_frame, font=("Consolas", 11), wrap=tk.WORD, bg=self.theme["entry_bg"], fg=self.theme["fg"], relief=tk.FLAT)
        transcript_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        transcript_text.insert('1.0', self.current_transcript)
        transcript_text.config(state=tk.DISABLED)

        # Quotes Tab
        if self.current_quotes:
            quotes_frame = tk.Frame(notebook, bg=self.theme["entry_bg"])
            notebook.add(quotes_frame, text="💬 Quotes")
            quotes_text_widget = scrolledtext.ScrolledText(quotes_frame, font=("Consolas", 11), wrap=tk.WORD, bg=self.theme["entry_bg"], fg=self.theme["fg"], relief=tk.FLAT)
            quotes_text_widget.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
            quotes_content = '\n\n'.join(self.current_quotes) if self.current_quotes else "No quotes extracted."
            quotes_text_widget.insert('1.0', quotes_content)
            quotes_text_widget.config(state=tk.DISABLED)

        # Export buttons
        export_frame = tk.Frame(results_window, bg=self.theme["bg"])
        export_frame.pack(fill=tk.X, padx=20, pady=(0, 10))
        tk.Button(export_frame, text="💾 Save Transcript", command=self.save_transcript, font=("Arial", 10), bg=self.theme["accent"], fg='white', relief=tk.FLAT).pack(side=tk.LEFT, padx=5)
        if self.current_quotes:
            tk.Button(export_frame, text="💾 Save Quotes", command=self.save_quotes, font=("Arial", 10), bg=self.theme["accent"], fg='white', relief=tk.FLAT).pack(side=tk.LEFT, padx=5)

    def save_transcript(self):
        """Save transcript to file."""
        if not self.current_transcript:
            messagebox.showwarning("Warning", "No transcript to save!")
            return
        
        filename = filedialog.asksaveasfilename(defaultextension=".txt", filetypes=[("Text files", "*.txt")], initialname=f"{self.current_video_title}_transcript.txt" if self.current_video_title else "transcript.txt")
        
        if filename:
            try:
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(self.current_transcript)
                messagebox.showinfo("Success", f"Transcript saved to {filename}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save: {e}")
    
    def save_quotes(self):
        """Save quotes to file."""
        if not self.current_quotes:
            messagebox.showwarning("Warning", "No quotes to save!")
            return
        
        filename = filedialog.asksaveasfilename(defaultextension=".txt", filetypes=[("Text files", "*.txt")], initialname=f"{self.current_video_title}_quotes.txt" if self.current_video_title else "quotes.txt")
        
        if filename:
            try:
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write('\n\n'.join(self.current_quotes))
                messagebox.showinfo("Success", f"Quotes saved to {filename}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save: {e}")
    
    def run(self):
        """Start the application."""
        self.root.mainloop()

def main():
    """Run the GUI application."""
    print("Starting YouTube Quote Extractor GUI...")
    app = YouTubeExtractorGUI()
    app.run()

if __name__ == "__main__":
    main() 