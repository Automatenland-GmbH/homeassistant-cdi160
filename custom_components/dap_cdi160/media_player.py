"""Support for DAP CDI160-BT Audio Player."""
import logging
from typing import Any

import aiohttp

from homeassistant.components.media_player import (
    BrowseMedia,
    MediaPlayerEntity,
    MediaPlayerEntityFeature,
    MediaPlayerState,
    MediaClass,
    MediaType,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, CONF_NAME
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import (
    DEFAULT_NAME,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
    ENDPOINT_FAVORITE,
    ENDPOINT_GET_PLAYING,
    ENDPOINT_PRESET,
    ENDPOINT_VOLUME,
    MAX_FAVORITES,
    MAX_PRESETS,
    VOLUME_DOWN,
    VOLUME_MUTE,
    VOLUME_UP,
)

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the DAP CDI160 media player from a config entry."""
    host = config_entry.data[CONF_HOST]
    name = config_entry.data.get(CONF_NAME, DEFAULT_NAME)

    # Ensure host starts with http:// or https://
    if not host.startswith("http://") and not host.startswith("https://"):
        host = f"http://{host}"

    session = async_get_clientsession(hass)
    player = DapCdi160MediaPlayer(hass, session, host, name, config_entry)
    async_add_entities([player], True)


class DapCdi160MediaPlayer(MediaPlayerEntity):
    """Representation of a DAP CDI160 Audio Player."""

    _attr_has_entity_name = True
    _attr_name = None

    def __init__(
        self,
        hass: HomeAssistant,
        session: aiohttp.ClientSession,
        host: str,
        name: str,
        config_entry: ConfigEntry,
    ) -> None:
        """Initialize the DAP CDI160 device."""
        self.hass = hass
        self._session = session
        self._host = host
        self._attr_unique_id = f"dap_cdi160_{host}"
        self._device_name = name
        self._config_entry = config_entry

        # State attributes
        self._state = MediaPlayerState.IDLE
        self._muted = False
        self._media_title = None
        self._media_artist = None
        self._in_favorite = False

        # Supported features
        self._attr_supported_features = (
            MediaPlayerEntityFeature.VOLUME_STEP
            | MediaPlayerEntityFeature.VOLUME_MUTE
            | MediaPlayerEntityFeature.SELECT_SOURCE
            | MediaPlayerEntityFeature.PAUSE
            | MediaPlayerEntityFeature.PLAY
            | MediaPlayerEntityFeature.STOP
            | MediaPlayerEntityFeature.BROWSE_MEDIA
            | MediaPlayerEntityFeature.PLAY_MEDIA
        )

        # Build source list with both presets and favorites
        self._source_list = []
        self._source_to_id = {}  # Map custom names to IDs

        # Add presets with custom names if available
        for i in range(1, MAX_PRESETS + 1):
            custom_name = config_entry.options.get(f"preset_{i}_name", f"Preset {i}")
            self._source_list.append(custom_name)
            self._source_to_id[custom_name] = ("preset", i)

        # Add favorites with custom names if available
        for i in range(1, MAX_FAVORITES + 1):
            custom_name = config_entry.options.get(f"favorite_{i}_name", f"Favorite {i}")
            self._source_list.append(custom_name)
            self._source_to_id[custom_name] = ("favorite", i)

        self._current_source = None

    @property
    def device_info(self):
        """Return device information about this entity."""
        return {
            "identifiers": {(DOMAIN, self._host)},
            "name": self._device_name,
            "manufacturer": "DAP",
            "model": "CDI160-BT",
        }

    @property
    def state(self) -> MediaPlayerState:
        """Return the state of the device."""
        return self._state

    @property
    def is_volume_muted(self) -> bool:
        """Return boolean if volume is currently muted."""
        return self._muted

    @property
    def media_title(self) -> str | None:
        """Return the title of current playing media."""
        return self._media_title

    @property
    def media_artist(self) -> str | None:
        """Return the artist of current playing media."""
        return self._media_artist

    @property
    def source_list(self) -> list[str]:
        """Return the list of available input sources."""
        return self._source_list

    @property
    def source(self) -> str | None:
        """Return the current input source."""
        return self._current_source

    async def async_update(self) -> None:
        """Fetch new state data for the player."""
        url = f"{self._host}{ENDPOINT_GET_PLAYING}"
        try:
            async with self._session.get(
                url, timeout=aiohttp.ClientTimeout(total=10)
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    await self._process_playing_data(data)
                else:
                    _LOGGER.error(
                        "Failed to fetch status from %s: HTTP %s", url, response.status
                    )
                    self._state = MediaPlayerState.OFF
        except aiohttp.ClientError as err:
            _LOGGER.error("Error connecting to %s: %s", url, err)
            self._state = MediaPlayerState.OFF
        except Exception as err:
            _LOGGER.exception("Unexpected error updating DAP CDI160: %s", err)
            self._state = MediaPlayerState.OFF

    async def _process_playing_data(self, data: dict[str, Any]) -> None:
        """Process the playing data from the API."""
        mply_sta = data.get("mPlySta", [])
        self._muted = data.get("bMuted", False)
        self._in_favorite = data.get("bInFav", False)

        # Parse mPlySta array
        # Index 0: Title/Station name
        # Index 1: Artist/Additional info
        # Index 2: Play state description
        if len(mply_sta) > 0:
            self._media_title = mply_sta[0] if mply_sta[0] else None

        if len(mply_sta) > 1:
            self._media_artist = mply_sta[1] if mply_sta[1] else None

        if len(mply_sta) > 2:
            play_state_str = mply_sta[2].lower()
            if "playing" in play_state_str:
                self._state = MediaPlayerState.PLAYING
            elif "paused" in play_state_str:
                self._state = MediaPlayerState.PAUSED
            elif "stopped" in play_state_str:
                self._state = MediaPlayerState.IDLE
            else:
                self._state = MediaPlayerState.ON
        else:
            self._state = MediaPlayerState.ON

        # Override state based on mute status
        # If muted, show as paused (so play button appears)
        # If unmuted and playing, show as playing (so pause button appears)
        if self._muted:
            self._state = MediaPlayerState.PAUSED
        elif self._state in (MediaPlayerState.PAUSED, MediaPlayerState.ON):
            # If not muted but was paused/on, change to playing
            self._state = MediaPlayerState.PLAYING

    async def async_volume_up(self) -> None:
        """Volume up the media player."""
        await self._send_volume_command(VOLUME_UP)

    async def async_volume_down(self) -> None:
        """Volume down the media player."""
        await self._send_volume_command(VOLUME_DOWN)

    async def async_mute_volume(self, mute: bool) -> None:
        """Mute or unmute the media player."""
        if mute:
            await self._send_volume_command(VOLUME_MUTE)
        else:
            # Unmute by sending volume up command
            await self._send_volume_command(VOLUME_UP)

    async def async_media_play(self) -> None:
        """Send play command (unmute to resume playback)."""
        # Use volume up to unmute/resume playback
        await self._send_volume_command(VOLUME_UP)

    async def async_media_pause(self) -> None:
        """Send pause command (mute to pause playback)."""
        # Use volume mute to pause playback
        await self._send_volume_command(VOLUME_MUTE)

    async def async_media_stop(self) -> None:
        """Send stop command (mute to stop playback)."""
        # Use volume mute to stop playback
        await self._send_volume_command(VOLUME_MUTE)

    async def _send_volume_command(self, volume_value: int) -> None:
        """Send volume control command to the device."""
        url = f"{self._host}{ENDPOINT_VOLUME}"
        data = {"vl": volume_value}

        try:
            async with self._session.post(
                url, data=data, timeout=aiohttp.ClientTimeout(total=10)
            ) as response:
                if response.status != 200:
                    _LOGGER.error(
                        "Failed to send volume command to %s: HTTP %s",
                        url,
                        response.status,
                    )
        except aiohttp.ClientError as err:
            _LOGGER.error("Error sending volume command to %s: %s", url, err)
        except Exception as err:
            _LOGGER.exception("Unexpected error sending volume command: %s", err)

    async def async_select_source(self, source: str) -> None:
        """Select input source (preset or favorite)."""
        try:
            # Look up the source in our mapping
            if source not in self._source_to_id:
                _LOGGER.error("Invalid source: %s", source)
                return

            source_type, source_id = self._source_to_id[source]

            if source_type == "preset":
                await self._select_preset(source, source_id)
            elif source_type == "favorite":
                await self._select_favorite(source, source_id)

        except aiohttp.ClientError as err:
            _LOGGER.error("Error selecting source %s: %s", source, err)
        except Exception as err:
            _LOGGER.exception("Unexpected error selecting source: %s", err)

    async def _select_preset(self, source: str, preset_num: int) -> None:
        """Select a preset source."""
        try:
            preset_id = preset_num - 1  # Convert to 0-based index

            if preset_id < 0 or preset_id >= MAX_PRESETS:
                _LOGGER.error("Invalid preset number: %s", preset_num)
                return

            url = f"{self._host}{ENDPOINT_PRESET}"
            data = {"do": "lip", "pid": preset_id}

            async with self._session.post(
                url, data=data, timeout=aiohttp.ClientTimeout(total=10)
            ) as response:
                if response.status == 200:
                    self._current_source = source
                    _LOGGER.info("Selected preset: %s (pid=%s)", source, preset_id)
                else:
                    _LOGGER.error(
                        "Failed to select preset %s: HTTP %s", source, response.status
                    )
        except Exception as err:
            _LOGGER.error("Error selecting preset %s: %s", source, err)

    async def _select_favorite(self, source: str, favorite_num: int) -> None:
        """Select a favorite source."""
        try:
            if favorite_num < 1 or favorite_num > MAX_FAVORITES:
                _LOGGER.error("Invalid favorite number: %s", favorite_num)
                return

            url = f"{self._host}{ENDPOINT_FAVORITE}"
            data = {"do": "lif", "id": favorite_num, "grp": -1}

            async with self._session.post(
                url, data=data, timeout=aiohttp.ClientTimeout(total=10)
            ) as response:
                if response.status == 200:
                    self._current_source = source
                    _LOGGER.info("Selected favorite: %s (id=%s)", source, favorite_num)
                else:
                    _LOGGER.error(
                        "Failed to select favorite %s: HTTP %s", source, response.status
                    )
        except Exception as err:
            _LOGGER.error("Error selecting favorite %s: %s", source, err)

    async def async_browse_media(
        self, media_content_type: str | None = None, media_content_id: str | None = None
    ) -> BrowseMedia:
        """Implement the browse_media service."""
        if media_content_id is None:
            # Root level - show Presets and Favorites folders
            return BrowseMedia(
                title="DAP CDI160 Stations",
                media_class=MediaClass.DIRECTORY,
                media_content_id="root",
                media_content_type="library",
                can_play=False,
                can_expand=True,
                children=[
                    BrowseMedia(
                        title="Presets",
                        media_class=MediaClass.DIRECTORY,
                        media_content_id="presets",
                        media_content_type="presets",
                        can_play=False,
                        can_expand=True,
                        thumbnail="https://brands.home-assistant.io/_/media_player/icon.png",
                    ),
                    BrowseMedia(
                        title="Favorites",
                        media_class=MediaClass.DIRECTORY,
                        media_content_id="favorites",
                        media_content_type="favorites",
                        can_play=False,
                        can_expand=True,
                        thumbnail="https://brands.home-assistant.io/_/media_player/icon.png",
                    ),
                ],
            )

        if media_content_id == "presets":
            # Show all presets
            children = []
            for i in range(1, MAX_PRESETS + 1):
                custom_name = self._config_entry.options.get(f"preset_{i}_name", f"Preset {i}")
                children.append(
                    BrowseMedia(
                        title=custom_name,
                        media_class=MediaClass.MUSIC,
                        media_content_id=f"preset:{custom_name}",
                        media_content_type="music",
                        can_play=True,
                        can_expand=False,
                        thumbnail="https://brands.home-assistant.io/_/media_player/icon.png",
                    )
                )

            return BrowseMedia(
                title="Presets",
                media_class=MediaClass.DIRECTORY,
                media_content_id="presets",
                media_content_type="presets",
                can_play=False,
                can_expand=True,
                children=children,
            )

        if media_content_id == "favorites":
            # Show all favorites
            children = []
            for i in range(1, MAX_FAVORITES + 1):
                custom_name = self._config_entry.options.get(f"favorite_{i}_name", f"Favorite {i}")
                children.append(
                    BrowseMedia(
                        title=custom_name,
                        media_class=MediaClass.MUSIC,
                        media_content_id=f"favorite:{custom_name}",
                        media_content_type="music",
                        can_play=True,
                        can_expand=False,
                        thumbnail="https://brands.home-assistant.io/_/media_player/icon.png",
                    )
                )

            return BrowseMedia(
                title="Favorites",
                media_class=MediaClass.DIRECTORY,
                media_content_id="favorites",
                media_content_type="favorites",
                can_play=False,
                can_expand=True,
                children=children,
            )

        # Invalid media_content_id
        raise ValueError(f"Invalid media_content_id: {media_content_id}")

    async def async_play_media(
        self, media_type: str, media_id: str, **kwargs: Any
    ) -> None:
        """Play media from browse_media."""
        # Extract the station name from media_id (format: "preset:Station Name" or "favorite:Station Name")
        if ":" in media_id:
            _, station_name = media_id.split(":", 1)
            await self.async_select_source(station_name)
