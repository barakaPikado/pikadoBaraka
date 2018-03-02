# -*- coding: utf-8 -*-
# Game by ... Poilou !
#import config
#from config import *
#import include
from include import CPlayer
from include import CScores

#Include used for backupTurn
from copy import deepcopy

# To choose wich hit to play :
import random

GameLogo = 'Practice.png' # Background image - relative to images folder
Headers = [ "Try","-","-","-","-","-","-"] # Columns headers - Must be a string
GameOpts = {'totalround':'10','master':'False'} # Dictionnay of options in string format
nbdarts=3
# The score associated to each hit
LSTPoints = {'SB': 25,'DB': 50,
				'S20': 20, 'D20': 40, 'T20': 60,
				'S19': 19,'D19': 38,'T19': 57,
				'S18': 18,'D18': 36,'T18': 54,
				'S17': 17,'D17': 34,'T17': 51,
				'S16': 16,'D16': 32,'T16': 48,
				'S15': 15,'D15': 30,'T15': 45,
				'S14': 14,'D14': 28,'T14': 42,
				'S13': 13,'D13': 26,'T13': 39,
				'S12': 12,'D12': 24,'T12': 36,
				'S11': 11,'D11': 22,'T11': 33,
				'S10': 10,'D10': 20,'T10': 30,
				'S9': 9,'D9': 18,'T9': 27,
				'S8': 8,'D8': 16,'T8': 24,
				'S7': 7,'D7': 14,'T7': 21,
				'S6': 6,'D6': 12,'T6': 18,
				'S5': 5,'D5': 10,'T5': 15,
				'S4': 4,'D4': 8,'T4': 12,
				'S3': 3,'D3': 6,'T3': 9,
				'S2': 2,'D2': 4,'T2': 6,
				'S1': 1,'D1': 2,'T1': 3
				}

############
#Extend the basic player
############
class CPlayerExtended(CPlayer.CPlayer):
   def __init__(self,x,NbPlayers,Config,res):
      CPlayer.CPlayer.__init__(self,x,NbPlayers,Config,res)
      # Read the CJoueur class parameters, and add here yours if needed

############
# Your Game's Class
############
class CGame:
   def __init__(self,myDisplay,GameChoice,nbplayers,GameOpts,Config,Logs):
      self.TxtRecap="\n###### Welcome to practice game ! ######"
      # Load logging system
      self.Logs=Logs
      # You need to use display all game long
      self.myDisplay=myDisplay
      # GameChoice contains the first screen game selection
      self.GameChoice=GameChoice
      # How many players ?
      self.nbplayers=nbplayers
      # GameOpts are the choices the user made with your options
      self.GameOpts=GameOpts
      # ConfigGlobals are the are the options contained in your config file
      self.Config=Config
      # First, random is generated locally, and then if the client is slave, this var will be set to true
      self.RandomIsFromNet = False
      # Local data
      self.GameLogo = GameLogo
      self.Headers = Headers
      self.nbdarts=nbdarts # Total darts the player has to play

###############
# Actions done before each dart throw - for example, check if the player is allowed to play
   def PreDartsChecks(self,LSTPlayers,actualround,actualplayer,playerlaunch):
      return_code = 0
      # TxtRecap Can be used to create a per-player debug output
      if playerlaunch == 1 and actualplayer == 0 and actualround == 1:
         self.myDisplay.PlaySound('practice_intro')
      # You will probably save the turn to be used in case of backup turn (each first launch) :
      if playerlaunch==1 :
         self.SaveTurn(LSTPlayers)
         rand = random.randint(1,22)
         if rand==21 and self.GameOpts['master']=='True':
            rand='SB'
         elif rand==22 and self.GameOpts['master']=='True':
            rand='DB'
         elif (rand==21 or rand==22) and self.GameOpts['master']=='False':
            rand='B'
         elif self.GameOpts['master']=='False':
            rand='{}'.format(rand)
         elif self.GameOpts['master']=='True':
            randMultiple=random.randint(1,3)
            if randMultiple == 1:
               rand='S{}'.format(rand)
            elif randMultiple == 2:
               rand='D{}'.format(rand)
            elif randMultiple == 3:
               rand='T{}'.format(rand)
         if self.RandomIsFromNet == False:
            # Clean table of any previousinformation
            for Column,Value in enumerate(LSTPlayers[actualplayer].LSTColVal):
               LSTPlayers[actualplayer].LSTColVal[Column] = ('','txt')
            # Then Rand it
            LSTPlayers[actualplayer].LSTColVal[0] = (rand,'txt')
      
      self.Logs.Log("DEBUG",self.TxtRecap)
      return return_code      

