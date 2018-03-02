#!/usr/bin/env python

import socket
import time
import sys
import select
import json
#import config

class CClient():
   def __init__(self,Logs,Config):
      self.BUFFER_SIZE = 256 # unit is char in our case
      self.Logs=Logs
      self.wait4gametimeout=60
      self.Config=Config
      self.timeout = 3600 # Time for an open connexion timeout (1 hour)
      self.cx_timeout = 10 # Timeout for a connexion (in seconds)
#
# Join selected server
#
   def connect_host(self,TCP_IP,TCP_PORT):
      self.cx = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
      self.cx.settimeout(self.cx_timeout)
      self.cx.connect((TCP_IP, TCP_PORT))
      self.cx.settimeout(None)
      #s.setblocking(0)

#
# PLAY and wait that someone play
#
   def play(self,actualround,actualplayer,playerlaunch,Message):
      d={'GAMENAME':self.gamename,'REQUEST':'PLAY','ACTUALPLAYER':actualplayer,'ACTUALROUND':actualround,'PLAYERLAUNCH':playerlaunch,'PLAY':Message}
      self.send(d)
      
   def WaitSomeonePlay(self,actualround,actualplayer,playerlaunch,waitfor=False):
      if waitfor==False:
         r={'GAMENAME':self.gamename,'REQUEST':'WAIT4PLAYER','ACTUALPLAYER':actualplayer,'ACTUALROUND':actualround,'PLAYERLAUNCH':playerlaunch}
      else:
         r={'GAMENAME':self.gamename,'REQUEST':'WAIT4PLAYER','ACTUALPLAYER':actualplayer,'ACTUALROUND':actualround,'PLAYERLAUNCH':playerlaunch,'WAITFOR':waitfor}
      self.send(r)
      d={}
      d['REQUEST']=None
      d['ACTUALPLAYER']=None
      d['ACTUALROUND'] = None
      d['PLAYERLAUNCH'] = None
      if not waitfor:
         while d['REQUEST'] != 'SOMEONEPLAYED' or d['ACTUALPLAYER'] != actualplayer or d['ACTUALROUND'] != actualround or d['PLAYERLAUNCH']!=playerlaunch:
            d = self.rcv()
         self.Logs.Log("DEBUG","Received acceptable hit : {} from remote server.".format(d['PLAY']))
         return d['PLAY'].upper()
      else:
         while d['REQUEST'] != 'SOMEONEPLAYED' or d['ACTUALPLAYER'] != actualplayer or d['ACTUALROUND'] != actualround or d['PLAYERLAUNCH']!=playerlaunch or d['PLAY']!=waitfor:
            d = self.rcv()
         self.Logs.Log("DEBUG","Received {} from remote server, as expected !".format(d['PLAY']))
         return d['PLAY'].upper()

#
# Send Player Names (in one line, comma separated)
#
   def sendPlayers(self,names):
      d={'GAMENAME':self.gamename,'REQUEST':'HEREAREPLAYERNAMES','PLAYERNAMES':names}
      self.send(d)
#
# Get player names (in one line, comma separated). The Ack is the player names return
#

   def GetPlayers(self): # JSON
      d={'GAMENAME':self.gamename,'REQUEST':'PLAYERNAMES'}
      self.send(d)
      data=[]
      while "PLAYERNAMES" not in data:
         data = self.rcv()
      return data["PLAYERNAMES"]
      
#
# Game Options
#   
   def sendOpts2(self,Opts,nbdarts): # JSON
      d={'GAMENAME':self.gamename,'REQUEST':'HEREAREGAMEOPTS','GAMEOPTS':Opts,'NBDARTS':nbdarts}
      self.send(d)

   def getOpts2(self): # JSON
      r={'GAMENAME':self.gamename,'REQUEST':'GAMEOPTS'}
      d={}
      self.send(r)
      while 'GAMEOPTS' not in d:
         d = self.rcv()
         #time.sleep(1)
      return d['GAMEOPTS']
         
