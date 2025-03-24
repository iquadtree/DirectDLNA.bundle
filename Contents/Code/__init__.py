#!/usr/bin/env python
# -*- coding: utf-8 -*-

from collections import namedtuple
import sys, uuid

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

WebApiResult = namedtuple('WebApiResult', ['values', 'attributes'])

def WebApiRequest(endpoint):
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
    prefs = WebApiRequest('/:/prefs')

    for pref in prefs.values:
        if 'id' in pref and 'value' in pref and pref['id'] == 'DlnaEnabled':
            return bool(pref['value'])
    else:
        Log.Warning('Cannot obtain DLNA status')

    return False


def Start():
    Log.Debug("Starting DirectDLNA...")

    global BASE_PORT, LIBRARIES, DLNA_HOST, DLNA_UUID

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

    pass

def Restart():
    pass


@handler('/applications/dlna', 'DirectDLNA')
def Main():
    pass

@route('applications/dlna/debug')
def DumpDebugInfo():
    global DLNA_HOST, DLNA_PORT, DLNA_UUID, LIBRARIES

    # FIXME: more correct way to display 404?
    if not Prefs['debug_endpoint']:
        Response.Headers['Content-Length'] = 85
        Response.Headers['Content-Type']   = 'text/html'

        Response.Status = 404

        return str('<html><head><title>Not Found</title></head><body><h1>404 Not Found</h1></body></html>')

    dbg  = '\n'
    dbg += '=====> DIRECTDLNA DEBUG INFO <=====\n'
    dbg += 'Server DLNA enabled:\t%s\n' % str(CheckDLNAEnabled())
    dbg += 'Server DLNA URI:\thttp://%s:%d\n' % (DLNA_HOST, DLNA_PORT)
    dbg += 'Server DLNA UUID:\t%s\n' % DLNA_UUID
    dbg += '\n'

    for key in LIBRARIES:
        dbg += 'Media library \'%s\':\t%s\n' % (key, LIBRARIES[key])

    dbg += '========= CLIENT  REQUEST =========\n'

    maxtabs = (len(max(Request.Headers.keys(), key=len)) + 1) // 8

    for k, v in Request.Headers.items():
        dbg += '%s:%s%s\n' % (k, '\t' * (maxtabs - ((len(k) + 1) // 8) + 1), v)

    dbg += '<===== DIRECTDLNA DEBUG INFO =====>\n'

    Log.Debug(dbg)

    Response.Headers['Content-Length'] = 0
    Response.Status = 204

    return str()

@route('/applications/dlna/media.m3u8')
def GetPlaylist():
    global DLNA_HOST, DLNA_PORT, DLNA_UUID, LIBRARIES

    # FIXME: more correct way to display 404?
    if not CheckDLNAEnabled():
        Response.Headers['Content-Length'] = 85
        Response.Headers['Content-Type']   = 'text/html'

        Response.Status = 404

        return str('<html><head><title>Not Found</title></head><body><h1>404 Not Found</h1></body></html>')

    Response.Headers['Content-Type'] = 'application/x-mpegURL'

    playlist =  '#EXTM3U\n'

    for key in LIBRARIES:
        playlist += '#EXTINF:0,%s\n' % key
        playlist += 'upnp://http://%s:%d/ContentDirectory/%s/control.xml?ObjectID=%s\n' % (DLNA_HOST, DLNA_PORT, DLNA_UUID, LIBRARIES[key])

    Response.Headers['Content-Length'] = len(playlist)
    Response.Status = 200

    return str(playlist)