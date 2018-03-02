#import config
#from config import *

class CPlayer:
   def __init__(self, ident, nbjoueurs, Config, res):
      #self.colheight = min(int((res['y']/1.8)/nbjoueurs),100) # MUST be the same than in CScreen.SetLineHeight
      #self.bottomspace = res['y'] / 40
      self.Config=Config
      self.nbcol = int(Config.GetValue('SectionGlobals','nbcol'))
      #self.posy = int(res['y']-nbjoueurs*self.colheight + ident*self.colheight - self.bottomspace)
      self.ident = ident
      # Init value of each column for this player
      self.LSTColVal = []
      for x in range(0,self.nbcol+1):
         self.LSTColVal.append(('','txt',None))
      # Score Init
      self.score = 0
      # Init number of total good hits
      self.totaltouches = 0
      # Init Player name
      self.PlayerName = "Player{}".format(self.ident+1)

   #
   def InitPlayerColor(self,color):
      self.couleur= color

   #
   def GetPositiony(self):
      return self.posy

   #
   def GetCouleur(self):
	   return self.couleur

   #
   def GetColVal(self,Col):
      if self.LSTColVal[Col][1] == 'int':
         return int(self.LSTColVal[Col][0])
      else:
         return self.LSTColVal[Col][0]
         
   #
   def IncrementColTouch(self,Col):
      if self.LSTColVal[Col][1] == 'int' or self.LSTColVal[Col][1] == 'leds':
         thetype = self.LSTColVal[Col][1]
         nb = self.LSTColVal[Col][0] + 1
         color = self.LSTColVal[Col][2]
         self.LSTColVal[Col] = (nb,thetype,color)
      else:
         return False

   #If a tocuh given, Increment with correponding value, else, add touch value
   def IncrementTotalTouch(self,Touch=1):
        if str(Touch)[:1] == 'S':
           self.totaltouches+=1
        elif str(Touch)[:1] == 'D':
           self.totaltouches+=2
        elif str(Touch)[:1] == 'T':
           self.totaltouches+=3
        else:
           self.totaltouches+=Touch

   # Increment and Decrement A column
   def IncrementCol(self,Nb,Col):
      if self.LSTColVal[Col][1] == 'int':
         color = self.LSTColVal[Col][2]
         oldnb = self.LSTColVal[Col][0]
         self.LSTColVal[Col] = (oldnb + Nb, 'int',color) 
      else:
         return False

   # Remove nb unit from a column
   def DecrementCol(self,Nb,Col):
      if self.LSTColVal[Col][1] == 'int':
         color = self.LSTColVal[Col][2]
         oldnb = self.LSTColVal[Col][0]
         self.LSTColVal[Col] = (oldnb - Nb, 'int',color) 
      else:
         return False

   # Find if a touch is a Simple, Double, Triple
   def GetTouchType(self,Touch):
        if Touch[:1] == 'S':
           value = "Simple "
        elif Touch[:1] == 'D':
           value = "Double "
        elif Touch[:1] == 'T':
           value = "Triple "
        if Touch[1:] == "B":
           value += "Bull"
        else:
           value += Touch[1:]
        return value

   # Return Total touchs
   def GetTotalTouch(self):
      return self.totaltouches

   # Add point to players' score
   def ModifyScore(self,qty):
      self.score+=qty
      return self.score

   # Set score to given
   def SetScore(self,Score):
      self.score=Score
      return self.score
      
   def GetScore(self):
      return int(self.score)

#
# Return a common average : the number of touch divided by the number of round
#
   def ShowAvg(self,actualround):
      return round(float(self.totaltouches) / float(actualround),2)

#
# Return score divided per number of rounds
#
   def ScorePerRound(self,actualround):
      return round(float(self.score) / float(actualround),2)

#
# Returns the id of the previous player
#
   def GetPreviousPlayerId(self,totalnbplayers):
      if self.ident>0:
         return self.ident-1
      else:
         return totalnbplayers-1

      
