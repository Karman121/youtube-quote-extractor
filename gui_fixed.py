"""
YouTube Quote Extractor - Fixed GUI Application
A GUI interface that works properly on macOS.
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog
import threading
import logging
import os
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

# Set up logging for GUI
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('youtube_extractor_gui.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class YouTubeExtractorGUI:
    def __init__(self):
        # Initialize main window with proper macOS settings
        self.root = tk.Tk()
        self.root.title("YouTube Quote Extractor")
        
        # Force window to appear on macOS
        self.root.lift()
        self.root.attributes('-topmost', True)
        self.root.after_idle(self.root.attributes, '-topmost', False)
        
        # Set window size and make it resizable
        self.root.geometry("1000x800")
        self.root.minsize(900, 700)
        
        # Configure for macOS
        if sys.platform == "darwin":
            self.root.configure(background='#f0f0f0')
        
        # Processing state
        self.is_processing = False
        self.current_transcript = ""
        self.current_video_title = ""
        
        # Settings with proper initialization
        self.context_after = tk.IntVar()
        self.context_before = tk.IntVar()
        self.processing_mode = tk.StringVar()
        
        # Set default values
        self.context_after.set(DEFAULT_SETTINGS["default_context_after_seconds"])
        self.context_before.set(DEFAULT_SETTINGS["default_context_before_seconds"])
        self.processing_mode.set("both")
        
        # Force initial update
        self.root.update_idletasks()
        
        self.setup_ui()
        self.setup_logging_handler()
        
        # Final update to ensure everything renders
        self.root.update()
        
    def setup_ui(self):
        """Set up the main user interface with explicit geometry management."""
        # Create main container
        main_frame = tk.Frame(self.root, bg='#f0f0f0')
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Title with explicit styling
        title_label = tk.Label(
            main_frame, 
            text="🎬 YouTube Quote Extractor", 
            font=("Helvetica", 20, "bold"),
            bg='#f0f0f0',
            fg='#333333'
        )
        title_label.pack(pady=(0, 25))
        
        # Create and configure notebook
        style = ttk.Style()
        style.theme_use('default')  # Use default theme for better compatibility
        
        self.notebook = ttk.Notebook(main_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True)
        
        # Setup tabs
        self.setup_main_tab()
        self.setup_results_tab()
        
        # Status bar
        self.setup_status_bar(main_frame)
        
        # Force geometry update
        self.root.update_idletasks()
        
    def setup_main_tab(self):
        """Set up the main processing tab with explicit layout."""
        # Main tab frame
        main_tab = tk.Frame(self.notebook, bg='#f8f8f8')
        self.notebook.add(main_tab, text="  Main  ")
        
        # Scrollable frame for main content
        canvas = tk.Canvas(main_tab, bg='#f8f8f8')
        scrollbar = ttk.Scrollbar(main_tab, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg='#f8f8f8')
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Pack canvas and scrollbar
        canvas.pack(side="left", fill="both", expand=True, padx=20, pady=20)
        scrollbar.pack(side="right", fill="y")
        
        # Processing mode selection
        mode_frame = tk.LabelFrame(
            scrollable_frame, 
            text=" Processing Mode ", 
            font=("Helvetica", 12, "bold"),
            bg='#f8f8f8',
            padx=15,
            pady=15
        )
        mode_frame.pack(fill=tk.X, pady=(0, 20))
        
        tk.Radiobutton(
            mode_frame, 
            text="Generate Transcript Only", 
            variable=self.processing_mode, 
            value="transcript",
            font=("Helvetica", 11),
            bg='#f8f8f8'
        ).pack(anchor=tk.W, pady=5)
        
        tk.Radiobutton(
            mode_frame, 
            text="Generate Transcript + Extract Quotes", 
            variable=self.processing_mode, 
            value="both",
            font=("Helvetica", 11),
            bg='#f8f8f8'
        ).pack(anchor=tk.W, pady=5)
        
        # URL input section
        url_frame = tk.LabelFrame(
            scrollable_frame, 
            text=" YouTube URL ", 
            font=("Helvetica", 12, "bold"),
            bg='#f8f8f8',
            padx=15,
            pady=15
        )
        url_frame.pack(fill=tk.X, pady=(0, 20))
        
        self.url_entry = tk.Entry(
            url_frame, 
            font=("Consolas", 12),
            width=60
        )
        self.url_entry.pack(fill=tk.X, pady=(0, 10))
        
        # URL validation button
        validate_btn = tk.Button(
            url_frame, 
            text="Validate URL", 
            command=self.validate_youtube_url,
            font=("Helvetica", 10),
            bg='#e1e1e1'
        )
        validate_btn.pack(anchor=tk.E)
        
        # Context settings
        context_frame = tk.LabelFrame(
            scrollable_frame, 
            text=" Context Settings (seconds) ", 
            font=("Helvetica", 12, "bold"),
            bg='#f8f8f8',
            padx=15,
            pady=15
        )
        context_frame.pack(fill=tk.X, pady=(0, 20))
        
        context_grid = tk.Frame(context_frame, bg='#f8f8f8')
        context_grid.pack(fill=tk.X)
        
        tk.Label(
            context_grid, 
            text="Context Before:", 
            font=("Helvetica", 11),
            bg='#f8f8f8'
        ).grid(row=0, column=0, sticky=tk.W, padx=(0, 10), pady=5)
        
        tk.Spinbox(
            context_grid, 
            from_=0, 
            to=300, 
            textvariable=self.context_before,
            width=8,
            font=("Helvetica", 11)
        ).grid(row=0, column=1, sticky=tk.W, pady=5)
        
        tk.Label(
            context_grid, 
            text="Context After:", 
            font=("Helvetica", 11),
            bg='#f8f8f8'
        ).grid(row=0, column=2, sticky=tk.W, padx=(30, 10), pady=5)
        
        tk.Spinbox(
            context_grid, 
            from_=0, 
            to=600, 
            textvariable=self.context_after,
            width=8,
            font=("Helvetica", 11)
        ).grid(row=0, column=3, sticky=tk.W, pady=5)
        
        # Timestamps input
        self.timestamps_frame = tk.LabelFrame(
            scrollable_frame, 
            text=" Timestamps & Descriptions ", 
            font=("Helvetica", 12, "bold"),
            bg='#f8f8f8',
            padx=15,
            pady=15
        )
        self.timestamps_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 20))
        
        instruction_text = (
            "Enter timestamps (MM:SS or HH:MM:SS) with optional descriptions:\n"
            "Example: 1:30 - Discussion about AI\n"
            "         2:45 - Important quote"
        )
        
        tk.Label(
            self.timestamps_frame, 
            text=instruction_text,
            font=("Helvetica", 10),
            fg="gray",
            bg='#f8f8f8',
            justify=tk.LEFT
        ).pack(anchor=tk.W, pady=(0, 10))
        
        self.timestamps_text = scrolledtext.ScrolledText(
            self.timestamps_frame, 
            height=8,
            font=("Consolas", 11),
            wrap=tk.WORD
        )
        self.timestamps_text.pack(fill=tk.BOTH, expand=True)
        
        # Processing buttons
        button_frame = tk.Frame(scrollable_frame, bg='#f8f8f8')
        button_frame.pack(fill=tk.X, pady=(20, 0))
        
        self.process_btn = tk.Button(
            button_frame, 
            text="🚀 Start Processing", 
            command=self.start_processing,
            font=("Helvetica", 12, "bold"),
            bg='#4CAF50',
            fg='white',
            padx=20,
            pady=8
        )
        self.process_btn.pack(side=tk.LEFT, padx=(0, 15))
        
        self.stop_btn = tk.Button(
            button_frame, 
            text="⏹ Stop", 
            command=self.stop_processing,
            state=tk.DISABLED,
            font=("Helvetica", 12),
            bg='#f44336',
            fg='white',
            padx=20,
            pady=8
        )
        self.stop_btn.pack(side=tk.LEFT, padx=(0, 15))
        
        self.clear_btn = tk.Button(
            button_frame, 
            text="🗑 Clear All", 
            command=self.clear_all,
            font=("Helvetica", 12),
            bg='#ff9800',
            fg='white',
            padx=20,
            pady=8
        )
        self.clear_btn.pack(side=tk.LEFT)
        
        # Progress bar
        self.progress_var = tk.StringVar(value="Ready")
        self.progress_bar = ttk.Progressbar(
            scrollable_frame, 
            mode='indeterminate'
        )
        self.progress_bar.pack(fill=tk.X, pady=(20, 0))
        
        # Show/hide timestamps section based on mode
        self.processing_mode.trace('w', self.on_mode_change)
        
        # Force update
        self.root.update_idletasks()
        
    def setup_results_tab(self):
        """Set up the results display tab."""
        results_tab = tk.Frame(self.notebook, bg='#f8f8f8')
        self.notebook.add(results_tab, text="  Results  ")
        
        # Results notebook
        self.results_notebook = ttk.Notebook(results_tab)
        self.results_notebook.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Transcript tab
        transcript_frame = tk.Frame(self.results_notebook, bg='white')
        self.results_notebook.add(transcript_frame, text="📝 Transcript")
        
        self.transcript_text = scrolledtext.ScrolledText(
            transcript_frame, 
            font=("Consolas", 11),
            wrap=tk.WORD,
            padx=10,
            pady=10
        )
        self.transcript_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Quotes tab
        quotes_frame = tk.Frame(self.results_notebook, bg='white')
        self.results_notebook.add(quotes_frame, text="💬 Extracted Quotes")
        
        self.quotes_text = scrolledtext.ScrolledText(
            quotes_frame, 
            font=("Consolas", 11),
            wrap=tk.WORD,
            padx=10,
            pady=10
        )
        self.quotes_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Export buttons
        export_frame = tk.Frame(results_tab, bg='#f8f8f8')
        export_frame.pack(fill=tk.X, padx=20, pady=(0, 20))
        
        tk.Button(
            export_frame, 
            text="💾 Save Transcript", 
            command=self.save_transcript,
            font=("Helvetica", 11),
            bg='#2196F3',
            fg='white',
            padx=15,
            pady=5
        ).pack(side=tk.LEFT, padx=(0, 15))
        
        tk.Button(
            export_frame, 
            text="💾 Save Quotes", 
            command=self.save_quotes_file,
            font=("Helvetica", 11),
            bg='#2196F3',
            fg='white',
            padx=15,
            pady=5
        ).pack(side=tk.LEFT)
        
    def setup_status_bar(self, parent):
        """Set up the status bar."""
        status_frame = tk.Frame(parent, bg='#f0f0f0')
        status_frame.pack(fill=tk.X, pady=(20, 0))
        
        self.status_label = tk.Label(
            status_frame, 
            textvariable=self.progress_var,
            font=("Helvetica", 10),
            bg='#f0f0f0',
            fg='#666666'
        )
        self.status_label.pack(side=tk.LEFT)
        
    def setup_logging_handler(self):
        """Set up custom logging handler for GUI updates."""
        class GUILogHandler(logging.Handler):
            def __init__(self, gui):
                super().__init__()
                self.gui = gui
                
            def emit(self, record):
                msg = self.format(record)
                # Update GUI status safely from any thread
                self.gui.root.after(0, lambda: self.gui.update_status(msg))
        
        gui_handler = GUILogHandler(self)
        gui_handler.setLevel(logging.INFO)
        logger.addHandler(gui_handler)
        
    def update_status(self, message):
        """Update status message thread-safely."""
        self.progress_var.set(message)
        self.root.update_idletasks()
        
    def on_mode_change(self, *args):
        """Handle processing mode change."""
        if self.processing_mode.get() == "transcript":
            self.timestamps_frame.pack_forget()
        else:
            self.timestamps_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 20))
        self.root.update_idletasks()
            
    def validate_youtube_url(self):
        """Validate the entered YouTube URL."""
        url = self.url_entry.get().strip()
        if validate_url(url):
            messagebox.showinfo("Validation", "✅ Valid YouTube URL!")
        else:
            messagebox.showerror("Validation", "❌ Invalid or empty YouTube URL!")
            
    def clear_all(self):
        """Clear all input fields and results."""
        self.url_entry.delete(0, 'end')
        self.timestamps_text.delete('1.0', 'end')
        self.transcript_text.delete('1.0', 'end')
        self.quotes_text.delete('1.0', 'end')
        self.current_transcript = ""
        self.current_video_title = ""
        self.update_status("Cleared all fields")
        
    def start_processing(self):
        """Start the processing in a separate thread."""
        if self.is_processing:
            return
            
        url = self.url_entry.get().strip()
        if not url:
            messagebox.showerror("Error", "Please enter a YouTube URL!")
            return
            
        mode = self.processing_mode.get()
        if mode == "both":
            timestamps_text = self.timestamps_text.get('1.0', 'end').strip()
            if not timestamps_text:
                messagebox.showerror("Error", "Please enter timestamps for quote extraction!")
                return
                
        self.is_processing = True
        self.process_btn.config(state=tk.DISABLED)
        self.stop_btn.config(state=tk.NORMAL)
        self.progress_bar.start()
        
        # Start processing in separate thread
        thread = threading.Thread(target=self.process_video, args=(url, mode))
        thread.daemon = True
        thread.start()
        
    def process_video(self, url, mode):
        """Process video in background thread."""
        try:
            if mode == "transcript":
                self.process_transcript_only(url)
            else:
                self.process_with_quotes(url)
                
        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror("Error", f"Processing failed: {str(e)}"))
            logger.error(f"Processing error: {e}")
        finally:
            self.root.after(0, self.processing_complete)
            
    def process_transcript_only(self, url):
        """Process video for transcript only."""
        result = process_youtube_url_only(url, progress_callback=self.update_status)
        
        if result:
            transcript, filename, title = result
            self.current_transcript = transcript
            self.current_video_title = title
            
            # Update GUI
            self.root.after(0, lambda: self.transcript_text.delete('1.0', 'end'))
            self.root.after(0, lambda: self.transcript_text.insert('1.0', transcript))
            self.root.after(0, lambda: self.notebook.select(1))  # Switch to results tab
            
    def process_with_quotes(self, url):
        """Process video with quote extraction."""
        # First get transcript
        self.update_status("Downloading and processing video...")
        result = process_youtube_url_only(url, progress_callback=self.update_status)
        
        if not result:
            return
            
        transcript, filename, title = result
        self.current_transcript = transcript
        self.current_video_title = title
        
        # Update transcript display
        self.root.after(0, lambda: self.transcript_text.delete('1.0', 'end'))
        self.root.after(0, lambda: self.transcript_text.insert('1.0', transcript))
        
        # Parse timestamps
        timestamps_text = self.timestamps_text.get('1.0', 'end').strip()
        _, timestamps_to_process = parse_input(f"{url}\n{timestamps_text}")
        
        if not timestamps_to_process:
            self.root.after(0, lambda: messagebox.showerror("Error", "No valid timestamps found!"))
            return
            
        if not validate_timestamps_format(timestamps_to_process):
            self.root.after(0, lambda: messagebox.showerror("Error", "Invalid timestamp format found!"))
            return
            
        # Process quotes
        self.update_status("Extracting quotes...")
        extracted_quotes = process_timestamps(
            timestamps_to_process, 
            transcript, 
            self.context_after.get(), 
            self.context_before.get(), 
            ""  # video_description placeholder
        )
        
        # Update quotes display
        quotes_text = '\n\n'.join(extracted_quotes) if extracted_quotes else "No quotes extracted."
        self.root.after(0, lambda: self.quotes_text.delete('1.0', 'end'))
        self.root.after(0, lambda: self.quotes_text.insert('1.0', quotes_text))
        self.root.after(0, lambda: self.notebook.select(1))  # Switch to results tab
        
    def stop_processing(self):
        """Stop the current processing."""
        self.is_processing = False
        self.processing_complete()
        
    def processing_complete(self):
        """Clean up after processing is complete."""
        self.is_processing = False
        self.process_btn.config(state=tk.NORMAL)
        self.stop_btn.config(state=tk.DISABLED)
        self.progress_bar.stop()
        self.update_status("Processing complete!")
        
    def save_transcript(self):
        """Save transcript to file."""
        if not self.current_transcript:
            messagebox.showwarning("Warning", "No transcript to save!")
            return
            
        filename = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")],
            initialname=f"{self.current_video_title}_transcript.txt" if self.current_video_title else "transcript.txt"
        )
        
        if filename:
            try:
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(self.current_transcript)
                messagebox.showinfo("Success", f"Transcript saved to {filename}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save transcript: {e}")
                
    def save_quotes_file(self):
        """Save quotes to file."""
        quotes = self.quotes_text.get('1.0', 'end').strip()
        if not quotes or quotes == "No quotes extracted.":
            messagebox.showwarning("Warning", "No quotes to save!")
            return
            
        filename = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")],
            initialname=f"{self.current_video_title}_quotes.txt" if self.current_video_title else "quotes.txt"
        )
        
        if filename:
            try:
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(quotes)
                messagebox.showinfo("Success", f"Quotes saved to {filename}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save quotes: {e}")
                
    def run(self):
        """Start the GUI application."""
        # Bring window to front on macOS
        if sys.platform == "darwin":
            os.system('''/usr/bin/osascript -e 'tell app "Finder" to set frontmost of process "Python" to true' ''')
        
        self.root.mainloop()


def main():
    """Run the GUI application."""
    print("Starting YouTube Quote Extractor GUI...")
    app = YouTubeExtractorGUI()
    app.run()


if __name__ == "__main__":
    main() 