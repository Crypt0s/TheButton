#!/usr/bin/python
from multiprocessing import Process
import hashlib
import string
import web
import pdb
import RPi.GPIO as GPIO
import pygame
import threading
import glob
import random
import signal
import sys
import os
import stockoo
import logging
import time
import subprocess

# Some housekeeping items
pygame.init()
poison = True

# Webpage
urls = (
    '/upload','Upload',
    '/','Index',
    '/press','Press',
    '/useradd','Useradd',
)

class Useradd:
    def GET(self):
        return "POST ONLY"

    def POST(self):
        userinput = web.input()
        login(userinput.username,userinput.password,True)
        return "OK"

class Press:
    def GET(self):
        return "You must submit a username/token via POST"

    def POST(self):
        userinput = web.input()
        if login(userinput.username,userinput.password):
            logging.debug('Playing from web')
            play()
            return "OK"
        else:
           return "Username / Password combo not good"

class Index:
    def __init__(self):
        logging.debug('started web server')

    def GET(self):
        web.seeother('/upload')


class Upload:
    def GET(self):
        return """<html><head></head><body>
<form method="POST" enctype="multipart/form-data" action="">
<input type="file" name="myfile" />
<br/>
<input type="submit" />
</form>

</body></html>"""

    def POST(self):
        x = web.input(myfile={})
        filename = x['myfile'].filename
        file = x['myfile'].file.read()

        # Check that name!
        filename = rand_filename() #os.path.basename(filename)

        # Make sure that we aren't filling the disk
        if os.path.getsize('files/') > 1000000000:
            return "The disk limit has been reached - Thanks Jake and Ben"

        # Jake is the asshole
        x['myfile'].file.seek(0,2)
        file_size = x['myfile'].file.tell()
        if file_size > 5000000:
            return "Error 'Jake is the asshole' - File too big.  Bryan is stoopid"
        x['myfile'].file.seek(0)

        # Ben check.
        if glob.glob('files/'+filename) != []:
            return "Error 'Ben is the asshole' - Already exists"

        # write the file out to disk
        open('files/'+filename,'w').write(file)

        # attempt to play the file on upload - if you can't, then remove it
        try:
            pygame.mixer.music.load('files/'+filename)
        except:
            os.remove('files/'+filename)
            return "That isn't a file format that I can play"
        raise web.seeother('/upload')

def login(username,password, add=False):
    with open('userpass','a+') as userfile:
        # Add a user
        if add == True:
            password = hashlib.sha224(password).hexdigest()
            userfile.write(username+':'+password)
            return True

        # Compare a user/pass combo
        for line in userfile.readlines():
            s_line = line.split(':')
            c_user = s_line[0]
            if c_user == username and s_line[1] == password:
                return True
        return False

# do the thing        
def play():
    clip = select_clip()
    stats.write(str(time.time())+'\n')
    try:
        pygame.mixer.music.load(clip)
        pygame.mixer.music.play()
    except:
        logging.debug("Couldn't play " + clip + " -- deleting it, thanks jake and ben")
        os.remove(clip)
        play()
        pass
    return True

# Selects a random clip
lastchoice = []
def select_clip(num=False):
    # Quick and dirty override to return num of files
    if num == True:
        return len(glob.glob('files/*'))

    choice = random.choice(glob.glob('files/*'))
    # if we select something we just played - select it again.
    if choice in lastchoice:
        choice = select_clip()

    # we don't want to have the same thing occur over and over
    lastchoice.append(choice)
    if len(lastchoice) > 3:
       lastchoice.pop(0)

    return choice

def rand_filename():
    N = 10
    return ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(N))

# Constantly monitors for the button push and montiors changes in state.
def status_monitor_loop():
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(17, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    #GPIO.setup(18, GPIO.IN, pull_up_down=GPIO.PUD_UP)

    while poison:
        unpressed_state = GPIO.input(17)
        if not unpressed_state and not pygame.mixer.music.get_busy():
            logging.debug('Button Pressed')
            play()
            #clip = select_clip()
            #stats.write(str(time.time())+'\n')
            #try:
            #    pygame.mixer.music.load(clip)
            #    pygame.mixer.music.play()
            #except:
            #    logging.debug("Couldn't play " + clip + " -- deleting it, thanks jake and ben")
            #    os.remove(clip)
            #    pass

if __name__ == "__main__":
    # logging setup
    logging.basicConfig(filename='/opt/button/log.log', level=logging.DEBUG)
    logging.debug('Service starting...')

    # grab the stats file handle so we can record when the button is pressed
    stats = open('stats','a')
 
    # Thread for the button monitor
    monitor_loop = threading.Thread(target=status_monitor_loop)
    monitor_loop.start()
    logging.debug('Started button thread')

    # Thread for the stock application
    #stockthread = Process(target=stockoo.Stock)
    #stockthread.start()
    # Craptastic workaround to getting the stock ticker to play nice

    os.system('python stockoo.py &')
    logging.debug('Started stock ticker application')

    logging.debug('Starting webserver')
    web.config.debug = False
    # Thread for the web application
    app = web.application(urls, globals())
    app.run()

    # We generally don't get here unless we ctrl-c
    #sockthread.join()
    sys.exit(0)
