'''
Created by sumeet Khule
Referred to code from beertorrent : https://github.com/Ezibenroc/beertorrent/tree/master/src
'''

from hashlib import md5, sha1
from random import choice
import socket
from struct import pack, unpack
from threading import Thread
from time import sleep, time
import types
from urllib import urlencode, urlopen

from bencode import decode, encode
import json
import sys
from sys import argv
import argparse
import re
import subprocess
import os
import socket

CLIENT_NAME = "pyp2p"
CLIENT_ID = "PY"
CLIENT_VERSION = "0001"

def generate_peer_id():
    """ Returns a 20-byte peer id. """

    # As Azureus style seems most popular, we'll be using that.
    # Generate a 12 character long string of random numbers.
    random_string = ""
    while len(random_string) != 12:
        random_string = random_string + choice("1234567890")

    return "-" + CLIENT_ID + CLIENT_VERSION + "-" + random_string

def make_tracker_request(info_hash, peer_id, tracker_url, type_peer, accountno, enodeid, memory):
    """ Given a torrent info, and tracker_url, returns the tracker
    response. """
    
    # Generate a tracker GET request.
    payload = {
            "peer_id" : peer_id,
            "port" : 6881,
            "cpu" : 1,
            "memory" : memory,
            "info_hash" : info_hash,
            "type" : type_peer,
            "no_of_peers" : 0,
            "accountno" : accountno,
        "enodeid" : enodeid
            }
    payload = urlencode(payload)

    # Send the request
    response = urlopen(tracker_url + "?" + payload).read()

    return response



def decode_port(port):
    """ Given a big-endian encoded port, returns the numerical port. """

    return unpack(">H", port)[0]

def generate_handshake(info_hash, peer_id):
    """ Returns a handshake. """

    protocol_id = "BitTorrent protocol"
    len_id = str(len(protocol_id))
    reserved = "00000000"

    return len_id + protocol_id + reserved + info_hash + peer_id

def send_recv_handshake(handshake, host, port):
    """ Sends a handshake, returns the data we get back. """

    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((host, port))
    s.send(handshake)

    data = s.recv(len(handshake))
    s.close()

    return data

def make_torrent_file(tracker = None, comment = None):
    """ Returns the bencoded contents of a torrent file. """

    
    if not tracker:
        raise TypeError("make_torrent_file requires at least one tracker, non given.")

    torrent = {}

    # We only have one tracker, so that's the announce
    if type(tracker) != list:
        torrent["announce"] = tracker
    # Multiple trackers, first is announce, and all go in announce-list
    elif type(tracker) == list:
        torrent["announce"] = tracker[0]
        # And for some reason, each needs its own list
        torrent["announce-list"] = [[t] for t in tracker]

    torrent["creation date"] = int(time())
    torrent["created by"] = CLIENT_NAME
    if comment:
        torrent["comment"] = comment
    torrent["info"] = '200'
    return torrent

    
def gettaskname():
    host = ''        # Symbolic name meaning all available interfaces
    port = 9020     # Arbitrary non-privileged port
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind((host, port))
    s.listen(1)
    conn, addr = s.accept()
    print('Connected by', addr)
    data = conn.recv(200)
    return data

def sendtaskname(host, agentname, enodeid):
    port = 9020                   # The same port as used by the server
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((host, port))
    s.sendall(host + ' ' + agentname + ' ' + enodeid)
    
def setup_ethereum():
    p1 = os.system('~/ethereum/ether.sh')
    file = open("data.txt")
    data = file.read()
    p = re.compile("enode: (.*)")
    enodeid = p.search(data).group(1)
    print enodeid
    file = open("accountno.txt")
    accountno = file.read()
    temp_list = []
    temp_list.append(enodeid)
    temp_list.append(accountno)
    return temp_list

