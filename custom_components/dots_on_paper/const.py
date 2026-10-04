"""Constants for Dots on Paper."""

from homeassistant.const import Platform

DOMAIN = "dots_on_paper"
PLATFORMS = (Platform.IMAGE, Platform.SENSOR, Platform.SELECT)
CONF_BASE_URL = "base_url"
CONF_API_TOKEN = "api_token"
CONF_PROFILE = "profile"
CONF_POLL_INTERVAL = "poll_interval"
CONF_FRAME_INTERVAL = "frame_interval"
DEFAULT_PROFILE = "trmnl_x"
DEFAULT_POLL_INTERVAL = 5
DEFAULT_FRAME_INTERVAL = 5
PROFILES = ("trmnl_x", "trmnl", "inkplate", "kindle", "oep_296", "oep_400")
CHARACTERS = ("artist", "curious", "bookish", "cool")
DISPLAY_MODES = ("last_reply", "full_conversation")
STATUSES = ("idle", "thinking", "answer", "error")
EVENT_DOT_REPLY = "dot_reply"
