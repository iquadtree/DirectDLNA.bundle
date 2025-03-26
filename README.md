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

  - Enable DLNA server in Plex settings (click on wrench icon at the top-right corner and select *Settings - DLNA* in the list at the left pane)
  - Point your player to URI [http://BASE-URL:32400/applications/dlna/media.m3u8](http://BASE-URL:32400/applications/dlna/media.m3u8) to get playlist (format will be defined automatically according to HTTP headers of user agent — see below)
  - Unless DLNA server is enabled 404 status returns

## Configuring the plugin

### Debugging endpoint

To inspect user agent requests debug endpoint can be used. It disabled by default thus you have to set *debug_endpoint* preference to 'true'. Then point UA to `/applications/dlna/debug` endpoint to get some plugin and user agent information into plugin log.

### Customizing the playlist

By default (when no rules applied) plugin generates media library URI in following format: `upnp://http://$HOST:$PORT/ContentDirectory/$UUID/control.xml?ObjectID=$LIID` where:

  - `$HOST` — DLNA server host (IP or hostname Plex Media Server runs on)
  - `$PORT` — DLNA server port (implementation defined, always **32469** till PMS 1.41.5.9522-a96edc606)
  - `$UUID` — ContentDirectory service UUID (constructed from 32 hexadecimal symbols of PMS machine id string (40 bytes long) in form `8-4-4-4-12`)
  - `$LIID` — media library unique identifier (always hard-coded at least in PMS version 1.41.5.9522-a96edc606)

The rules are colon-separated pairs of JSON dictionary and URI template string. The dictionary contain key-value pairs of DLNA user agent HTTP headers. Header values are Perl Compatible Regular Expressions until another matcher type is specified. Possible matchers are:

  - **plain** — plain text strings only comparison will be performed (the fastest matcher)
  - **fnmatch** — matching is identical to what's used in the shell to match filenames, so for example `VLC *` matches everything that begins with 'VLC' (compromise matcher)
  - **pcre** — Perl Compatible Regular Expressions matcher (the slowest one but full of features)

Matcher can be chosen using *media_uri_rules_matcher* preference. Rules are specified with *media_uri_rule_0* - *media_uri_rule_4* prefs. Some examples:

  - `{'Accept-Language' : 'en_US', 'User-Agent' : 'VLC/3.0.20 LibVLC/3.0.20'}, 'upnp://http://$URI/ContentDirectory/$UUID/control.xml?ObjectID=$ID'`
  - `{'Accept-Language' : 'en_US', 'User-Agent' : 'VLC/3.0.21 LibVLC/3.0.21'}, 'http://$URI/ContentDirectory/$UUID/control.xml?ObjectID=$ID'`
  - `{'Accept-Language' : 'ru'   , 'User-Agent' : 'VLC/3.0.21 LibVLC/3.0.21'}, None`

Using 'None' instead of URI template causes HTTP status 406 ('Not Acceptable'). It can be used to forbid particular (or unsupported) user agents.

To explicitly reload the rules point your UA to `/applications/dlna/reloadrules`.
