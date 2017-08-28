'''
Created on Jun 28, 2017

@author: sumeetkhule
'''

from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer
from threading import Thread
from logging import basicConfig, info, INFO
from pickle import dump, load
from socket import inet_aton
from struct import pack
from urllib import urlopen
from urlparse import parse_qs
import peewee
from peewee import *
import json
from playhouse.shortcuts import model_to_dict, dict_to_model

db = MySQLDatabase('webapi', user='root',passwd='train1234')

class Peer(peewee.Model):
    peer_id = peewee.CharField()
    ip = peewee.TextField()
    cpu = peewee.IntegerField()
    memory = peewee.IntegerField()
    Status = peewee.TextField()
    type = peewee.TextField()
    accountno = peewee.TextField()
    enodeid = peewee.TextField()

    class Meta:
        database = db

def decode_request(path):
    """ Return the decoded request string. """

    # Strip off the start characters
    if path[:1] == "?":
        path = path[1:]
    elif path[:2] == "/?":
        path = path[2:]

    return parse_qs(path)

def add_peer(peer_id, ip, cpu, memory, Status, type, accountno, enodeid):
    """ Add the peer to the torrent database. """
    peer = Peer(peer_id = peer_id, ip = ip, cpu = cpu, memory = memory, Status = Status, type = type, accountno = accountno, enodeid = enodeid)
    try:
        check_peer = Peer.get(peer_id = peer_id)
        query = peer.update(Status = "active").where(peer_id = peer.peer_id)
        query.execute()
    except:
        peer.save()
    
    return peer
        
def peer_list(peer_list, compact):
    """ Depending on compact, dispatches to compact or expanded peer
    list functions. """

    if compact:
        return make_compact_peer_list(peer_list)
    else:
        return make_peer_list(peer_list)
    
def make_compact_peer_list(peer_list):
    """ Return a compact peer string, given a list of peer details. """

    peer_string = ""
    for peer in peer_list:
        ip = inet_aton(peer[1])
        port = pack(">H", int(peer[2]))

        peer_string += (ip + port)

    return peer_string

def make_peer_list(memory, cpu, no_of_peers):
    """ Return an expanded peer list suitable for the client, given
    the peer list. """
    
    peers = []
    for peer in Peer.select().where(Peer.memory > memory, Peer.Status == 'active', Peer.type == 'provider'):
        peers.append(model_to_dict(peer))
        
    return peers

class RequestHandler(BaseHTTPRequestHandler):
    def do_GET(s):
        """ Take a request, do some some database work, return a peer
        list response. """

        # Decode the request
        package = decode_request(s.path)
        print package
        if not package:
            s.send_error(403)
            return

        # Get the necessary info out of the request
        info_hash = package["info_hash"][0]
        type = package["type"][0]
        ip = s.client_address[0]
        port = package["port"][0]
        peer_id = package["peer_id"][0]
        cpu = package["cpu"][0]
        memory = package["memory"][0]
        no_of_peers = package["no_of_peers"][0]
        accountno = package["accountno"][0]
        enodeid = package["enodeid"][0]
        
        peer_list = []
        
        if type == "provider":
            peer = add_peer(peer_id, ip, cpu, memory, 'active', type, accountno)
            peer_list.append(model_to_dict(peer))
        else:
            peer_list = make_peer_list(memory, cpu, no_of_peers)
        
        print peer_list
        #add_peer(s.server.torrents, info_hash, peer_id, ip, port)

        # Generate a response
        response = {}
        response["interval"] = s.server.interval
        response["peers"] = peer_list

        # Send off the response
        s.send_response(200)
        s.end_headers()
        data_string = json.dumps(response)
        s.wfile.write(data_string)

        # Log the request, and what we send back
        info("PACKAGE: %s", package)
        info("RESPONSE: %s", response)

    def log_message(self, format, *args):
        """ Just supress logging. """

        return

class Tracker():
    def __init__(self, host = "", port = 9010, interval = 5, \
        torrent_db = "tracker.db", log = "tracker.log", \
        inmemory = True):
        """ Read in the initial values, load the database. """

        self.host = host
        self.port = port

        self.inmemory = inmemory

        self.server_class = HTTPServer
        self.httpd = self.server_class((self.host, self.port), \
            RequestHandler)

        self.running = False    # We're not running to begin with

        self.server_class.interval = interval

        # Set logging info
        basicConfig(filename = log, level = INFO)


    def runner(self):
        """ Keep handling requests, until told to stop. """

        while self.running:
            self.httpd.handle_request()

    def run(self):
        """ Start the runner, in a seperate thread. """

        if not self.running:
            self.running = True

            self.thread = Thread(target = self.runner)
            self.thread.start()

    def send_dummy_request(self):
        """ Send a dummy request to the server. """

        # To finish off httpd.handle_request()
        address = "http://127.0.0.1:" + str(self.port)
        urlopen(address)

    def stop(self):
        """ Stop the thread, and join to it. """

        if self.running:
            self.running = False

            self.send_dummy_request()
            self.thread.join()

    def __del__(self):
        """ Stop the tracker thread, write the database. """

        self.stop()
        self.httpd.server_close()

if __name__ == '__main__':
    tracker = Tracker()
    tracker.run()