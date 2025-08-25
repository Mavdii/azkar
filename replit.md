# Overview

This is a Telegram bot for Islamic remembrance (Azkar) that automatically activates in groups when added. The bot sends random Islamic remembrances every 5 minutes, alternating between text, images, voice messages, and audio files from various folders. It also sends morning and evening remembrance images at scheduled times, provides prayer time notifications for Cairo, and includes prayer reminders 5 minutes before each prayer time. Features an advanced button-based admin panel for content management restricted to developer ID 7089656746.

# User Preferences

Preferred communication style: Simple, everyday language.

# System Architecture

## Bot Framework
- **Telegram Bot API**: Uses python-telegram-bot library for handling Telegram interactions
- **Async Architecture**: Built with asyncio for handling concurrent operations and scheduled tasks
- **Auto-activation**: Automatically activates in groups upon being added without manual setup

## Scheduling System
- **APScheduler**: Uses AsyncIOScheduler for time-based message scheduling
- **Cairo Timezone**: All scheduling operates on Africa/Cairo timezone for prayer times
- **Multiple Schedule Types**:
  - Every 5 minutes for random azkar
  - Specific times for morning/evening reminders (5:30, 7:00, 8:00 AM/PM)
  - Prayer time notifications (5 minutes before each prayer)

## Content Management
- **4-Way Content Rotation**: Implements turn-based system alternating between text, images, voice messages, and audio files
- **Message Cleanup**: Automatically deletes previous messages before sending new ones
- **Multi-source Content**:
  - Text azkar from `Azkar.txt` file (separated by "---")
  - Random images from `random/` folder
  - Voice messages from `voices/` folder
  - Audio files from `audios/` folder
  - Morning azkar images from `morning/` folder
  - Evening azkar images from `evening/` folder
  - Prayer-related images from `prayers/` folder
- **Metadata Storage**: Each media file has corresponding `.info` file with caption and creation details

## Group Management
- **Active Group Tracking**: Maintains set of active groups for message broadcasting
- **Message ID Tracking**: Stores last message IDs for deletion before sending new content
- **Universal Inline Keyboard**: All messages include "تلاوات قرانية - أجر" button linking to Quran recitation channel

## Admin Panel System
- **Button-Based Interface**: Modern interactive admin panel accessible via `/admin` command
- **Restricted Access**: Limited to developer ID 7089656746 only
- **Content Management Features**:
  - Add text azkar with immediate integration
  - Upload images, voice messages, audio files, and documents
  - Interactive caption/description system for media files
  - Real-time content statistics and overview
  - File type auto-detection and proper folder placement
- **State Management**: Tracks admin sessions for seamless multi-step operations
- **Error Handling**: Comprehensive error handling with user-friendly messages

## Prayer Time Integration
- **Aladhan API**: Fetches prayer times from api.aladhan.com for Cairo
- **Method 8**: Uses Egyptian General Authority of Survey calculation method
- **5-Minute Warnings**: Sends detailed Islamic reminders about prayer importance before each prayer

## Data Storage
- **File-based Configuration**: Uses text files for azkar content and placeholder files for image folders
- **In-memory State**: Maintains bot state (active groups, last messages, turn tracking) in memory
- **No Database**: Simple file-based approach without external database dependencies

## Error Handling & Logging
- **Comprehensive Logging**: Uses Python logging module for debugging and monitoring
- **Graceful Degradation**: Handles missing files or API failures without crashing

# External Dependencies

## APIs
- **Aladhan Prayer Times API**: `https://api.aladhan.com/v1/timingsByCity/` for Cairo prayer times using method 8 (Egyptian General Authority of Survey)

## Python Libraries
- **python-telegram-bot**: Telegram Bot API wrapper
- **APScheduler**: Advanced Python Scheduler for time-based tasks
- **pytz**: Timezone handling (Africa/Cairo)
- **requests**: HTTP requests for prayer times API
- **asyncio**: Asynchronous programming support

## Media Resources
- **Image Folders**: Requires PNG/JPG images in morning/, evening/, random/, and prayers/ directories
- **Text Content**: Azkar.txt file containing Arabic remembrances separated by "---"

## External Links
- **Telegram Channel**: Links to `https://t.me/Telawat_Quran_0` for Quran recitations

## Environment Variables
- **TELEGRAM_BOT_TOKEN**: Required bot token from Telegram BotFather