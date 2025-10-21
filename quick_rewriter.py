"""
# requirements.txt
# customtkinter==5.2.2
# pynput==1.7.6
# pyperclip==1.8.2
# requests==2.31.0

Quick Rewriter - Minimalist Windows Text Utility

This single-file script provides a borderless prompt window triggered by a
global hotkey (Ctrl+Shift+Q) to rewrite selected text using OpenRouter.
"""

from __future__ import annotations

import json
import os
import threading
import time
from typing import Any, Dict, List, Optional

import customtkinter as ctk
import pyperclip
import requests
from pynput.keyboard import Controller, Key, GlobalHotKeys


# ----------------------------
# Constants and file locations
# ----------------------------

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.path.join(BASE_DIR, "config.json")
PROMPTS_PATH = os.path.join(BASE_DIR, "prompts.json")


# -----------------
# Helper Functions
# -----------------

def load_config() -> Dict[str, Any]:
    """Load config.json; create with placeholder if missing."""
    if not os.path.exists(CONFIG_PATH):
        default = {"api_key": "YOUR_OPENROUTER_API_KEY_HERE"}
        save_config(default)
        return default
    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        # Reset to default if file is corrupted
        default = {"api_key": "YOUR_OPENROUTER_API_KEY_HERE"}
        save_config(default)
        return default


def save_config(data: Dict[str, Any]) -> None:
    """Persist config to config.json."""
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def _default_prompts() -> List[Dict[str, str]]:
    return [
        {
            "name": "Professional Tone",
            "prompt": (
                "Rewrite the following text in a clear, formal, and professional business tone. "
                "Output ONLY the rewritten text with no preamble, explanation, or notes:\n\n{text}"
            ),
        },
        {
            "name": "Fix Grammar",
            "prompt": (
                "Correct any spelling and grammar mistakes in the following text. "
                "Output ONLY the corrected text with no explanations or notes:\n\n{text}"
            ),
        },
    ]


def load_prompts() -> List[Dict[str, str]]:
    """Load prompts.json; create with examples if missing."""
    if not os.path.exists(PROMPTS_PATH):
        defaults = _default_prompts()
        save_prompts(defaults)
        return defaults
    try:
        with open(PROMPTS_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
            if isinstance(data, list):
                return data
            return _default_prompts()
    except Exception:
        defaults = _default_prompts()
        save_prompts(defaults)
        return defaults


def save_prompts(data: List[Dict[str, str]]) -> None:
    """Persist prompts to prompts.json."""
    with open(PROMPTS_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


# --------------
# API Integration
# --------------

def _combine_prompt(captured_text: str, instruction_or_template: str) -> str:
    template = instruction_or_template or ""
    
    # Add strict instruction to avoid surrounding text
    strict_suffix = "\n\nIMPORTANT: Output ONLY the rewritten text. Do not add any explanations, preambles, notes, or surrounding text. Just the result."
    
    if "{text}" in template:
        try:
            return template.format(text=captured_text) + strict_suffix
        except Exception:
            # Fallback to concatenation if formatting fails
            return f"{template}\n\n{captured_text}" + strict_suffix
    else:
        return f"{template.strip()}\n\n{captured_text}".strip() + strict_suffix


def call_openrouter_api(captured_text: str, instruction_or_template: str) -> str:
    """Call OpenRouter with the final prompt and return first choice content."""
    cfg = load_config()
    api_key = cfg.get("api_key", "").strip()
    if not api_key or api_key == "YOUR_OPENROUTER_API_KEY_HERE":
        raise RuntimeError("OpenRouter API key missing. Set it in Settings (⚙️).")

    final_prompt = _combine_prompt(captured_text, instruction_or_template)

    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}",
    }
    json_data = {
        "model": "google/gemini-2.5-flash-preview-09-2025",
        "messages": [
            {"role": "user", "content": final_prompt},
        ],
    }

    response = requests.post(url, headers=headers, json=json_data, timeout=60)
    response.raise_for_status()
    data = response.json()
    choices = data.get("choices", [])
    if not choices:
        raise RuntimeError("No choices returned from OpenRouter.")
    content = choices[0].get("message", {}).get("content", "")
    if not content:
        raise RuntimeError("Empty response content from OpenRouter.")
    return content


