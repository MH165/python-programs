# Python Programs Repository

A collection of practical Python utilities and tools for file processing, web browsing, text extraction, and system operations.

## Features

✨ **File Searching** - Search for specific words in text files  
🌐 **Web Browser Automation** - Open multiple websites with a single command  
📄 **PDF Text Extraction** - Extract highlighted text from PDF documents  
📧 **Email Automation** - Send emails programmatically

## Installation

```bash
git clone https://github.com/MH165/python-programs.git
cd python-programs
pip install -r requirements.txt
```

## Usage Guide

### File Search
```bash
python search.py filename.txt "search_word"
```

### Web Browser
```bash
python webBrowsing.py
```

### PDF Text Extraction
```bash
python extractMarkedText.py document.pdf
```

### Google Search
```bash
python googleSearch.py "query"
```

### Email Sender
```bash
python mail-sender.py
```

## Tools

| Script | Purpose |
|--------|---------|
| search.py | Search text in files |
| webBrowsing.py | Web browser automation |
| extractMarkedText.py | Extract PDF highlights |
| googleSearch.py | Google search launcher |
| mail-sender.py | Email automation |

## Requirements

- PyMuPDF==1.23.8
- fpdf==1.7.2
- pynput==1.7.6
