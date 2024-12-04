# XSPF Maker Telegram Bot

## Project Overview

A sophisticated Telegram bot that streamlines video file management and streaming across group and private chats using advanced cloud storage integration.

## Key Features

- 🤖 **Telegram Bot Integration**
  - Generate XSPF playlist files for video uploads
  - Support for both group and private chat interactions
  - Advanced command handling (/nokate, /find, /xspf)

- 🗂️ **Google Drive File Management**
  - Seamless file search and retrieval
  - Secure authentication via service account
  - Pagination and inline keyboard navigation

- 🎬 **Video Streaming Optimization**
  - Convert video files to VLC-compatible XSPF playlists
  - Enable streaming of large video files
  - Cross-platform compatibility

## Demo

### Bot Interaction in Telegram
<video controls src="screenshots\1.mp4" title="Title"></video>


https://github.com/user-attachments/assets/eee6f472-e734-41f9-be4c-16dfc958f2aa


### File Search Interface
<video controls src="screenshots\2.mp4" title="Title"></video>


https://github.com/user-attachments/assets/af1c32c6-0401-43e5-919b-1daaf98f96bd


### XSPF Playlist Generation
<video controls src="screenshots\3.mp4" title="Title"></video>


https://github.com/user-attachments/assets/65455f98-7178-4fc5-b057-3094d6bde9d6



## Technical Architecture

### Technologies
- **Languages**: Python
- **APIs**: 
  - Telegram Bot API
  - Google Drive API
- **Authentication**: OAuth 2.0 Service Account
- **Libraries**: 
  - python-telegram-bot
  - google-api-python-client

### System Design
```
Telegram Bot (app.py)
│
├── File Upload Handling
├── XSPF Playlist Generation
├── Google Drive Integration (upload.py)
│   ├── Credentials Management
│   ├── File Search
│   └── Download/Upload Mechanisms
│
└── Interactive User Interface
    ├── Inline Keyboards
    └── Pagination Support
```

## Usage Examples

### Generate XSPF Playlist
1. Send a video in a Telegram group
2. Reply with `/xspf`
3. Receive a playable XSPF file

### Search Files
- Use `/find <keyword>` to search video files
- Select from inline keyboard results

## Setup & Installation

1. Clone the repository
2. Install dependencies: `pip install -r requirements.txt`
3. Configure environment variables:
   - `TELEGRAM_TOKEN`
   - Google Drive service account credentials

## Deployment

- Supports local and cloud hosting
- Docker containerization recommended
- Continuous integration with GitHub Actions

## Performance Metrics

- **Scalability**: Handles multiple concurrent file requests
- **Latency**: Minimal overhead in file generation and retrieval
- **Security**: Secure, token-based authentication

## Future Roadmap

- [ ] Enhanced file preview capabilities
- [ ] Multi-cloud storage support
- [ ] Advanced search and filtering

## Contributions

Contributions are welcome! Please read the contributing guidelines and submit pull requests.