# ---------
# GUI Layer
# ---------


class ManagementWindow(ctk.CTkToplevel):
    def __init__(self, master: ctk.CTk):
        super().__init__(master)
        self.title("Settings")

        # Open maximized
        try:
            self.state('zoomed')
        except Exception:
            w, h = self.winfo_screenwidth(), self.winfo_screenheight()
            self.geometry(f"{w}x{h}+0+0")
            
        self.resizable(True, True)
        self.minsize(800, 600)

        # Modern styling
        self.configure(fg_color=("#0f0f0f", "#0f0f0f"))

        self.config_data = load_config()
        self.prompts = load_prompts()

        self._build_ui()

        # Ensure window appears on top
        self.lift()
        self.focus_force()
        
        self.grab_set()

    def _build_ui(self) -> None:
        # Main container with transparent background
        container = ctk.CTkFrame(self, fg_color="transparent")
        container.pack(fill="both", expand=True, padx=20, pady=20)

        # Title
        title_font = ctk.CTkFont(family="SF Pro Display", size=24, weight="bold")
        title = ctk.CTkLabel(
            container,
            text="⚙ Settings",
            font=title_font,
            text_color=("#ffffff", "#ffffff")
        )
        title.pack(anchor="w", pady=(0, 20))

        # API Key Card
        api_card = ctk.CTkFrame(
            container,
            fg_color=("#1a1a1a", "#1a1a1a"),
            corner_radius=16,
            border_width=1,
            border_color=("#2a2a2a", "#2a2a2a")
        )
        api_card.pack(fill="x", pady=(0, 16))
        
        api_inner = ctk.CTkFrame(api_card, fg_color="transparent")
        api_inner.pack(fill="x", padx=16, pady=16)
        
        label_font = ctk.CTkFont(family="SF Pro Text", size=12, weight="bold")
        api_label = ctk.CTkLabel(
            api_inner,
            text="OPENROUTER API KEY",
            font=label_font,
            text_color=("#6b7280", "#6b7280")
        )
        api_label.pack(anchor="w", pady=(0, 8))
        
        entry_font = ctk.CTkFont(family="SF Mono", size=13)
        self.api_entry = ctk.CTkEntry(
            api_inner,
            height=40,
            corner_radius=10,
            border_width=0,
            fg_color=("#2a2a2a", "#2a2a2a"),
            text_color=("#ffffff", "#ffffff"),
            font=entry_font,
            placeholder_text="sk-or-v1-..."
        )
        self.api_entry.insert(0, self.config_data.get("api_key", ""))
        self.api_entry.pack(fill="x", pady=(0, 10))
        
        api_save_btn = ctk.CTkButton(
            api_inner,
            text="Save API Key",
            height=36,
            corner_radius=10,
            fg_color=("#3b82f6", "#3b82f6"),
            hover_color=("#2563eb", "#2563eb"),
            font=ctk.CTkFont(family="SF Pro Text", size=13, weight="bold"),
            command=self._save_api_key
        )
        api_save_btn.pack(fill="x")

        # Prompts section header
        header = ctk.CTkFrame(container, fg_color="transparent")
        header.pack(fill="x", pady=(8, 12))
        
        prompts_label = ctk.CTkLabel(
            header,
            text="QUICK PROMPTS",
            font=label_font,
            text_color=("#6b7280", "#6b7280")
        )
        prompts_label.pack(side="left")
        
        add_btn = ctk.CTkButton(
            header,
            text="+ Add",
            width=80,
            height=32,
            corner_radius=10,
            fg_color=("#3b82f6", "#3b82f6"),
            hover_color=("#2563eb", "#2563eb"),
            font=ctk.CTkFont(family="SF Pro Text", size=12, weight="bold"),
            command=self._add_prompt
        )
        add_btn.pack(side="right")

        # Scrollable prompt list with cards (expands to fill available space)
        self.list_frame = ctk.CTkScrollableFrame(
            container,
            fg_color="transparent",
            scrollbar_button_color=("#3b82f6", "#3b82f6"),
            scrollbar_button_hover_color=("#2563eb", "#2563eb")
        )
        self.list_frame.pack(fill="both", expand=True, pady=(0, 0))

        self._refresh_prompt_list()

    def _save_api_key(self) -> None:
        self.config_data["api_key"] = self.api_entry.get().strip()
        save_config(self.config_data)

    def _refresh_prompt_list(self) -> None:
        for child in self.list_frame.winfo_children():
            child.destroy()

        name_font = ctk.CTkFont(family="SF Pro Text", size=14, weight="bold")
        desc_font = ctk.CTkFont(family="SF Pro Text", size=11)
        
        for idx, p in enumerate(self.prompts):
            # iOS-style card for each prompt
            card = ctk.CTkFrame(
                self.list_frame,
                fg_color=("#1a1a1a", "#1a1a1a"),
                corner_radius=12,
                border_width=1,
                border_color=("#2a2a2a", "#2a2a2a")
            )
            card.pack(fill="x", pady=6)
            
            # Inner container
            inner = ctk.CTkFrame(card, fg_color="transparent")
            inner.pack(fill="x", padx=12, pady=12)
            
            # Left side - name and preview
            left = ctk.CTkFrame(inner, fg_color="transparent")
            left.pack(side="left", fill="x", expand=True)
            
            name_label = ctk.CTkLabel(
                left,
                text=p.get("name", "(unnamed)"),
                font=name_font,
                text_color=("#ffffff", "#ffffff"),
                anchor="w"
            )
            name_label.pack(anchor="w")
            
            # Show preview of prompt (first 60 chars)
            prompt_text = p.get("prompt", "")[:60] + "..." if len(p.get("prompt", "")) > 60 else p.get("prompt", "")
            preview_label = ctk.CTkLabel(
                left,
                text=prompt_text,
                font=desc_font,
                text_color=("#6b7280", "#6b7280"),
                anchor="w"
            )
            preview_label.pack(anchor="w", pady=(4, 0))
            
            # Right side - action buttons
            right = ctk.CTkFrame(inner, fg_color="transparent")
            right.pack(side="right")
            
            edit_btn = ctk.CTkButton(
                right,
                text="Edit",
                width=70,
                height=32,
                corner_radius=8,
                fg_color=("#2a2a2a", "#2a2a2a"),
                hover_color=("#3a3a3a", "#3a3a3a"),
                font=ctk.CTkFont(family="SF Pro Text", size=12),
                command=lambda i=idx: self._edit_prompt(i)
            )
            edit_btn.pack(side="left", padx=4)

            del_btn = ctk.CTkButton(
                right,
                text="Delete",
                width=70,
                height=32,
                corner_radius=8,
                fg_color=("#dc2626", "#dc2626"),
                hover_color=("#b91c1c", "#b91c1c"),
                font=ctk.CTkFont(family="SF Pro Text", size=12),
                command=lambda i=idx: self._delete_prompt(i)
            )
            del_btn.pack(side="left", padx=4)

    def _add_prompt(self) -> None:
        self._open_prompt_editor()

    def _edit_prompt(self, index: int) -> None:
        self._open_prompt_editor(index=index)

    def _delete_prompt(self, index: int) -> None:
        if 0 <= index < len(self.prompts):
            del self.prompts[index]
            save_prompts(self.prompts)
            self._refresh_prompt_list()

    def _open_prompt_editor(self, index: Optional[int] = None) -> None:
        editor = ctk.CTkToplevel(self)
        editor.title("Edit Prompt" if index is not None else "New Prompt")
        editor.geometry("680x480")
        editor.resizable(False, False)
        editor.configure(fg_color=("#0f0f0f", "#0f0f0f"))
        editor.grab_set()

        frame = ctk.CTkFrame(editor, fg_color="transparent")
        frame.pack(fill="both", expand=True, padx=20, pady=20)

        # Title
        title_font = ctk.CTkFont(family="SF Pro Display", size=20, weight="bold")
        title = ctk.CTkLabel(
            frame,
            text="✏ Edit Prompt" if index is not None else "✨ New Prompt",
            font=title_font,
            text_color=("#ffffff", "#ffffff")
        )
        title.pack(anchor="w", pady=(0, 20))

        # Name field
        label_font = ctk.CTkFont(family="SF Pro Text", size=12, weight="bold")
        name_label = ctk.CTkLabel(
            frame,
            text="PROMPT NAME",
            font=label_font,
            text_color=("#6b7280", "#6b7280")
        )
        name_label.pack(anchor="w", pady=(0, 6))
        
        name_entry = ctk.CTkEntry(
            frame,
            height=40,
            corner_radius=10,
            border_width=0,
            fg_color=("#1a1a1a", "#1a1a1a"),
            text_color=("#ffffff", "#ffffff"),
            font=ctk.CTkFont(family="SF Pro Text", size=14),
            placeholder_text="e.g., Professional Tone"
        )
        name_entry.pack(fill="x", pady=(0, 16))

        # Prompt field
        prompt_label = ctk.CTkLabel(
            frame,
            text="PROMPT TEMPLATE (must include {text})",
            font=label_font,
            text_color=("#6b7280", "#6b7280")
        )
        prompt_label.pack(anchor="w", pady=(0, 6))
        
        prompt_text = ctk.CTkTextbox(
            frame,
            height=230,
            corner_radius=10,
            border_width=0,
            fg_color=("#1a1a1a", "#1a1a1a"),
            text_color=("#ffffff", "#ffffff"),
            font=ctk.CTkFont(family="SF Mono", size=12)
        )
        prompt_text.pack(fill="both", expand=True, pady=(0, 16))

        def save_and_close() -> None:
            name_val = name_entry.get().strip()
            prompt_val = prompt_text.get("1.0", "end").strip()

            # Be forgiving: if name empty, use a default
            if not name_val:
                name_val = "Untitled Prompt"

            # If {text} placeholder missing, append it automatically
            if "{text}" not in prompt_val:
                prompt_val = (prompt_val.rstrip() + "\n\n{text}").strip()
            if index is None:
                self.prompts.append({"name": name_val, "prompt": prompt_val})
            else:
                self.prompts[index] = {"name": name_val, "prompt": prompt_val}
            save_prompts(self.prompts)
            self._refresh_prompt_list()
            editor.destroy()

        # Pre-fill for edit
        if index is not None and 0 <= index < len(self.prompts):
            name_entry.insert(0, self.prompts[index].get("name", ""))
            prompt_text.insert("1.0", self.prompts[index].get("prompt", ""))

        # Buttons
        buttons = ctk.CTkFrame(frame, fg_color="transparent")
        buttons.pack(fill="x")
        
        cancel_btn = ctk.CTkButton(
            buttons,
            text="Cancel",
            height=40,
            corner_radius=10,
            fg_color=("#2a2a2a", "#2a2a2a"),
            hover_color=("#3a3a3a", "#3a3a3a"),
            font=ctk.CTkFont(family="SF Pro Text", size=13, weight="bold"),
            command=editor.destroy
        )
        cancel_btn.pack(side="left", fill="x", expand=True, padx=(0, 8))
        
        save_btn = ctk.CTkButton(
            buttons,
            text="Save Prompt",
            height=40,
            corner_radius=10,
            fg_color=("#3b82f6", "#3b82f6"),
            hover_color=("#2563eb", "#2563eb"),
            font=ctk.CTkFont(family="SF Pro Text", size=13, weight="bold"),
            command=save_and_close
        )
        save_btn.pack(side="right", fill="x", expand=True)


