"""Constants for the DAP CDI160-BT Audio Player integration."""

DOMAIN = "dap_cdi160"

# Configuration keys
CONF_HOST = "host"
CONF_NAME = "name"

# Default values
DEFAULT_NAME = "DAP CDI160 Audio Player"
DEFAULT_SCAN_INTERVAL = 30  # seconds

# API endpoints
ENDPOINT_GET_PLAYING = "/php/getPlaying.php"
ENDPOINT_GET_PRESETS = "/php/getPre.php"
ENDPOINT_VOLUME = "/php/webChVol.php"
ENDPOINT_PRESET = "/php/webListenP.php"
ENDPOINT_FAVORITE = "/php/webListen.php"

# Volume settings
VOLUME_UP = 1
VOLUME_DOWN = -1
VOLUME_MUTE = 128
VOLUME_MIN = 0
VOLUME_MAX = 5  # Device reports volume on 0-5 scale

# Favorite/Preset limits
MAX_FAVORITES = 10  # Number of favorites to expose (1-10)
MAX_PRESETS = 4  # Number of presets (1-4)
