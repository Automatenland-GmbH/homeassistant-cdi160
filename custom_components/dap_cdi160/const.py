"""Constants for the DAP CDI160-BT Audio Player integration."""

DOMAIN = "dap_cdi160"

# Configuration keys
CONF_HOST = "host"
CONF_NAME = "name"

# Default values
DEFAULT_NAME = "DAP CDI160 Audio Player"
DEFAULT_SCAN_INTERVAL = 5  # seconds

# API endpoints
ENDPOINT_GET_PLAYING = "/php/getPlaying.php"
ENDPOINT_VOLUME = "/php/webChVol.php"
ENDPOINT_PRESET = "/php/webListenP.php"

# Volume settings
VOLUME_UP = 1
VOLUME_DOWN = -1
VOLUME_MUTE = 128
