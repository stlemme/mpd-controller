#!/usr/bin/python
# -*- coding: utf-8 -*-

import mpd
import bottle
import os
import uuid


app = bottle.Bottle()

@app.route('/')
def index():
    return bottle.redirect('/webapp/')

@app.route('/webapp/')
@app.route('/webapp/<filename>')
def static(filename='index.html'):
    return bottle.static_file(filename, root='./webapp')

@app.route('/list')
def list():
    mpc = mc.get_client()
    listinfo = mpc.playlistinfo()
    mc.release_client()
    return {'list': listinfo}

@app.route('/volume')
@app.route('/volume/<level:int>')
def volume(level=None):
    mpc = mc.get_client()
    if level:
        mpc.setvol(level)
    level = int(mpc.status()['volume'])
    mc.release_client()
    return {'level': level}

@app.route('/play')
def play():
    mpc = mc.get_client()
    mpd_status = mpc.status()
    if mpd_status['state'] == 'pause':
        mpc.pause(0)
    else:
        mpc.play(0)
    #status = mpc.status()
    mc.release_client()
    return status()

@app.route('/stop')
def stop():
    mpc = mc.get_client()
    mpc.stop()
    status = mpc.status()
    mc.release_client()
    return {'state' : status['state']}

@app.route('/pause')
def pause():
    mpc = mc.get_client()
    mpc.pause(1)
    status = mpc.status()
    mc.release_client()
    return {'state' : status['state']}

@app.route('/queue', method='POST')
def queue():
    song = bottle.request.files.get('song')
    name, ext = os.path.splitext(song.filename)
    #print(name, ext, mc.extensions)
    if ext[1:] not in mc.extensions:
        return 'File extension not allowed.'

    save_path = mc.get_save_path(ext)
    song.save(save_path)
    mpc = mc.get_client()
    uri = 'file://' + os.path.abspath(save_path)
    mpc.add(uri)
    mc.release_client()

@app.route('/status')
def status():
    mpc = mc.get_client()
    status = mpc.status()
    #print(status)
    volume = int(status['volume'])
    state = status['state']
    song_info = None
    elapsed = None
    if state == 'play':
        song_info = mpc.currentsong()
        song_info['time'] = int(song_info['time'])
        elapsed = float(status['elapsed'])
    mc.release_client()
    return {'state': state, 'song': song_info, 'volume': int(volume), 'elapsed': elapsed}


class mpd_controller:
    def __init__(self, host, port):
        self.client = mpd.MPDClient()
        self.host = host
        self.port = port

        try:
            self.client.connect(self.host, self.port)
        except mpd.ConnectionError:
            print("already connected")
    
        #self.client.clear()
        self.extensions = ['mp3']
        self.client.consume(1)

        self.client.disconnect()

    def get_client(self):
        try:
            self.client.connect(self.host, self.port)
        except mpd.ConnectionError:
            print("already connected")
        return self.client

    def release_client(self):
        try:
            self.client.disconnect()
        except mpd.ConnectionError:
            print("can't disconnect")

    def get_save_path(self, ext):
        cache_file = 'song_cache/%s%s'
        return cache_file % (uuid.uuid4(), ext)


if __name__ == "__main__":
    MPD_HOST = '/run/mpd/socket'
    MPD_PORT = None

    mc = mpd_controller(MPD_HOST, MPD_PORT)

    app.run(host='0.0.0.0', port='8080', debug=True)

