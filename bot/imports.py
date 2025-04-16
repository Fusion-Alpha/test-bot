import os
import json
import time
import asyncio
from typing import Dict, List, Optional, Union, Tuple, Any

# Third-party imports
import aiohttp
from bs4 import BeautifulSoup, SoupStrainer
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from aiogram.filters import Command
from aiogram.filters.command import CommandObject
from aiogram.client.default import DefaultBotProperties

# Module-specific common imports
# Config constants used across modules
from bot.config import CHAT_ID, ENABLE_REPEAT_NOTIFICATION, DEFAULT_REPEAT_INTERVAL

# Storage functions used across modules
from bot.storage import storage, save_website_data, save_last_number

# UI and utility functions used across modules
from bot.utils import format_time, delete_message_after_delay, parse_website_content, fetch_url_content

# Notification functions used across modules
from bot.notifications import get_buttons, get_multiple_buttons, add_countdown_to_latest_notification, update_message_with_countdown, send_notification

# Additional monitoring imports
from bot.monitoring import WebsiteMonitor, monitor_websites

# Handler functions
from bot.handlers import register_handlers, send_startup_message

# Additional config constants
from bot.config import TELEGRAM_BOT_TOKEN, load_website_configs

# Additional storage functions
from bot.storage import load_website_data
