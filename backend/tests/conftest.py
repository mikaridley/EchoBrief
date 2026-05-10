"""Pytest hooks: keep tests from picking up MONGO_URI / auth from a dev .env."""

import os

os.environ['MONGO_URI'] = ''
os.environ['AUTH_ENABLED'] = '0'

from app.core.config import get_settings

get_settings.cache_clear()
