import tkinter as tk
from tkinter import ttk
import customtkinter as ctk
from PIL import Image, ImageTk
from youtube_transcript_api import YouTubeTranscriptApi
from groq import Groq
import requests
from bs4 import BeautifulSoup
import threading
import asyncio
import re
import json
from urllib.parse import urlparse
from datetime import datetime
import os
import webbrowser
import platform
import sys
import urllib.parse

class SummarAI:
    def __init__(self):
        self.window = ctk.CTk()
        self.window.title("SummarAI")
        self.window.geometry("1400x800")
        
        # Modern color scheme
        self.colors = {
            "background": "#0F0F0F",
            "card": "#1E1E1E",
            "accent": "#7289DA",
            "text": "#FFFFFF",
            "subtext": "#AAAAAA",
            "error": "#FF5555"
        }
        
        self.window.configure(fg_color=self.colors["background"])
        
        # Initialize Groq client with your API key
        self.client = Groq(
            api_key="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"  # Replace with your actual API key
        )
        
        # Settings for API key
        self.api_key = "Your_api_key_here"  # Default key
        self.load_settings()  # Load saved settings
        self.client = Groq(api_key=self.api_key)
        
        # Initialize history
        self.history_file = os.path.join(os.path.expanduser("~"), ".summarai_history.json")
        print(f"History file location: {self.history_file}")  # Debug print
        self.load_history()
        
        self.create_ui()
        
        self.version = "1.2.1"  # Store version as class variable
        
    def create_ui(self):
        # Left panel (40% width)
        left_panel = ctk.CTkFrame(self.window, fg_color=self.colors["card"])
        left_panel.place(relx=0, rely=0, relwidth=0.4, relheight=1)
        
        # Input area
        input_area = ctk.CTkFrame(left_panel, fg_color="transparent")
        input_area.place(relx=0.5, rely=0.1, relwidth=0.8, anchor="n")
        
        # Stylish title
        title = ctk.CTkLabel(
            input_area,
            text="SummarAI",
            font=("Helvetica", 40, "bold"),
            text_color=self.colors["accent"]
        )
        title.pack(pady=(0, 20))
        
        # URL input with icon
        self.url_var = tk.StringVar()
        url_frame = ctk.CTkFrame(input_area, fg_color=self.colors["background"])
        url_frame.pack(fill="x", pady=(0, 20))
        
        self.url_entry = ctk.CTkEntry(
            url_frame,
            textvariable=self.url_var,
            placeholder_text="Paste URL here...",
            font=("Helvetica", 14),
            height=45,
            border_width=0
        )
        self.url_entry.pack(fill="x", padx=2, pady=2)
        
        # Action buttons
        self.summarize_btn = ctk.CTkButton(
            input_area,
            text="Generate Summary",
            font=("Helvetica", 16, "bold"),
            height=50,
            fg_color=self.colors["accent"],
            command=self.start_summary
        )
        self.summarize_btn.pack(fill="x", pady=(0, 10))
        
        # Status indicator
        self.status_label = ctk.CTkLabel(
            input_area,
            text="Ready",
            font=("Helvetica", 12),
            text_color=self.colors["subtext"]
        )
        self.status_label.pack()
        
        # Settings button
        settings_btn = ctk.CTkButton(
            input_area,
            text="⚙️ Settings",
            font=("Helvetica", 14),
            height=40,
            fg_color=self.colors["card"],
            hover_color=self.colors["accent"],
            command=self.show_settings
        )
        settings_btn.pack(fill="x", pady=(0, 10))
        
        # Add history button after the settings button
        history_btn = ctk.CTkButton(
            input_area,
            text="📋 View History",
            font=("Helvetica", 14),
            height=40,
            fg_color=self.colors["card"],
            hover_color=self.colors["accent"],
            command=self.show_history
        )
        history_btn.pack(fill="x", pady=(0, 10))
        
        # Add history panel components - modify initial position to be hidden
        self.history_panel = ctk.CTkFrame(self.window, fg_color=self.colors["card"])
        self.history_panel.place(relx=0, rely=1.0, relwidth=1, relheight=0.9)  # Start hidden below the window
        
        # Add header frame for buttons
        header_frame = ctk.CTkFrame(self.history_panel, fg_color="transparent", height=40)
        header_frame.place(relx=0.05, rely=0.02, relwidth=0.9)
        
        # Add back button
        back_btn = ctk.CTkButton(
            header_frame,
            text="← Back",
            width=100,
            font=("Helvetica", 14),
            fg_color=self.colors["accent"],
            hover_color=self.colors["background"],
            command=self.hide_history
        )
        back_btn.pack(side="left", padx=5)
        
        # Add clear history button
        clear_btn = ctk.CTkButton(
            header_frame,
            text="🗑️ Clear History",
            width=120,
            font=("Helvetica", 14),
            fg_color=self.colors["error"],
            hover_color="#FF3333",
            command=self.clear_history
        )
        clear_btn.pack(side="left", padx=5)
        
        # Add loading label (hidden by default)
        self.loading_label = ctk.CTkLabel(
            header_frame,
            text="",
            font=("Helvetica", 14),
            text_color=self.colors["accent"]
        )
        self.loading_label.pack(side="left", padx=10)
        
        # Add scrollable frame for history items
        self.history_scroll = ctk.CTkScrollableFrame(
            self.history_panel,
            fg_color="transparent"
        )
        self.history_scroll.place(relx=0.05, rely=0.1, relwidth=0.9, relheight=0.85)
        
        # Right panel (60% width)
        right_panel = ctk.CTkFrame(self.window, fg_color=self.colors["card"])
        right_panel.place(relx=0.4, rely=0, relwidth=0.6, relheight=1)
        
        # Output tabs
        self.tab_view = ctk.CTkTabview(
            right_panel,
            fg_color=self.colors["background"],
            segmented_button_fg_color=self.colors["card"],
            segmented_button_selected_color=self.colors["accent"]
        )
        self.tab_view.place(relx=0.05, rely=0.05, relwidth=0.9, relheight=0.9)
        
        # Add tabs
        self.tab_view.add("Summary")
        self.tab_view.add("Ask Questions")
        
        # Summary output
        self.summary_text = ctk.CTkTextbox(
            self.tab_view.tab("Summary"),
            font=("Helvetica", 14),
            fg_color="transparent",
            wrap="word",
            padx=20,
            pady=20
        )
        self.summary_text.pack(fill="both", expand=True)
        
        # Q&A interface
        qa_frame = ctk.CTkFrame(
            self.tab_view.tab("Ask Questions"),
            fg_color="transparent"
        )
        qa_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        self.question_entry = ctk.CTkEntry(
            qa_frame,
            placeholder_text="Ask a question about the summary...",
            font=("Helvetica", 14),
            height=45
        )
        self.question_entry.pack(fill="x", pady=(0, 10))
        
        self.ask_btn = ctk.CTkButton(
            qa_frame,
            text="Ask",
            font=("Helvetica", 14, "bold"),
            height=40,
            fg_color=self.colors["accent"],
            command=self.ask_question
        )
        self.ask_btn.pack(pady=(0, 20))
        
        self.answer_text = ctk.CTkTextbox(
            qa_frame,
            font=("Helvetica", 14),
            fg_color=self.colors["background"],
            wrap="word"
        )
        self.answer_text.pack(fill="both", expand=True)
    
    async def animate_text(self, text):
        self.summary_text.configure(state="normal")
        self.summary_text.delete("1.0", "end")
        
        # Faster typing speed - reduced sleep time from 0.01 to 0.001
        # You can adjust this number to make it even faster/slower
        typing_speed = 0.001
        
        # Optional: Type multiple characters at once for even faster display
        chunk_size = 3  # Will type 3 characters at a time
        
        for i in range(0, len(text), chunk_size):
            chunk = text[i:i + chunk_size]
            self.summary_text.insert("end", chunk)
            self.summary_text.see("end")
            await asyncio.sleep(typing_speed)
        
        self.summary_text.configure(state="disabled")
    
    def start_summary(self):
        url = self.url_var.get()
        if not url:
            self.show_error("Please enter a URL")
            return
            
        self.summarize_btn.configure(state="disabled")
        self.status_label.configure(text="Processing...", text_color=self.colors["accent"])
        
        threading.Thread(target=self.process_url, args=(url,), daemon=True).start()
    
    def process_url(self, url):
        """Process URL and generate summary"""
        try:
            # Clear previous content
            self.summary_text.configure(state="normal")
            self.summary_text.delete("1.0", "end")
            self.summary_text.configure(state="disabled")
            
            # Get content
            try:
                text = self.get_content(url)
            except Exception as e:
                self.display_error(f"Error getting content: {str(e)}")
                return
                
            if not text:
                self.display_error("No content could be extracted")
                return
                
            # Generate summary
            try:
                summary = self.generate_summary(text)
                asyncio.run(self.animate_text(summary))
                self.status_label.configure(text="Summary ready!", text_color=self.colors["text"])
                
                # Add to history after successful summary generation
                self.add_to_history(url, summary)
                
            except Exception as e:
                self.display_error(f"Error generating summary: {str(e)}")
                
        except Exception as e:
            self.display_error(f"Processing error: {str(e)}")
        finally:
            self.summarize_btn.configure(state="normal")
    
    def ask_question(self):
        question = self.question_entry.get()
        if not question:
            self.show_error("Please enter a question")
            return
            
        self.ask_btn.configure(state="disabled")
        threading.Thread(target=self.process_question, args=(question,), daemon=True).start()
    
    def show_error(self, message):
        self.status_label.configure(text=message, text_color=self.colors["error"])
    
    # Your existing helper functions (get_content, generate_summary, etc.)
    def get_content(self, url):
        """Extract content from YouTube or website URL"""
        try:
            # Check if YouTube URL
            video_id = self.get_video_id(url)
            if video_id:
                return self.get_youtube_transcript(video_id)
            
            # Otherwise treat as website URL
            return self.get_website_content(url)
        except Exception as e:
            raise Exception(f"Failed to extract content: {str(e)}")

    def get_video_id(self, url):
        """Extract YouTube video ID from URL"""
        youtube_regex = (
            r'(https?://)?(www\.)?(youtube|youtu|youtube-nocookie)\.(com|be)/'
            '(watch\?v=|embed/|v/|.+\?v=)?([^&=%\?]{11})'
        )
        match = re.search(youtube_regex, url)
        return match.group(6) if match else None

    def get_youtube_transcript(self, video_id):
        """Get transcript from YouTube video"""
        try:
            transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
            transcript = transcript_list.find_manually_created_transcript(['en'])
            return " ".join([entry['text'] for entry in transcript.fetch()])
        except Exception:
            try:
                # Fallback to auto-generated transcript
                transcript = transcript_list.find_generated_transcript(['en'])
                return " ".join([entry['text'] for entry in transcript.fetch()])
            except Exception as e:
                raise Exception(f"Could not get YouTube transcript: {str(e)}")

    def get_website_content(self, url):
        """Extract content from website including subpages"""
        try:
            base_domain = self.get_domain(url)
            visited_urls = set()
            pages_content = []
            
            def crawl_page(url, depth=0):
                if depth > 2 or len(visited_urls) >= 10 or url in visited_urls:
                    return
                    
                try:
                    visited_urls.add(url)
                    self.status_label.configure(
                        text=f"Analyzing page {len(visited_urls)}...",
                        text_color=self.colors["accent"]
                    )
                    
                    response = requests.get(url, timeout=10)
                    soup = BeautifulSoup(response.content, 'html.parser')
                    
                    # Get title
                    title = soup.find('title')
                    title_text = title.get_text() if title else url
                    
                    # Get main content
                    main_content = (
                        soup.find('main') or 
                        soup.find('article') or 
                        soup.find(['div'], {'class': ['content', 'main']}) or 
                        soup
                    )
                    
                    # Extract text
                    content = []
                    for elem in main_content.find_all(['h1', 'h2', 'h3', 'p']):
                        text = elem.get_text().strip()
                        if text:
                            content.append(text)
                    
                    if content:
                        newline = '\n'
                        pages_content.append(f"\n=== {title_text} ===\nURL: {url}\n\n{newline.join(content)}")
                    
                    # Find more links
                    if depth < 2:
                        for link in soup.find_all('a', href=True):
                            href = link['href']
                            if href.startswith('/'):
                                href = f"https://{base_domain}{href}"
                            if href.startswith('http') and self.get_domain(href) == base_domain:
                                crawl_page(href, depth + 1)
                                
                except Exception as e:
                    pages_content.append(f"\nError analyzing {url}: {str(e)}")
            
            # Start crawling from main URL
            crawl_page(url)
            
            if not pages_content:
                raise Exception("No content could be extracted from the website")
                
            return "\n\n".join(pages_content)
            
        except Exception as e:
            raise Exception(f"Failed to analyze website: {str(e)}")

    def format_content(self, content, metadata):
        """Format content with clear page structure"""
        formatted_parts = []
        
        # Add main page URL
        formatted_parts.append(f"MAIN PAGE URL: {metadata['main_page']}\n")
        
        # Add page contents with metadata
        for page in metadata['pages']:
            formatted_parts.append(
                f"\n=== PAGE: {page['title']} ===\n"
                f"URL: {page['url']}\n"
                f"TYPE: {page['type']}\n"
                f"CONTENT LENGTH: {page['content_length']} characters\n"
                f"CONTENT:\n{page['content']}\n"
                f"{'=' * 50}\n"
            )
        
        return "\n".join(formatted_parts)

    def crawl_page(self, url, base_domain, visited_urls, content, metadata, max_pages, max_depth, current_depth=0):
        """Recursively crawl pages to extract content"""
        if len(visited_urls) >= max_pages or current_depth >= max_depth:
            return
            
        if url in visited_urls or not url.startswith(('http://', 'https://')):
            return
            
        try:
            self.status_label.configure(
                text=f"Analyzing page {len(visited_urls) + 1}/{max_pages} (depth: {current_depth})...",
                text_color=self.colors["accent"]
            )
            
            visited_urls.add(url)
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8'
            }
            response = requests.get(url, timeout=15, headers=headers)
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Remove unwanted elements
            for element in soup.find_all(['script', 'style', 'nav', 'footer', 'header', 'aside']):
                element.decompose()
            
            # Extract page type based on meta tags and content
            page_type = self.determine_page_type(soup)
            
            # Extract main content
            main_content = (
                soup.find('main') or 
                soup.find('article') or 
                soup.find('div', {'class': ['content', 'main', 'post', 'entry']}) or 
                soup.find('div', {'id': ['content', 'main', 'post']}) or 
                soup
            )
            
            # Extract text with headers and structure
            content_parts = []
            for elem in main_content.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'p', 'li']):
                if elem.name.startswith('h'):
                    content_parts.append(f"\n[{elem.name.upper()}] {elem.get_text().strip()}")
                else:
                    content_parts.append(elem.get_text().strip())
            
            page_content = "\n".join(content_parts).strip()
            
            if page_content:
                # Get page title
                title = (
                    soup.find('meta', {'property': 'og:title'})
                    or soup.find('meta', {'name': 'title'})
                    or soup.find('title')
                )
                title_text = title.get('content', None) if title and title.get('content') else (
                    title.get_text() if title else url
                )
                
                # Store page metadata
                page_data = {
                    'title': title_text,
                    'url': url,
                    'type': page_type,
                    'content': page_content,
                    'content_length': len(page_content)
                }
                metadata['pages'].append(page_data)
            
            # Find and prioritize links
            links = []
            for link in soup.find_all('a', href=True):
                href = link['href']
                
                if href.startswith('/'):
                    href = f"https://{base_domain}{href}"
                elif not href.startswith(('http://', 'https://')):
                    continue
                    
                if self.get_domain(href) != base_domain:
                    continue
                    
                # Prioritize links
                priority = self.calculate_link_priority(href, link.get_text())
                links.append((priority, href))
            
            # Sort and crawl prioritized links
            for _, href in sorted(links, reverse=True):
                if len(visited_urls) < max_pages:
                    self.crawl_page(
                        href, 
                        base_domain, 
                        visited_urls, 
                        content, 
                        metadata,
                        max_pages,
                        max_depth,
                        current_depth + 1
                    )
                    
        except Exception as e:
            print(f"Error crawling {url}: {e}")

    def determine_page_type(self, soup):
        """Determine the type of page based on content and meta tags"""
        page_type = "General"
        
        # Check meta tags
        meta_type = soup.find('meta', {'property': 'og:type'})
        if meta_type:
            return meta_type.get('content', 'General').capitalize()
        
        # Check common patterns
        if soup.find('article'):
            page_type = "Article"
        elif soup.find(['product', 'div'], {'class': ['product', 'product-details']}):
            page_type = "Product"
        elif soup.find(['form', 'div'], {'class': ['contact', 'contact-form']}):
            page_type = "Contact"
        elif soup.find('div', {'class': ['about', 'about-us']}):
            page_type = "About"
        
        return page_type

    def calculate_link_priority(self, url, link_text):
        """Calculate priority score for a link"""
        priority = 0
        important_terms = {
            'article': 3,
            'post': 3,
            'product': 2,
            'about': 2,
            'contact': 1,
            'category': 1,
            'tag': 1
        }
        
        url_lower = url.lower()
        text_lower = link_text.lower()
        
        for term, score in important_terms.items():
            if term in url_lower or term in text_lower:
                priority += score
        
        return priority

    def generate_summary(self, text):
        """Generate summary using Groq API"""
        try:
            max_chars = 15000
            truncated_text = text[:max_chars] + ("..." if len(text) > max_chars else "")
            
            prompt = (
                "As an expert analyst, please provide a comprehensive analysis of this website content. "
                "Structure your response with these detailed sections:\n\n"
                "📌 EXECUTIVE SUMMARY:\n"
                "- Core purpose and mission of the website\n"
                "- Target audience and main value proposition\n"
                "- Overall tone and professional assessment\n\n"
                "📑 DETAILED CONTENT ANALYSIS:\n"
                "- Breakdown of major sections and their purposes\n"
                "- Key features, products, or services offered\n"
                "- Notable strengths and unique selling points\n\n"
                "💡 KEY INSIGHTS:\n"
                "- Most important takeaways\n"
                "- Valuable information for users\n"
                "- Standout features or offerings\n"
                "- Professional recommendations\n\n"
                "📊 CONTENT ORGANIZATION:\n"
                "- Structure and navigation assessment\n"
                "- Content quality and depth\n"
                "- Information accessibility\n\n"
                "❓ FREQUENTLY ADDRESSED TOPICS:\n"
                "- Common questions and their answers\n"
                "- Important clarifications\n"
                "- User concerns addressed\n\n"
                "🎯 ACTIONABLE INSIGHTS:\n"
                "- What users can do with this information\n"
                "- Next steps for interested parties\n"
                "- Important contact points or resources\n\n"
                f"Content to analyze:\n{truncated_text}"
            )
            
            chat_completion = self.client.chat.completions.create(
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert content analyst and professional summarizer. "
                        "Provide detailed, well-structured analyses that are both comprehensive and practical. "
                        "Focus on extracting maximum value for the reader while maintaining clarity and relevance."
                    },
                    {"role": "user", "content": prompt}
                ],
                model="mixtral-8x7b-32768",
                max_tokens=15000,
                temperature=0.7  # Added some creativity while keeping it professional
            )
            
            return chat_completion.choices[0].message.content
            
        except Exception as e:
            raise Exception(f"API Error: {str(e)}")

    def process_question(self, question):
        """Process Q&A about the summary"""
        try:
            summary = self.summary_text.get("1.0", "end").strip()
            if not summary:
                raise Exception("Please generate a summary first")
            
            prompt = (
                f"Based on the following summary, please answer this question:\n\n"
                f"Summary:\n{summary}\n\n"
                f"Question: {question}\n\n"
                f"Please provide a clear and concise answer based only on the information in the summary."
            )
            
            chat_completion = self.client.chat.completions.create(
                messages=[
                    {
                        "role": "user",
                        "content": prompt,
                    }
                ],
                model="mixtral-8x7b-32768",
                max_tokens=1000,
            )
            
            answer = chat_completion.choices[0].message.content
            
            # Update answer display
            self.answer_text.configure(state="normal")
            self.answer_text.delete("1.0", "end")
            self.answer_text.insert("1.0", answer)
            self.answer_text.configure(state="disabled")
            
        except Exception as e:
            self.show_error(str(e))
        finally:
            self.ask_btn.configure(state="normal")
    
    def run(self):
        self.window.mainloop()

    def load_settings(self):
        """Load settings from file"""
        try:
            with open('settings.json', 'r') as f:
                settings = json.load(f)
                self.colors.update(settings.get('colors', {}))
                saved_api_key = settings.get('api_key')
                if saved_api_key:
                    self.api_key = saved_api_key
        except FileNotFoundError:
            pass

    def save_settings(self):
        """Save settings to file"""
        settings = {
            'colors': self.colors,
            'api_key': self.api_key
        }
        with open('settings.json', 'w') as f:
            json.dump(settings, f)

    def show_settings(self):
        """Show settings dialog"""
        settings_window = ctk.CTkToplevel(self.window)
        settings_window.title("Settings")
        settings_window.geometry("500x600")
        settings_window.grab_set()  # Make window modal

        # Create tabs for different settings
        tab_view = ctk.CTkTabview(settings_window)
        tab_view.pack(fill="both", expand=True, padx=20, pady=20)
        
        colors_tab = tab_view.add("Colors")
        api_tab = tab_view.add("API Key")
        bug_tab = tab_view.add("Bug Report")  # Add new tab

        # Color settings
        color_vars = {}
        for i, (name, color) in enumerate(self.colors.items()):
            frame = ctk.CTkFrame(colors_tab, fg_color="transparent")
            frame.pack(fill="x", pady=5)
            
            label = ctk.CTkLabel(frame, text=name.capitalize())
            label.pack(side="left", padx=10)
            
            color_vars[name] = tk.StringVar(value=color)
            entry = ctk.CTkEntry(frame, textvariable=color_vars[name])
            entry.pack(side="left", expand=True, fill="x", padx=10)
            
            # Color preview
            preview = ctk.CTkFrame(frame, width=30, height=30)
            preview.configure(fg_color=color)
            preview.pack(side="right", padx=10)
            
            # Update preview when color changes
            def update_preview(name, preview):
                def callback(*args):
                    try:
                        color = color_vars[name].get()
                        preview.configure(fg_color=color)
                    except:
                        pass
                return callback
            
            color_vars[name].trace_add("write", update_preview(name, preview))

        # API Key settings
        api_frame = ctk.CTkFrame(api_tab, fg_color="transparent")
        api_frame.pack(fill="x", pady=20, padx=20)
        
        api_label = ctk.CTkLabel(api_frame, text="Groq API Key")
        api_label.pack(anchor="w")
        
        api_var = tk.StringVar(value=self.api_key)
        api_entry = ctk.CTkEntry(api_frame, textvariable=api_var, show="*", width=300)
        api_entry.pack(fill="x", pady=(5, 0))
        
        # Show/Hide API key
        def toggle_api_visibility():
            api_entry.configure(show="" if api_entry.cget("show") else "*")
        
        show_api = ctk.CTkButton(
            api_frame,
            text="Show/Hide API Key",
            command=toggle_api_visibility
        )
        show_api.pack(pady=10)

        # Bug Report tab
        bug_frame = ctk.CTkFrame(bug_tab, fg_color="transparent")
        bug_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Description label
        description_label = ctk.CTkLabel(
            bug_frame,
            text="Describe the issue you're experiencing:",
            font=("Arial", 14, "bold")
        )
        description_label.pack(anchor="w", pady=(0, 5))
        
        # Bug description text area
        bug_description = ctk.CTkTextbox(
            bug_frame,
            height=150,
            font=("Arial", 12)
        )
        bug_description.pack(fill="x", pady=(0, 10))
        
        def send_bug_report():
            # Get the description
            bug_text = bug_description.get("1.0", "end-1c").strip()
            
            if not bug_text:
                status_label.configure(text="Please describe the issue", text_color=self.colors["error"])
                return
            
            # Get system info
            system_info = f"""
System Information:
- OS: {platform.system()} {platform.version()}
- Python: {sys.version}
- App Version: {self.version}
            """
            
            # Create email content
            subject = "SummarAI Bug Report"
            body = f"""
Bug Description:
{bug_text}

{system_info}
            """
            
            # Create mailto URL
            mailto_url = (
                f"mailto:nesbes2012@gmail.com"
                f"?subject={urllib.parse.quote(subject)}"
                f"&body={urllib.parse.quote(body)}"
            )
            
            # Open default mail client
            webbrowser.open(mailto_url)
            
            # Clear the text area
            bug_description.delete("1.0", "end")
            status_label.configure(
                text="Mail client opened with bug report!",
                text_color=self.colors["accent"]
            )
        
        # Status label for feedback
        status_label = ctk.CTkLabel(
            bug_frame,
            text="",
            font=("Arial", 12),
            text_color=self.colors["accent"]
        )
        status_label.pack(pady=10)
        
        # Send button
        send_btn = ctk.CTkButton(
            bug_frame,
            text="Open Mail Client",
            font=("Arial", 14, "bold"),
            height=40,
            fg_color=self.colors["accent"],
            command=send_bug_report
        )
        send_btn.pack(pady=10)

        # Save button
        def save_settings():
            # Update colors
            for name, var in color_vars.items():
                try:
                    # Validate color
                    color = var.get()
                    self.colors[name] = color
                except:
                    continue
            
            # Update API key
            new_api_key = api_var.get()
            if new_api_key and new_api_key != self.api_key:
                self.api_key = new_api_key
                self.client = Groq(api_key=self.api_key)
            
            # Save to file
            self.save_settings()
            
            # Update UI colors
            self.window.configure(fg_color=self.colors["background"])
            # Add more UI updates as needed
            
            settings_window.destroy()
            
        save_btn = ctk.CTkButton(
            settings_window,
            text="Save Settings",
            command=save_settings,
            fg_color=self.colors["accent"]
        )
        save_btn.pack(pady=20)

    def display_error(self, message):
        """Display error in the summary text box"""
        self.summary_text.configure(state="normal")
        self.summary_text.delete("1.0", "end")
        self.summary_text.insert("1.0", f"❌ Error:\n\n{message}")
        self.summary_text.configure(state="disabled")
        self.status_label.configure(text="Error occurred", text_color=self.colors["error"])

    def get_domain(self, url):
        """Extract domain from URL"""
        try:
            return urlparse(url).netloc
        except Exception:
            # Fallback to simple splitting if urlparse fails
            domain = url.split('://')[1] if '://' in url else url
            return domain.split('/')[0]

    def load_history(self):
        """Load summary history from file"""
        try:
            if os.path.exists(self.history_file):
                with open(self.history_file, 'r', encoding='utf-8') as f:
                    self.history = json.load(f)
            else:
                self.history = []
        except Exception:
            self.history = []
            
    def save_history(self):
        """Save summary history to file"""
        try:
            with open(self.history_file, 'w', encoding='utf-8') as f:
                json.dump(self.history, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Error saving history: {e}")
            
    def generate_title(self, summary):
        """Generate a concise title for the summary using Groq API"""
        try:
            prompt = (
                "Generate a very short, concise title (max 40 characters) for this content. "
                "Make it descriptive but brief, like ChatGPT's conversation titles. "
                "Return only the title, nothing else.\n\n"
                f"Content: {summary[:500]}..."  # Send first 500 chars for context
            )
            
            chat_completion = self.client.chat.completions.create(
                messages=[
                    {
                        "role": "system",
                        "content": "You are a title generator. Generate very concise, descriptive titles."
                    },
                    {"role": "user", "content": prompt}
                ],
                model="mixtral-8x7b-32768",
                max_tokens=20,
                temperature=0.7
            )
            
            title = chat_completion.choices[0].message.content.strip('" ')
            return title[:40]  # Ensure max length
        except Exception as e:
            print(f"Error generating title: {e}")
            return "Untitled Summary"

    def add_to_history(self, url_or_text, summary):
        """Add a summary to history with a generated title"""
        title = self.generate_title(summary)
        
        history_entry = {
            "timestamp": datetime.now().isoformat(),
            "title": title,
            "source": url_or_text[:200] + "..." if len(url_or_text) > 200 else url_or_text,
            "summary": summary
        }
        self.history.insert(0, history_entry)  # Add to start of list
        if len(self.history) > 100:  # Keep only last 100 entries
            self.history = self.history[:100]
        self.save_history()

    def show_history(self):
        """Show history with sliding animation"""
        # Clear existing history items
        for widget in self.history_scroll.winfo_children():
            widget.destroy()
        
        # Ensure history panel is on top
        self.history_panel.lift()
        
        if not self.history:
            # Show message when history is empty
            empty_label = ctk.CTkLabel(
                self.history_scroll,
                text="No history entries yet",
                font=("Helvetica", 16),
                text_color=self.colors["subtext"]
            )
            empty_label.pack(pady=20)
        else:
            # Add debug print to verify history content
            print(f"Loading {len(self.history)} history entries")
            
            # Populate history items
            for i, entry in enumerate(self.history):
                entry_frame = ctk.CTkFrame(self.history_scroll, fg_color=self.colors["background"])
                entry_frame.pack(fill="x", pady=5, padx=5)
                
                # Add title with larger font
                title_label = ctk.CTkLabel(
                    entry_frame,
                    text=entry.get("title", "Untitled Summary"),
                    font=("Arial", 16, "bold"),
                    text_color=self.colors["accent"]
                )
                title_label.pack(anchor="w", padx=10, pady=(10, 5))
                
                # Add timestamp
                try:
                    date_str = datetime.fromisoformat(entry["timestamp"]).strftime("%Y-%m-%d %H:%M")
                except:
                    date_str = "Unknown date"
                
                date_label = ctk.CTkLabel(
                    entry_frame,
                    text=date_str,
                    font=("Arial", 12),
                    text_color=self.colors["subtext"]
                )
                date_label.pack(anchor="w", padx=10, pady=(0, 5))
                
                # Add source with icon
                source_label = ctk.CTkLabel(
                    entry_frame,
                    text=f"🔗 {entry.get('source', 'Unknown')}",
                    font=("Arial", 12),
                    wraplength=700
                )
                source_label.pack(anchor="w", padx=10, pady=5)
                
                # Add summary preview with icon
                summary_preview = entry.get("summary", "")[:200] + "..." if len(entry.get("summary", "")) > 200 else entry.get("summary", "")
                summary_label = ctk.CTkLabel(
                    entry_frame,
                    text=f"📝 {summary_preview}",
                    font=("Arial", 12),
                    wraplength=700,
                    justify="left"
                )
                summary_label.pack(anchor="w", padx=10, pady=5)
                
                # Button frame for actions
                btn_frame = ctk.CTkFrame(entry_frame, fg_color="transparent")
                btn_frame.pack(fill="x", padx=10, pady=(5, 10))
                
                # Copy button
                copy_btn = ctk.CTkButton(
                    btn_frame,
                    text="📋 Copy Full Summary",
                    width=150,
                    command=lambda s=entry.get("summary", ""): self.copy_to_clipboard(s)
                )
                copy_btn.pack(side="left", padx=5)
                
                # Delete button
                delete_btn = ctk.CTkButton(
                    btn_frame,
                    text="🗑️ Delete",
                    width=100,
                    fg_color=self.colors["error"],
                    hover_color="#FF3333",
                    command=lambda idx=i: self.delete_history_entry(idx)
                )
                delete_btn.pack(side="left", padx=5)
        
        # Animate panel sliding up
        self.animate_panel_slide(True)

    def hide_history(self):
        """Hide history with sliding animation"""
        self.animate_panel_slide(False)

    def animate_panel_slide(self, show):
        """Animate the history panel sliding up or down"""
        target_y = 0.1 if show else 1.0
        current_y = float(self.history_panel.place_info()['rely'])
        steps = 20
        
        def animate_step(current_step):
            if current_step <= steps:
                progress = current_step / steps
                if not show:
                    progress = 1 - progress
                new_y = 1.0 - (0.9 * progress)
                self.history_panel.place_configure(rely=new_y)
                self.window.after(10, lambda: animate_step(current_step + 1))
        
        animate_step(1)

    def delete_history_entry(self, index):
        """Delete a specific history entry with animation"""
        if 0 <= index < len(self.history):
            # Show loading animation
            self.loading_label.configure(text="Deleting entry...")
            
            def animate_deletion():
                dots = [".", "..", "..."]
                current_dot = 0
                
                def update_dots():
                    nonlocal current_dot
                    if self.loading_label.cget("text").startswith("Deleting"):
                        self.loading_label.configure(text=f"Deleting entry{dots[current_dot]}")
                        current_dot = (current_dot + 1) % len(dots)
                        self.window.after(300, update_dots)
                
                update_dots()
                
                # Simulate deletion process (you can adjust the time)
                self.window.after(1500, complete_deletion)
            
            def complete_deletion():
                del self.history[index]
                self.save_history()
                self.loading_label.configure(text="Entry deleted!")
                self.window.after(1000, lambda: self.loading_label.configure(text=""))
                self.show_history()  # Refresh the history view
            
            animate_deletion()

    def clear_history(self):
        """Clear all history entries with animation"""
        confirm = ctk.CTkInputDialog(
            text="Type 'DELETE' to confirm clearing all history:",
            title="Confirm Clear History"
        )
        if confirm.get_input() == "DELETE":
            # Show loading animation
            self.loading_label.configure(text="Clearing all history...")
            
            def animate_clearing():
                dots = [".", "..", "..."]
                current_dot = 0
                
                def update_dots():
                    nonlocal current_dot
                    if self.loading_label.cget("text").startswith("Clearing"):
                        self.loading_label.configure(text=f"Clearing all history{dots[current_dot]}")
                        current_dot = (current_dot + 1) % len(dots)
                        self.window.after(300, update_dots)
                
                update_dots()
                
                # Simulate clearing process
                self.window.after(2000, complete_clearing)
            
            def complete_clearing():
                self.history = []
                self.save_history()
                self.loading_label.configure(text="History cleared!")
                self.window.after(1000, lambda: self.loading_label.configure(text=""))
                self.hide_history()
            
            animate_clearing()
    
    def copy_to_clipboard(self, text):
        """Copy text to clipboard"""
        self.window.clipboard_clear()
        self.window.clipboard_append(text)
        self.window.update()

if __name__ == "__main__":
    app = SummarAI()
    app.run()
