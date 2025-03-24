# DirectDLNA.bundle

When DLNA streaming enabled on server this plugin exposes M3U playlist containing top-level media directory structure. This functionality allows to connect to media server in networks where SSDP discovery isn't available (such as VPN).

## Installation

- This plugin can be installed via [DirectDLNA.bundle](https://github.com/iquadtree/DirectDLNA.bundle) or manually using the directions below.
- Download and install by following the Plex [instructions](https://support.plex.tv/articles/201187656-how-do-i-manually-install-a-plugin/) or the instructions below.
  - Unzip and rename the directory from **DirectDLNA.bundle-master** to **DirectDLNA.bundle**
  - Copy **DirectDLNA.bundle** into the Plex Media Server [Plug-ins](https://support.plex.tv/articles/201106098-how-do-i-find-the-plug-ins-folder/) directory
  - Unix based platforms need to `chown plex:plex -R DirectDLNA.bundle` after moving it into the [Plug-ins](https://support.plex.tv/articles/201106098-how-do-i-find-the-plug-ins-folder/) directory _(`user:group` may differ by platform)_
  - Restart Plex Media Server
  
## Usage

  - Enable DLNA server in Plex settings (click on wrench icon at the top-right corner and select 'Settings - DLNA' in the list at the left pane)
  - Point your player to URI http://BASE-URL:32400/applications/dlna/media.m3u8 to get playlist (format will be defined automatically according to HTTP headers of user agent)
  - Unless DLNA server is enabled 404 status returns

## Configuring the plugin

### Debugging endpoint

  - To inspect user agent requests debug endpoint can be used. It disabled by default thus you have to set 'debug_endpoint' preference to 'true'. Then point UA to '/applications/dlna/debug' endpoint to get some plugin and user agent information into plugin log