# -*- coding: utf-8 -*-
# Game by LB
#import config
#from config import *
#import include
from include import CPlayer
from include import CScores

import operator
import random
from copy import deepcopy

#VAR
#a = len(totalnbplayers)
#b=a*100+101
#c=200*a+201
GameLogo = 'Cricket.png' # Background image - relative to images folder
LSTRandom = [ 20,19,18,17,16,15,14,13,12,11,10,9,8,7 ]
Headers=['20','19','18','17','16','15','B']
GameOpts = {'totalround':'25','optioncutthroat':'True','zvezdice': '301','dve zvezdice': '601'} # Options in string format
nbdarts = 3 # How many darts the player is allowed to throw

#Hit/Points tab
LSTPoints = {	'SB': 25,'DB': 50,
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

#Extend the basic player
class CPlayerExtended(CPlayer.CPlayer):
   def __init__(self,x,nbjoueurs,Config,res):
      CPlayer.CPlayer.__init__(self,x,nbjoueurs,Config,res)
      self.PayDrink=False # Flag used to know if player has reached the drink score
      self.PayDrink2=False # Flag used to know if player has reached the drink score
      self.DistribPoints=0 # COunt how many points the player gave to the others (cut throat)
      self.nbhits = 0 # Count the number of hits per round for a specific player.
class CGame:
   def __init__(self,Affichage,gamechoice,nbplayers,GameOpts,Config,Logs):
      self.Logs=Logs
      self.GameOpts=GameOpts
      self.gamechoice=gamechoice
      self.nbplayers = nbplayers
      self.Config=Config
      self.Affichage=Affichage
      self.TxtRecap = ""
      self.nbdarts=nbdarts # Total darts the player has to play
      self.nbcol=int(self.Config.GetValue('SectionGlobals','nbcol'))
      self.RandomIsFromNet = False
      self.GameLogo = GameLogo
      self.Headers = Headers
#
   def SaveTurn(self,LSTJoueurs):
      #Create Backup Properies Array
      try:
         self.PreviousBackUpPlayer = deepcopy(self.BackUpPlayer)
      except:
         self.TxtRecap+="No previous round to backup.\n"
      self.BackUpPlayer = deepcopy(LSTJoueurs)
      self.TxtRecap+="Score Backup.\n"
#
   def PostDartsChecks(self,key,LSTJoueurs,actualround,actualplayer,playerlaunch):
		#Init
      PlayClosed = False # Should we play the closed sound ?
      PlayHit = False # Should we play the Double & triple sound ?
      BlinkText =""
      return_code = 0
      touchcount4total = False
      self.TxtRecap="Player {} - Score avant de jouer : {}\n".format(LSTJoueurs[actualplayer].ident,format(LSTJoueurs[actualplayer].ModifyScore(0)))
      #On met dans une variable la colone touchée
      TouchedColumn=key[1:]
      MultipleColumn=key[0:1]
      #Si cette colone est actuellement affichée - Touche valide
      if str(TouchedColumn) in self.Headers:
         #Cherche la colonne correspondant a la valeur (renvoie un string)
         IndexColTouched=self.Headers.index(str(TouchedColumn))
         if MultipleColumn=='S':
            TouchToAdd=1
         elif MultipleColumn=='D':
            TouchToAdd=2
         elif MultipleColumn=='T':
            TouchToAdd=3

         overtouched = 0 # To count how many over touched hits
         ###Affiche les leds correspondantes
         for x in range(0,TouchToAdd):
            #Pour chaque touche a ajouter - Si le joueur a moins de 3 touches
            if LSTJoueurs[actualplayer].GetColVal(IndexColTouched) < 3:
               #On ajoute une touche à son score
               LSTJoueurs[actualplayer].IncrementColTouch(IndexColTouched)
               # Increment All Rounds hit count
               LSTJoueurs[actualplayer].IncrementTotalTouch()
               # Increment this round hit count
               LSTJoueurs[actualplayer].nbhits += 1
               # Play Closed sound only if first time reaching 3 hit in the same Column :
               if LSTJoueurs[actualplayer].GetColVal(IndexColTouched) == 3:
                  PlayClosed = True
               elif x==0:
                  PlayHit = True
            #Si il a deja trois touches, on calcule combien de touches en plus le joueur a fait
            elif LSTJoueurs[actualplayer].GetColVal(IndexColTouched) == 3:
               # Increment overtouched for every touch over the 3 required ones
               overtouched+=1
                     
         #Si il y a du surplus
         if overtouched > 0:
            for LSTobj in LSTJoueurs:
               y = LSTobj.GetColVal(IndexColTouched)
               # On regarde combien rapporte une simple touche
               valueofsimplehit=LSTPoints['S' + key[1:]]
               # On multiplie la simple touche par le nombre de fois que le joueur a touche au dessus de 3
               overtouchedpts = overtouched * int(valueofsimplehit)
               # Si Cut Throat et pas fermé on ajoute les points au autres
               if y < 3 and self.GameOpts['optioncutthroat']=='True':
                  # On ajoute les points a ceux qui n ont pas ferme
                  self.TxtRecap+="Player {} prends {} points dans les naseaux ! (Cut-throat)\n".format(LSTobj.ident,overtouchedpts)
                  LSTobj.ModifyScore(overtouchedpts)
                  # Add points to player's Stats
                  LSTJoueurs[actualplayer].DistribPoints += overtouchedpts
                  # Si des joueurs prennent des points, les touches comptent pour le total du joueur
                  touchcount4total=True
               #Si pas Cut Throat on ajoute les points à soi uniquement si il n 'est pas fermé pour tous
               elif self.GameOpts['optioncutthroat'] == 'False' and LSTobj.ident==LSTJoueurs[actualplayer].ident:
                  TotallyClosed = True
                  #Check if the gate is totally closed for normal mode
                  for LSTobj2 in LSTJoueurs:
                     z = LSTobj2.GetColVal(IndexColTouched)
                     if z < 3:
                        TotallyClosed=False
                  if TotallyClosed==False:
                     self.TxtRecap+="Ce joueur gagne {} points supplementaire !\n".format(overtouchedpts)
                     LSTobj.ModifyScore(overtouchedpts)
                     touchcount4total=True
               #if the player reached the required drink score (usually 500), tell him to pay a drink !
               if LSTobj.PayDrink == False and LSTobj.score >= int(self.GameOpts['zvezdice']) and self.GameOpts['optioncutthroat']=='True' :
                  LSTobj.PayDrink=True
                  self.Affichage.PlaySound('padajuzvijezde')
               elif LSTobj.PayDrink2 == False and LSTobj.score >= int(self.GameOpts['dve zvezdice']) and self.GameOpts['optioncutthroat']=='True' :
                  LSTobj.PayDrink2=True
                  self.Affichage.PlaySound('dvijezvjezdice')

         #Ajout des touches si le joueur a eu du surplus (commun a Cut Throat et Mode Normal)
         if overtouched > 0 and touchcount4total == True:
            #On ajoute ses touches supplémentaires a son total puisque elle ont compté (des joueurs ont pris des points)
            LSTJoueurs[actualplayer].IncrementTotalTouch(overtouched)
            # Increment this round hit count
            LSTJoueurs[actualplayer].nbhits += 1
            PlayHit = True # Its a valid hit, play sound

         # Sound handling to avoid multiple sounds playing at a time
         if  PlayClosed:# Play sound only once, even if multiple TouchToAdd, and only if another sound is not played at the moment
            self.Affichage.PlaySound('closed')
         elif PlayHit: 
            self.Affichage.Sound4Touch(key) # Its a valid hit, play sound

         self.TxtRecap += "Touche : {} - Colonnes actives : {}\n".format(LSTJoueurs[actualplayer].GetTouchType(key), self.Headers)
         self.TxtRecap += "Nb de touches totales de ce joueur : {}\n".format(LSTJoueurs[actualplayer].GetTotalTouch())
         self.TxtRecap += "Nb de fleches lancees de ce joueur : {}\n".format(playerlaunch)

      # If it was last throw and no touch : play sound for "round missed"
      if playerlaunch == self.nbdarts and LSTJoueurs[actualplayer].nbhits == 0:
         self.Affichage.PlaySound('chaussette')
         
      # Last throw of the last round
      if actualround >= int(self.GameOpts['totalround']) and actualplayer==self.nbplayers-1 and playerlaunch == self.nbdarts:
         self.TxtRecap += "/!\ Dernier round atteint ({})\n".format(actualround)
         return_code = 2
      #
      #Check if there is a winner
      winner = self.CheckWinner(LSTJoueurs)
      if winner != -1:
         self.TxtRecap += "/!\ Player {} wins !\n".format(winner)
         self.winner = winner
         return_code = 3
      #
      # If there is blink text to display
      if BlinkText != "":
         self.Affichage.InfoMessage([BlinkText],None,None,'middle','big')
      #
      self.Logs.Log("DEBUG",self.TxtRecap)
      # Display Hit
      #self.Affichage.InfoMessage([str(key)],1000,None,'middle','huge')
      return return_code
#
   # Method to check if there is a winnner
   def CheckWinner(self,LSTJoueurs):
      bestscoreid = -1
      ClosedCols=True
      #Find the better score
      for ObjJoueur in LSTJoueurs:
         if (bestscoreid == -1 or ObjJoueur.score < LSTJoueurs[bestscoreid].score) and self.GameOpts['optioncutthroat']=='True':
            bestscoreid = ObjJoueur.ident
         elif (bestscoreid == -1 or ObjJoueur.score > LSTJoueurs[bestscoreid].score) and self.GameOpts['optioncutthroat']=='False':
            bestscoreid = ObjJoueur.ident
      #Check if the player who have the better score has closed all gates
      for LSTColVal in LSTJoueurs[bestscoreid].LSTColVal:
         if LSTColVal[0] != 3:
            ClosedCols = False
      # If the player who have the best score has closed all the gates
      if ClosedCols == True:
         return bestscoreid
      else:
         return -1
#
   
#Action lancée avant chaque lancé de flechette
#
   def PreDartsChecks(self,LSTJoueurs,actualround,actualplayer,playerlaunch):
      self.TxtRecap = ""
      # If first round - set display as leds
      if playerlaunch == 1 and actualround == 1 and actualplayer == 0:
         self.Affichage.PlaySound('cricket')         
         for Player in LSTJoueurs:
            for Column,Value in enumerate(Player.LSTColVal):
               Player.LSTColVal[Column] = [0,'leds','grey2']
      if playerlaunch == 1:
         # Reset number of hits in this round for this player 
         LSTJoueurs[actualplayer].nbhits = 0
         self.TxtRecap+="Active columns : {}".format(self.Headers)
         self.Logs.Log("DEBUG",self.TxtRecap)
         self.SaveTurn(LSTJoueurs)

 
#
# If player Hit the Player button before having threw all his darts
#
   def EarlyPlayerButton(self,LSTPlayers,actualplayer,actualround):
      self.TxtRecap+="You hit Player button before throwing all your darts ! Did you hit the PNEU ?"
      self.TxtRecap+="Actualround {} Totalround {} actualplayer {} nbplayers {}".format(actualround,self.GameOpts['totalround'],actualplayer,self.nbplayers - 1)
      # If no touch for this player at this round : play sound for "round missed"
      if LSTPlayers[actualplayer].nbhits == 0:
         self.Affichage.PlaySound('chaussette')
      if actualround == int(self.GameOpts['totalround']) and actualplayer == self.nbplayers - 1:
         # If its a EarlyPlayerButton just at the last round - return GameOver
         return 2

   """ New gamestats handling """
#
# Game Stats Handling - Construct stats stable
#
   def GameStats(self,LSTPlayers,actualround):
      # Init Stats table headers
      StatsTable = [('','Average','GiveOut')]
      # Stats table from this game
      for LSTobj in LSTPlayers:
         StatsTable += [(str(LSTobj.PlayerName), str(LSTobj.ShowAvg(actualround)),str(LSTobj.DistribPoints))]
      # Append HiScores and player Names for Hi Scores
      HiScores = CScores.CScores('Cricket',self.Logs)
      # Append Hi scores
      for i in range(1,4):
         Record_average = str(HiScores.GetValue('average_' + str(i),'float'))
         Record_average_WHO = HiScores.GetPlayerName4Value('average_' + str(i))
         Record_giveout = str(HiScores.GetValue('giveout_' + str(i),'int'))
         Record_giveout_WHO = HiScores.GetPlayerName4Value('giveout_' + str(i))
         StatsTable += [('HISCORES',"{} ({})".format(Record_average,Record_average_WHO),"{} ({})".format(Record_giveout,Record_giveout_WHO))]
      return StatsTable


#
# Check if there is new record in this game ! If true, update records ! (New version with multiple Hi score)
#

   def CheckRecord(self,LSTPlayers,actualround):
      NewRecord = False
      HiScores = CScores.CScores('Cricket',self.Logs) # Create instance
      # Check and update Records
      for LSTobj in LSTPlayers:
         MyPlace_average = HiScores.CheckHiScorePosition('average','float',LSTobj.ShowAvg(actualround),'HI')
         MyPlace_giveout = HiScores.CheckHiScorePosition('giveout','int',LSTobj.DistribPoints,'HI')
         if MyPlace_average != None :
            NewRecord = True
            HiScores.InsertHiScore('average', MyPlace_average,str(LSTobj.ShowAvg(actualround)),LSTobj.PlayerName)
         if MyPlace_giveout != None:
            NewRecord = True
            HiScores.InsertHiScore('giveout', MyPlace_giveout,str(LSTobj.DistribPoints),LSTobj.PlayerName)
      return NewRecord

#
# Returns and Random things, to send to clients in case of a network game
#

#
# Set Random things, while received by master in case of a network game
#
   def SetRandom(self,LSTPlayers,actualround,actualplayer,playerlaunch,data):
      if data != False:
         self.Headers = data
         self.RandomIsFromNet = True