class PromptWindow(ctk.CTkToplevel):
    def __init__(self, master: ctk.CTk, captured_text: str, keyboard_controller: Controller, on_done: Optional[callable] = None):
        super().__init__(master)
        self.captured_text = captured_text
        self.on_done = on_done
        self.keyboard_controller = keyboard_controller
        self.prompt_select_mode = False
        self.prompts = load_prompts()
        self.name_to_prompt = {p["name"]: p["prompt"] for p in self.prompts}
        # Keep an alphabetically sorted list of prompt names for display and navigation
        self.sorted_prompt_names = sorted(self.name_to_prompt.keys(), key=lambda s: s.lower())
        self.selected_prompt_index = 0
        self._base_width = 650
        self._base_height = 70
        self._select_height = 280
        self._paste_executed = False  # Prevent double paste

        self.overrideredirect(True)
        # Removed -topmost so window doesn't stay above everything
        self.attributes("-alpha", 0.96)  # Slight transparency for glass effect
        self.geometry(self._center_geometry(self._base_width, self._base_height))

        self._build_ui()
        self._focus_entry()
        # Global key bindings
        self.bind("<Escape>", self._cancel)
        self.bind("<Return>", self._submit)

    def _center_geometry(self, width: int, height: int) -> str:
        self.update_idletasks()
        screen_w = self.winfo_screenwidth()
        screen_h = self.winfo_screenheight()
        x = int((screen_w - width) / 2)
        y = int((screen_h - height) / 2)
        return f"{width}x{height}+{x}+{y}"

    def _build_ui(self) -> None:
        # iOS-style glassmorphism outer frame
        outer = ctk.CTkFrame(
            self,
            corner_radius=20,
            border_width=1,
            border_color=("#3a3a3a", "#3a3a3a"),
            fg_color=("#1a1a1a", "#1a1a1a")
        )
        outer.pack(fill="both", expand=True, padx=2, pady=2)

        # Inner content with minimal padding
        inner = ctk.CTkFrame(outer, fg_color="transparent")
        inner.pack(fill="both", expand=True, padx=12, pady=10)

        # Top bar for entry and settings
        top_bar = ctk.CTkFrame(inner, fg_color="transparent")
        top_bar.pack(fill="x")

        # iOS-style entry field
        entry_font = ctk.CTkFont(family="SF Pro Text", size=14)
        self.entry = ctk.CTkEntry(
            top_bar,
            height=42,
            corner_radius=12,
            border_width=0,
            fg_color=("#2a2a2a", "#2a2a2a"),
            text_color=("#ffffff", "#ffffff"),
            placeholder_text="Ask anything or press / for Quick Prompts…",
            placeholder_text_color=("#6b7280", "#6b7280"),
            font=entry_font,
        )
        self.entry.pack(side="left", fill="x", expand=True, padx=(0, 8))
        self.entry.bind("<Return>", self._submit)
        self.entry.bind("<Escape>", self._cancel)
        self.entry.bind("<KeyRelease>", self._maybe_enter_prompt_select)

        # Status label in same row as entry (hidden initially)
        status_font = ctk.CTkFont(family="SF Pro Text", size=11)
        self.status_label = ctk.CTkLabel(
            top_bar,
            text="",
            font=status_font,
            text_color=("#fbbf24", "#fbbf24")
        )
        self.status_label.pack(side="left", padx=(8, 0))

        # Minimal settings button
        settings_btn = ctk.CTkButton(
            top_bar,
            text="⚙",
            width=28,
            height=28,
            corner_radius=14,
            fg_color=("#2a2a2a", "#2a2a2a"),
            hover_color=("#3a3a3a", "#3a3a3a"),
            font=ctk.CTkFont(size=13),
            command=self._open_settings
        )
        settings_btn.pack(side="right")

        # Quick Prompt selection UI (hidden by default) - iOS-style list
        self.select_frame = ctk.CTkFrame(inner, fg_color="transparent")
        
        label_font = ctk.CTkFont(family="SF Pro Text", size=11, weight="bold")
        self.select_label = ctk.CTkLabel(
            self.select_frame,
            text="⚡ QUICK PROMPTS",
            font=label_font,
            text_color=("#6b7280", "#6b7280")
        )
        self.select_label.pack(anchor="w", padx=4, pady=(8, 6))
        
        # Scrollable list container for prompts
        self.prompts_list_frame = ctk.CTkScrollableFrame(
            self.select_frame,
            fg_color=("#2a2a2a", "#2a2a2a"),
            corner_radius=12,
            height=180,
            scrollbar_button_color=("#3b82f6", "#3b82f6"),
            scrollbar_button_hover_color=("#2563eb", "#2563eb")
        )
        self.prompts_list_frame.pack(fill="both", expand=True, padx=4, pady=(0, 4))
        
        # Will populate with prompt buttons
        self.prompt_buttons = []
        self._build_prompt_list()

    def _build_prompt_list(self) -> None:
        """Build iOS-style list of prompt buttons (alphabetically sorted)."""
        # Clear any existing buttons
        for child in self.prompts_list_frame.winfo_children():
            child.destroy()

        prompt_names = list(self.sorted_prompt_names)
        button_font = ctk.CTkFont(family="SF Pro Text", size=13)
        
        for idx, name in enumerate(prompt_names):
            btn = ctk.CTkButton(
                self.prompts_list_frame,
                text=name,
                height=36,
                corner_radius=8,
                fg_color="transparent",
                hover_color=("#3a3a3a", "#3a3a3a"),
                text_color=("#ffffff", "#ffffff"),
                font=button_font,
                anchor="w",
                command=lambda i=idx: self._select_prompt(i)
            )
            btn.pack(fill="x", padx=4, pady=2)
            self.prompt_buttons.append(btn)
        
        # Highlight first item
        if self.prompt_buttons:
            self._highlight_prompt(0)

    def _highlight_prompt(self, index: int) -> None:
        """Highlight the selected prompt button."""
        for i, btn in enumerate(self.prompt_buttons):
            if i == index:
                btn.configure(
                    fg_color=("#3b82f6", "#3b82f6"),
                    text_color=("#ffffff", "#ffffff")
                )
            else:
                btn.configure(
                    fg_color="transparent",
                    text_color=("#ffffff", "#ffffff")
                )

    def _select_prompt(self, index: int) -> None:
        """Select a prompt by index."""
        self.selected_prompt_index = index
        self._highlight_prompt(index)

    def _focus_entry(self) -> None:
        self.after(50, lambda: (self.entry.focus_set(), self.entry.icursor("end")))

    def _open_settings(self) -> None:
        ManagementWindow(self)

    def _maybe_enter_prompt_select(self, _event=None) -> None:
        content = self.entry.get()
        if content.startswith("/") and not self.prompt_select_mode:
            self._enter_prompt_select(content)
        elif not content.startswith("/") and self.prompt_select_mode:
            self._exit_prompt_select()

    def _enter_prompt_select(self, content: str) -> None:
        self.entry.pack_forget()
        self.select_frame.pack(fill="both", expand=True, pady=(8, 0))
        self.prompt_select_mode = True
        # Grow window to show selection UI
        self._resize_window(self._base_width, self._select_height)
        
        # Add arrow key bindings for navigation
        self.bind("<Up>", self._navigate_up)
        self.bind("<Down>", self._navigate_down)
        # Bind alpha keys for quick jump
        for ch in "abcdefghijklmnopqrstuvwxyz":
            self.bind(ch, self._jump_to_alpha)
        
        # Reset selection to first
        self.selected_prompt_index = 0
        self._highlight_prompt(0)

    def _exit_prompt_select(self, _event=None) -> None:
        if self.prompt_select_mode:
            self.select_frame.pack_forget()
            self.entry.pack(side="left", fill="x", expand=True, padx=(0, 8))
            self.prompt_select_mode = False
            self._focus_entry()
            # Shrink back to base height
            self._resize_window(self._base_width, self._base_height)
            # Remove arrow key bindings
            self.unbind("<Up>")
            self.unbind("<Down>")
            for ch in "abcdefghijklmnopqrstuvwxyz":
                self.unbind(ch)

    def _jump_to_alpha(self, event=None) -> None:
        """Jump to first prompt starting with pressed alphabet key."""
        if not self.prompt_select_mode or not event or not hasattr(event, "keysym"):
            return
        key = event.keysym.lower()
        if len(key) != 1 or not key.isalpha():
            return
        # Find first index whose name starts with the key
        for idx, name in enumerate(self.sorted_prompt_names):
            if name.lower().startswith(key):
                self.selected_prompt_index = idx
                self._highlight_prompt(idx)
                # Ensure visibility by scrolling near the button if needed
                try:
                    btn = self.prompt_buttons[idx]
                    self.prompts_list_frame._parent_canvas.yview_moveto(max(0, (btn.winfo_y() - 20) / max(1, self.prompts_list_frame.winfo_height())))
                except Exception:
                    pass
                break

    def _navigate_up(self, _event=None) -> None:
        """Navigate up in prompt list."""
        if self.prompt_select_mode and self.prompt_buttons:
            self.selected_prompt_index = (self.selected_prompt_index - 1) % len(self.prompt_buttons)
            self._highlight_prompt(self.selected_prompt_index)
            return "break"

    def _navigate_down(self, _event=None) -> None:
        """Navigate down in prompt list."""
        if self.prompt_select_mode and self.prompt_buttons:
            self.selected_prompt_index = (self.selected_prompt_index + 1) % len(self.prompt_buttons)
            self._highlight_prompt(self.selected_prompt_index)
            return "break"

    def _cancel(self, _event=None) -> None:
        self.destroy()

    def _submit(self, _event=None) -> None:
        if self.prompt_select_mode:
            # Get selected prompt from list by index
            prompt_names = list(self.name_to_prompt.keys())
            if 0 <= self.selected_prompt_index < len(prompt_names):
                selected_name = prompt_names[self.selected_prompt_index]
                template = self.name_to_prompt.get(selected_name, "")
                instruction = template
            else:
                return
        else:
            instruction = self.entry.get().strip()
        if not instruction:
            return

        self._set_status("⏳ Processing your request...")
        self._disable_inputs()
        self._pulse_status()

        def worker():
            try:
                result = call_openrouter_api(self.captured_text, instruction)
                pyperclip.copy(result)
                # Schedule window close on main thread
                self.after(0, self._finish_success)
                # Auto-paste in background after window closes
                time.sleep(0.25)  # Wait for window to close and focus to restore
                self._auto_paste()
            except Exception as e:
                msg = f"Error: {e}"
                pyperclip.copy(msg)
                self.after(0, lambda: self._finish_error(str(e)))

        threading.Thread(target=worker, daemon=True).start()

    def _disable_inputs(self) -> None:
        try:
            self.entry.configure(state="disabled")
        except Exception:
            pass
        try:
            for btn in self.prompt_buttons:
                btn.configure(state="disabled")
        except Exception:
            pass

    def _set_status(self, text: str) -> None:
        self.status_label.configure(text=text)

    def _pulse_status(self) -> None:
        """Simple pulsing animation for status text."""
        colors = [
            ("#fbbf24", "#fbbf24"),
            ("#f59e0b", "#f59e0b"),
            ("#fbbf24", "#fbbf24"),
            ("#f59e0b", "#f59e0b"),
        ]
        self._pulse_index = 0
        
        def pulse():
            if self.winfo_exists() and self.status_label.cget("text").startswith("⏳"):
                self.status_label.configure(text_color=colors[self._pulse_index % len(colors)])
                self._pulse_index += 1
                self.after(400, pulse)
        
        pulse()

    def _finish_success(self) -> None:
        # Close immediately on success
        if self.on_done:
            self.on_done()
        self.destroy()

    def _finish_error(self, err: str) -> None:
        try:
            if self.winfo_exists():
                self.status_label.configure(text_color=("#ef4444", "#ef4444"))
                self._set_status(f"❌ {err}")
                self.after(2000, self.destroy)
        except Exception:
            self.destroy()
        if self.on_done:
            self.on_done()

    def _resize_window(self, width: int, height: int) -> None:
        self.geometry(self._center_geometry(width, height))

    def _auto_paste(self) -> None:
        """Automatically paste the clipboard content using Ctrl+V."""
        # Check flag to prevent double execution
        if self._paste_executed:
            return
        self._paste_executed = True
        
        try:
            # This runs in the worker thread, window is already closed
            with self.keyboard_controller.pressed(Key.ctrl):
                self.keyboard_controller.press('v')
                self.keyboard_controller.release('v')
        except Exception:
            pass  # Silently fail if paste doesn't work