#
# Send Choosed Game to server. Wait for an ACK
#

   def sendGame(self,ChoosedGame):
      d={'GAMENAME':self.gamename,'REQUEST':'HEREISCHOOSEDGAME','CHOOSEDGAME':ChoosedGame}
      self.send(d)
      
#
# Get the game from master server - JSON
#
   def getGame(self):
      d={'GAMENAME':self.gamename,'REQUEST':'GETCHOOSEDGAME'}
      self.send(d)
      data=[]
      while "CHOOSEDGAME" not in data:
         data = self.rcv()
      return data["CHOOSEDGAME"]
#
# Get Random values
#
   def getRandom(self,actualround,actualplayer,playerlaunch):
      r={'GAMENAME':self.gamename,'REQUEST':'RANDOMVALUES','ACTUALROUND':actualround,'ACTUALPLAYER':actualplayer,'PLAYERLAUNCH':playerlaunch}
      self.send(r)
      d={}
      d['REQUEST']=None
      d['ACTUALPLAYER']=None
      d['PLAYERLAUNCH']=None
      d['ACTUALROUND']=None
      while d['REQUEST']!="RANDOMVALUES" or d['ACTUALPLAYER']!=actualplayer or d['ACTUALROUND']!=actualround or d['PLAYERLAUNCH']!=playerlaunch:
         d = self.rcv()
      self.Logs.Log("DEBUG","Received acceptables random values {} for player {}".format(d['RANDOMVALUES'],d['ACTUALPLAYER']))
      return d['RANDOMVALUES']
      
#
# Send Random values
#
   def sendRandom(self,rand,actualround,actualplayer,playerlaunch):
      d={'GAMENAME':self.gamename,'REQUEST':'HEREARERANDOMVALUES','RANDOMVALUES':rand,'ACTUALPLAYER':actualplayer,'ACTUALROUND':actualround,'PLAYERLAUNCH':playerlaunch}
      self.send(d)

#
# Request server version
#

   def GetServerVersion(self,gamename):
      self.Logs.Log('DEBUG','Getting server version...')
      d={'REQUEST':'GETVERSION','GAMENAME':gamename}
      self.send(d)
      while d['REQUEST'] != "VERSION":
         d = self.rcv()
      return d['VERSION']

#
# Tell the server that the client is ready to play
#

   def IAmReady(self,nblocalplayers):
      d={'GAMENAME':self.gamename,'REQUEST':'READY','NBLOCALPLAYERS':nblocalplayers}
      self.send(d)
      time.sleep(1)
      d={'GAMENAME':self.gamename,'REQUEST':'ISEVERYBODYREADY'}
      self.send(d)
      while d['REQUEST']!='EVERYBODYISREADY':
         d = self.rcv()

   def SendLocalPlayers(self,Players):
      s={'GAMENAME':self.gamename,'REQUEST':'READY','PLAYERSNAMES':Players}
      self.send(s)
      d={}
      while 'REQUEST' not in d:
         d = self.rcv()
      return d
         
#
# Explicitely tell the server we are leaving
#
   def close_host(self):
      time.sleep(1)
      d={'GAMENAME':self.gamename,'REQUEST':'EXIT'}
      self.send(d)
      self.cx.close()



#
# New JSON Client implementation
#

# Send a message
   def send(self,message):
      self.Logs.Log("DEBUG","Sending to game server : {}... ".format(message))
      self.cx.send(json.dumps(message).encode('UTF-8'))
      self.Ack() # Wait for ACK for each message

#
# Wait for a message
#

   def rcv(self):
      d=""
      while True:
         try:
            self.cx.settimeout(self.timeout)
            time.sleep(0.1)# Avoid consuming all cpu
            d = self.cx.recv(self.BUFFER_SIZE)
            d=json.loads(str(d.decode('UTF-8')))
            self.cx.settimeout(None)
         except:
            self.Logs.Log("FATAL","Bad data received or timeout ({}) has been reached for connection with game server. Aborting.".format(self.timeout))
            sys.exit(2)
         if d=="":
            self.Logs.Log("DEBUG","Connection closed or bad data received from game server. Aborting.")
            sys.exit(3)
         self.Logs.Log("DEBUG","Received : {}".format(d))
         return d
      
   def Ack(self):
      ACK_BUFFER=18
      d={'REQUEST':None}
      while d['REQUEST']!='ACK':
         f = self.cx.recv(ACK_BUFFER)
         try:
            d=json.loads(str(f.decode('UTF-8')))
         except:
            pass
      self.Logs.Log("DEBUG","Received : {}".format(d))
      return True
      

