#!/usr/bin/env python
#-*- coding: utf-8 -*-

#########
# External classes and system requirement checks
#########
try:
   # To use exit...
   import sys
   # To use time.sleep
   import time
   #To browse folders...
   import os, os.path
   # Pygame is the main dependancy
   import pygame
   from pygame.locals import *
   # Pyserial is capital :) !
   import serial
   # Json used for communications with Web Services
   import json
   # Python array deep copy (backup turn)
   from copy import deepcopy
   # Threading for keyboard...
   from threading import Thread
   #
except Exception as e: # Report error
	print("[FATAL] Unable to load at least one dependancy : pygame|pyserial|json|copy|netifaces|threading. Please install them (and check wiki if needed).")
	print("[FATAL] Error was {}".format(e))
	sys.exit(1)

################
# Import pyDarts internal classes
################

# Config file
from include.config import *
# All classes
from include import CScreen
from include import CPlayer
from include import CInput
from include import CConfig
from include import CArgs
from include import CPatchs
from include import CLogs
from include import CClient
from include import CLocale

# Sys requirements check
if sys.version[:3] not in python_versions:
   print("[FATAL] Your version of python {} is not pydarts compatible. Please execute pydarts with one of this version of python : {}.".format(sys.version,python_versions))
   sys.exit(1)

########################
# Create various instances of internal classes
########################
# Starts logger system, it will filter on a config basis
Logs=CLogs.CLogs()
# To manage cli opts
Args = CArgs.CArgs()
# This one handle Config File - Serial is used to try to detect serial port
Config=CConfig.CConfig(Args,Logs)
# Check local config file existance and create if necessary
Config.CheckConfigFile()
# Read hidden default values
Config.ReadConfigFile("SectionAdvanced")
# Read config file for main configuration and store it in object data storage
Config.ReadConfigFile("SectionGlobals")
# Read Config file for keys combination : Arduino send a key=> it correspond to a hit
ConfigKeys=Config.ReadConfigFile("SectionKeys")
# Update Logs system with loglevel set in config
Logs.SetConfig(Config)
# Create locale instance
Lang=CLocale.GTLocale(Logs,Config)
# Manage display
myDisplay = CScreen.CScreen(Config,Logs,Lang)
# Manage mouse events
Inputs = CInput.CInput(Logs,Config,myDisplay)
myDisplay.SetInputs(Inputs) # Give input object to screen object
# Object used to apply patches
Patch = CPatchs.CScoresPatches(Logs)
#Patch.Patch_08_01_Score_format() # New score format starting from v0.8
# Client of Master Server
NetMasterClient = CClient.MasterClient(Logs)


##########
# SOFTWARE LOOP
##########

###### Wizard menu
if not Config.configfileexists or Config.GetValue('SectionAdvanced','forcecalibration'):
   Logs.Log("DEBUG","Launching serial input wizard")
   Config.FindSerialPort()#At this step, multiple serial port can be found
   # If there is multiple available devices
   if Config.detectedserialport and (len(Config.detectedserialport)>1 or Config.GetValue('SectionAdvanced','forcecalibration')):
      selectedport = myDisplay.SelectPort(Config.detectedserialport)#At this step, we display a menu to force the user to choose a port (Config.detectedserialport is a list)
      Config.detectedserialport = selectedport# We pass the selected port to the config object (selectedport is not a list anymore)
      Logs.Log("DEBUG","You chose port {}.".format(Config.detectedserialport))
   elif Config.detectedserialport and len(Config.detectedserialport)==1:
      Config.detectedserialport = Config.detectedserialport[0]
      Logs.Log("DEBUG","Using detected serial port {}".format(Config.detectedserialport))
   else:
      Logs.Log("WARNING","No suitable serial port detected.")

   # Connect
   Inputs.Serial_Connect()# We connect with the unique selected port
   # Display first use wizard
   NewConfigKeys = myDisplay.GetConfig()
   # Write config file
   Config.WriteConfigFile(NewConfigKeys)
   # Read it
   ConfigKeys=Config.ReadConfigFile("SectionKeys")#Refresh new keys
   # Pass config to input object
   Inputs.ConfigKeys = ConfigKeys
