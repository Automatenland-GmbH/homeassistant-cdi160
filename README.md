# DAP CDI160-BT Audio Player Integration for Home Assistant

This custom integration allows you to control DAP CDI160-BT Audio Player through Home Assistant.

## Features

- **Media Player Entity**: Full media player control in Home Assistant
- **Playback Control**: Play, pause, and stop buttons in the UI
- **Volume Control**: Volume up, volume down, and mute functionality
- **Source Selection**: Switch between 4 presets and 10 favorites
  - **Presets**: Preset 1-4 (quick access to predefined stations)
  - **Favorites**: Favorite 1-10 (access to saved favorite stations)
- **Status Monitoring**: Display current playing track, artist, and play state
- **UI Configuration**: Easy setup through Home Assistant UI

> **Note**: Due to hardware limitations, play/pause/stop controls are mapped to the device's mute functionality (vl=128 for pause/stop, volume up for play). This provides a seamless UI experience while working within the device's API constraints.

## Installation

### HACS (Recommended)

1. Make sure [HACS](https://hacs.xyz/) is installed
2. Add this repository as a custom repository in HACS:
   - Go to HACS → Integrations → ⋮ (top right) → Custom repositories
   - Add URL: `https://github.com/Automatenland-GmbH/homeassistant-cdi160`
   - Category: Integration
3. Click "Install" on the DAP CDI160 card
4. Restart Home Assistant

### Manual Installation

1. Copy the `custom_components/dap_cdi160` folder to your Home Assistant's `custom_components` directory
2. Restart Home Assistant

## Configuration

### UI Configuration (Recommended)

1. Go to **Settings** → **Devices & Services**
2. Click **+ Add Integration**
3. Search for **DAP CDI160-BT Audio Player**
4. Enter the following information:
   - **Host**: IP address or hostname of your DAP CDI160 device (e.g., `musik.int.automatenland.de` or `192.168.1.100`)
   - **Name**: Friendly name for the device (default: "DAP CDI160 Audio Player")
5. Click **Submit**

### YAML Configuration (Alternative)

While UI configuration is recommended, you can also add the integration via YAML:

```yaml
# configuration.yaml
dap_cdi160:
```

Then configure through the UI as described above.

## Usage

Once configured, the integration creates a media player entity that you can control through:

- **Home Assistant UI**: Use the media player card
- **Automations**: Trigger actions based on player state
- **Scripts**: Control the player programmatically
- **Voice Assistants**: Control via Google Assistant, Alexa, etc.

### Available Services

The media player supports the following services:

- `media_player.media_play`: Start/resume playback (unmutes the device)
- `media_player.media_pause`: Pause playback (mutes the device)
- `media_player.media_stop`: Stop playback (mutes the device)
- `media_player.volume_up`: Increase volume
- `media_player.volume_down`: Decrease volume
- `media_player.volume_mute`: Mute/unmute audio
- `media_player.select_source`: Select preset (1-4) or favorite (1-10)
  - Presets: `"Preset 1"`, `"Preset 2"`, `"Preset 3"`, `"Preset 4"`
  - Favorites: `"Favorite 1"`, `"Favorite 2"`, ..., `"Favorite 10"`

### Example Automation

```yaml
automation:
  - alias: "Play preset 1 at 7 AM"
    trigger:
      - platform: time
        at: "07:00:00"
    action:
      - service: media_player.select_source
        target:
          entity_id: media_player.dap_cdi160_audio_player
        data:
          source: "Preset 1"
      - service: media_player.media_play
        target:
          entity_id: media_player.dap_cdi160_audio_player

  - alias: "Pause music at 10 PM"
    trigger:
      - platform: time
        at: "22:00:00"
    action:
      - service: media_player.media_pause
        target:
          entity_id: media_player.dap_cdi160_audio_player

  - alias: "Play favorite station on weekend mornings"
    trigger:
      - platform: time
        at: "09:00:00"
    condition:
      - condition: time
        weekday:
          - sat
          - sun
    action:
      - service: media_player.select_source
        target:
          entity_id: media_player.dap_cdi160_audio_player
        data:
          source: "Favorite 1"
      - service: media_player.media_play
        target:
          entity_id: media_player.dap_cdi160_audio_player
```

### Example Script

```yaml
script:
  morning_radio:
    sequence:
      - service: media_player.select_source
        target:
          entity_id: media_player.dap_cdi160_audio_player
        data:
          source: "Preset 2"
      - service: media_player.media_play
        target:
          entity_id: media_player.dap_cdi160_audio_player
      - service: media_player.volume_up
        target:
          entity_id: media_player.dap_cdi160_audio_player
```

## API Endpoints

The integration uses the following HTTP API endpoints:

- **Status**: `GET /php/getPlaying.php` - Get current playing information
- **Volume**: `POST /php/webChVol.php` - Control volume (vl=-1, vl=1, vl=128)
- **Preset**: `POST /php/webListenP.php` - Select preset (do=lip, pid=0-3)
- **Favorite**: `POST /php/webListen.php` - Select favorite (do=lif, id=1-10, grp=-1)

## Troubleshooting

### Device Not Found

- Verify the host/IP address is correct
- Ensure the device is powered on and connected to the network
- Check firewall settings allow HTTP traffic to the device

### Connection Timeout

- Increase timeout in the integration code if needed
- Check network connectivity between Home Assistant and the device

### Enable Debug Logging

Add to your `configuration.yaml`:

```yaml
logger:
  default: warning
  logs:
    custom_components.dap_cdi160: debug
```

## Support

For issues and feature requests, please use the [GitHub issue tracker](https://github.com/Automatenland-GmbH/homeassistant-cdi160/issues).

## License

This project is licensed under the MIT License.