#
# Join a game (json version)
#
   def join2(self,gamename):
      self.gamename = gamename
      tab={'REQUEST':'JOIN','GAMENAME':gamename}
      self.send(tab)
      # The server should return one of the following
      data={}
      while "NETSTATUS" not in data:
         data=self.rcv()
      # Return
      return str(data['NETSTATUS'])


   def LeaveGame(self,gamename,LoPl,NetStatus):
      d={'REQUEST':'LEAVE','GAMENAME':gamename,"NETSTATUS":NetStatus,"PLAYERSNAMES":LoPl}
      self.send(d)
###################
# Join Globals Game List servers to get game list - if they exists
###################

class MasterClient():
   def __init__(self,Logs):
      self.BUFFER_SIZE = 4096 # unit is char in our case - bigger
      self.Logs=Logs
      self.cx_timeout=10

   def connect_master(self,TCP_IP,TCP_PORT):
      self.cx = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
      self.cx.settimeout(self.cx_timeout)
      self.cx.connect((TCP_IP, TCP_PORT))
      self.cx.settimeout(None)

#
# Wait for Listing
#

   def wait_list(self,NuPl):
      GotIt=False
      while GotIt==False:
         self.send({'REQUEST':'LIST'})
         d = self.rcv()
         if d!="":
            try:
               d=json.loads(d)
            except:
               self.Logs.Log("ERROR","Error loading json data for : {}".format(d))
            if 'RESPONSE' in d and d['RESPONSE']=='EMPTY':
               return False
            else:
               serverlist=d
               GotIt=True
      # Clean list from all games where there is not enough room for us
      i=0
      filtered_serverlist = []
      for L in serverlist:
         if int(L['PLAYERS']) + int(NuPl) <= 12: # If it goes up to the max number of players
            filtered_serverlist.append(serverlist[i])
         i+=1
      if len(filtered_serverlist)==0:
         return False
      else:
         return filtered_serverlist
#
# Send a message to the server
#
   def send(self,message): # JSON
      self.Logs.Log("DEBUG","Sending to master server : {}... ".format(message))
      self.cx.send(json.dumps(message).encode('UTF-8'))
      
 
   def SendGameInfo(self,servername,serveralias,serverport,netgamename,NuPl):
      if not serveralias:
         ip=servername
      else:
         ip=serveralias
      tab={'REQUEST':'CREATION','SERVERIP':ip,'SERVERPORT':serverport,'GAMENAME':netgamename,'PLAYERS':NuPl}
      self.send(tab)
      
      
   def JoinaGame(self,gamename,NuPl):
      tab={'REQUEST':'JOIN','GAMENAME':gamename,'PLAYERS':NuPl}
      self.send(tab)

   def LeaveaGame(self,gamename,NuPl):
      tab={'REQUEST':'LEAVE','GAMENAME':gamename,'PLAYERS':NuPl}
      self.send(tab)
#
# Send a removal query to server
#
   def RemoveGame(self,GameName):
      tab={'REQUEST':'REMOVAL','GAMENAME':GameName}
      self.send(tab)

#
# Explicitely tell the server we are leaving
#
   def close_cx(self):
      self.cx.close()

#
# Receive Data and be sure that the end has been reached
#
   def rcv(self,delim='|'):
      buf = ''
      data = True
      while True:
         time.sleep(0.1)# Avoid consuming all cpu
         data = self.cx.recv(self.BUFFER_SIZE)
         buf += data.decode('utf-8')
         if buf.find(delim):
            msg = buf.split(delim, 1)
            return str(msg[0])
