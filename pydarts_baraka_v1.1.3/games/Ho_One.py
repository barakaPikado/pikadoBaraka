# -*- coding: utf-8 -*-
# Game by ... poilou !
#import config
#from config import *
#import include
from include import CPlayer
from include import CScores

#Include used for backupTurn
from copy import deepcopy

GameLogo = 'Ho_One.png' # Background image - relative to images folder
Headers = [ "D1","D2","D3","","","","" ] # Columns headers - Must be a string
GameOpts = {'startingat':'301','totalround':'20','double_in':'False','double_out':'False'} # Dictionnay of options - will be used at the initial screen
nbdarts = 3 # How many darts the player is allowed to throw

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
      self.PrePlayScore = None

############
# Your Game's Class
############
class CGame:
   def __init__(self,myDisplay,GameChoice,nbplayers,GameOpts,Config,Logs):
      self.TxtRecap="###### New Ho One Round ! ######\n"
      # Load logger system
      self.Logs=Logs
      # You need to use display all game long
      self.myDisplay=myDisplay
      # GameChoice contains the first screen game selection
      self.GameChoice=GameChoice
      # nbplayers is the number of players engaged in game
      self.nbplayers = nbplayers
      # GameOpts are the choices the user made with your options
      self.GameOpts=GameOpts
      # Config are the are the options contained in your config file
      self.Config=Config
      # By default, random is generated locally, and later if the client is slave, this var will be set to true
      self.RandomIsFromNet = False
      # Total darts
      self.nbdarts=nbdarts # Total darts the player has to play
      self.GameLogo = GameLogo
      self.Headers = Headers

###############
# Actions done before each dart throw - for example, check if the player is allowed to play
   def PreDartsChecks(self,LSTPlayers,actualround,actualplayer,playerlaunch):
      return_code = 0

      # Set score at startup
      if actualround == 1 and playerlaunch == 1 and actualplayer == 0:
         for Player in LSTPlayers:
            Player.score = int(self.GameOpts['startingat'])
            #self.myDisplay.DisplayScore(Player.ident,Player.posy,Player.score) # refresh score
         self.myDisplay.PlaySound('ho_one_intro')

      # Each new player
      if playerlaunch==1:
         self.SaveTurn(LSTPlayers)
         LSTPlayers[actualplayer].PrePlayScore = LSTPlayers[actualplayer].score # Backup current score

         #Reset Table
         LSTPlayers[actualplayer].LSTColVal = []
         for i in range(0,3):
            LSTPlayers[actualplayer].LSTColVal.append(['','int'])

      # Print debug output
      self.Logs.Log("DEBUG",self.TxtRecap)
      return return_code      

###############
# Function run after each dart throw - for example, add points to player
   def PostDartsChecks(self,hit,LSTPlayers,actualround,actualplayer,playerlaunch):
      return_code = 0

      # Define a var for substracted score
      subscore = LSTPlayers[actualplayer].score - LSTPoints[hit]
      # Double in/out cases
      if self.GameOpts['double_in']=='True' and subscore > 0 and hit[:1] == 'D' and LSTPlayers[actualplayer].score == int(self.GameOpts['startingat']):# Double in !
         self.myDisplay.Sound4Touch(hit) # Successed double in !
         LSTPlayers[actualplayer].score = subscore # Substract
      elif self.GameOpts['double_in']=='True' and subscore > 0 and hit[:1] != 'D' and LSTPlayers[actualplayer].score == int(self.GameOpts['startingat']):# Double in failed, pass
         pass
      elif self.GameOpts['double_out']=='True' and subscore == 0 and hit[:1] == 'D':# Successed Double out !
         self.myDisplay.Sound4Touch(hit)
         return_code = 3 # There is a winner
         self.winner = actualplayer
         LSTPlayers[actualplayer].score = 0
      elif self.GameOpts['double_out']=='True' and subscore <= 1:# Double out failed, next player !
         return_code = 1 # Next player
         LSTPlayers[actualplayer].score = LSTPlayers[actualplayer].PrePlayScore
         self.myDisplay.PlaySound('whatamess')
      # Classic cases
      elif subscore > 0: # Normal case, hit a score
         self.myDisplay.Sound4Touch(hit) # Touched !
         LSTPlayers[actualplayer].score = subscore # Substract
      elif subscore == 0: # Winner
         self.myDisplay.Sound4Touch(hit)
         return_code = 3
         self.winner = actualplayer
         LSTPlayers[actualplayer].score = 0
      else: # Under Zero- put the original score back
         return_code = 1 # Next player
         LSTPlayers[actualplayer].score = LSTPlayers[actualplayer].PrePlayScore
         self.myDisplay.PlaySound('whatamess')
      
      # Check last round
      if actualround >= int(self.GameOpts['totalround']) and actualplayer==self.nbplayers-1 and playerlaunch == int(self.nbdarts):
         self.TxtRecap += "/!\ Last round reached ({})\n".format(actualround)
         return_code = 2
         
      # Store what he played in the table
      LSTPlayers[actualplayer].LSTColVal[playerlaunch-1] = (LSTPoints[hit],'int')
      # Display Hit
      #self.myDisplay.InfoMessage([str(hit)],1000,None,'middle','huge')
      # Good bye !
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
      self.TxtRecap+="Pneu func.\n"
      if actualround == int(self.GameOpts['totalround']) and actualplayer == self.nbplayers - 1:
         # If its a EarlyPlayerButton just at the last round - return GameOver
         return 2
###############
# Game Stats Handling - Construct stats stable and return it to be displayed
   def GameStats(self,LSTPlayers,actualround):
      # Init Stats table headers
      StatsTable = [('','Pts/Rnd','Residue')]
      # Stats table from this game
      for LSTobj in LSTPlayers:
         StatsTable += [(str(LSTobj.PlayerName), str(round(float((int(self.GameOpts['startingat'])-LSTobj.score)/actualround),2)), str(LSTobj.score))]
      # Append HiScores
      HiScores = CScores.CScores('Ho_One',self.Logs)
      for i in range(1,4):
         Record_hiscore = str(HiScores.GetValue('pointsperround_' + str(i),'float'))
         Record_hiscore_WHO = HiScores.GetPlayerName4Value('pointsperround_' + str(i))
         StatsTable += [('HISCORES',"{}-{}".format(Record_hiscore,Record_hiscore_WHO),'-')]
      return StatsTable
###############
# Check if there is new record in this game ! If true, update records !
   def CheckRecord(self,LSTPLayers,actualround):
      NewRecord = False
      HiScores = CScores.CScores('Ho_One',self.Logs)
      # Check and update Records
      for LSTobj in LSTPLayers:
         PointsPerRound = round(float((int(self.GameOpts['startingat'])-LSTobj.score)/actualround),2)
         MyPlace_hiscore = HiScores.CheckHiScorePosition('pointsperround','float',PointsPerRound,'HI')
         if MyPlace_hiscore != None:
            NewRecord = True
            HiScores.InsertHiScore('pointsperround',MyPlace_hiscore,str(PointsPerRound),LSTobj.PlayerName)
      return NewRecord
###############
# Returns Random things, to send to clients in case of a network game
   def GetRandom(self,LSTPlayers,actualround,actualplayer,playerlaunch):
      return None # Means that there is no random
###############
# Set Random things, while received by master in case of a network game
   def SetRandom(self,LSTPlayers,actualround,actualplayer,playerlaunch,data):
      pass