class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.withdraw()  # Root window stays hidden
        self.title("Quick Rewriter")
        self.protocol("WM_DELETE_WINDOW", self._on_close)

        # Preload or create data files
        load_config()
        load_prompts()

        self.keyboard_controller = Controller()
        self.current_prompt_window: Optional[PromptWindow] = None
        self._start_hotkey_listener()

    def _start_hotkey_listener(self) -> None:
        self.listener = GlobalHotKeys({
            '<ctrl>+<shift>+q': self._on_hotkey,
        })
        self.listener.start()

    def _on_hotkey(self) -> None:
        # Runs in listener thread
        captured = self._capture_selected_text()
        if not captured:
            return
        self.after(0, lambda: self._open_prompt_window(captured))

    def _capture_selected_text(self) -> str:
        try:
            # Ensure Shift isn't held so Chrome doesn't see Ctrl+Shift+C (Inspect)
            for k in (getattr(Key, 'shift', None), getattr(Key, 'shift_l', None), getattr(Key, 'shift_r', None)):
                if k is not None:
                    try:
                        self.keyboard_controller.release(k)
                    except Exception:
                        pass
            time.sleep(0.02)
            with self.keyboard_controller.pressed(Key.ctrl):
                self.keyboard_controller.press('c')
                self.keyboard_controller.release('c')
            time.sleep(0.12)
            text = pyperclip.paste()
            return text if isinstance(text, str) else ""
        except Exception:
            return ""

    def _open_prompt_window(self, captured_text: str) -> None:
        if self.current_prompt_window and self.current_prompt_window.winfo_exists():
            try:
                self.current_prompt_window.lift()
                self.current_prompt_window.focus_force()
                return
            except Exception:
                pass

        def on_done() -> None:
            self.current_prompt_window = None

        self.current_prompt_window = PromptWindow(self, captured_text, self.keyboard_controller, on_done=on_done)
        self.current_prompt_window.lift()
        self.current_prompt_window.focus_force()

    def open_settings(self) -> None:
        ManagementWindow(self)

    def _on_close(self) -> None:
        try:
            self.listener.stop()
        except Exception:
            pass
        self.destroy()


def main() -> None:
    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("blue")

    app = App()
    app.mainloop()


if __name__ == "__main__":
    main()


