#!/usr/bin/env python
# -*- coding: utf-8 -*-
import socket # Network
import sys # Various things
import json # Encode array in json for transport
from include import CArgs # Argument parsing
from include import CLogs # Import Clogs from path
from include import CConfig # Import Config Class to read config file
#
# This script provide a server to share Game Names, players and so on ! 
#

class CMasterServer:
   def __init__(self,NetIp,NetPort,Logs):
      self.TCP_IP = NetIp
      self.TCP_PORT = NetPort
      self.BUFFER_SIZE = 4096  # Usually 1024, unit is char in this case
      # Create socket object
      self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
      # Set socket options
      self.s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
      self.s.bind((self.TCP_IP, self.TCP_PORT))
      self.s.listen(20) # Max number of clients
      self.Games = [] # Init Games array
      self.MsgQueue = [] # Queue of Message Dict
      self.colorlist = [color for color in range(31,39)] # First color will be red, and then green, yellow, blue, rose, cyan, grey, and back to first color.
      self.Logs=Logs
      self.delim='|' # Delimiter for msg - so the client knows that the end of the msg has been reached
#
# Main loop 
#
   def __main__(self,Config):
      self.color = {}
      self.Games=[]
      self.Config=Config
      i=0
      pl=1
      nbgames=26
      if self.Config.GetValue('SectionAdvanced','mastertest'):# if test mode
         for i in range(1,nbgames+1):
            if pl==13:
               pl=1
            self.Games.append({'STATUS':'OPEN','GAMENAME':'SAMPLEGAME{}'.format(i),'SERVERIP':'1.2.3.{}'.format(i),'SERVERPORT':1234,'PLAYERS':pl})
      while True:
         data=""
         self.cx, addr = self.s.accept()
         cxid="{}-{}".format(addr[0],addr[1])
         self.Logs.Log("DEBUG","{} client joined server on port {}.".format(addr[0],addr[1]))
         try:
            data = self.cx.recv(self.BUFFER_SIZE) # Buffer_size stands for bytes of data to be received
         except:
            pass # Nothing to receive - pass
         if data!="":
            try:
               Ddata=json.loads(str(data.decode('UTF-8')))
               req=Ddata['REQUEST']
            except:
               self.Logs.Log("ERROR","Received non JSON data : {}".format(data))
               Ddata=None
               req=None
            print(Ddata)
            # Please create Game :)
            if req == 'CREATION':
               self.Logs.Log("DEBUG","Hu hu ! We received a creation notice :) from {}. We put it in storage.".format(cxid))
               #Ddata=json.loads(str(data.decode('UTF-8)))
               del Ddata['REQUEST']
               #Ddata['ID']=cxid
               Ddata['STATUS']='OPEN'
               self.Games.append(Ddata)
            # Add thoses people to the game
            elif req == 'JOIN':
               for G in self.Games:
                  if G['GAMENAME']==Ddata['GAMENAME']:
                     G['PLAYERS']+=int(Ddata['PLAYERS'])
               self.Logs.Log("DEBUG","We received a join notice :) from {}. We add players.".format(cxid))
            # Remove those players from the game
            elif req == 'LEAVE':
               for G in self.Games:
                  if G['GAMENAME']==Ddata['GAMENAME']:
                     G['PLAYERS']-=int(Ddata['PLAYERS'])
               self.Logs.Log("DEBUG","We received a leaving notice :) from {}. We remove players.".format(cxid))
            # Please give me a list of available games !!
            elif req == 'LIST':
               del Ddata['REQUEST']
               self.Logs.Log("DEBUG","Hu hu ! We received a listing request :) from {}. Let send it.".format(cxid))
               if (len(self.Games)==0):
                  self.Logs.Log("WARNING","List is empty. Sending notice of emptiness")
                  r={'RESPONSE':'EMPTY'}
               else:
                  r=self.Games
               r=json.dumps(r).encode('UTF-8')
               #print(r)
               self.send(r)
            # Please delete the game - based on game name
            elif req == 'REMOVAL' :
               index = self.FindIndex(Ddata['GAMENAME'])
               self.Logs.Log("DEBUG","Let's go ! We received a removing request ! from {} for game {} indexed {} . Let remove it.".format(cxid,Ddata['GAMENAME'],index))
               try:
                  del self.Games[index]
               except:
                  self.Logs.Log("ERROR","Unable to remove game {}".format(Ddata['GAMENAME']))
            else:
               self.Logs.Log("ERROR","Unhandled message : {}".format(data))
         self.Logs.Log("DEBUG","Closing connexion with {}".format(cxid))
         self.cx.close()

#
# Send the msg and append the delimiter
#
   def send(self,msg):
      self.cx.send("{}{}".format(msg,self.delim))

   def FindIndex(self,gamename):
      for K,Game in enumerate(self.Games):
         if Game['GAMENAME']==gamename:
            return K
      return False
      
      
#
# Init
#
#
Logs = CLogs.CLogs()
Args = CArgs.CArgs()
Config=CConfig.CConfig(Args,Logs)
ConfigGlobals=Config.ReadConfigFile("SectionGlobals") # Read config file for main configuration
ConfigAdvanced=Config.ReadConfigFile("SectionAdvanced") # Read config file for main configuration
Logs.SetConfig(Config)
Args.SetLogs(Logs)

# Verbosity
debuglevel = int(Config.GetValue('SectionGlobals','debuglevel'))
if debuglevel>=1 and debuglevel<=4:
   Logs.UpdateFacility(debuglevel)

# Getting Interface or setting default
ServerInterface = Config.GetValue('SectionAdvanced','listen')

# Setting Ip from interface
ServerIp = Args.get_ip_address(ServerInterface)

if ServerIp==None:
   Logs.Log("FATAL","Unable to determine Ip address from interface {}. Use -h for help.".format(ServerInterface))
   sys.exit(1)
# Getting port or set default
ServerPort = int(Config.GetValue('SectionGlobals','masterport'))

Logs.Log("DEBUG","Starting Master Server on interface {} ({}), on port {}".format(ServerInterface,ServerIp,ServerPort))

#
# Launch
#
Master=CMasterServer(ServerIp,ServerPort,Logs)
Master.__main__(Config)