###############
# Function run after each dart throw - for example, add points to player
   def PostDartsChecks(self,hit,LSTPlayers,actualround,actualplayer,playerlaunch):
      return_code = 0
      ####
      #Your main game code will be here
      ####

      # Apply the coefficient to simple double triple and bull (Master case)
      if self.GameOpts['master']=='True':
         if hit[:1] == 'S':
            hitcoeff = 1
         elif hit[:1] == 'D':
            hitcoeff = 3
         elif hit[:1] == 'T':
            hitcoeff = 6
         if hit == 'SB':
            hitcoeff = 5
         elif hit == 'DB':
            hitcoeff = 10

      # Apply the coefficient to simple double triple and bull (No Master case)
      if self.GameOpts['master']=='False':
         if hit[:1] == 'S':
            hitcoeff = 1
         elif hit[:1] == 'D':
            hitcoeff = 2
         elif hit[:1] == 'T':
            hitcoeff = 3
         if hit == 'SB':
            hitcoeff = 1
         elif hit == 'DB':
            hitcoeff = 1

      
      
      # Check Hit
      if (self.GameOpts['master']=='True' and hit == LSTPlayers[actualplayer].GetColVal(0)) or (self.GameOpts['master']=='False' and (hit[1:] == LSTPlayers[actualplayer].GetColVal(0))) :
         # Play sound if touch is valid
         self.myDisplay.Sound4Touch(hit) # Play sound
         # Add score
         LSTPlayers[actualplayer].score += 1 * hitcoeff
         LSTPlayers[actualplayer].LSTColVal[playerlaunch] = ("+{}".format(hitcoeff), 'txt')
      
      # Display Hit
      # self.myDisplay.InfoMessage([str(hit)],1000,None,'middle','huge')
      
      # Check for end of game (no more rounds to play)
      if playerlaunch == self.nbdarts and actualround == int(self.GameOpts['totalround']) and actualplayer == len(LSTPlayers)-1:
         bestscoreid = -1
         bestscore = -1
         for Player in LSTPlayers:
            if Player.score > bestscore:
               bestscore = Player.score
               bestscoreid = Player.ident
         self.winner = bestscoreid
         return_code = 3
      return return_code

###############
# Function used to backup turn - you don't needs to modify it (for the moment) 
   def SaveTurn(self,LSTPlayers):
      #Create Backup Properies Array
      try:
         self.PreviousBackUpPlayer = deepcopy(self.BackUpPlayer)
      except:
         self.TxtRecap+="No previous turn to backup.\n"
      self.BackUpPlayer = deepcopy(LSTPlayers)
      self.TxtRecap+="Score Backup.\n"
###############
# Function launched if the player hit the player button before having thrown all his darts (Pneu)
   def EarlyPlayerButton(self,LSTPlayers,actualplayer,actualround):
      self.Logs.Log("DEBUG","Pneu func.")
      if actualround == int(self.GameOpts['totalround']) and actualplayer == self.nbplayers - 1:
         # If its a EarlyPlayerButton just at the last round - return GameOver
         return 2
###############
# Game Stats Handling - Construct stats stable and return it to be displayed
   def GameStats(self,LSTPlayers,actualround):
      # Init Stats table headers
      StatsTable = [('','Avg')]
      # Stats table from this game
      for LSTobj in LSTPlayers:
         StatsTable += [(str(LSTobj.PlayerName), str(round(float(LSTobj.score)/float(actualround),2)))]
      # Append HiScores
      HiScores = CScores.CScores('Practise',self.Logs)
      for i in range(1,4):
         Record_hiscore = str(HiScores.GetValue('avg_' + str(i),'float'))
         Record_hiscore_WHO = HiScores.GetPlayerName4Value('avg_' + str(i))
         StatsTable += [('HISCORES',"{}-{}".format(Record_hiscore,Record_hiscore_WHO))]
      return StatsTable
###############
# Check if there is new record in this game ! If true, update records !
   def CheckRecord(self,LSTPLayers,actualround):
      NewRecord = False
      HiScores = CScores.CScores('Practise',self.Logs)
      # Check and update Records
      for LSTobj in LSTPLayers:
         cur_score = round(float(LSTobj.score)/float(actualround),2)
         MyPlace_avg = HiScores.CheckHiScorePosition('avg','float',cur_score,'HI')
         if MyPlace_avg != None:
            NewRecord = True
            HiScores.InsertHiScore('avg',MyPlace_avg,str(cur_score),LSTobj.PlayerName)
      return NewRecord
###############
# Returns Random things, to send to clients in case of a network game
   def GetRandom(self,LSTPlayers,actualround,actualplayer,playerlaunch):
      if playerlaunch == 1:
         return LSTPlayers[actualplayer].GetColVal(0)
      else:
         return None
###############
# Set Random things, while received by master in case of a network game
   def SetRandom(self,LSTPlayers,actualround,actualplayer,playerlaunch,data):
      if data != None:
         LSTPlayers[actualplayer].LSTColVal[0] = (data, 'txt')
         self.Logs.Log("DEBUG","Setting random value for player {} to {}".format(actualplayer,data))
      self.RandomIsFromNet = True
