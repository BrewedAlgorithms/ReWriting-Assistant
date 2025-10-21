# Quick Rewriter

A minimalist Windows utility for rewriting selected text on-the-fly using the OpenRouter API, triggered by a global hotkey.

## Features

- **Global Hotkey:** Select text anywhere and press `Ctrl+Shift+Q` to activate the rewrite window.
- **Custom Prompts:** Define and save reusable rewrite prompts (e.g., "Fix Grammar," "Make Professional").
- **Dynamic Instructions:** Type custom rewrite instructions for one-off tasks.
- **Automatic Paste:** The rewritten text is automatically copied to the clipboard and pasted back, replacing the original selection.
- **Modern UI:** A clean, modern interface built with CustomTkinter.

## Prerequisites

- Python 3.8+
- An [OpenRouter API key](https://openrouter.ai/keys)

## Installation

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/your-username/your-repository-name.git
    cd your-repository-name
    ```

2.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

3.  **Configure API Key:**
    -   Run the application once (`python quick_rewriter.py`). It will generate a `config.json` file.
    -   Open `config.json` and replace `"YOUR_OPENROUTER_API_KEY_HERE"` with your actual OpenRouter API key.
    -   Alternatively, launch the app and open the settings (⚙️) to add your key via the UI.

## Usage

### Running from Source

To run the application directly from the source code:

```bash
python quick_rewriter.py
```

The application will run in the background, listening for the hotkey.

### How to Use

1.  Select any text in any application.
2.  Press `Ctrl+Shift+Q`.
3.  In the popup window:
    -   Type a custom instruction (e.g., "Summarize this in one sentence") and press `Enter`.
    -   Or, type `/` to select from a list of pre-configured quick prompts.
4.  The rewritten text will automatically replace your selection.

### Building from Source

To compile the application into a standalone Windows executable and create an installer, run the `compile.bat` script. This requires [Inno Setup 6](https://jrsoftware.org/isinfo.php) to be installed.

```bash
./compile.bat
```

The final installer will be located in the `Output/` directory.

## Architecture (Brief)

This application is a single-file Python script using `customtkinter` for the GUI, `pynput` for global hotkey management, and the `requests` library to interact with the OpenRouter API.
