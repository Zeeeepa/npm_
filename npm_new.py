"""NPM Package Analyzer Pro - Ultimate Edition
A comprehensive tool for discovering, analyzing, and downloading NPM packages
with advanced features, proper markdown rendering, and high-performance concurrency."""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog, scrolledtext
import requests
import requests.adapters
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import json
import sqlite3
import os
import subprocess
import threading
import concurrent.futures
import datetime
import time
import random
import logging
from logging.handlers import RotatingFileHandler
from typing import Dict, List, Optional, Tuple, Union, Sequence, Callable, Any, cast, Set
from dataclasses import dataclass, asdict, field
import platform
import sys
import re
from urllib.parse import urlparse, urljoin
import webbrowser
import configparser
import markdown
from markdown.extensions.codehilite import CodeHiliteExtension
from markdown.extensions.fenced_code import FencedCodeExtension
from markdown.extensions.tables import TableExtension
from markdown.extensions.toc import TocExtension
from markdown.extensions.extra import ExtraExtension
import html
import base64
from bs4 import BeautifulSoup
import queue
import hashlib
import zlib
from functools import lru_cache, partial
import tkinter.font as tkfont
import mimetypes
import tempfile
import shutil
from pathlib import Path
import humanize
import dateutil.parser
from dateutil.relativedelta import relativedelta
import tarfile
import zipfile
import io

# Configure logging with rotation
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        RotatingFileHandler('npm_analyzer.log', maxBytes=5*1024*1024, backupCount=2),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Configuration constants
CACHE_DB = "npm_cache.db"
SEARCH_HISTORY_DB = "search_history.db"
SETTINGS_FILE = "npm_analyzer_settings.ini"
CACHE_TTL_DAYS = 7
DEFAULT_MAX_CONCURRENT_REQUESTS = 40  # Increased from 20 to 40
REQUEST_TIMEOUT = 30
DEFAULT_MAX_RESULTS = 50000
MAX_SEARCH_HISTORY = 20
DEFAULT_DOWNLOAD_DIR = os.path.join(os.path.expanduser("~"), "npm_packages")
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"

# Platform detection
IS_WINDOWS = platform.system() == "Windows"
IS_MAC = platform.system() == "Darwin"
IS_LINUX = platform.system() == "Linux"

# Modern Dark Theme with additional colors
class Theme:
    BG = "#0D1117"
    BG_SECONDARY = "#161B22"
    BG_TERTIARY = "#21262D"
    BG_HOVER = "#30363D"
    BG_INPUT = "#010409"
    TEXT = "#E6EDF3"
    TEXT_SECONDARY = "#8B949E"
    TEXT_MUTED = "#6E7681"
    ACCENT = "#58A6FF"
    ACCENT_DARK = "#1F6FEB"
    SUCCESS = "#3FB950"
    SUCCESS_DARK = "#2EA043"
    WARNING = "#D29922"
    WARNING_DARK = "#B3881E"
    ERROR = "#F85149"
    ERROR_DARK = "#DA3633"
# ... File continuation ...