else:
   # Init serial
   Inputs.Serial_Connect()# We connect with the unique selected port

# Init
MatchQty=0 # Count number of matches
solo=int(Config.GetValue('SectionGlobals','solo'))
Logs.Log("DEBUG","Solo option is set to : {} ms".format(solo))
LoPl=[]
StatsScreen = False#Return value of Stats Screen (start again a new game with same parameters)
GT = None# Game type
directplay = False#Direct play functionnlity (play without having to use menus)
netgamename = Config.GetValue('SectionAdvanced','netgamename',False) # Game Name
servername = Config.GetValue('SectionAdvanced','servername',False) # Server ip or name
serveralias = Config.GetValue('SectionAdvanced','serveralias',False) # Server alias
serverport = Config.GetValue('SectionAdvanced','serverport') # Server port
GT = Args.GetGameType(Config.GetValue('SectionAdvanced','gametype',False)) # Game type (local,netmaster,netmanual)
localplayers = Config.GetValue('SectionAdvanced','localplayers',False) # Local players
selectedgame = Config.GetValue('SectionAdvanced','selectedgame',False) # Selected game

while True:
   
   # Init network data
   NetStatus = None # Master or slave

   #############################
   # NEW MENUS SEQUENCE
   #############################

   ######
   # Start straight forward is all required information are already given
   if GT=='local' and StatsScreen=='startagain':
      menu=True
   # Direct Play mode
   elif GT=='local' and localplayers and selectedgame:
      try:
         LoPl = localplayers.split(",")
         Game = selectedgame
         menu=True
         NuPl = len(LoPl)
         AllPl = LoPl
         ChoosedGame = __import__("games.{}".format(Game), fromlist=["games"])
         # Merge config file options and default game options
         GameOpts_Default = ChoosedGame.GameOpts
         GameOpts_Config = Config.ReadConfigFile(selectedgame)# Take config file Game options if they exists
         if not GameOpts_Config:GameOpts_Config={}# Default to empty dict
         GameOpts = GameOpts_Default.copy()
         GameOpts.update(GameOpts_Config)
         # Enable Direct Play mode
         directplay = True
      except Exception as e:
         Logs.Log("ERROR","Unable launch Direct Play mode. Error was {}".format(e))
         menu='gametype'
   else:
      menu='gametype'
   # Or display menus
   while menu!=True:
      ########
      # GAME TYPE (LOCAL, NETWORK, NETWORK MANUAL)
      ########
      if menu=='gametype':
         GT=myDisplay.GameType()
         menu='players'

      ########
      # PLAYERS NAMES
      ########
      if menu=='players':
         LoPl=myDisplay.PlayersNamesMenu3(LoPl)# LoPl = Local Players
         if LoPl=='escape':
            menu='gametype'
            LoPl=[]
         elif GT=='netmaster' and LoPl!='escape':
            menu='serverlist'
         elif GT=='netmanual' and LoPl!='escape':
            menu='netoptions'
         elif GT=='local' and LoPl!='escape':
            menu='gamelist'
         NuPl = len(LoPl)# NuPl = Number of players

      ########
      # NETWORK MASTER SERVER
      ########
      if GT=='netmaster' and menu=='serverlist':   # Connexion to master server if requested
         menu='connect'
         NetSettings=myDisplay.ServerList(NetMasterClient,NuPl)
         if NetSettings == 'escape':
            menu='players'
         else:
            netgamename=NetSettings['GAMENAME']
            servername=NetSettings['SERVERIP']
            serverport=NetSettings['SERVERPORT']
            serveralias=servername

      ########
      # NETWORK MANUAL
      ########
      if GT=='netmanual' and menu=='netoptions':   # Display menu to manually setup or check network settings
         menu='connect'
         NetSettings=myDisplay.NetOptions()
         if NetSettings=='escape':
            menu='players'
         else:
            netgamename=NetSettings['GAMENAME']
            servername=NetSettings['SERVERIP']
            serverport=NetSettings['SERVERPORT']
            serveralias=NetSettings['SERVERALIAS']

      ########
      # NET CONNECTION
      ########
      # If network, connect to server and force the SOLO MODE OFF from config (players must push PLAYERBUTTON every rounds - mandatory for network
      if (GT=='netmaster' or GT=='netmanual') and menu=='connect':
         Logs.Log("DEBUG","Net game requested. Please report bugs on official website !")
         NetClient = CClient.CClient(Logs,Config)
         solo = 0
         try:
            myDisplay.DisplayBackground()
            myDisplay.InfoMessage([Lang.lang('game-client-connecting')])
            NetClient.connect_host(servername,int(serverport))
            menu='net1'
         except Exception as e:
            Logs.Log("ERROR","Unable to reach server : {} on port : {}. Error is {}".format(servername,serverport,e))
            myDisplay.DisplayBackground()
            myDisplay.InfoMessage([Lang.lang('game-client-no-connection')],3000)
            menu='gametype'
      if (GT=='netmaster' or GT=='netmanual') and menu=='net1':   
         # Check server compatibility of client and server version first
         serverversion = NetClient.GetServerVersion(netgamename)
         myDisplay.VersionCheck(serverversion)
         menu='net2'
      # Then join
      if (GT=='netmaster' or GT=='netmanual') and menu=='net2':
         NetStatus = NetClient.join2(netgamename)
         if NetStatus=='YOUAREMASTER':
            menu='gamelist'
         elif NetStatus=='YOUARESLAVE':
            menu='net3'
      ########
      # GAME SELECTION
      ########
      if (NetStatus=='YOUAREMASTER' or GT=='local') and menu=='gamelist': # Display game choice and option only for game creators (local and netmanual)
         Games=myDisplay.GetGameList()
         Game=myDisplay.GameList(Games)
         if Game=='escape' and NetStatus!=None:
            NetClient.LeaveGame(netgamename,LoPl,NetStatus)
            NetClient.close_host()
            menu='players'
         elif Game=='escape' and NetStatus==None:
            menu='gametype'
         else:
            ChoosedGame = __import__("games.{}".format(Game), fromlist=["games"])
            menu='gameoptions'

      ########
      # GAME OPTIONS
      ########
      if (NetStatus=='YOUAREMASTER' or GT=='local') and menu=='gameoptions': # Display game choice and option only for game creators (local and netmanual)
         GameOpts_Default = ChoosedGame.GameOpts
         GameOpts_Config = Config.ReadConfigFile(Game)# Take config file Game options if they exists
         if not GameOpts_Config:GameOpts_Config={}# Default to empty dict
         GameOpts = GameOpts_Default.copy()
         GameOpts.update(GameOpts_Config)
         GameOpts = myDisplay.OptionsMenu2(GameOpts,Game) ################# MENU 3
         if GameOpts=='escape' and NetStatus!=None:
            NetClient.LeaveGame(netgamename,LoPl,NetStatus)
            NetClient.close_host()
            menu='gametype'
         elif GameOpts=='escape' and NetStatus==None:
            menu='gametype'
         elif NetStatus==None:
            menu=True
         elif NetStatus!=None:
            menu='net3'

      # MasterPlayer send game info to server
      if NetStatus == 'YOUAREMASTER' and menu=='net3': # Send Game info (gamename and selected options - can be merged)
         NetClient.sendGame(Game)
         NetClient.sendOpts2(GameOpts,ChoosedGame.nbdarts) # 2
         menu='starting'
         try: # Check if it is the right place
            Logs.Log("DEBUG","Sending game info to master server {} on port {}".format(Config.GetValue('SectionGlobals','masterserver'),Config.GetValue('SectionGlobals','masterport')))
            NetMasterClient.connect_master(Config.GetValue('SectionGlobals','masterserver'),int(Config.GetValue('SectionGlobals','masterport')))
            NetMasterClient.SendGameInfo(servername,serveralias,serverport,netgamename,NuPl)
            NetMasterClient.close_cx()
            #time.sleep(1)
         except Exception as e:
            Logs.Log("WARNING","Unable to reach Master Server {} on port {}".format(Config.GetValue('SectionGlobals','masterserver'),Config.GetValue('SectionGlobals','masterport')))
      
      # Notice Master server that we joined and add local players to game on master server
      if NetStatus == 'YOUARESLAVE' and menu=='net3':
         try:
            NetMasterClient.connect_master(Config.GetValue('SectionGlobals','masterserver'),int(Config.GetValue('SectionGlobals','masterport')))
            NetMasterClient.JoinaGame(netgamename,len(LoPl))
            NetMasterClient.close_cx()
            menu='starting'
         except:
            Logs.Log("WARNING","Unable to add local players to Master Server")
      
      # If network enabled, all players is updated via network
      if NetStatus != None  and menu=='starting':
         AllPl=myDisplay.Starting(NetClient,NetStatus,LoPl)
         menu=True # Means that goes on...
         if AllPl==[] or AllPl==-1:# Empty network Player List or -1 signal
            NetClient.LeaveGame(netgamename,LoPl,NetStatus)
            NetClient.close_host()
            # For Slave Players, display the message and wait for Enter to be pressed
            if AllPl==[]:
               myDisplay.InfoMessage([Lang.lang('master-player-has-left')],0,None,'middle')
               NetMasterClient.connect_master(Config.GetValue('SectionGlobals','masterserver'),int(Config.GetValue('SectionGlobals','masterport')))
               NetMasterClient.RemoveGame(netgamename)
               NetMasterClient.close_cx()
               Inputs.ListenInputs(['arrows'],['escape','enter'])
            elif AllPl==-1:#Notice Master server that someone is leaving
               NetMasterClient.connect_master(Config.GetValue('SectionGlobals','masterserver'),int(Config.GetValue('SectionGlobals','masterport')))
               NetMasterClient.LeaveaGame(netgamename,len(LoPl))
               NetMasterClient.close_cx()
            menu='gametype'
         else:
            menu='net4'
      else:
         AllPl=LoPl # In local games, all players are local players
         NuPl = len(AllPl) # Refresh count of number of players again

      if NetStatus == 'YOUARESLAVE' and menu=='net4':
         NuPl = len(AllPl) # Refresh count of number of players again
         #Wait=NetClient.wait4GameReady2(myDisplay) # be sure that all information has been sent to server (from masterplayer)
         myDisplay.InfoMessage([Lang.lang('getting-info-from-server')],None,None,'middle')
         # Wait for the game name from server
         Game = NetClient.getGame()
         ChoosedGame = __import__("games.{}".format(Game), fromlist=["games"])
         GameOpts=NetClient.getOpts2()
         #debug - print GameOpts
         Logs.Log("DEBUG","Starting a network game of {} (with options {} with {} players : {}".format(Game,GameOpts,NuPl,AllPl))
         menu=True

      # Players are ready - game will be launch so we can delete game from master server
      if NetStatus == "YOUAREMASTER" and menu=='net4':
         NuPl = len(AllPl) # Refresh count of number of players again
         menu=True
         try:
            NetMasterClient.connect_master(Config.GetValue('SectionGlobals','masterserver'),int(Config.GetValue('SectionGlobals','masterport')))
            NetMasterClient.RemoveGame(netgamename)
            NetMasterClient.close_cx()
         except Exception as e:
            Logs.Log("WARNING","Unable to reach Master Server {} on port {} to remove game".format(Config.GetValue('SectionGlobals','masterserver'),Config.GetValue('SectionGlobals','masterport')))

   ######## END OF MENU LOOP ##########

   # At the very end, create players objects
   LSTJoueurs = []
   for x in range(0, NuPl):
      #Get Player color
      pcolor=list(myDisplay.ColorSet.values())[x]
      # Create Player object
      LSTJoueurs.append(ChoosedGame.CPlayerExtended(x,NuPl,Config,myDisplay.res))
      LSTJoueurs[x].InitPlayerColor(pcolor)
      LSTJoueurs[x].PlayerName = AllPl[x]

   ################
   # MATCH Loop
   ################

   # Match loop ends if MatchDone is true
   MatchDone = False
   # Round init
   actualround = 1
   # Player Launch Init
   playerlaunch = 1
   # Actual Player Init
   actualplayer = 0
   # Create Game objects and init var
   objGame = ChoosedGame.CGame(myDisplay,Game,NuPl,GameOpts,Config,Logs)
   # Dart Stroke Init
   DartStroke=-1
   # Increment the number of Match done
   MatchQty+=1
   # Backup of the Hit for a usage in following round
   Prev_DartStroke = None
   # Main loop (each dart a loop)
   while not MatchDone:
      #
      # Step 1 : The player plays
      #
      PreDartsChecks = -1
      PostDarts = -1
      EarlyPlayerButton = -1

      Logs.Log("DEBUG","###### NEW ROUND #########")
      Logs.Log("DEBUG","Game Round {}. Round of player {}. Dart {}.".format(actualround,LSTJoueurs[actualplayer].PlayerName,playerlaunch))
      # Pre Play Checks
      if NetStatus == 'YOUARESLAVE':
         try:
            randomval = NetClient.getRandom(actualround,actualplayer,playerlaunch)
            objGame.SetRandom(LSTJoueurs,actualround,actualplayer,playerlaunch,randomval)
         except Exception as e: 
            Logs.Log("ERROR","Problem getting and setting random value from master client : {}".format(e))
      #
      PreDartsChecks = objGame.PreDartsChecks(LSTJoueurs,actualround,actualplayer,playerlaunch)
      #
      if NetStatus == 'YOUAREMASTER':
         try:
            randomval = objGame.GetRandom(LSTJoueurs,actualround,actualplayer,playerlaunch)
            NetClient.sendRandom(randomval,actualround,actualplayer,playerlaunch)
         except Exception as e: 
            Logs.Log("ERROR","Problem sending random value to slave clients : {}".format(e))

      # If the player is allowed to play
      if PreDartsChecks != 4 and playerlaunch <= objGame.nbdarts:
         # First Dart special case - Display get ready !
         if playerlaunch  == 1:
            myDisplay.InfoMessage([Lang.lang('get-ready')],int(Config.GetValue('SectionGlobals','releasedartstime')),None,'middle','big')
            Inputs.Serial_Flush()
            myDisplay.InfoMessage([str(LSTJoueurs[actualplayer].PlayerName) + " : Go ! "],int(Config.GetValue('SectionGlobals','releasedartstime')),None,'middle','big')
            myDisplay.SoundStartRound(str(LSTJoueurs[actualplayer].PlayerName)) # Play sound for first dart (playername otherwise default)
            
         # Display board
         myDisplay.RefreshGameScreen(LSTJoueurs,actualround,objGame.GameOpts['totalround'],objGame.nbdarts - playerlaunch+1, objGame.nbdarts, objGame.GameLogo,objGame.Headers,actualplayer)
      
         # The player plays !
         if NetStatus==None or LSTJoueurs[actualplayer].PlayerName in LoPl:
            # If its a local game or our turn to play in a net game : We read serial.
            while True:
               DartStroke = Inputs.ListenInputs([],['PLAYERBUTTON','GAMEBUTTON','BACKUPBUTTON','TOGGLEFULLSCREEN'],[],'game') # Context game, accept all Serial inputs and some specials chars
               if DartStroke=='TOGGLEFULLSCREEN':
                  myDisplay.CreateScreen(True)
                  myDisplay.RefreshGameScreen(LSTJoueurs,actualround,objGame.GameOpts['totalround'],objGame.nbdarts - playerlaunch+1,objGame.nbdarts,objGame.GameLogo,objGame.Headers,actualplayer)
               else:
                  break
            # What did we play ?
            Logs.Log("DEBUG","You have played : {}".format(DartStroke))
            # Send DartStroke to server if player has played
            if NetStatus != None:
               NetClient.play(actualround,actualplayer,playerlaunch,DartStroke)
         else:
            # Else its a net game and it's our turn to wait from network !
            Logs.Log("DEBUG","Waiting for remote player (Player {} and Round {})...".format(actualplayer,actualround))
            DartStroke = NetClient.WaitSomeonePlay(actualround,actualplayer,playerlaunch)
      
         # Post Darts Checks
         if DartStroke.lower() in ConfigKeys and DartStroke!='PLAYERBUTTON' and DartStroke!='BACKUPBUTTON' and DartStroke!='GAMEBUTTON':
            PostDarts = objGame.PostDartsChecks(DartStroke,LSTJoueurs,actualround,actualplayer,playerlaunch)
            # Display score in differents ways depending on options
            if int(Config.GetValue('SectionGlobals','scoreonlogo'))==1:
               myDisplay.RefreshGameScreen(LSTJoueurs,actualround,objGame.GameOpts['totalround'],objGame.nbdarts - playerlaunch+1,objGame.nbdarts,objGame.GameLogo,objGame.Headers,actualplayer,str(DartStroke),1000)
            else:
               myDisplay.InfoMessage([str(DartStroke)],1000,None,'middle','huge')
            
         # WAIT For Player Button...
         if (NetStatus==None or LSTJoueurs[actualplayer].PlayerName in LoPl) and solo == 0  and DartStroke!='PLAYERBUTTON' and DartStroke!='GAMEBUTTON' and DartStroke!='BACKUPBUTTON' and (playerlaunch==objGame.nbdarts or PostDarts==1) and PostDarts!=2 and PostDarts!=3:
            # Display board
            myDisplay.RefreshGameScreen(LSTJoueurs,actualround,objGame.GameOpts['totalround'],0,objGame.nbdarts,objGame.GameLogo,objGame.Headers,actualplayer)
            myDisplay.DisplayPressPlayer(Lang.lang('press-player'))
            Inputs.ListenInputs(['num','alpha','fx','arrows'],['PLAYERBUTTON'],['PLAYERBUTTON'],'game')# Game context, wait for PLAYERBUTTON only...
            if NetStatus != None:
               NetClient.play(actualround,actualplayer,playerlaunch,'PLAYERBUTTON')

         # OR Wait that the remote player has pushed PLAYERBUTTON
         elif NetStatus!=None and LSTJoueurs[actualplayer].PlayerName not in LoPl and solo == 0  and DartStroke!='PLAYERBUTTON' and DartStroke!='GAMEBUTTON' and DartStroke!='BACKUPBUTTON' and (playerlaunch==objGame.nbdarts or PostDarts==1) and PostDarts!=2 and PostDarts!=3:
            myDisplay.RefreshGameScreen(LSTJoueurs,actualround,objGame.GameOpts['totalround'],0,objGame.nbdarts,objGame.GameLogo,objGame.Headers,actualplayer)
            myDisplay.DisplayPressPlayer(Lang.lang('press-player-remote'),'blue')
            # Else its a net game and it's our turn to wait from network !
            Logs.Log("DEBUG","Waiting for remote player to push PLAYERBUTTON...")
            NetClient.WaitSomeonePlay(actualround,actualplayer,playerlaunch,'PLAYERBUTTON') # Wait to receive PLAYERBUTTON

         # OR Wait parametered time (Disabled if network enabled).
         elif solo > 0  and DartStroke!='PLAYERBUTTON' and DartStroke!='GAMEBUTTON' and DartStroke!='BACKUPBUTTON' and (playerlaunch==objGame.nbdarts or PostDarts==1) and PostDarts!=2 and PostDarts!=3:
            myDisplay.InfoMessage([Lang.lang('release-darts')],solo,None,'middle','big')
            Inputs.Serial_Flush() #Flush Serial input values (prevent user to hit while prog sleeps)

      # If not allowed to play (PreDartsChecks = 4)
      else:
         # Repeat BACKUPBUTTON if previous hit was a BACKUPBUTTON
         if Prev_DartStroke == 'BACKUPBUTTON':
            DartStroke = Prev_DartStroke
         # Else, go to next player
         else:
            DartStroke = 'PLAYERBUTTON'
      
      #
      # Step 2 : All the differents possibilities
      #

      # BackUpTurn case
      if DartStroke=='BACKUPBUTTON' and (actualplayer>0 or actualround>1):
         if playerlaunch == 1:
            Logs.Log("DEBUG","Ho Hooooo... Special Backup Turn !")
            RestoreSession=objGame.PreviousBackUpPlayer
            if actualplayer == 0:
               actualround = actualround - 1
               actualplayer = NuPl - 1
            else:
               actualplayer=actualplayer-1
         else:
            RestoreSession=objGame.BackUpPlayer
         try:
            LSTJoueurs = deepcopy(RestoreSession)
            playerlaunch = 0 # 
            Logs.Log("DEBUG","Backup Turn !")
         except Exception as e:
            Logs.Log("ERROR","Backup Turn is not available in this game. : {}".format(e))
      
      # Early Player Button
      if DartStroke == 'PLAYERBUTTON' and playerlaunch <= objGame.nbdarts:
         EarlyPlayerButton = objGame.EarlyPlayerButton(LSTJoueurs,actualplayer,actualround)

      # Victory
      if PostDarts == 3 or EarlyPlayerButton == 3:
         txtwinner = "Winner : {}".format(LSTJoueurs[objGame.winner].PlayerName)
         myDisplay.SoundEndGame(LSTJoueurs[objGame.winner].PlayerName) # Play sound for winner (Playername otherwise default)
         myDisplay.InfoMessage([txtwinner],3000,None,'middle','big')
         # End of match loop
         MatchDone=True
      
      # Game Over 
      if PostDarts == 2 or EarlyPlayerButton == 2:
         myDisplay.InfoMessage([Lang.lang('last-round-reached')],3000,None,'middle')
         myDisplay.PlaySound('whatamess')
         MatchDone = True
         
      # GAMEBUTTON Pressed
      if DartStroke == 'GAMEBUTTON':
         Logs.Log("DEBUG","Who has pushed the Game Button ?")
         MatchDone = True

      # Next hit, please !
      playerlaunch+=1
         
      # Next Player ?
      if playerlaunch > objGame.nbdarts or PostDarts == 1 or PostDarts == 4 or DartStroke == 'PLAYERBUTTON':
         actualplayer+=1
         playerlaunch=1

      # Next Round ? - Only jump to next round if there is no victory, no end of match (stats are more accurate)
      if actualplayer >= NuPl and PostDarts != 2 and PostDarts != 3:
         actualplayer=0
         actualround+=1
      # Backup this DartStroke for next round
      Prev_DartStroke = DartStroke
   # MATCH IS OVER
   # Quit if it was a network game
   Logs.Log("DEBUG","This game is over")
   if NetStatus!=None:
      NetClient.close_host()
   # Retrieve Stats from the game
   try:
      Stats = objGame.GameStats(LSTJoueurs,actualround)
   except Exception as e:
      Logs.Log("ERROR","Problem building stats with GameStats Game method : {}".format(e))
   # Check for New Record and update File (except if -b cli option)
   if int(Config.GetValue('SectionAdvanced','bypass-stats'))==0:
      try:
         NewRecord = objGame.CheckRecord(LSTJoueurs,actualround)
      except Exception as e:
         Logs.Log("ERROR","Problem running CheckRecord method in this Game : {}".format(e))
   else:
      NewRecord = False
      Logs.Log("DEBUG","Bypassing stats update...")
   # Display Stats screen
   try:
      StatsScreen = myDisplay.DisplayStats(Stats,LSTJoueurs,NewRecord,GT)
      # Exit if the mode was directplay and the player pressed escape. Else, if the user press escape, back to menu, or enter, play again
      if StatsScreen == 'escape' and directplay:
         sys.exit(0)
   except Exception as e:
      Logs.Log("ERROR","Problem displaying stats table : {}".format(e))
      StatsScreen = False
