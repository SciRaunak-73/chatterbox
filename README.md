# ChatterBox - Secure Chat Application

A secure web-based chat application with end-to-end encryption and various features for intimate communication.

## Features

- End-to-End Encryption
- Custom Emojis and Stickers
- Voice Notes and Image Sharing
- Secret Diary Section
- Scheduled Messages

## Setup Instructions

1. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up the database:
```bash
python manage.py migrate
```

4. Create a superuser:
```bash
python manage.py createsuperuser
```

5. Run the development server:
```bash
python manage.py runserver
```

## Security Note

This application uses strong encryption for all messages. Make sure to keep your encryption keys safe and never share them with anyone. 