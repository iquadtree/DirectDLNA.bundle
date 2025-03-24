#!/usr/bin/env python
# -*- coding: utf-8 -*-

BASE_HOST = str(Network.Address)
BASE_PORT = 32400

def Start():
    Log.Debug("Starting DirectDLNA...")

def Restart():
    pass

@handler('/applications/dlna', 'DirectDLNA')
def Main():
    pass

@route('applications/dlna/debug')
def DumpDebugInfo():
    global BASE_HOST, BASE_PORT

    if not Prefs['debug_endpoint']:
        Response.Headers['Content-Length'] = 85
        Response.Headers['Content-Type']   = 'text/html'

        Response.Status = 404

        return str('<html><head><title>Not Found</title></head><body><h1>404 Not Found</h1></body></html>')

    dbg  = '\n'
    dbg += '=====> DIRECTDLNA DEBUG INFO <=====\n'
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