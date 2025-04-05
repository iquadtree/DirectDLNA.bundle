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

from locale_patch import L, SetAvailableLanguages
import quirks

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
    html = '<html><head><title>Not Found</title></head><body><h1>%s</h1></body></html>' % reason

    Response.Headers['Content-Length'] = len(html)
    Response.Headers['Content-Type']   = 'text/html'

    Response.Status = 404

    return str(html)

def Response406(reason = '406 Not Acceptable'):
    """Send response 406 (Not Acceptable) to user agent. Can only be used in request context."""
    html = '<html><head><title>Not Acceptable</title></head><body><h1></h1></body></html>' % reason

    Response.Headers['Content-Length'] = len(html)
    Response.Headers['Content-Type']   = 'text/html'

    Response.Status = 406

    return str(html)

def WebApiRequest(endpoint):
    """Perform request to Plex Web API. Returns value list of MediaContainer and its attributes."""
    global BASE_PORT

    uri = 'http://%s:%d%s' % (BASE_HOST, BASE_PORT, endpoint)

    res = JSON.ObjectFromURL(uri, None, { 'Accept': 'application/json' })

    if not res:
        return None

    if 'MediaContainer' not in res or 'size' not in res['MediaContainer']:
        raise ValueError('not a MediaContainer')

    # container title1 key is unknown to us so we have to deduce it by searching
    # corresponding list element
    size  = res['MediaContainer']['size']
    vals  = list()
    attrs = dict()

    for k, v in res['MediaContainer'].items():
        if (isinstance(v, list)):
            if (size != len(v)):
                raise ValueError('invalid MediaContainer size (expected %d, got %d)' % (size, len(v)))
            else:
                vals = v
        elif (k != 'size'):
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

    global MEDIA_URI_RULES

    errors = []
    rules = []

    for n in range(5):
        key = 'media_uri_rule_%d' % n

        if not Prefs[key]:
            continue

        location = None
        rule = None

        try:
            rule = ast.literal_eval(Prefs[key])

        except SyntaxError as e:
            location = e.offset - 1

        except ValueError as e:
            location = 0

        if rule:
            rules.append(MediaUriRule(rule[0], rule[1]))
        else:
            sloc = str(location) if location else '<unknown>'
            errors.append(RuleLoadError(key, Prefs[key], location))
            Log.Error('Error occured while loading rule from preference \'%s\': syntax error at col %s' % (key, sloc))

    MEDIA_URI_RULES = rules

    return errors


def Start():
    """Entry point of the plugin."""
    Log.Debug("Starting DirectDLNA...")

    global BASE_PORT, LIBRARIES, DLNA_HOST, DLNA_UUID, MEDIA_URI_RULES_MATCHER

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

    pass

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
    global DLNA_HOST, DLNA_PORT, DLNA_UUID, LIBRARIES
    global MEDIA_URI_RULES, NEDIA_URI_RULES_MATCHER

    if not Prefs['debug_endpoint']: return Response404()

    dbg  = '\n'
    dbg += '===========================> DIRECTDLNA DEBUG INFO <===========================\n'
    dbg += 'Server DLNA enabled:\t%s\n' % str(CheckDLNAEnabled())
    dbg += 'Server DLNA URI:\thttp://%s:%d\n' % (DLNA_HOST, DLNA_PORT)
    dbg += 'Server DLNA UUID:\t%s\n' % DLNA_UUID
    dbg += '\n'

    for key in LIBRARIES:
        dbg += 'Media library \'%s\':\t%s\n' % (key, LIBRARIES[key])

    dbg += '\n'

    dbg += 'URI rules matcher:\t%s\n' % MEDIA_URI_RULES_MATCHER
    dbg += '\n'

    for rule in MEDIA_URI_RULES:
        dbg += 'URI rule: template:\t%s\n' % rule.template
        for k, v in rule.selectors.items():
            dbg += 'URI rule: selector:\t\'%s: %s\'\n' % (k ,v)
        dbg += '\n'

    dbg += '=============================== CLIENT  REQUEST ===============================\n'

    maxtabs = (len(max(Request.Headers.keys(), key=len)) + 1) // 8

    for k, v in Request.Headers.items():
        dbg += '%s:%s%s\n' % (k, '\t' * (maxtabs - ((len(k) + 1) // 8) + 1), v)

    dbg += '<=========================== DIRECTDLNA DEBUG INFO ===========================>\n'

    Log.Debug(dbg)

    Response.Headers['Content-Length'] = 0
    Response.Status = 204

    return str()

@route('/applications/dlna/media.m3u8')
def GetPlaylist():
    """Send formatted playlist to user agent or 406 when UA is not allowed by rule."""
    global DLNA_HOST, DLNA_PORT, DLNA_UUID, LIBRARIES
    global MEDIA_URI_RULES, MEDIA_URI_RULES_MATCHER

    if not CheckDLNAEnabled(): return Response404()

    uri_template = 'upnp://http://$HOST:$PORT/ContentDirectory/$UUID/control.xml?ObjectID=$LIID'

    for rule in MEDIA_URI_RULES:
        if not set(rule.selectors.keys()).issubset(Request.Headers.keys()):
            continue # try next rule

        match_fn = None

        if MEDIA_URI_RULES_MATCHER == 'plain':
            match_fn = lambda v, s: v == s
        elif MEDIA_URI_RULES_MATCHER == 'fnmatch':
            match_fn = lambda v, s: fnmatch.fnmatch(v, s)
        elif MEDIA_URI_RULES_MATCHER == 'pcre':
            match_fn = lambda v, s: re.match(s, v)
        else:
            Log.Warning('Invalid media URI rules matcher configured, using default URI template')
            break

        if quirks.all([match_fn(Request.Headers[k], rule.selectors[k]) for k in rule.selectors]):
            uri_template = rule.template
            break

    if not uri_template: return Response406('User agent has been rejected by media URI rule')

    Response.Headers['Content-Type'] = 'application/x-mpegURL'

    playlist =  '#EXTM3U\n'

    for key in LIBRARIES:
        playlist += '#EXTINF:0,%s\n' % key
        playlist += Template(uri_template).safe_substitute(HOST=DLNA_HOST, PORT=DLNA_PORT, UUID=DLNA_UUID, LIID=LIBRARIES[key]) + '\n'

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
        message += ' \'%s\'' % error.preference
        message += ':\n' if error.location else '%s:\n' % unicode(L('(no source location available)'))
        message += error.rule + '\n'
        if error.location:
            message += ' ' * error.location + '^~~~~' + '\n'
        message += '\n'

        return MessageContainer(
            L('Error'),
            message
        )
