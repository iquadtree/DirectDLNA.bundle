#!/usr/bin/env python
# -*- coding: utf-8 -*-

# pylint: disable=invalid-name, undefined-variable # disabled due to Plex plugin code style guide

"""
    Simple and experimental Plex Media Server plugin which
    allows to play streams via DLNA without SSDP discovery
    Copyright: 2025, iquadtree
    License: GPL-3.0
"""

from collections import namedtuple
from string import Template

import ast
import fnmatch
import re
import sys

from locale_patch import L, SetAvailableLanguages # pylint: disable=E0401
import quirks # pylint: disable=E0401

BASE_HOST = str(Network.Address)
BASE_PORT = 32400

DLNA_HOST = str(Network.Hostname)
DLNA_PORT = 32469

DLNA_UUID = '00000000-0000-0000-0000-000000000000'

# PMS implementation of ContentDirectory service has hard-coded
# UUIDs for top-level containers
LIBRARIES = {'Video'  : '94467912-bd40-4d2f-ad25-7b8423f7b05a',
             'Music'  : 'abe6121c-1731-4683-815c-89e1dcd2bf11',
             'Photos' : 'b0184133-f840-4a4f-a583-45f99645edcd'}

MEDIA_URI_RULES_MATCHER = 'pcre'
MEDIA_URI_RULES = []

WebApiResult = namedtuple('WebApiResult', ['values', 'attributes'])
MediaUriRule = namedtuple('MediaUriRule', ['selectors', 'template'])
RuleLoadError = namedtuple('RuleLoadError', ['preference', 'rule', 'location'])

def Response404(reason = '404 Not Found'):
    """Send response 404 (Not Found) to user agent. Can only be used in request context."""
    html = f'<html><head><title>Not Found</title></head><body><h1>{reason}</h1></body></html>'

    Response.Headers['Content-Length'] = len(html)
    Response.Headers['Content-Type']   = 'text/html'

    Response.Status = 404

    return str(html)

def Response406(reason = '406 Not Acceptable'):
    """Send response 406 (Not Acceptable) to user agent. Can only be used in request context."""
    html = f'<html><head><title>Not Acceptable</title></head><body><h1>{reason}</h1></body></html>'

    Response.Headers['Content-Length'] = len(html)
    Response.Headers['Content-Type']   = 'text/html'

    Response.Status = 406

    return str(html)

def WebApiRequest(endpoint):
    """Perform request to Plex Web API. Returns value list of MediaContainer and its attributes."""
    uri = f'http://{BASE_HOST}:{BASE_PORT}{endpoint}'

    res = JSON.ObjectFromURL(uri, None, { 'Accept': 'application/json' })

    if not res:
        return None

    if 'MediaContainer' not in res or 'size' not in res['MediaContainer']:
        raise ValueError('not a MediaContainer')

    # container title1 key is unknown to us so we have to deduce it by searching
    # corresponding list element
    size  = res['MediaContainer']['size']
    vals  = []
    attrs = []

    for k, v in res['MediaContainer'].items():
        if isinstance(v, list):
            if size != len(v):
                raise ValueError(f'wrong MediaContainer size: expected {size}, got {len(v)}')
            vals = v
        elif k != 'size':
            attrs[k] = v

    return WebApiResult(vals, attrs)

def CheckDLNAEnabled():
    """Check using Web API whether DLNA is enabled in Plex settings."""
    prefs = WebApiRequest('/:/prefs')

    for pref in prefs.values:
        if 'id' in pref and 'value' in pref and pref['id'] == 'DlnaEnabled':
            return bool(pref['value'])
    else:
        Log.Warning('Cannot obtain DLNA status')

    return False

def LoadMediaUriRules():
    """Load media URI selection rules from corresponding preferences."""
    Log.Debug("Loading DLNA media URI rules...")

    global MEDIA_URI_RULES # pylint: disable=W0603

    errors = []
    rules = []

    for n in range(5):
        key = f'media_uri_rule_{n}'

        if not Prefs[key]:
            continue

        location = None
        rule = None

        try:
            rule = ast.literal_eval(Prefs[key])

        except SyntaxError as e:
            location = e.offset - 1

        except ValueError:
            location = 0

        if rule:
            rules.append(MediaUriRule(rule[0], rule[1]))
        else:
            sloc = str(location) if location else '<unknown>'
            errors.append(RuleLoadError(key, Prefs[key], location))
            Log.Error((
                f'Error occured while loading rule from preference \'{key}\': '
                f'syntax error at col {sloc}'
            ))

    MEDIA_URI_RULES = rules

    return errors


def Start():
    """Entry point of the plugin."""
    Log.Debug("Starting DirectDLNA...")

    global BASE_PORT, DLNA_HOST, DLNA_UUID, MEDIA_URI_RULES_MATCHER # pylint: disable=W0603

    SetAvailableLanguages({'en', 'ru'})

    MEDIA_URI_RULES_MATCHER = Prefs['media_uri_rules_matcher']

    server = WebApiRequest('/servers')

    if server:
        # adjust base port and DLNA URI
        BASE_PORT = server.values[0]['port']
        DLNA_HOST = server.values[0]['host']

        # construct UUID for ContentDirectory service
        machine_identifier = server.values[0]['machineIdentifier']

        DLNA_UUID = machine_identifier[0:8] + '-'
        DLNA_UUID += machine_identifier[8:12] + '-'
        DLNA_UUID += machine_identifier[12:16] + '-'
        DLNA_UUID += machine_identifier[16:20] + '-'
        DLNA_UUID += machine_identifier[20:32]
    else:
        Log.Error('Cannot determine running server information')

    LoadMediaUriRules()