class TorrentClient():
    def __init__(self, tracker, type_peer, memory):
        self.running = False
        self.type_peer = type_peer
        self.data = make_torrent_file(tracker)
        self.info_hash = sha1(encode(self.data["info"])).digest()
        print self.info_hash
        self.peer_id = generate_peer_id()
        self.handshake = generate_handshake(self.info_hash, self.peer_id)
        self.temp_list = setup_ethereum()
        self.enodeid = self.temp_list[0]
        self.accountno = self.temp_list[1]
        self.data_loaded = ''    
        self.memory = memory

    def perform_tracker_request(self, url, info_hash, peer_id, accountno, enodeid, memory):
        """ Make a tracker request to url, every interval seconds, using
        the info_hash and peer_id, and decode the peers on a good response. """

        #while self.running:
        print 'Making Tracker Request.'
	self.tracker_response = make_tracker_request(info_hash, peer_id, url, self.type_peer, accountno, enodeid, memory)
        self.data_loaded = json.loads(self.tracker_response)

        """if "failure reason" not in self.tracker_response:
        self.peers = get_peers(self.tracker_response["peers"])
        sleep(self.tracker_response["interval"])"""
    
    def run(self):
        """ Start the torrent running. """
        try:
            if not self.running:
                self.running = True

                self.perform_tracker_request(self.data["announce"], self.info_hash, self.peer_id, self.accountno, self.enodeid, self.memory)
                if self.type_peer=='provider':
                    print "Registered as provider. Waiting for task from requestor"
		    taskname = gettaskname()
                    ip = taskname.split(' ')[0]
                    agentname = taskname.split(' ')[1]
		    print 'Task Received: ' + agentname + ' from ' + ip
                    req_enodeid = taskname.split(' ')[2]
                    req_enodeid = req_enodeid.split('@')[0]
                    final_enodeid = req_enodeid + '@' + ip + ':30303\"'
                    p1 = subprocess.Popen(['geth','attach',os.path.expanduser('~/ethereum/geth.ipc')], stdout=subprocess.PIPE, stdin=subprocess.PIPE, stderr=subprocess.PIPE)
                    stdout_data = p1.communicate(input='admin.addPeer(' + final_enodeid + ')')[0]
                    p1 = os.system('go run ~/fog/' + agentname +'.go')
                else:
		    print "Providers are: "
		    for i in range(0,3):
                        print self.data_loaded["peers"][i]["ip"]
                    for i in range(0,3):
                        req_enodeid = self.data_loaded["peers"][i]["enodeid"]
                        req_enodeid = req_enodeid.split('@')[0]
                        final_enodeid = req_enodeid + '@' + self.data_loaded["peers"][i]["ip"] + ':30303\"'
                        p1 = subprocess.Popen(['geth','attach',os.path.expanduser('~/ethereum/geth.ipc')], stdout=subprocess.PIPE, stdin=subprocess.PIPE, stderr=subprocess.PIPE)
                        stdout_data = p1.communicate(input='admin.addPeer(' + final_enodeid + ')')[0]
                    sendtaskname(self.data_loaded["peers"][0]["ip"], 'agent1' , self.data_loaded["peers"][0]["enodeid"])
                    sendtaskname(self.data_loaded["peers"][1]["ip"], "agent2", self.data_loaded["peers"][1]["enodeid"])
                    sendtaskname(self.data_loaded["peers"][2]["ip"], "agent3", self.data_loaded["peers"][2]["enodeid"])
                    sleep(10)
                    for i in range(0,3):
                        p1 = subprocess.Popen(['geth','attach',os.path.expanduser('~/ethereum/geth.ipc')], stdout=subprocess.PIPE, stdin=subprocess.PIPE, stderr=subprocess.PIPE)
                        stdout_data = p1.communicate(input='eth.sendTransaction({from: eth.accounts[0], to: ' + self.data_loaded["peers"][i]["accountno"] + ', value: web3.toWei(2, "ether")})')[0]
                    p1 = os.system('go run ~/fog/fog.go')
        except KeyboardInterrupt:
            self.type_peer = 'inactive'
            self.perform_tracker_request(self.data["announce"], self.info_hash, self.peer_id, self.accountno, self.enodeid, self.memory)
            
    def stop(self):
        """ Stop the torrent from running. """

        if self.running:
            self.running = False

            self.tracker_loop.join()




if __name__ == '__main__':
    '''write_torrent_file('my.torrent', 'http://127.0.0.1:9010')'''
    parser = argparse.ArgumentParser(description='Example with long option names')
    parser.add_argument('--type', action="store", dest="type_peer")
    parser.add_argument('--memory', action="store", dest="memory")
    results = parser.parse_args()
    type_peer = results.type_peer
    memory = results.memory
    client = TorrentClient('http://10.11.10.1:9010', type_peer, memory)
    client.run()
    

