#!/usr/bin/env python
# -*- coding: utf-8 -*-

from collections import namedtuple
import sys, uuid

BASE_HOST = str(Network.Address)
BASE_PORT = 32400

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
    pass

def Restart():
    pass


@handler('/applications/dlna', 'DirectDLNA')
def Main():
    pass

@route('applications/dlna/debug')
def DumpDebugInfo():
    global BASE_HOST, BASE_PORT

    # FIXME: more correct way to display 404?
    if not Prefs['debug_endpoint']:
        Response.Headers['Content-Length'] = 85
        Response.Headers['Content-Type']   = 'text/html'

        Response.Status = 404

        return str('<html><head><title>Not Found</title></head><body><h1>404 Not Found</h1></body></html>')

    dbg  = '\n'
    dbg += '=====> DIRECTDLNA DEBUG INFO <=====\n'
    dbg += 'Server DLNA enabled:\t%s\n' % str(CheckDLNAEnabled())
    dbg += 'Server base URI:\thttp://%s:%d\n' % (BASE_HOST, BASE_PORT)

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
    # FIXME: more correct way to display 404?
    if not CheckDLNAEnabled():
        Response.Headers['Content-Length'] = 85
        Response.Headers['Content-Type']   = 'text/html'

        Response.Status = 404

        return str('<html><head><title>Not Found</title></head><body><h1>404 Not Found</h1></body></html>')

    Response.Headers['Content-Type'] = 'application/x-mpegURL'

    playlist =  '#EXTM3U\n'
    playlist += '#EXTINF:0,Video\n'
    playlist += 'upnp://http://synologynas.hometown:32469/ContentDirectory/a35dee1b-9a31-9af9-ad9a-193f5864553e/control.xml?ObjectID=94467912-bd40-4d2f-ad25-7b8423f7b05a\n'
    playlist += '#EXTINF:0,Music\n'
    playlist += 'upnp://http://synologynas.hometown:32469/ContentDirectory/a35dee1b-9a31-9af9-ad9a-193f5864553e/control.xml?ObjectID=abe6121c-1731-4683-815c-89e1dcd2bf11\n'
    playlist += '#EXTINF:0,Photos\n'
    playlist += 'upnp://http://synologynas.hometown:32469/ContentDirectory/a35dee1b-9a31-9af9-ad9a-193f5864553e/control.xml?ObjectID=b0184133-f840-4a4f-a583-45f99645edcd\n'

    Response.Headers['Content-Length'] = len(playlist)
    Response.Status = 200

    return str(playlist)