def Restart():
    """Executes at plugin reload."""

def ValidatePrefs():
    """Executes at preference change."""


@handler('/applications/dlna', 'DirectDLNA')
def Main():
    """URI handler binding to plugin. This function does nothing though..."""


@route('applications/dlna/debug')
def DumpDebugInfo():
    """Emits various debug info to log. Returns 204 (No Content) to user agent when success."""
    if not Prefs['debug_endpoint']:
        return Response404()

    dbg  = '\n'
    dbg += '===========================> DIRECTDLNA DEBUG INFO <===========================\n'
    dbg += f'Server DLNA enabled:\t{str(CheckDLNAEnabled())}\n'
    dbg += f'Server DLNA URI:\thttp://{DLNA_HOST}:{DLNA_PORT}\n'
    dbg += f'Server DLNA UUID:\t{DLNA_UUID}\n'
    dbg += '\n'

    media_libs = LIBRARIES

    for name, uuid in media_libs.items():
        dbg += f'Media library \'{name}\':\t{uuid}\n'

    dbg += '\n'

    dbg += f'URI rules matcher:\t{MEDIA_URI_RULES_MATCHER}\n'
    dbg += '\n'

    for rule in MEDIA_URI_RULES:
        dbg += f'URI rule: template:\t{rule.template}\n'
        for k, v in rule.selectors.items():
            dbg += f'URI rule: selector:\t\'{k}: {v}\'\n'
        dbg += '\n'

    dbg += '=============================== CLIENT  REQUEST ===============================\n'

    maxtabs = (len(max(Request.Headers.keys(), key=len)) + 1) // 8

    for k, v in Request.Headers.items():
        tabs = '\t' * (maxtabs - ((len(k) + 1) // 8) + 1)
        dbg += f'{k}:{tabs}{v}\n'

    dbg += '<=========================== DIRECTDLNA DEBUG INFO ===========================>\n'

    Log.Debug(dbg)

    Response.Headers['Content-Length'] = 0
    Response.Status = 204

    return str()

@route('/applications/dlna/media.m3u8')
def GetPlaylist():
    """Send formatted playlist to user agent or 406 when UA is not allowed by rule."""
    if not CheckDLNAEnabled():
        return Response404()

    uri_template = 'upnp://http://$HOST:$PORT/ContentDirectory/$UUID/control.xml?ObjectID=$LIID'

    for rule in MEDIA_URI_RULES:
        if not set(rule.selectors.keys()).issubset(Request.Headers.keys()):
            continue # try next rule

        match_fn = None

        if MEDIA_URI_RULES_MATCHER == 'plain':
            match_fn = lambda v, s: v == s # pylint: disable=C3001
        elif MEDIA_URI_RULES_MATCHER == 'fnmatch':
            match_fn = lambda v, s: fnmatch.fnmatch(v, s) # pylint: disable=C3001, W0108
        elif MEDIA_URI_RULES_MATCHER == 'pcre':
            match_fn = lambda v, s: re.match(s, v) # pylint: disable=C3001
        else:
            Log.Warning('Invalid media URI rules matcher configured, using default URI template')
            break

        if quirks.all([match_fn(Request.Headers[k], rule.selectors[k]) for k in rule.selectors]):
            uri_template = rule.template
            break

    if not uri_template:
        return Response406('User agent has been rejected by media URI rule')

    Response.Headers['Content-Type'] = 'application/x-mpegURL'

    subst = {'HOST': DLNA_HOST, 'PORT': DLNA_PORT, 'UUID': DLNA_UUID, 'LIID': None}
    media_libs = LIBRARIES

    playlist =  '#EXTM3U\n'

    for name, uuid in media_libs.items():
        subst['LIID'] = uuid
        playlist += f'#EXTINF:0,{name}\n'
        playlist += Template(uri_template).safe_substitute(subst) + '\n'

    Response.Headers['Content-Length'] = len(playlist)
    Response.Status = 200

    return str(playlist)

@route('/applications/dlna/reloadrules')
def ReloadRules():
    """Explicitly reload rules by user agent request."""
    errors = LoadMediaUriRules()

    if not errors:
        return MessageContainer(
            L('Success'),
            L('All media URI selection rules loaded')
        )

    message = str()

    for error in errors:
        message += unicode(L('Syntax error while parsing media URI selection rule from preference'))
        message += f' \'{error.preference}\''
        if not error.location:
            message += ' ' + unicode(L('(no source location available)'))
        message += ':\n'
        message += error.rule + '\n'
        if error.location:
            message += ' ' * error.location + '^~~~~' + '\n'
        message += '\n'

        return MessageContainer(
            L('Error'),
            message
        )
