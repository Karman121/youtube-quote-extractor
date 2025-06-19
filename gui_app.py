"""
YouTube Quote Extractor - GUI Application
A modern GUI interface for extracting transcripts and quotes from YouTube videos.
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog
import threading
import logging
import os
from typing import List, Optional
import ttkbootstrap as ttk_bs
from ttkbootstrap.constants import *

# Import our core functionality
from main import (
    process_youtube_url_only, 
    download_and_prepare_audio,
    get_or_create_transcript,
    process_timestamps,
    save_quotes,
    validate_url,
    validate_timestamps_format
)
from transcript_utils import parse_input, TimestampInfo
from config import (
    DEFAULT_SETTINGS, 
    TRANSCRIPTION_PROMPT,
    QUOTE_EXTRACTION_INSTRUCTIONS,
    get_quote_extraction_prompt
)

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
        # Initialize main window with modern theme
        self.root = ttk_bs.Window(themename="superhero")
        self.root.title("YouTube Quote Extractor")
        self.root.geometry("1000x800")
        self.root.minsize(900, 700)
        
        # Processing state
        self.is_processing = False
        self.current_transcript = ""
        self.current_video_title = ""
        self.current_video_description = ""
        
        # Settings
        self.context_after = tk.IntVar(value=DEFAULT_SETTINGS["default_context_after_seconds"])
        self.context_before = tk.IntVar(value=DEFAULT_SETTINGS["default_context_before_seconds"])
        self.processing_mode = tk.StringVar(value="both")  # "transcript" or "both"
        
        # Custom prompts (for advanced settings)
        self.custom_transcription_prompt = tk.StringVar(value=TRANSCRIPTION_PROMPT)
        self.custom_quote_instructions = []
        for instruction in QUOTE_EXTRACTION_INSTRUCTIONS:
            self.custom_quote_instructions.append(tk.StringVar(value=instruction))
        
        self.setup_ui()
        self.setup_logging_handler()
        
    def setup_ui(self):
        """Set up the main user interface."""
        # Create main container with padding
        main_frame = ttk_bs.Frame(self.root, padding=20)
        main_frame.pack(fill=BOTH, expand=True)
        
        # Title
        title_label = ttk_bs.Label(
            main_frame, 
            text="YouTube Quote Extractor", 
            font=("Helvetica", 20, "bold")
        )
        title_label.pack(pady=(0, 20))
        
        # Create notebook for tabbed interface
        self.notebook = ttk_bs.Notebook(main_frame)
        self.notebook.pack(fill=BOTH, expand=True)
        
        # Main processing tab
        self.setup_main_tab()
        
        # Advanced settings tab
        self.setup_advanced_tab()
        
        # Results tab
        self.setup_results_tab()
        
        # Status bar
        self.setup_status_bar(main_frame)
        
    def setup_main_tab(self):
        """Set up the main processing tab."""
        main_tab = ttk_bs.Frame(self.notebook, padding=20)
        self.notebook.add(main_tab, text="Main")
        
        # Processing mode selection
        mode_frame = ttk_bs.LabelFrame(main_tab, text="Processing Mode", padding=15)
        mode_frame.pack(fill=X, pady=(0, 15))
        
        ttk_bs.Radiobutton(
            mode_frame, 
            text="Generate Transcript Only", 
            variable=self.processing_mode, 
            value="transcript",
            style="success.TRadiobutton"
        ).pack(anchor=W, pady=2)
        
        ttk_bs.Radiobutton(
            mode_frame, 
            text="Generate Transcript + Extract Quotes", 
            variable=self.processing_mode, 
            value="both",
            style="success.TRadiobutton"
        ).pack(anchor=W, pady=2)
        
        # URL input section
        url_frame = ttk_bs.LabelFrame(main_tab, text="YouTube URL", padding=15)
        url_frame.pack(fill=X, pady=(0, 15))
        
        self.url_entry = ttk_bs.Entry(url_frame, font=("Consolas", 11))
        self.url_entry.pack(fill=X, pady=(0, 10))
        
        # URL validation button
        validate_btn = ttk_bs.Button(
            url_frame, 
            text="Validate URL", 
            command=self.validate_youtube_url,
            style="info.TButton"
        )
        validate_btn.pack(anchor=E)
        
        # Context settings
        context_frame = ttk_bs.LabelFrame(main_tab, text="Context Settings (seconds)", padding=15)
        context_frame.pack(fill=X, pady=(0, 15))
        
        context_grid = ttk_bs.Frame(context_frame)
        context_grid.pack(fill=X)
        
        ttk_bs.Label(context_grid, text="Context Before:").grid(row=0, column=0, sticky=W, padx=(0, 10))
        ttk_bs.Spinbox(
            context_grid, 
            from_=0, 
            to=300, 
            textvariable=self.context_before,
            width=10
        ).grid(row=0, column=1, sticky=W)
        
        ttk_bs.Label(context_grid, text="Context After:").grid(row=0, column=2, sticky=W, padx=(20, 10))
        ttk_bs.Spinbox(
            context_grid, 
            from_=0, 
            to=600, 
            textvariable=self.context_after,
            width=10
        ).grid(row=0, column=3, sticky=W)
        
        # Timestamps input (only for quote extraction)
        self.timestamps_frame = ttk_bs.LabelFrame(main_tab, text="Timestamps & Descriptions", padding=15)
        self.timestamps_frame.pack(fill=BOTH, expand=True, pady=(0, 15))
        
        ttk_bs.Label(
            self.timestamps_frame, 
            text="Enter timestamps (MM:SS or HH:MM:SS) with optional descriptions:\nExample: 1:30 - Discussion about AI\n2:45 - Important quote",
            font=("Helvetica", 9),
            foreground="gray"
        ).pack(anchor=W, pady=(0, 10))
        
        self.timestamps_text = scrolledtext.ScrolledText(
            self.timestamps_frame, 
            height=8,
            font=("Consolas", 10)
        )
        self.timestamps_text.pack(fill=BOTH, expand=True)
        
        # Processing buttons
        button_frame = ttk_bs.Frame(main_tab)
        button_frame.pack(fill=X, pady=(15, 0))
        
        self.process_btn = ttk_bs.Button(
            button_frame, 
            text="Start Processing", 
            command=self.start_processing,
            style="success.TButton"
        )
        self.process_btn.pack(side=LEFT, padx=(0, 10))
        
        self.stop_btn = ttk_bs.Button(
            button_frame, 
            text="Stop", 
            command=self.stop_processing,
            style="danger.TButton",
            state=DISABLED
        )
        self.stop_btn.pack(side=LEFT, padx=(0, 10))
        
        self.clear_btn = ttk_bs.Button(
            button_frame, 
            text="Clear All", 
            command=self.clear_all,
            style="secondary.TButton"
        )
        self.clear_btn.pack(side=LEFT)
        
        # Progress bar
        self.progress_var = tk.StringVar(value="Ready")
        self.progress_bar = ttk_bs.Progressbar(
            main_tab, 
            mode='indeterminate',
            style="success.Horizontal.TProgressbar"
        )
        self.progress_bar.pack(fill=X, pady=(15, 0))
        
        # Show/hide timestamps section based on mode
        self.processing_mode.trace('w', self.on_mode_change)
        
    def setup_advanced_tab(self):
        """Set up the advanced settings tab."""
        advanced_tab = ttk_bs.Frame(self.notebook, padding=20)
        self.notebook.add(advanced_tab, text="Advanced Settings")
        
        # Create scrollable frame
        canvas = tk.Canvas(advanced_tab)
        scrollbar = ttk_bs.Scrollbar(advanced_tab, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk_bs.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Transcription prompt settings
        trans_frame = ttk_bs.LabelFrame(scrollable_frame, text="Transcription Prompt", padding=15)
        trans_frame.pack(fill=X, pady=(0, 20))
        
        ttk_bs.Label(trans_frame, text="Custom transcription prompt:").pack(anchor=W, pady=(0, 5))
        
        self.trans_prompt_text = scrolledtext.ScrolledText(
            trans_frame, 
            height=6,
            font=("Consolas", 9)
        )
        self.trans_prompt_text.pack(fill=X, pady=(0, 10))
        self.trans_prompt_text.insert('1.0', self.custom_transcription_prompt.get())
        
        ttk_bs.Button(
            trans_frame, 
            text="Reset to Default", 
            command=self.reset_transcription_prompt,
            style="warning.TButton"
        ).pack(anchor=E)
        
        # Quote extraction instructions
        quote_frame = ttk_bs.LabelFrame(scrollable_frame, text="Quote Extraction Instructions", padding=15)
        quote_frame.pack(fill=X, pady=(0, 20))
        
        ttk_bs.Label(quote_frame, text="Customize the 12 main instructions for quote extraction:").pack(anchor=W, pady=(0, 10))
        
        self.instruction_entries = []
        for i, instruction_var in enumerate(self.custom_quote_instructions):
            frame = ttk_bs.Frame(quote_frame)
            frame.pack(fill=X, pady=2)
            
            ttk_bs.Label(frame, text=f"{i+1}.", width=3).pack(side=LEFT)
            
            entry = ttk_bs.Entry(frame, textvariable=instruction_var, font=("Helvetica", 9))
            entry.pack(side=LEFT, fill=X, expand=True)
            self.instruction_entries.append(entry)
        
        ttk_bs.Button(
            quote_frame, 
            text="Reset Instructions to Default", 
            command=self.reset_quote_instructions,
            style="warning.TButton"
        ).pack(anchor=E, pady=(10, 0))
        
        # Model settings
        model_frame = ttk_bs.LabelFrame(scrollable_frame, text="AI Model Settings", padding=15)
        model_frame.pack(fill=X)
        
        ttk_bs.Label(model_frame, text=f"Current Model: {DEFAULT_SETTINGS['gemini_model']}").pack(anchor=W)
        ttk_bs.Label(model_frame, text=f"Retry Attempts: {DEFAULT_SETTINGS['retry_attempts']}").pack(anchor=W)
        ttk_bs.Label(model_frame, text=f"Rate Limit: {DEFAULT_SETTINGS['rate_limit_calls']} calls per {DEFAULT_SETTINGS['rate_limit_period']} second").pack(anchor=W)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
    def setup_results_tab(self):
        """Set up the results display tab."""
        results_tab = ttk_bs.Frame(self.notebook, padding=20)
        self.notebook.add(results_tab, text="Results")
        
        # Results display
        self.results_notebook = ttk_bs.Notebook(results_tab)
        self.results_notebook.pack(fill=BOTH, expand=True, pady=(0, 15))
        
        # Transcript tab
        transcript_frame = ttk_bs.Frame(self.results_notebook, padding=10)
        self.results_notebook.add(transcript_frame, text="Transcript")
        
        self.transcript_text = scrolledtext.ScrolledText(
            transcript_frame, 
            font=("Consolas", 10),
            wrap=tk.WORD
        )
        self.transcript_text.pack(fill=BOTH, expand=True)
        
        # Quotes tab
        quotes_frame = ttk_bs.Frame(self.results_notebook, padding=10)
        self.results_notebook.add(quotes_frame, text="Extracted Quotes")
        
        self.quotes_text = scrolledtext.ScrolledText(
            quotes_frame, 
            font=("Consolas", 10),
            wrap=tk.WORD
        )
        self.quotes_text.pack(fill=BOTH, expand=True)
        
        # Export buttons
        export_frame = ttk_bs.Frame(results_tab)
        export_frame.pack(fill=X)
        
        ttk_bs.Button(
            export_frame, 
            text="Save Transcript", 
            command=self.save_transcript,
            style="info.TButton"
        ).pack(side=LEFT, padx=(0, 10))
        
        ttk_bs.Button(
            export_frame, 
            text="Save Quotes", 
            command=self.save_quotes_file,
            style="info.TButton"
        ).pack(side=LEFT)
        
    def setup_status_bar(self, parent):
        """Set up the status bar."""
        status_frame = ttk_bs.Frame(parent)
        status_frame.pack(fill=X, pady=(15, 0))
        
        self.status_label = ttk_bs.Label(
            status_frame, 
            textvariable=self.progress_var,
            font=("Helvetica", 9)
        )
        self.status_label.pack(side=LEFT)
        
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
            self.timestamps_frame.pack(fill=BOTH, expand=True, pady=(0, 15))
            
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
        
    def reset_transcription_prompt(self):
        """Reset transcription prompt to default."""
        self.trans_prompt_text.delete('1.0', 'end')
        self.trans_prompt_text.insert('1.0', TRANSCRIPTION_PROMPT)
        
    def reset_quote_instructions(self):
        """Reset quote extraction instructions to default."""
        for i, instruction in enumerate(QUOTE_EXTRACTION_INSTRUCTIONS):
            self.custom_quote_instructions[i].set(instruction)
            
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
        self.process_btn.config(state=DISABLED)
        self.stop_btn.config(state=NORMAL)
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
            transcript, filename, title, video_description = result
            self.current_transcript = transcript
            self.current_video_title = title
            self.current_video_description = video_description
            
            # Update GUI
            self.root.after(0, lambda: self.transcript_text.delete('1.0', 'end'))
            self.root.after(0, lambda: self.transcript_text.insert('1.0', transcript))
            self.root.after(0, lambda: self.notebook.select(2))  # Switch to results tab
            
    def process_with_quotes(self, url):
        """Process video with quote extraction."""
        # First get transcript
        self.update_status("Downloading and processing video...")
        result = process_youtube_url_only(url, progress_callback=self.update_status)
        
        if not result:
            return
            
        transcript, filename, title, video_description = result
        self.current_transcript = transcript
        self.current_video_title = title
        self.current_video_description = video_description
        
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
            video_description  # Now passing actual video description
        )
        
        # Update quotes display
        quotes_text = '\n\n'.join(extracted_quotes) if extracted_quotes else "No quotes extracted."
        self.root.after(0, lambda: self.quotes_text.delete('1.0', 'end'))
        self.root.after(0, lambda: self.quotes_text.insert('1.0', quotes_text))
        self.root.after(0, lambda: self.notebook.select(2))  # Switch to results tab
        
    def stop_processing(self):
        """Stop the current processing."""
        self.is_processing = False
        self.processing_complete()
        
    def processing_complete(self):
        """Clean up after processing is complete."""
        self.is_processing = False
        self.process_btn.config(state=NORMAL)
        self.stop_btn.config(state=DISABLED)
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
        self.root.mainloop()


def main():
    """Run the GUI application."""
    app = YouTubeExtractorGUI()
    app.run()


if __name__ == "__main__":
    main() 