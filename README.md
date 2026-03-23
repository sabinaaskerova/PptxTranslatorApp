# PptxTranslatorApp

An application that translates PowerPoint presentations while preserving the original slide formatting and layout. 

## How It Works

1. Upload a `.pptx` file
2. Select source and target languages
3. Download the translated presentation with formatting intact

## Structure

- `app.py` — Flask web server handling file uploads and download routes
- `translator.py` — translation logic, slide text extraction, and reinsertion
- `utils.py` — helper functions for PPTX parsing and text manipulation
- `templates/` — HTML frontend for the upload interface

## Tech

Python · Flask · python-pptx · OPUS Machine Translation · HTML/CSS · Deployed on Vercel
