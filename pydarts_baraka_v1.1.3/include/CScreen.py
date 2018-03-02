# -*- coding: utf-8 -*-
import os, os.path
from include.config import *
import pygame
from pygame.locals import *
import sys
from . import CScores
import random #Randomize player names / and create a random game name / ...
import subprocess #Run external commands (shell)
import math
import getpass #To get current username

class CScreen(pygame.Surface):
#
# Init
#
   def __init__(self, Config, Logs, Lang):
      # Init
      self.netgamename=None
      self.servername=None
      self.serveralias=None
      self.serverport=None
      # Store config in local value
      self.Logs=Logs
      self.Lang=Lang # Import language values
      self.lineheight = None # Depends of player number - calculated later
      self.Config=Config
      # For drawing a dart board
      self.LSTOrder = {20:1,1:2,18:3,4:4,13:5,6:6,10:7,15:8,2:9,17:10,3:11,19:12,7:13,16:14,8:15,11:16,14:17,9:18,12:19,5:20}
      # Set default Sound Volume (percent)
      try:
         self.SoundVolume = int(self.Config.GetValue('SectionGlobals','soundvolume'))
      except:
         pass
      pygame.init()
      # Create resolution prameters
      if int(self.Config.GetValue('SectionGlobals','fullscreen'))!=1:
         self.fullscreen = False
      else:
         self.fullscreen = True
      # CreateScreen Init or toggle screen
      self.CreateScreen()
      # Choose color set
      self.InitColorSet()
      # Define constants - first without the required nb of players
      self.DefineConstants()

#
# Give Inputs object to Screen object
#
   def SetInputs(self,Inputs):
      self.Inputs = Inputs

#
# Create screen and optionnaly toggle Fullscreen/windowed
#
   def CreateScreen(self,Toggle=False):
      # Toggle if requested
      if self.fullscreen and Toggle:
         self.fullscreen = False 
      elif Toggle and not self.fullscreen:
         self.fullscreen = True
      # If toggle screen
      if Toggle:
         # Grab information before quitting actual screen
         self.screen = pygame.display.get_surface()#Get a reference to the currently set display surface
         tmp = self.screen.convert()# change the pixel format of an image ? Can't remember why I do that ;)
         caption = pygame.display.get_caption()#Get current caption
         cursor = pygame.mouse.get_cursor()# Get the image for the system mouse cursor
         bits = self.screen.get_bitsize()#Get the bit depth of the Surface pixel format
         # Bye bye old screen !
         pygame.display.quit()

      # Welcome new screen !
      pygame.display.init()
      # Define resolution
      self.InitResolution()
      # Define screen constants (depends on resolution)
      self.DefineConstants()
      # Tell pygame it is fullscreen if it is
      if self.fullscreen:
         self.screen = pygame.display.set_mode((0,0),pygame.FULLSCREEN)# Set fullscreen with actual resolution
      else:
         self.screen = pygame.display.set_mode((self.res['x'],self.res['y'])) # Start windowed with settings
      # If Toggling, blit the new screen
      if Toggle:
         self.screen.blit(tmp,(0,0))
      
      # Get caption back
      pygame.display.set_caption('pyDarts v.{}'.format(pyDartsVersion))
      # Set soft images
      imagefile = self.GetPathOfFile('images', 'icon_white.png')
      if imagefile != False:
         iconimage=pygame.image.load(imagefile)
         pygame.display.set_icon(iconimage)
      else:
         self.Logs.Log("WARNING","Unable to load icon image.")
      pygame.key.set_mods(0) #HACK: work-a-round for a SDL bug??
      if Toggle:
         pygame.mouse.set_cursor( *cursor )  # Duoas 16-04-2007

#
# Init the choosen ColorSet
#
   def InitColorSet(self):
      self.FallbackColorSet = 'clear' # In case of failure to load reuested color set
      self.ChoosenColorSet=self.Config.GetValue('SectionGlobals','colorset')
      try:
         self.ColorSet=ColorSet[self.ChoosenColorSet]
      except:
         self.Logs.Log("WARNING","The colorset \"{}\" does not exists ! Falling back to default ({}) ".format(self.Config.GetValue('SectionGlobals','colorset'),self.FallbackColorSet))
         self.ColorSet=ColorSet[self.FallbackColorSet]
 
#
# Get best parametered display resolution or best resolution if fullscreen
#
   def InitResolution(self):
      """Init a dictionnary named "res" which contains x and y display resolutions"""
      self.res = {}
      if self.fullscreen==False:
         self.res['x']=int(self.Config.GetValue('SectionGlobals','resx'))
         self.res['y']=int(self.Config.GetValue('SectionGlobals','resy'))
         self.Logs.Log("DEBUG","Using display mode : {}x{}".format(self.res['x'],self.res['y']))
      else:
         infoObject = pygame.display.Info()
         self.res['x']=infoObject.current_w
         self.res['y']=infoObject.current_h
         self.Logs.Log("DEBUG","Ho yeah, going fullscreen : {}x{}".format(infoObject.current_w,infoObject.current_h))

####################### METHODS FOR V1+ DISPLAY ####################

#
# Display a rect with transparency, with optionnal border
#
   def BlitRect(self,X,Y,SX,SY,Color,Border=False,BorderColor=False,Alpha=None):
      if Alpha==None : Alpha = self.alpha
      if not BorderColor : BorderColor = self.ColorSet['grey']
      s = pygame.Surface((SX,SY))  # the size of your rect
      s.set_alpha(Alpha)                # alpha level
      s.fill(Color)           # this fills the entire surface
      self.screen.blit(s, (X,Y))    # (0,0) are the top-left coordinates
      if Border:
         pygame.draw.rect(self.screen, BorderColor, (X,Y,SX,SY), Border)

#
# Return best text size to scale text in a given box size (for responsvie design)
#
   def ScaleTxt(self,txt,boxX,boxY,startingtextsize=None,dafont=None,divider=1,step=0.1):
      if dafont==None:dafont=self.defaultfontpath
      if startingtextsize==None:startingtextsize=boxY 
      while True:
         TxtSize = int(startingtextsize / divider)
         font = pygame.font.Font(dafont, TxtSize)
         fontsize = font.size(txt)
         #print("PROUT : {} - {} and text size is {} and text is {}".format(boxX,boxY,TxtSize,txt))
         if TxtSize<=0: 
            self.Logs.Log("ERROR","Unable to find suitable text size for a box of size {}x{} and for text {}".format(boxX,boxY,txt))
            return False
         if fontsize[0] < boxX and fontsize[1]<boxY:
            spaceX = int((boxX - fontsize[0]) / 2)
            spaceY = int((boxY - fontsize[1]) / 2)
            # Returns Best text size, horizontal space needed to center text, vertical space to center text
            return [TxtSize,spaceX,spaceY]
         else:divider+=step

#
# All menus use the same header
#  
   def MenuHeader(self,txt,subtxt=None):
      Y=int(self.res['y'] / 30)
      X=0
      SX = self.res['x']
      SYtxt = int(self.res['y'] / 15)
      if subtxt:
         SYsubtxt = int(self.res['y'] / 25)
      TStxt = int(SYtxt/2)
      if subtxt:
         TSsubtxt= int(SYsubtxt/2)
      ScaledTStxt = self.ScaleTxt(txt,self.res['x']-self.space*2,SYtxt)
      TStxt = ScaledTStxt[0]
      if subtxt:
         ScaledTSsubtxt = self.ScaleTxt(subtxt,self.res['x']-self.space*2,SYsubtxt)
         TSsubtxt = ScaledTSsubtxt[0]
         font = pygame.font.Font(self.defaultfontpath, TSsubtxt)
      fontbig = pygame.font.Font(self.defaultfontpath, TStxt)
      self.BlitRect(X,Y,SX,SYtxt,self.ColorSet['black'])
      if subtxt:
         self.BlitRect(X , Y + SYtxt + self.space*2,SX,SYsubtxt,self.ColorSet['black'])
         subtext = font.render(subtxt,True, self.ColorSet['white'])
         self.screen.blit(subtext, [X + self.space*2 , Y + SYtxt + ScaledTSsubtxt[2] + self.space*2])#+int(TStxt*2.5)+int(TSsubtxt/2)
      text = fontbig.render(txt,True, self.ColorSet['white'])
      self.screen.blit(text, [X+self.space*2,Y+ScaledTStxt[2]])#+int(TStxt/2.5)

#
# Main UI messaging method - can display multiple phrases, mutiple sizes, multiple places
#
   def InfoMessage(self,txts,wait=None,Color=None,Y=None,BS=None,Enter=False):
      if BS =='small':
         BS = self.res['y'] / 40
      if BS == None or BS =='normal':
         BS = self.res['y'] / 20
      if BS =='big':
         BS = self.res['y'] / 7
      if BS == 'huge':
         BS = self.res['y'] / 4
      if wait==None:
         wait=3000
      if Color==None:
         Color = self.ColorSet['white']
         
      # Constants
      SX = self.res['x']
      RectX = 0
      # For each sentence in list
      for txt in txts:
         # Display background
         self.DisplayBackground()
         # Calculate Y
         if Y==None or Y=='bottom':
            Y = self.res['y'] / 3 * 2
         if Y=='fullbottom':
            Y = self.res['y']-(BS/2)
         if Y=='top':
            Y = self.res['y'] / 3
         if Y=='middle':
            Y = self.res['y'] / 2
         # Calculate rect size and place
         RectY = int(Y - (BS / 2))
         # Display Rect
         self.BlitRect(RectX,RectY,SX,BS,self.ColorSet['black'])
         # Determine text size
         ScaledTS = self.ScaleTxt(txt,SX,BS)
         TS = ScaledTS[0]
         # Create font
         font = pygame.font.Font(self.defaultfontpath, int(TS))
         Tx = RectX + ScaledTS[1]
         Ty = RectY + ScaledTS[2]
         # Render text
         txt = font.render(txt,True, self.ColorSet['white'])
         # Blit content
         self.screen.blit(txt, [Tx,Ty])
         # Update screen
         self.UpdateScreen()
         # Optionnaly wait a few sec between each message
         if wait!=None:
            pygame.time.wait(wait) # Wait X millisecond


####################### Menus ##############

#
# Special menu - getting board config
#
   def GetConfig(self):
      NewKeys = {}
      self.DisplayBackground() # display basic screen
      i=0
      total = 65
      self.Inputs.Serial_Flush()
      j=0
      while True:
         key=OrderedDartKeys[j]
         i=0
         txt=self.Lang.lang('press-on') + " " + str(key)
         self.InfoMessage([txt],0,None,'fullbottom','big')
         for key2 in OrderedDartKeys:
            # Get type
            Type=key2[:1]
            # Define colors
            if i%2==0 and (Type=='D' or Type=='T'):
                  partcolor = self.ColorSet['green']
            elif Type=='D' or Type=='T':
                  partcolor = self.ColorSet['red']
            else : partcolor = None
            if key2==key : partcolor = self.ColorSet['yellow']
            # Draw the right thing
            if key2[1:]!='B' and len(key2)<=3:Score=int(key2[1:])
            elif key2[1:]=='B':Score='B'
            if Type=='S' and Score!='B':
               self.Drawsimple(self.LSTOrder[Score],partcolor)
            elif Type=='D' and Score!='B':
               self.Drawdouble(self.LSTOrder[Score],partcolor)
            elif Type=='T' and Score!='B':
               self.Drawtriple(self.LSTOrder[Score],partcolor)
            elif Type=='S' and  Score=='B':
               self.Drawbull(True,False,partcolor)
            elif Type=='D' and Score=='B':
               self.Drawbull(False,True,partcolor)
            if key2!='D5':# On T20 we switch color order
               i+=1
            if key2==key or len(key2)>3:break# If key2 is not yet configurer or if it is buttons
         subtxt = self.Lang.lang('press-on-parts') + " - " + self.Lang.lang('left') + " : " + str(total-i)
         self.MenuHeader(self.Lang.lang('board-calibration'),subtxt)
         self.UpdateScreen()
         K=self.Inputs.ListenInputs([],['escape','enter','space'],[],'wizard')
         self.Inputs.Serial_Flush()
         if K=='enter':
            return NewKeys
         elif K=='space':
            NewKeys[key]=''
         elif K=='escape':
            if j>0:
               j-=2
            else:
               sys.exit(0)
         else:
            NewKeys[key]=K
         i+=1
         j+=1
         # All keys calibrated
         if j==total:
            return NewKeys
         
         
# Display Players engaged in a network game menu
#
   def Starting(self,NetClient,NetStatus,LoPl):
      self.DisplayBackground() # display basic screen
      # Init empty values
      Rdy={'REQUEST':None,'PLAYERSNAMES':None}
      AllPl=[]      
      # We refresh user list until the message LAUNCH arrives from server
      nexttick = int(pygame.time.get_ticks()/1000)
      # This loop will ends when the game will be launched
      while True:
         # Get actual tick from pygame
         tick=int(pygame.time.get_ticks()/1000)
         # Listen for keyboard
         K=self.Inputs.KbdAndMouse(['fx','arrows'],['tab','enter','escape'])
         if (K=='enter' or K=='return') and NetStatus=='YOUAREMASTER':# If the Master player pressed enter
            d={'REQUEST':'LAUNCH','GAMENAME':NetClient.gamename} # He is ok to launch the game. Tell it to server
            NetClient.send(d)# Send message
         elif K=='tab' and NetStatus=='YOUAREMASTER':# If the Master player pressed tab 
            d={'REQUEST':'SHUFFLE','GAMENAME':NetClient.gamename} # Request the server to shuffle player names
            NetClient.send(d)# Send message
         elif K=='escape' and NetStatus=='YOUARESLAVE':
            return -1 # Return -1 means yourself, as a slave client left the game
         elif K=='escape' and NetStatus=='YOUAREMASTER':
            return []# Return -1 means yourself, as a slave client left the game
         SY = self.res['y']/40
         Y = int(self.res['y']/7)
         # Refreshing players list
         if nexttick==tick:
            self.InfoMessage([self.Lang.lang('net-client-refresh-players')],0) # Display refreshing from server
            Rdy = NetClient.SendLocalPlayers(LoPl) # Send name of local players, and wait for game to be launched
            self.DisplayBackground() # display basic screen
            nexttick+=int(self.Config.GetValue('SectionAdvanced','clientpolltime'))
            # Refresh player list if provided by server
            if 'PLAYERSNAMES' in Rdy:
               AllPl=Rdy['PLAYERSNAMES']
            # Display page title
            if NetStatus=='YOUAREMASTER' : txt=self.Lang.lang('players-ready-masterplayer')
            else : txt=self.Lang.lang('players-ready-slaveplayer')
            self.MenuHeader(txt)
            Y+=SY*2 # and add a space
            SY = SY*2
            # Following for loop is for displaying players' names purpose
            X = 0
            SX = self.res['x']
            for P in AllPl:
               self.BlitRect(X,Y,SX,SY,self.ColorSet['black'],True)
               # Print text
               Scaled = self.ScaleTxt(P,SX,SY)
               font = pygame.font.Font(self.defaultfontpath, Scaled[0])
               txt = font.render(P,True, self.ColorSet['white'])
               self.screen.blit(txt, [X+Scaled[1],Y+Scaled[2]])
               Y+=SY
            self.PreviousMenu()
            self.UpdateScreen()
            #pygame.time.wait(1) # Wait one second, but what for?
            # If we received the order to LAUNCH or to ABORT game
            if Rdy['REQUEST']=='LAUNCH' or Rdy['REQUEST']=='ABORT':
               # Return Player list to main game
               return AllPl

#
# Player Names menu
#
   def PlayersNamesMenu3(self,AllPl,bgimage='background.png'):
      # Init
      edit={}
      Players=AllPl
      if len(AllPl)==0:
         Players.append(getpass.getuser())
      # This loop breaks when the player press enter
      while True:
         S = int(self.res['y']/18)
         #AllBoxesBorders
         BB=2
         # Fx box
         X = int(self.res['x']/15)
         Y = int(self.res['y']/9)
         # Fx Text
         TX = int(X + (self.space * 2)) 
         TY = int(Y)
         # Players name Box
         NX = X+S
         NY = Y
         NS = int(self.res['x'] - X*2 - S*2)
         # Player name Text
         TX2= int(X + S) 
         TY2= int(TY + self.space*2)
         # Init enabled F keys
         fkeys = []
         # Draw background
         self.DisplayBackground(bgimage)
         # Draw Text
         self.MenuHeader(self.Lang.lang('players-names'),self.Lang.lang('players-names-subtitle'))
         # Draw each line a player name
         i=0
         for Player in Players:
            Y+=S
            TY+=S
            TY2+=S
            NY+=S
            # Construct available F keys list
            fkeys.append('f{}'.format(i+1))
            # First Column : Fx
            if str(i) in edit:
               pygame.draw.rect(self.screen, self.ColorSet['grey'], (X,Y,S,S), 0)
            else:
               pygame.draw.rect(self.screen, self.ColorSet['blue'], (X,Y,S,S), 0)
            pygame.draw.rect(self.screen, self.ColorSet['black'], (X,Y,S,S), BB)
            # Display Fx
            pygame.draw.rect(self.screen, self.ColorSet['black'], (NX,NY,NS,S), BB)# Sqare around Fx
            font = pygame.font.Font(self.defaultfontpath, int(S/1.8))
            textF = font.render("F{}".format(i+1) ,True, self.ColorSet['black'])
            self.screen.blit(textF, [TX,TY2])
            # Display player name
            if str(i) in edit:
               txtPlayerName="{}_".format(edit[str(i)][:12])
               Players[i]=edit[str(i)][:12]
            else:
               txtPlayerName=Players[i]
            
            self.BlitRect(NX,NY,NS,S,self.ColorSet['black'])#Square around players' name
            ScaledTS = self.ScaleTxt(txtPlayerName,NS-self.space*2,S)
            TS = ScaledTS[0]
            font = pygame.font.Font(self.defaultfontpath, TS)
            textEachPlayer= font.render(txtPlayerName,True, self.ColorSet['white'])
            self.screen.blit(textEachPlayer, [TX2 + self.space,TY2 + ScaledTS[2]])
            # Increment
            i+=1
         # Draw - sign
         if i>1:
            font = pygame.font.Font(self.defaultfontpath, int(S/1.8))
            MinusX=X+NS+S
            MinusTX=TX+NS+S
            pygame.draw.rect(self.screen, self.ColorSet['red'], (MinusX,Y,S,S), 0)
            pygame.draw.rect(self.screen, self.ColorSet['black'], (MinusX,Y,S,S), BB) 
            textF = font.render("-",True, self.ColorSet['white'])
            self.screen.blit(textF, [MinusTX,TY])
         # Draw + sign
         if len(Players)<12:
            font = pygame.font.Font(self.defaultfontpath, int(S/1.8))
            Y+=S
            TY+=S
            TY2+=S
            NY+=S
            pygame.draw.rect(self.screen, self.ColorSet['green'], (X,Y,S,S), 0)
            pygame.draw.rect(self.screen, self.ColorSet['black'], (X,Y,S,S), BB) 
            textF = font.render("+",True, self.ColorSet['white'])
            self.screen.blit(textF, [TX,TY])
         self.PreviousMenu()
         self.UpdateScreen()
         # Read Keyboard
         if len(edit)==0:
            K=self.Inputs.ListenInputs(['alpha','num','fx','math','arrows'],['escape','enter','backspace','tab','TOGGLEFULLSCREEN'])
         else:
            K=self.Inputs.ListenInputs(['alpha','num','fx','math','arrows'],['enter','backspace'],context='editing')
         # Key analysis
         if K == 'escape':# Previous menu
            return K
         elif (K == 'TOGGLEFULLSCREEN') and len(edit)==0:#Toggle Fullscreen
            self.CreateScreen(True)
         elif (K == 'return' or K == 'enter') and len(edit)==0:# VALID !
            self.DefineConstants(len(Players))
            return Players
         elif (K == 'return' or K == 'enter') and len(edit)>0:
            edit={}
         elif K == 'backspace' and len(edit)>0:
            for k in edit:
               edit[k] = edit[k][:-1]
         elif K == 'tab' and len(edit)==0: # Randomize Player names
            random.shuffle(Players)
         elif K == '+' and len(Players)<12:
            nbplayers=len(Players)
            Players.append('Player{}'.format(nbplayers+1))
            #print("Nombre de joueurs : {}".format(len(Players)))
         elif K == '-' and len(Players)>1:
            nbplayers=len(Players)
            Players.pop()
            #print("Nombre de joueurs : {}".format(len(Players)))
         elif K in fkeys:
            edit={}
            ident = int(K[1:])-1
            edit[str(ident)]=''
         elif len(edit)>0:
            for curr in edit:
               if len(edit[curr])<12:
                  edit[curr] = "{}{}".format(edit[curr],K)

#
# Choose Game Type : Local - Network
#
   def GameType(self):
      while True:
         BB=2
         # Base display
         Y = int(self.res['y']/4)
         X = int(self.res['x']/15)
         S = int(self.res['y']/15)
         line_space = int(S*1.5)
         space = int(S*1.5)

         # Game type name box
         NX = X+S
         NY = Y
         NS = int(self.res['x'] - X - NX)

         # Draw bg
         self.DisplayBackground()
         # Titles
         self.MenuHeader(self.Lang.lang('game-type'))
         
         # First Menu
         # Fonts & text creation
         txt1 = "F1"
         ScaledTS1 = self.ScaleTxt(txt1, S-self.space*2, S)
         TS1 = ScaledTS1[0]# Get only first value
         font1 = pygame.font.Font(self.defaultfontpath, TS1)
         txt2 = self.Lang.lang('game-type-local')
         ScaledTS2 = self.ScaleTxt(txt2, NS-self.space*2, S)
         TS2 = ScaledTS2[0]
         font2 = pygame.font.Font(self.defaultfontpath, TS2)
         #
         TX= int(X + self.space) 
         TY= int(Y + self.space)
         TX2= int(X + S + self.space) 
         TY2= int(Y + self.space)
         #
         self.BlitRect(NX,NY,NS,S,self.ColorSet['black'])
         self.BlitRect(X,Y,S,S,self.ColorSet['blue'])
         #
         pygame.draw.rect(self.screen, self.ColorSet['black'], (X,Y,S,S), BB)
         pygame.draw.rect(self.screen, self.ColorSet['black'], (NX,NY,NS,S), BB)
         #
         textF = font1.render(txt1,True, self.ColorSet['black'])
         self.screen.blit(textF, [TX,TY+ScaledTS1[2]])
         txt2 = font2.render(txt2,True, self.ColorSet['white'])
         self.screen.blit(txt2, [TX2,TY2+ScaledTS2[2]])

         # Second Menu
         # Fonts & text creation
         Y += line_space
         NY += line_space
         TY += line_space
         TY2 += line_space
         txt1 = "F2"
         ScaledTS1 = self.ScaleTxt(txt1, S-self.space*2, S)
         TS1 = ScaledTS1[0]
         font1 = pygame.font.Font(self.defaultfontpath, TS1)
         txt2 = self.Lang.lang('game-type-master')
         ScaledTS2 = self.ScaleTxt(txt2, NS-self.space*2, S)
         TS2 = ScaledTS2[0]
         font2 = pygame.font.Font(self.defaultfontpath, TS2)
         # boxes
         self.BlitRect(NX,NY,NS,S,self.ColorSet['black'])
         self.BlitRect(X,Y,S,S,self.ColorSet['blue'])
         # border
         pygame.draw.rect(self.screen, self.ColorSet['black'], (X,Y,S,S), BB)
         pygame.draw.rect(self.screen, self.ColorSet['black'], (NX,NY,NS,S), BB)
         # text
         textF = font1.render(txt1,True, self.ColorSet['black'])
         self.screen.blit(textF, [TX,TY+ScaledTS1[2]])
         txt2 = font2.render(txt2,True, self.ColorSet['white'])
         self.screen.blit(txt2, [TX2,TY2+ScaledTS2[2]])
         
         # Third Menu
         # Fonts & text creation
         Y += line_space
         NY += line_space
         TY += line_space
         TY2 += line_space
         txt1 = "F3"
         ScaledTS1 = self.ScaleTxt(txt1, S-self.space*2, S)
         TS1 = ScaledTS1[0]
         font1 = pygame.font.Font(self.defaultfontpath, TS1)
         txt2 = self.Lang.lang('game-type-manual')
         ScaledTS2 = self.ScaleTxt(txt2, NS-self.space*2, S)
         TS2 = ScaledTS2[0]
         font2 = pygame.font.Font(self.defaultfontpath, TS2)
         # boxes
         self.BlitRect(NX,NY,NS,S,self.ColorSet['black'])
         self.BlitRect(X,Y,S,S,self.ColorSet['blue'])
         # border
         pygame.draw.rect(self.screen, self.ColorSet['black'], (X,Y,S,S), BB)
         pygame.draw.rect(self.screen, self.ColorSet['black'], (NX,NY,NS,S), BB)
         # text
         textF = font1.render(txt1,True, self.ColorSet['black'])
         self.screen.blit(textF, [TX,TY+ScaledTS1[2]])
         txt2 = font2.render(txt2,True, self.ColorSet['white'])
         self.screen.blit(txt2, [TX2,TY2+ScaledTS2[2]])

         # Third Menu
         # Fonts & text creation
         Y += line_space
         NY += line_space
         TY += line_space
         TY2 += line_space
         txt1 = "Esc"
         ScaledTS1 = self.ScaleTxt(txt1, S-self.space*2, S)
         TS1 = ScaledTS1[0]
         font1 = pygame.font.Font(self.defaultfontpath, TS1)
         txt2 = self.Lang.lang('exit')
         ScaledTS2 = self.ScaleTxt(txt2, NS-self.space*2, S)
         TS2 = ScaledTS2[0]
         font2 = pygame.font.Font(self.defaultfontpath, TS2)
         # boxes
         self.BlitRect(NX,NY,NS,S,self.ColorSet['black'])
         self.BlitRect(X,Y,S,S,self.ColorSet['blue'])
         # border
         pygame.draw.rect(self.screen, self.ColorSet['black'], (X,Y,S,S), BB)
         pygame.draw.rect(self.screen, self.ColorSet['black'], (NX,NY,NS,S), BB)
         # text
         textF = font1.render(txt1,True, self.ColorSet['black'])
         self.screen.blit(textF, [TX,TY+ScaledTS1[2]])
         txt2 = font2.render(txt2,True, self.ColorSet['white'])
         self.screen.blit(txt2, [TX2,TY2+ScaledTS2[2]])       
         
         # Update screen
         self.UpdateScreen()
         K=self.Inputs.ListenInputs(['arrows','fx','alpha'],['escape','TOGGLEFULLSCREEN'])
         if K=='f1':
            return 'local'
         if K=='f2':
            return 'netmaster'
         if K=='f3':
            return 'netmanual'
         if K=='TOGGLEFULLSCREEN':#Toggle fullscreen
            self.CreateScreen(True)
         if K=='escape':
            sys.exit(0)

#
# Menu to setup Network options
#
   def NetOptions(self):
      # Max length for fields
      maxlength={}
      maxlength['netgamename']=20
      maxlength['servername']=60
      maxlength['serveralias']=60
      maxlength['serverport']=10
      # Create a random game name ending by this number
      randgamename = random.randint(10000, 99999)
      if self.netgamename==None:
         self.netgamename=str(self.Config.GetValue('SectionAdvanced','netgamename')).lower()
         if self.netgamename=='false':self.netgamename='game{}'.format(randgamename)
      if self.servername==None:
         self.servername=str(self.Config.GetValue('SectionAdvanced','servername'))
         if self.servername=='False':self.servername=''
      if self.serveralias==None:
         self.serveralias=str(self.Config.GetValue('SectionAdvanced','serveralias'))
         if self.serveralias=='False':self.serveralias=''
      if self.serverport==None:
         self.serverport=str(self.Config.GetValue('SectionAdvanced','serverport'))
         if self.serverport=='False':self.serverport=''
      edit={}
      while True:
         # Constants
         BB=2#Border
         Y = int(self.res['y']/4)
         X = int(self.res['x']/15)
         S = int(self.res['y']/22)# Basic size unit
         space = int(S*3)
         NX = X+S
         NY = Y
         BoxX = self.res['x'] - 2*X - 2*S#Size of the option box
         # Background display
         self.DisplayBackground()
         
         # Display Title
         self.MenuHeader(self.Lang.lang('net-options'))
         
         # First Option : Game name
         if 'netgamename' in edit:boxcolor=self.ColorSet['red']#Change color of Fx box if editing in progress
         else: boxcolor=self.ColorSet['blue']# Else standard color
         self.BlitRect(X,Y-S,BoxX,S,self.ColorSet['white'])#Item title box
         self.BlitRect(X,Y,S,S,boxcolor,BB,self.ColorSet['black'])#Fx Box
         self.BlitRect(NX,NY,BoxX,S,self.ColorSet['black'],BB,self.ColorSet['white'])#Value box
         
         ScaledFSFx = self.ScaleTxt("F1",S,S)
         font = pygame.font.Font(self.defaultfontpath, ScaledFSFx[0])
         textF = font.render("F1",True, self.ColorSet['black'])
         
         ScaledFS = self.ScaleTxt(self.Lang.lang('net-options-netgamename'),BoxX,S)
         font = pygame.font.Font(self.defaultfontpath, ScaledFS[0])
         textE = font.render(self.Lang.lang('net-options-netgamename'),True, self.ColorSet['black'])
         
         self.screen.blit(textF, [X + ScaledFSFx[1] ,Y + ScaledFSFx[2]])
         self.screen.blit(textE, [X + self.space,Y-S-BB + ScaledFS[2]])
         
         if 'netgamename' in edit:
            self.netgamename=edit['netgamename']
            txt="{}_".format(self.netgamename.lower())
         else:
            txt=self.netgamename.lower()
         ScaledT = self.ScaleTxt(txt,BoxX,S)
         font = pygame.font.Font(self.defaultfontpath, ScaledT[0])
         txt=font.render(txt,True, self.ColorSet['white'])
         self.screen.blit(txt, [X + S + self.space*2 ,Y + ScaledT[2] + self.space])
         
         # Second Option : Server name
         if 'servername' in edit:boxcolor=self.ColorSet['red'] 
         else: boxcolor=self.ColorSet['blue']
         self.BlitRect(X,Y-S + space,BoxX,S,self.ColorSet['white'])#Item title box
         self.BlitRect(X,Y + space,S,S,boxcolor,BB,self.ColorSet['black'])#Fx Box
         self.BlitRect(NX,NY + space,BoxX,S,self.ColorSet['black'],BB,self.ColorSet['white'])#Value box
         
         ScaledFSFx = self.ScaleTxt("F2",S,S)
         font = pygame.font.Font(self.defaultfontpath, ScaledFSFx[0])
         textF = font.render("F2",True, self.ColorSet['black'])
         
         ScaledFS = self.ScaleTxt(self.Lang.lang('net-options-servername'),BoxX,S)
         font = pygame.font.Font(self.defaultfontpath, ScaledFS[0])
         textE = font.render(self.Lang.lang('net-options-servername'),True, self.ColorSet['black'])
         
         self.screen.blit(textF, [X + ScaledFSFx[1] ,Y + ScaledFSFx[2] + space])
         self.screen.blit(textE, [X + self.space,Y-S-BB + ScaledFS[2] + space])

         if 'servername' in edit:
            self.servername=edit['servername']
            txt="{}_".format(self.servername)
         else:
            txt=self.servername

         ScaledT = self.ScaleTxt(txt,BoxX,S)
         font = pygame.font.Font(self.defaultfontpath, ScaledT[0])
         txt=font.render(txt,True, self.ColorSet['white'])
         self.screen.blit(txt, [X + S + self.space*2 ,Y + ScaledT[2] + self.space + space])
         
         # Third Option : Server Alias
         if 'serveralias' in edit:boxcolor=self.ColorSet['red'] 
         else: boxcolor=self.ColorSet['blue']
         self.BlitRect(X,Y-S+space*2,BoxX,S,self.ColorSet['white'])#Item title box
         self.BlitRect(X,Y+space*2,S,S,boxcolor,BB,self.ColorSet['black'])#Fx Box
         self.BlitRect(NX,NY+space*2,BoxX,S,self.ColorSet['black'],BB,self.ColorSet['white'])#Value box
         
         ScaledFSFx = self.ScaleTxt("F3",S,S)
         font = pygame.font.Font(self.defaultfontpath, ScaledFSFx[0])
         textF = font.render("F3",True, self.ColorSet['black'])
         
         ScaledFS = self.ScaleTxt(self.Lang.lang('net-options-serveralias'),BoxX,S)
         font = pygame.font.Font(self.defaultfontpath, ScaledFS[0])
         textE = font.render(self.Lang.lang('net-options-serveralias'),True, self.ColorSet['black'])
         
         self.screen.blit(textF, [X + ScaledFSFx[1] ,Y + ScaledFSFx[2] + space*2])
         self.screen.blit(textE, [X + self.space,Y-S-BB + ScaledFS[2] + space*2])
         
         if 'serveralias' in edit:
            self.serveralias=edit['serveralias']
            txt="{}_".format(self.serveralias)
         else:
            txt=self.serveralias
         ScaledT = self.ScaleTxt(txt,BoxX,S)
         font = pygame.font.Font(self.defaultfontpath, ScaledT[0])
         txt=font.render(txt,True, self.ColorSet['white'])
         self.screen.blit(txt, [X + S + self.space*2 ,Y + ScaledT[2] + self.space + space*2])
         
         # Fourth Option : Server port
         if 'serverport' in edit:boxcolor=self.ColorSet['red'] 
         else: boxcolor=self.ColorSet['blue']
         self.BlitRect(X,Y-S+space*3,BoxX,S,self.ColorSet['white'])#Item title box
         self.BlitRect(X,Y+space*3,S,S,boxcolor,BB,self.ColorSet['black'])#Fx Box
         self.BlitRect(NX,NY+space*3,BoxX,S,self.ColorSet['black'],BB,self.ColorSet['white'])#Value box
         
         ScaledFSFx = self.ScaleTxt("F4",S,S)
         font = pygame.font.Font(self.defaultfontpath, ScaledFSFx[0])
         textF = font.render("F4",True, self.ColorSet['black'])
         
         ScaledFS = self.ScaleTxt(self.Lang.lang('net-options-serverport'),BoxX,S)
         font = pygame.font.Font(self.defaultfontpath, ScaledFS[0])
         textE = font.render(self.Lang.lang('net-options-serverport'),True, self.ColorSet['black'])
         
         self.screen.blit(textF, [X + ScaledFSFx[1] ,Y + ScaledFSFx[2] + space*3])
         self.screen.blit(textE, [X + self.space,Y-S-BB + ScaledFS[2] + space*3])
 
         if 'serverport' in edit:
            self.serverport=edit['serverport']
            txt="{}_".format(self.serverport)
         else:
            txt=self.serverport

         ScaledT = self.ScaleTxt(txt,BoxX,S)
         font = pygame.font.Font(self.defaultfontpath, ScaledT[0])
         txt=font.render(txt,True, self.ColorSet['white'])
         self.screen.blit(txt, [X + S + self.space*2 ,Y + ScaledT[2] + self.space + space*3])
         
         # display Previous Menu square to tell the player he can navigate in menus
         self.PreviousMenu()
         self.UpdateScreen()
         if edit and len(edit)>0:
            K=self.Inputs.ListenInputs(['fx','alpha','num','math','arrows'],['enter','backspace'],context='editing')
         else:
            K=self.Inputs.ListenInputs(['fx','alpha','num','math','arrows'],['backspace','enter','escape','TOGGLEFULLSCREEN'])
         if K=='f1':
            edit={}
            edit['netgamename']=''
         elif (K=='TOGGLEFULLSCREEN') and len(edit)==0:#Toggle fullscreen
            self.CreateScreen(True)
         elif K=='f2':
            edit={}
            edit['servername']=''
         elif K=='f3':
            edit={}
            edit['serveralias']=''
         elif K=='f4':
            edit={}
            edit['serverport']=''
         elif (K=='enter' or K=='return') and len(edit)==0:
            NetOptions={}
            NetOptions['GAMENAME']=self.netgamename
            NetOptions['SERVERIP']=self.servername
            NetOptions['SERVERALIAS']=self.serveralias
            NetOptions['SERVERPORT']=self.serverport
            return NetOptions
         elif (K=='enter' or K=='return') and len(edit)>0:
            edit={}
         elif K=='backspace' and len(edit)>0:
            for e in edit:
               edit[e] = edit[e][:-1]
         elif len(edit)>0 and len(str(K))==1:# If the user hit a standard char
            for e in edit:# Update value in the temp storage disct (MUST be only one value)
               if len(edit[e])<maxlength[e]:# Disallow typing more that the maxlength number of chars
                  edit[e]="{}{}".format(edit[e],K)
         elif K=='escape':
            return K

#
# Display Arrows to show the player that he can navigate in the menu
#

# Press enter
   def PressEnter(self,txt,X=None,Y=None,SX=None,SY=None,Update=False):
      BS = int(self.res['y']/15)
      if SX == None : SX = int(self.res['x']/7)
      if SY == None : SY = int(self.res['y']/15)
      if X == None : X = int(self.res['x'] - int(self.res['x'] / 15) - SX)
      if Y == None : Y = int(self.res['y'] - self.res['y']/10)#Same as PreviousMenu
      ImgSX = int(SY/2)
      ImgSY = ImgSX

      # Do not display text if screen is small
      if ImgSX >= int(SX/3):
         txt=False
         ImgSX = int(SY*0.8)
         ImgSY = ImgSX

      # Container
      BB = 2
      #pygame.draw.rect(self.screen, self.ColorSet['black'], (X,Y,SX,SY), BB)
      self.BlitRect(X,Y,SX,SY,self.ColorSet['black'])
      # Print text
      if txt:
         Scaled = self.ScaleTxt(txt,SX-ImgSX-self.space*2,SY)
         font = pygame.font.Font(self.defaultfontpath, Scaled[0])
         text = font.render(str(txt),True, self.ColorSet['white'])
         self.screen.blit(text, [X+Scaled[1]+ImgSX+self.space*2,Y+Scaled[2]])
      # Print image
      imagefile = self.GetPathOfFile('images', 'key_enter.png')
      if imagefile != False:
         Pbgimage=pygame.image.load(imagefile)
      else:
         self.Logs.Log("WARNING","Unable to find logo image key_enter.png. Please download pyDarts again.")
      # Get image size
      ImgSize=Pbgimage.get_rect().size
      # Calculate image size (save proportions)
      prop = ImgSize[0] / ImgSize[1] 
      # Scale on X
      #ImgSX = int(SY/2)
      ImgSY = int(ImgSX / prop)
      Pbgimage=pygame.transform.scale(Pbgimage,(ImgSX,ImgSY))
      self.screen.blit(Pbgimage, (X+self.space,Y + int((SY-ImgSY)/2)))
      if Update:self.UpdateScreen()

# Previous
   def PreviousMenu(self,X=None,Y=None,S=None,Update=False):
      if Y == None : Y = int(self.res['y'] - self.res['y']/10)
      if X == None : X = int(self.res['x'] / 15)
      if S == None : S = int(self.res['y']/15)
      BB = 2
      TX = int(X + S/6)
      TY = int(Y + S/6)
      TS = int(S/2)
      font = pygame.font.Font(self.defaultfontpath, TS)
      pygame.draw.rect(self.screen, self.ColorSet['black'], (X,Y,S,S), BB)
      self.BlitRect(X,Y,S,S,self.ColorSet['black'])
      text = font.render("Esc",True, self.ColorSet['white'])
      self.screen.blit(text, [TX,TY])
      if Update:self.UpdateScreen()

# Left
   def LeftArrow(self,X=None,Y=None,S=None,Update=False):
      if Y == None : Y = int(self.res['y'] - self.res['y']/10)
      if X == None : X = int(self.res['x'] / 15)
      if S == None : S = int(self.res['y']/15)
      BB = 2
      TX = int(X + S/3)
      TY = int(Y + S/6)
      TS = int(S/2)
      font = pygame.font.Font(self.defaultfontpath, TS)
      pygame.draw.rect(self.screen, self.ColorSet['black'], (X,Y,S,S), BB)
      self.BlitRect(X,Y,S,S,self.ColorSet['black'])
      text = font.render("<",True, self.ColorSet['white'])
      self.screen.blit(text, [TX,TY])
      if Update:self.UpdateScreen()

# Down
   def DownArrow(self,X=None,Y=None,S=None,Update=False):
      if S == None : S = int(self.res['y']/15)
      if Y == None : Y = int(self.res['y'] - S)
      if X == None : X = int(self.res['x'] - S)
      BB = 2
      TX = int(X + S/3)
      TY = int(Y + S/6)
      TS = int(S/2)
      font = pygame.font.Font(self.defaultfontpath, TS)
      pygame.draw.rect(self.screen, self.ColorSet['black'], (X,Y,S,S), BB)
      self.BlitRect(X,Y,S,S,self.ColorSet['black'])
      text = font.render("v",True, self.ColorSet['white'])
      self.screen.blit(text, [TX,TY])
      if Update:self.UpdateScreen()

# Up
   def UpArrow(self,X=None,Y=None,S=None,Update=False):
      if S == None : S = int(self.res['y']/15)
      if Y == None : Y = S
      if X == None : X = int(self.res['x'] - S)
      BB = 2
      TX = int(X + S/3)
      TY = int(Y + S/6)
      TS = int(S/2)
      font = pygame.font.Font(self.defaultfontpath, TS)
      pygame.draw.rect(self.screen, self.ColorSet['black'], (X,Y,S,S), BB)
      self.BlitRect(X,Y,S,S,self.ColorSet['black'])
      text = font.render("^",True, self.ColorSet['white'])
      self.screen.blit(text, [TX,TY])
      if Update:self.UpdateScreen()


#
# Get Game List from local game folder
#
   def GetGameList(self):
      #import pkgutil
      #[name for _, name, _ in pkgutil.iter_modules(['games'])]
      text=[]
      GameFilename={}
      fileiter = (os.path.join(root, f)
         for root, _, files in os.walk('games')
         for f in files)
      menu_data=[self.Lang.lang('game-list')]
      Games = []
      for foundfiles in fileiter:
         fileName,fileExtension = os.path.splitext(foundfiles)
         if fileExtension == '.py' and os.path.basename(fileName) != '__init__':
            Games.append(os.path.basename(fileName))
            GameFilename[fileName]=os.path.basename(fileName)
            menu_data.append(os.path.basename(fileName))
      # If Games list is empty, simulate it
      if len(Games) == 0:
         Games = officialgames
      # Display all games names
      txtgames="/".join(menu_data[1:])
      self.Logs.Log("DEBUG","Found these games : {}".format(txtgames))
      return Games      


#
# Get Game description (from language file)
#
   def GetDesc(self,Game):
      Desc=[]
      try:
         Desc=self.Lang.lang('Description-{}'.format(Game))
      except:
         Desc.append(self.Lang.lang('game-no-desc'))
         self.Logs.Log("WARNING","Unable to get a description for game {}".format(Game))
      return Desc


#
# Menu which display a table to choose server (MasterServer Client)
#
   def GameList(self,Games,bgimage='background.png'):
      self.Logs.Log("DEBUG","Waiting for game choice")
      sel=0
      i=-1
      prop_limit = 1
      while True:
         i+=1
         BB=2
         Y = int(self.res['y']/6)
         X = int(self.res['x']/15)
         W = int(self.res['x']/2.5)
         H = int(self.res['y']/(len(Games)*1.5))
         
         TH= int(H/2)
         TX= int(X + (TH / 4)) 
         TY= int(Y + (TH / 4))
         # Get Game details of selected game
         Desc=self.GetDesc(Games[sel])
         # Detail box 
         GX = int(self.res['x'] / 2.1)
         GY = Y
         GW = int(self.res['x']/2.1)
         GH = H*len(Games)
         Gspace=int(GW/20)
         # Game Image
         try:
            im = self.GetPathOfFile('images', '{}.png'.format(Games[sel]))
            im = pygame.image.load(im)
            im_size=im.get_rect().size# Get image size
            im_prop = im_size[0] / im_size[1]
            # Adapt image to screen size save proportions
            if im_size[0] >= im_size[1] and self.screen_proportions>=prop_limit:
               iW = int(GW / 3.5)
               iH = int(iW / im_prop)
            elif im_size[0] >= im_size[1] and self.screen_proportions<prop_limit:
               iW = int(GW / 1.5)
               iH = int(iW / im_prop)
            else:
               iH = int(GH / 8)
               iW = int(iH * im_prop)               
            iX = GX + ((GW-iW) / 2)
            # Responsive : center image if no text will be displayed
            if self.screen_proportions>=prop_limit:
               iY = GY + self.space*3
            else:
               iY = int(GY + (GH / 2) - (iH / 2))
            im = pygame.transform.scale(im,(iW,iH))
         except Exception as e:
            self.Logs.Log("FATAL","No image file for game {}. Error was : {}".format(Games[sel],e))
         
         # Game desc X and Y
         dX = GX + Gspace
         dY = GY + iH + Gspace + self.space
         # Draw
         self.DisplayBackground()
         # Titles
         self.MenuHeader(self.Lang.lang('game-list'))
         j=-1
         for G in Games:
            j+=1
            if j==sel:
               pygame.draw.rect(self.screen, self.ColorSet['grey'], (X,Y,W,H), 0)
            else:
               self.BlitRect(X,Y,W,H,self.ColorSet['black'])
            # Display border
            pygame.draw.rect(self.screen, self.ColorSet['black'], (X,Y,W,H), BB)
            # Display game name
            ScaledGameName = self.ScaleTxt(G,W,H)
            font = pygame.font.Font(self.defaultfontpath, ScaledGameName[0])
            text = font.render(G,True, self.ColorSet['white'])
            self.screen.blit(text, [X+ScaledGameName[1],Y+ScaledGameName[2]])
            # Increment
            Y+=H
            TY+=H
         # Display detail box
         self.BlitRect(GX,GY,GW,GH,self.ColorSet['black'])
         # Display image 
         self.screen.blit(im, (iX,iY))
         # Print game description, only if screen proportions allow it (width >= height)
         if self.screen_proportions >= prop_limit:
            idesc=0
            # Get longest string of list
            Desc=Desc.splitlines()
            longestid = 0
            maxsize = 0
            i=0
            for line in Desc:
               font = pygame.font.Font(self.defaultfontpath, 50)# Compare all string rendered
               fontsize = font.size(line)
               if fontsize[0]>maxsize:
                  maxsize = fontsize[0]
                  longestid = i
               i+=1
            Scaled = self.ScaleTxt(Desc[longestid],GW-Gspace*2,GH-iH)
            FS = min(Scaled[0],int(GW/20))
            for line in Desc:
               font = pygame.font.Font(self.defaultfontpath, FS)
               text = font.render(line,True, self.ColorSet['white'])
               self.screen.blit(text, [dX,dY + Gspace + Gspace*idesc])
               idesc+=1
         # Arrow to go back
         self.PreviousMenu()
         # Update screen
         self.UpdateScreen()
         K=self.Inputs.ListenInputs(['arrows','alpha'],['escape','enter','TOGGLEFULLSCREEN'])
         if K == 'return' or K == 'enter':
            return Games[sel]
         elif K=='TOGGLEFULLSCREEN':#Toggle fullscreen
            self.CreateScreen(True)
         elif K=='down' and sel<len(Games)-1:
            sel+=1
         elif K=='up' and sel>0:
            sel-=1
         elif K=='escape':
            return K

#        
# Menu which display a table to choose server (MasterServer Client)
#
   def ServerList(self,NetMasterClient,NuPl,bgimage='background.png'):
      self.Inputs.shift = False # Reinit Kbd Shift status
      # Display "Pending connexion..."
      self.DisplayBackground(bgimage)
      self.InfoMessage([self.Lang.lang('master-client-connecting')],1000)
      while True:
         try:
            NetMasterClient.connect_master(self.Config.GetValue('SectionGlobals','masterserver'),int(self.Config.GetValue('SectionGlobals','masterport')))
         except:
            self.Logs.Log("ERROR","Unable to reach Master Server : {} on port : {}".format(self.Config.GetValue('SectionGlobals','masterserver'),int(self.Config.GetValue('SectionGlobals','masterport'))))
            self.DisplayBackground()
            self.InfoMessage([self.Lang.lang('master-client-no-connection')])
            return 'escape' # Tels master loop to turn back to previous menu
         List=NetMasterClient.wait_list(NuPl) # get and clean server list
         NetMasterClient.close_cx()
         #txts=int(round(self.res['y'] / 20,0))
         selected=0
         if not List:
            self.InfoMessage([self.Lang.lang('master-client-empty')],2000)
            self.InfoMessage([self.Lang.lang('master-client-refresh')],0,'small','bottom')
            self.PreviousMenu(None,None,None,True)
            # Wait for input
            key=self.Inputs.ListenInputs(['arrows','alpha'],['escape','space','TOGGLEFULLSCREEN'])
            # Hit any key
            if key=='TOGGLEFULLSCREEN':# Toggle fullscreen
               self.CreateScreen(True)
            elif key=='escape':
               return key
         else:
            displaymax=10#How many lines to display
            #font = pygame.font.Font(self.defaultfontpath, int(round(txts/1.5))) # Text Size
            maxsel=min(len(List),displaymax)
            showst=0
            showend=maxsel
            ListLength=len(List)
            while True:
               # Set the width of each column depending on screen width
               if self.screen_proportions<1:
                  colfactor={'ID':0,'STATUS':0,'PLAYERS':3,'GAMENAME':11,'SERVERIP':0,'SERVERPORT':0}
               else:
                  colfactor={'ID':0,'STATUS':2,'PLAYERS':3,'GAMENAME':3,'SERVERIP':3,'SERVERPORT':3}
               # Some basics
               x=int(self.res['x'] / 17)
               y=int(self.res['y'] / 17)
               # Text size
               #txts=int(round(y / 2,0))
               # Display basis
               self.DisplayBackground(bgimage)
               self.MenuHeader(self.Lang.lang('master-client-title'),self.Lang.lang('master-client-refresh'))
               # Init
               celsizex=x
               i=-1
               # Cel position
               posx=0
               posy=y*i + (4 * y)
               # Draw table header
               for Opt,Val in List[0].items():
                  try:
                     txt = self.Lang.lang("serverlist-header-{}".format(Opt))
                  except:
                     self.Logs.Log("WARNING","No translation for table header {}".format(Opt))
                     txt = str(Opt)
                  posx+=celsizex
                  if colfactor.has_key(Opt):
                     celsizex=x*colfactor[Opt]
                  else:
                     celsizex=0
                  if celsizex>0 and (self.screen_proportions>1 or Opt=="GAMENAME" or Opt=="PLAYERS"):# On a small screen , display only GAMENAME
                     self.BlitRect(posx,posy,celsizex,y,self.ColorSet['white'])
                     Scaled = self.ScaleTxt(txt,celsizex,y)
                     font = pygame.font.Font(self.defaultfontpath, Scaled[0])
                     textF = font.render(txt,True, self.ColorSet['black'])
                     self.screen.blit(textF, [posx + Scaled[1],posy + Scaled[2]])
               # Optionnaly display UP arrow
               if showst > 0:
                  self.UpArrow(posx+celsizex,posy+y,y)

               # For each line of the table
               i+=1
               
               for Value in List[showst:showend]:
                  if selected==i:
                     celcolor=self.ColorSet['grey']
                  elif i%2==0:
                     celcolor=self.ColorSet['blue'] 
                  else:
                     celcolor=self.ColorSet['black']
                  modulo=i%2
                  celsizex=x
                  # Cel position
                  posx=0
                  posy=y*i + (4 * y)
                  j=1
                  # For each row of the table
                  for Opt,Val in Value.items():
                     posx+=celsizex
                     if colfactor.has_key(Opt):
                        celsizex=x*colfactor[Opt]
                     else:
                        celsizex=0
                     if celsizex>0 and (self.screen_proportions>1 or Opt=="GAMENAME" or Opt=="PLAYERS"):# On a small screen , display only GAMENAME
                        self.BlitRect(posx,posy,celsizex,y,celcolor)
                        Scaled = self.ScaleTxt(str(Val),celsizex,y)
                        font = pygame.font.Font(self.defaultfontpath, Scaled[0])
                        textF = font.render(str(Val),True, self.ColorSet['white'])
                        self.screen.blit(textF, [posx + Scaled[1],posy + Scaled[2]])
                     j+=1
                  i+=1
               # Optionnaly display DOWN arrow
               if ListLength > showend:
                  self.DownArrow(posx+celsizex,posy,y)               
               self.PreviousMenu()# Previous menu square
               self.UpdateScreen()# Refresh screen
               
               # Modify selected row
               key=self.Inputs.ListenInputs(['arrows','alpha'],['enter','escape','space','TOGGLEFULLSCREEN'])
               # Hit any key
               if key=='down' and selected<maxsel-1 and selected+showst<ListLength-1:
                  selected+=1
               elif key=='down' and selected==maxsel-1 and selected+showst<ListLength-1:
                  showst+=1
                  showend+=1
               elif key=='down' and selected==maxsel-1 and selected+showst==ListLength-1:
                  showst=0
                  showend=maxsel
                  selected=0
               elif key=='TOGGLEFULLSCREEN':#Toggle fullscreen
                  self.CreateScreen(True)
               elif key=='up' and selected>0:
                  selected-=1
               elif key=='up' and selected==0 and showst>0:
                  showst-=1
                  showend-=1
               elif key=='up' and selected==0 and showst==0:
                  selected=maxsel-1
                  showst=max(0,ListLength-displaymax)
                  showend=ListLength
               elif key=='enter' or key=='return':
                  return List[selected+showst]
               elif key=='escape':
                  return key
               else:
                  break

# Version 2 of menu to choose options
   def OptionsMenu2(self,GameOpts,Game,bgimage='background.png'):
      if GameOpts == {}: return {} # Case of a game without options
      self.Logs.Log("DEBUG","Waiting for game options")
      # Init
      numericmaxlen = 10
      editing = {}
      self.Inputs.shift = False # Reinit Kbd Shift status
      # Loop
      while True:
         border=2 # border in px
         fkeys = []
         self.DisplayBackground(bgimage)
         #Fx sizing
         Fx = int(self.res['x'] / 40) # Start point of first option
         Fy = int(self.res['y'] / 5.5) # Start point of first option
         Fsize = int(min(self.res['x'] / 15, self.res['y'] / 15))# Basic size of a box (height and width)
         space = int(Fsize / 2) # Space between options
         Vsize = Fsize * 4 # Value size 
         textsize=int(self.res['y'] / 35) # Size of basic text
         self.MenuHeader("{} {}".format(self.Lang.lang('game-options'),Game),self.Lang.lang('game-options-binary'))# Display menu header
         # Init
         i=1
         for EachOpt,EachValue in GameOpts.items():
            # Try to translate Option name
            try:
               AliasEachOpt = self.Lang.lang("{}-{}".format(Game,EachOpt))
            except:
               AliasEachOpt = EachOpt
               self.Logs.Log("ERROR","No translation for game option {} for the Game {}".format(EachOpt,Game))

            # Determine the place of the option name
            if EachValue=='True' or EachValue=='False':
               Tx = Fx + Fsize
               Tw = Fsize * 12
            else:
               Tx = Fx + Fsize + Fsize*6
               Tw = Fsize * 6
            
            # Scale Opt name
            ScaledOpt = self.ScaleTxt(AliasEachOpt,Tw - self.space*2,Fsize)
            font = pygame.font.Font(self.defaultfontpath, ScaledOpt[0]) # Text size for second & third line
            textEachOpt= font.render(AliasEachOpt,True, self.ColorSet['black'])
            # Display Option name square
            self.BlitRect(Tx,Fy,Tw,Fsize,self.ColorSet['white'])
            # Display Option name label
            self.screen.blit(textEachOpt, [Tx + self.space*2,Fy+ScaledOpt[2]])
            # Append actual Fx key to the usable keys
            fkeys.append('f{}'.format(i))
            # Draw Fx square and value
            # False or turning false
            if (EachValue=='False' and str(i) not in editing) or (EachValue=='True' and str(i) in editing):
               self.BlitRect(Fx,Fy,Fsize,Fsize,self.ColorSet['red'],border,False)
               try:del editing[str(i)]
               except:pass
               GameOpts[EachOpt]='False'#Switch to False
            # True or turning true
            elif (EachValue=='True' and str(i) not in editing) or (EachValue=='False' and str(i) in editing):
               self.BlitRect(Fx,Fy,Fsize,Fsize,self.ColorSet['green'],border,False)
               try:del editing[str(i)]
               except:pass
               GameOpts[EachOpt]='True'#Switch to true
            # Else its not a boolean
            else:
               self.BlitRect(Fx,Fy,Fsize,Fsize,self.ColorSet['grey'],border,False)
            
            # Draw Fx
            F = "F{}".format(i)
            ScaledF = self.ScaleTxt(F,Fsize,Fsize)
            font = pygame.font.Font(self.defaultfontpath, ScaledF[0])
            textF = font.render(F ,True, self.ColorSet['white'])
            self.screen.blit(textF, [Fx+ScaledF[1],Fy+ScaledF[2]])
            
            # Option Value (only for NUMERIC Values)
            if (EachValue!='False' and EachValue!='True'):
               if str(i) in editing:#Start editing, clear value
                  c = self.ColorSet['red']
                  if editing[str(i)] == '':
                     v=''
                  else:# Append new char to the numeric value
                     v = int(editing[str(i)])
                     GameOpts[EachOpt]=v
               else:
                  c = self.ColorSet['grey']
                  v=int(EachValue)
               # Draw value box for valuable options
               self.BlitRect(Fx+Fsize,Fy,Fsize*6,Fsize,self.ColorSet['black'],border,c)
               # Draw value
               ScaledV = self.ScaleTxt(str(v),Fsize*6,Fsize,None,'fonts/Digital.ttf')
               font = pygame.font.Font('fonts/Digital.ttf', ScaledV[0])
               textEachValue = font.render(str(v),True, self.ColorSet['white'])
               self.screen.blit(textEachValue, [Fx+ Fsize + self.space*2,Fy+ScaledV[2]-self.space])
            # Previous menu square
            self.PreviousMenu()
            # Update display
            pygame.display.update()
            # Increment
            Fy+=Fsize+space
            #texty+=textsize
            i+=1
         # Editing
         if len(editing) > 0:
            K=self.Inputs.ListenInputs(['num','fx'],['enter','backspace'])
         else:
            K=self.Inputs.ListenInputs(['num','fx','arrows'],['enter','escape','TOGGLEFULLSCREEN'])
         # What the user want to say?
         if (K == 'return' or K == 'enter') and len(editing)==0:
            return GameOpts
         elif (K=='TOGGLEFULLSCREEN') and len(editing)==0:#Toggle fullscreen
            self.CreateScreen(True)
         elif (K == 'return' or K == 'enter') and len(editing)>0:
            editing={}
         elif K == 'backspace' and len(editing)>0:
            for k in editing:
               editing[k] = editing[k][:-1]
         elif K in fkeys:
            editing={}
            editing[K[1:]]=''
         elif K=='escape':
            return K
         elif len(editing)>0 :
            for curr in editing:
               if len(editing[curr])<numericmaxlen:# Forbid to set a numeric value of more than numericmaxlen char
                  editing[curr] = "{}{}".format(editing[curr],K)

# Version 2 of menu to choose options
   def SelectPort(self,ports,bgimage='background.png'):
      self.Logs.Log("DEBUG","Please select game port")
      # Init
      fkeys=[]
      self.Inputs.shift = False # Reinit Kbd Shift status
      maxdisplayports=8
      # Loop
      while True:
         border=2 # border in px
         self.DisplayBackground(bgimage)
         #Fx sizing
         Fx = int(self.res['x'] / 40) # Start point of first option
         Fy = int(self.res['y'] / 5.5) # Start point of first option
         Fsize = int(self.res['y'] / 15)# Basic size of a box
         space = int(self.res['y'] / 40) # Space between options
         Vsize = int(self.res['x'] - Fsize - Fx*2) # Value size 
         textsize=int(self.res['y'] / 35) # Size of basic text
         self.MenuHeader(self.Lang.lang("select-port"),self.Lang.lang("select-port-subtxt"))# Display menu header
         # Init
         i=1
         
         for portname in ports:
            # Append actual Fx key to the usable keys
            fkeys.append("f{}".format(i))
            # Draw Fx square and value
            self.BlitRect(Fx,Fy,Fsize,Fsize,self.ColorSet['red'],border,False)
            # Draw Fx
            F = "F{}".format(i)
            ScaledF = self.ScaleTxt(F,Fsize,Fsize)
            font = pygame.font.Font(self.defaultfontpath, ScaledF[0])
            textF = font.render(F ,True, self.ColorSet['white'])
            self.screen.blit(textF, [Fx+ScaledF[1],Fy+ScaledF[2]])
            
            # Scale port name
            ScaledPort = self.ScaleTxt(portname,Vsize - self.space*2,Fsize)
            font = pygame.font.Font(self.defaultfontpath, ScaledPort[0]) # Text size for second & third line
            txt= font.render(portname,True, self.ColorSet['black'])
            # Display port square
            self.BlitRect(Fx+Fsize,Fy,Vsize,Fsize,self.ColorSet['white'])
            # Display port name
            self.screen.blit(txt, [Fx+Fsize + ScaledPort[1],Fy+ScaledPort[2]])

            # Previous menu square
            self.PreviousMenu()
            # Update display
            pygame.display.update()
            # Increment
            Fy+=Fsize+space
            #texty+=textsize
            i+=1
            #Limit to 10 ports
            if i>maxdisplayports:
               self.Logs.Log("ERROR","More than {} ports detected, but only {} first are displayed".format(maxdisplayports,maxdisplayports))
               break
         K=self.Inputs.ListenInputs(['num','fx','arrows'],['enter','escape','TOGGLEFULLSCREEN'])
         # What the user want to say?
         if (K == 'return' or K == 'enter'):
            pass
         elif (K=='TOGGLEFULLSCREEN'):#Toggle fullscreen
            self.CreateScreen(True)
         elif K in fkeys:
            selected = int(K[1:])
            return ports[selected-1]
         elif K=='escape':
            self.Logs.Log("DEBUG","See ya dude !")
            sys.exit(0)
#
# Stats Screen
#
   def DisplayStats(self,GameStats,LSTPlayers,NewRecord,GT,bgimage='background.png'):
      # Play Sound if there is a new record (only at first display)
      if NewRecord:
         self.PlaySound('newrecord')
      while True:
         # Init
         self.DisplayBackground(bgimage)
         k=0 # Hi score display increment
         txt = ""
         # Store number of columns to display
         cols = len(GameStats[0])
         rows = len(GameStats)

         if self.res['x']<self.res['y']:#Vertical display
            colsize = int((self.res['x'] / cols) - (self.space*2/cols))
         else:
            colsize = int(self.res['x'] / (cols +2))
         rowsize = int(self.res['y']/24)
         BB = int(self.res['y'] / 200)
         self.MenuHeader(self.Lang.lang('game-stats'))# Print page header
         # Write table
         Y = int(self.res['y'] / 7)
         # For every line of the table
         for i in range(0,rows):
            if self.res['x']<self.res['y']:#Vertical display
               X = self.space
            else:
               X = int((self.res['x']/2) - ((cols*colsize)/2))
            # For every row
            for j in range(0,cols):
               # "HISCORES" & "HISCORES_WHO" is a convention to recognize when the line to write HISCORES arrive
               # If it is a normal cel
               if str(GameStats[i][j])!='HISCORES' and str(GameStats[i][j])!='' :
                  if i==0:
                     self.BlitRect(X,Y,colsize,rowsize,self.ColorSet['green'],BB)
                  else:
                     self.BlitRect(X,Y,colsize,rowsize,self.ColorSet['black'],BB)
                  txt = str(GameStats[i][j])
               # If it as a Hi score cel
               elif str(GameStats[i][j])=='HISCORES' and str(GameStats[i][j])!='':
                  # Add a space between scores and Hi Scores
                  if k==0:
                     Y+=self.space*4
                  k += 1
                  self.BlitRect(X,Y,colsize,rowsize,self.ColorSet['green'],BB)
                  txt=u"{} {}".format(self.Lang.lang('hi-score'),str(k))
               Scaled=self.ScaleTxt(txt,colsize-self.space*2,rowsize)
               font = pygame.font.Font(self.defaultfontpath, Scaled[0])
               LSTtext_rd = font.render(txt,True, self.ColorSet['white'])
               self.screen.blit(LSTtext_rd, [X+Scaled[1]+self.space,Y+Scaled[2]])
               X += colsize
            Y += rowsize
         if GT=='local':
            self.PressEnter(self.Lang.lang('start-again'),None,None,None,None,True)
         # Previous menu square
         self.PreviousMenu()
         pygame.display.flip()
          # Wait for enter
         K=self.Inputs.ListenInputs(['fx'],['escape','enter','TOGGLEFULLSCREEN'])
         if K=='return' or K=='enter':
            return 'startagain'
         elif K=='TOGGLEFULLSCREEN':
            self.CreateScreen(True)
         elif K=='escape':
            return K

# This method fill background squares
   def PlayerLine(self,y,playerid,actualplayer,waittime=False):
      scoresize = int(self.res['x']/5)
      boxsize = int(self.res['x'] / 11.7)
      # Player names' box
      if playerid == actualplayer:bgcolor=self.ColorSet['blue']
      else:bgcolor=self.ColorSet['black']
      self.BlitRect(self.space,y,self.pnsize-self.space,self.lineheight-self.space,bgcolor)
      if waittime:
         pygame.time.wait(waittime)
         self.UpdateScreen()
      # All other boxes
      for i in range(0,int(self.Config.GetValue('SectionGlobals','nbcol'))+1):
         self.BlitRect(self.space + self.pnsize + boxsize*i, y, boxsize-self.space, self.lineheight-self.space, self.ColorSet['black'])
         if waittime:
            pygame.time.wait(waittime)
            self.UpdateScreen()
      # Score box
      self.BlitRect(self.space + self.pnsize + boxsize*(int(self.Config.GetValue('SectionGlobals','nbcol'))+1), y, scoresize-self.space, self.lineheight-self.space, self.ColorSet['black'])
      if waittime:
         pygame.time.wait(waittime)
         self.UpdateScreen()

# This method display column headers
   def Headers(self,Headers,nbpl):
      boxsize = int(self.res['x'] / 11.7)
      FS = self.lineheight
      y = self.Position[0] - self.lineheight - self.space
      #print("Headers Y is : {}".format(y))
      font = pygame.font.Font('fonts/Digital.ttf', FS) # Text Size
      for i in range(0,int(self.Config.GetValue('SectionGlobals','nbcol'))+1):
         #step = 0.2
         #divider = 1
         # Limit header to 3 char
         txt = str(Headers[i][:3])
         Scaled = self.ScaleTxt(txt,boxsize,self.lineheight)
         font = pygame.font.Font(self.defaultfontpath, Scaled[0])
         # Render text
         text = font.render(txt ,True,self.ColorSet['white'])
         # Calculate place of text
         Xtxt = int(self.space + self.pnsize+boxsize*i +  Scaled[1])
         Ytxt = int(y+Scaled[2])
         # Create BG rect
         self.BlitRect(self.space + self.pnsize+boxsize*i, y, boxsize-self.space, self.lineheight, self.ColorSet['grey'], False,False,self.alpha+10)
         # Display text
         self.screen.blit(text, [Xtxt ,Ytxt])         

#
# Refresh In-game screen
#
   def RefreshGameScreen(self,LSTPlayers,Round,TotalRound,RemDarts,nbdarts,LogoImg,Headers,actualplayer,TxtOnLogo=False,Wait=False):
      # Get number of players
      nbplayers = len(LSTPlayers)
      # Recalculate line height
      self.DefineConstants(nbplayers)
      # Clear
      self.screen.fill(self.ColorSet['black'])
      # Background image
      self.DisplayBackground()
      # Game Logo (or optionnaly "Text On Logo"
      if not TxtOnLogo:
         self.GameLogo(LogoImg)
      else:
         self.TxtOnLogo(str(TxtOnLogo))
      # Rounds
      self.DisplayRound(Round,TotalRound)
      # Rem Darts
      self.DisplayRemDarts(RemDarts,nbdarts)
      for P in LSTPlayers:
         # Display all other info on the player line
         if TxtOnLogo:
            self.PlayerLine(self.Position[P.ident],P.ident,actualplayer)# Do not trigger animation
         else:
            self.PlayerLine(self.Position[P.ident],P.ident,actualplayer,int(self.Config.GetValue('SectionAdvanced','animationduration')))# Trigger animation
         # Display Player Score
         self.DisplayScore(self.Position[P.ident],P.GetScore())
         # Displayer player name box
         self.DisplayPlayerName(self.Position[P.ident],P.couleur,P.ident,actualplayer,P.PlayerName)
      # Display Headers
      self.Headers(Headers,len(LSTPlayers))
      # Display Table Content
      self.DisplayTableContent(LSTPlayers)      
      # Refresh !
      self.UpdateScreen()
      # Wait if requested
      if Wait:
         pygame.time.wait(Wait)

#
# Display an image on the middle top of the screen
#
   def GameLogo(self,bgimage=False):
      # Local Constants
      boxsize = int(self.res['x'] / 11.7)
      # 
      X = self.pnsize + self.space
      Y = self.topspace
      SX = boxsize * (int(self.Config.GetValue('SectionGlobals','nbcol'))+1) - self.space
      SY = int((self.res['y'] / 8 * 3.25)-self.lineheight)
      # Load image
      imagefile = self.GetPathOfFile('images', bgimage)
      if imagefile != False:
         Pbgimage=pygame.image.load(imagefile)
      else:
         self.Logs.Log("WARNING","Unable to find logo image {}. Using default.".format(bgimage))
         Pbgimage=pygame.image.load('images/Sample_game.png')
      # Get image size
      ImgSize=Pbgimage.get_rect().size
      # Display rect container
      self.BlitRect(X,Y,SX,SY,self.ColorSet['black'])
      # Calculate image size (save proportions)
      prop = ImgSize[0] / ImgSize[1] 
      # Scale on X
      ImgSX = SX
      ImgSY = int(ImgSX / prop)
      # If scale on X do not fit, scale on Y
      if ImgSX > SX or ImgSY > SY:
         ImgSY = SY
         ImgSX = int(ImgSY * prop)
      Pbgimage=pygame.transform.scale(Pbgimage,(ImgSX,ImgSY))
      self.screen.blit(Pbgimage, (int(X+( (SX - ImgSX) / 2) ),int(Y+( (SY - ImgSY) / 2))))

#
# Display text instead of game logo
#
   def TxtOnLogo(self,txt,Wait=False,Update=False):
      # Local Constants
      boxsize = int(self.res['x'] / 11.7)
      # 
      X = self.pnsize + self.space
      Y = self.topspace
      SX = boxsize * (int(self.Config.GetValue('SectionGlobals','nbcol'))+1) - self.space
      SY = int((self.res['y'] / 8 * 3.25)-self.lineheight)
      BorderColor = self.ColorSet['grey']
      BgColor = self.ColorSet['black']
      BorderSize = int(boxsize / 20)
      TxtColor = self.ColorSet['white']
      Scaled=self.ScaleTxt(txt,SX,SY)
      font = pygame.font.Font(self.defaultfontpath, Scaled[0])
      # Display Rect
      self.BlitRect(X,Y,SX,SY,BgColor,BorderSize,BorderColor)
      # Render text
      text = font.render(txt ,True,TxtColor)
      # Text location
      TX = X + Scaled[1]
      TY = Y + Scaled[2]
      # Blit text
      self.screen.blit(text, [TX,TY])
      if Update:self.UpdateScreen()# Refresh screen if requested
      if Wait:pygame.time.wait(Wait)# Wait if requested

#
# Display a background image
#
   def DisplayBackground(self,bgimage='background.png'):
      imagefile = self.GetPathOfFile('images', bgimage)
      if imagefile != False:
         Pbgimage=pygame.image.load(imagefile)
      else:
         self.Logs.Log("WARNING","Unable to find background image {}. Using default.".format(bgimage))
         Pbgimage=pygame.image.load('images/background.png')
      Pbgimage=pygame.transform.scale(Pbgimage,(int(self.res['x']),int(self.res['y'])))
      self.screen.blit(Pbgimage, (0,0))

#
#  Define and eventually refresh some constants (most of them depends of user resolution)
#

   def DefineConstants(self,nbplayers=None):
      # Define bottom space
      self.bottomspace = int(self.res['y'] / 100)

      # All that depends of the nb of payers
      if nbplayers:
         # Define line height for each player line
         self.lineheight = min(int((self.res['y'] / 1.8 ) / nbplayers),100)
         # Define Y position of each line for each player
         self.Position=[]
         for p in range(0,nbplayers):
            positemp = int(self.res['y'] - self.bottomspace - ((nbplayers-p) *(self.lineheight)))
            self.Position.append(positemp)
      # Player name box size
      self.pnsize = int(self.res['x']/5)
      # Basic space
      self.space = int(self.res['y'] / 200)
      # Proportion between screen Height and Width
      self.screen_proportions = float(float(self.res['x']) / float(self.res['y']))
      # Transparency
      self.alpha = 210
      # Space on left side of the screen
      self.leftspace = int(self.res['x'] / 8)
      # Width of an in-game column
      self.colwidth = int(( self.res['x'] - self.leftspace ) / ( int(self.Config.GetValue('SectionGlobals','nbcol')) + 2 ))
      # Space between leds. Deprecated ?
      self.ledspace = int(self.colwidth / 4)
      # Space at the top side of the screen
      self.topspace = int(self.res['y'] / 55)
      # Default font path
      self.defaultfontpath = 'fonts/Purisa.ttf'
      # Animation time (in ms)
      self.animation = 10
#
# Display name of the player if given, Player X otherwise
#
   def DisplayPlayerName(self,y,couleur,ident,actualplayer,playername=None) :
      if (playername==None):
         playername = 'Player ' + str( ident )
      if actualplayer==ident:txtcolor = self.ColorSet['black']
      else:txtcolor = self.ColorSet['white']
      #  Player name size depends of player name number of char (dynamic size)
      Scaled = self.ScaleTxt(playername,self.pnsize-2*self.space,self.lineheight)
      font = pygame.font.Font(self.defaultfontpath, Scaled[0])
      # Render the text. "True" means anti-aliased text.
      playernamex = self.space * 2 + Scaled[1]
      playernamey = y + Scaled[2]
      text = font.render(playername ,True,txtcolor)
      self.screen.blit(text, [playernamex,playernamey])

# 
# Fill-in table With DISPLAY-LEDS func
# 
   def DisplayTableContent(self,LSTPlayers,Wait=False):
      for Player in LSTPlayers:
         for Column,Value in enumerate(Player.LSTColVal):
            if len(Value)==3:color=Value[2] 
            else:color=None
            #Value = ['killer_skull1','image']# TO REMOVE
            if Value[1] == 'image': # Maybe you want to put images in the table?
               self.DisplayLedsImg(self.Position[Player.ident],Value[0],Column)
            elif Value[1] == 'leds': # Maybe you want to display leds style?
               self.LedBox(self.Position[Player.ident],int(Value[0]),Column,color)
            else: # Else it is simply string/int to display
               self.TxtBox(self.Position[Player.ident],str(Value[0]),Column,color)
            if Wait:
               pygame.time.wait(self.animation)
#
# Graphical representation of a number in the box, from 0 to 3
#
   def LedBox(self,posy,NbLed,Col,Color=None):
      # 3 leds max
      # Constants
      scoresize = int(self.res['x']/5)
      boxsize = int(self.res['x'] / 11.7)
      #
      x = int(Col*boxsize + self.pnsize + self.space)
      y = int(posy)
      xend = int(Col*boxsize + boxsize + self.pnsize - self.space/4)
      yend = int(posy + self.lineheight - self.space*2)
      if Color == None:
         Color = self.ColorSet['white']
      else:
         Color = self.ColorSet[Color]
      BB = int(self.res['y'] / 130)
      if NbLed == 1 :
         pygame.draw.line(self.screen,Color,[x,y+self.space],[xend,yend],BB)
      elif NbLed == 2 :
         pygame.draw.line(self.screen,Color,[x,y+self.space],[xend,yend],BB)
         pygame.draw.line(self.screen,Color,[x,yend],[xend,y+self.space],BB)
      elif NbLed == 3:
         self.BlitRect(self.space + self.pnsize+boxsize*Col, y, boxsize-self.space, self.lineheight-self.space, Color)

# Display text or integer in the given column
   def TxtBox(self,posy,Txt,Col,color=None):
      # keep max 4 char
      Txt = Txt[:4]

      # Asign default color if required
      if color==None : color='white'

      # Constants
      scoresize = int(self.res['x']/5)
      boxsize = int(self.res['x'] / 11.7)

      # Write text in box

      Scaled = self.ScaleTxt(Txt,boxsize-self.space*2,self.lineheight-self.space*2)
      font = pygame.font.Font(self.defaultfontpath, Scaled[0])
      text = font.render(Txt, True, self.ColorSet[color])
      self.screen.blit(text, [Col*boxsize + self.pnsize + self.space*2 + Scaled[1], posy + Scaled[2]])

#
# Display an image in a specified column of a given player
#
   def DisplayLedsImg(self,posy,Image,Col):
     # Constants
      scoresize = int(self.res['x']/5)
      boxsize = int(self.res['x'] / 11.7)
      #
      imgHeight = int(self.lineheight - self.space*3)
      imgWidth = int(min(boxsize-self.space*3,imgHeight))
      #
      X = int(Col * boxsize + self.pnsize + self.space + (boxsize-imgWidth)/2)
      Y = int(posy + self.space)
      #
      imagefile = self.GetPathOfFile('images', '{}.png'.format(Image))
      if imagefile != False:
         Pimage=pygame.image.load(imagefile)
      else:
         self.Logs.Log("FATAL","Unable to find mandatory image {}. Please download pyDarts again or update it.".format(Image))
         sys.exit(1)
      Pimage=pygame.transform.scale(Pimage,(imgWidth,imgHeight))
      self.screen.blit(Pimage, (X,Y))
      pygame.display.flip()
#
# Display score for given player
#
   def DisplayScore(self,posy,txt):
      color = color=self.ColorSet['white']
      txt=str(txt)
      scoresize = int(self.res['x']/5)
      boxsize = int(self.res['x'] / 11.7)
      #
      xtxt = int(self.pnsize + (int(self.Config.GetValue('SectionGlobals','nbcol'))+1) * boxsize)
      Scaled = self.ScaleTxt(txt,scoresize-self.space*2,self.lineheight-self.space*2)
      font = pygame.font.Font(self.defaultfontpath, Scaled[0])
      text = font.render(txt, True, self.ColorSet['white'])
      self.screen.blit(text, [xtxt + self.space*2 + Scaled[1], posy + Scaled[2]])
      
#
# Display how many darts remain
#
   def DisplayRemDarts(self,nb,nbdarts,dartimage='target.png'):
      # Constants
      scoresize = int(self.res['x']/5)
      boxsize = int(self.res['x'] / 11.7)
      #
      X = int(self.space + self.pnsize + (boxsize * 7))
      Y = self.topspace
      #
      SX = int(self.res['x'] - X - self.space)
      SY = int(self.res['y'] / 8 * 3.2)
      #
      Th = int(SY / 10)#Title height
      #
      ImgHeight = min(int((SY-Th) / nbdarts),SX)
      ImgWidth = ImgHeight
      #
      Imgx = X + ((SX - ImgWidth) / 2)
      Imgy = Y + Th
      #
      imagefile = self.GetPathOfFile('images', dartimage)
      #
      ScaledFS=self.ScaleTxt(self.Lang.lang('remaining-darts'),SX,Th)
      fontsize = ScaledFS[0]
      font = pygame.font.Font(self.defaultfontpath, fontsize)
      xtxt = int(X + ScaledFS[1])
      ytxt = int(Y + ScaledFS[2])
      text = font.render(self.Lang.lang('remaining-darts'), True, self.ColorSet['white'])
      #
      if imagefile != False:
         Pdartimage=pygame.image.load(imagefile)
      else:
         self.Logs.Log("FATAL","Unable to find important image : {}. Please update pyDarts or download it again.".format(dartimage))
         sys.exit(1)
      #Display
      self.BlitRect(X,Y,SX,SY,self.ColorSet['black'])
      self.BlitRect(X,Y,SX,Th,self.ColorSet['blue'])
      Pdartimage=pygame.transform.scale(Pdartimage,(ImgWidth,ImgHeight))
      self.screen.blit(text, [xtxt,ytxt])
      for x in range(0,nb):
         self.screen.blit(Pdartimage, (Imgx,Imgy+(x*ImgWidth)))

#
# Display Round
#

   def DisplayRound(self,Round,TotalRound):
      # Constants
      scoresize = int(self.res['x']/5)
      boxsize = int(self.res['x'] / 11.7)
      #
      X = self.space
      Y = self.topspace
      #
      SX = int(self.pnsize-self.space)
      SY = int(self.res['y'] / 8 * 3.2)
      #
      Th = int(SY / 10)#Title Width
      #
      RndFs = int(SY / 12 ) * 5
      ScaledRnd = self.ScaleTxt(str(Round),SX,RndFs,None,'fonts/Digital.ttf')
      fontFs = pygame.font.Font('fonts/Digital.ttf', ScaledRnd[0])
      Rnd = fontFs.render(str(Round), True, self.ColorSet['white'])
      RndX = X + ScaledRnd[1]
      RndY = Y + ScaledRnd[2] + self.space
      #
      RndOverFs = int(SY / 12) * 3
      ScaledRndOver = self.ScaleTxt(str(self.Lang.lang('over')),SX,RndOverFs,None,self.defaultfontpath)
      fontOverFs = pygame.font.Font(self.defaultfontpath,ScaledRndOver[0])
      RndOver = fontOverFs.render(str(self.Lang.lang('over')), True, self.ColorSet['white'])
      RndOverX = X + ScaledRndOver[1]
      RndOverY = Y + RndFs + ScaledRndOver[2]  + self.space * 2 
      #
      RndMaxFs = int(SY / 12) * 4
      ScaledRndMax = self.ScaleTxt(str(TotalRound),SX,RndMaxFs,None,'fonts/Digital.ttf')
      fontMaxFs = pygame.font.Font('fonts/Digital.ttf',ScaledRndMax[0])
      RndMax = fontMaxFs.render(str(TotalRound), True, self.ColorSet['white'])
      RndMaxX = X + ScaledRndMax[1]
      RndMaxY = Y + RndFs + RndOverFs + ScaledRndMax[2]
      #
      ScaledTitle = self.ScaleTxt(str(self.Lang.lang('round')),SX,Th)
      font = pygame.font.Font(self.defaultfontpath, ScaledTitle[0])
      xtxt = X + ScaledTitle[1]
      ytxt = Y +  ScaledTitle[2]
      text = font.render(self.Lang.lang('round'), True, self.ColorSet['white'])
      #Display
      self.BlitRect(X,Y,SX,SY,self.ColorSet['black'])
      self.BlitRect(X,Y,SX,Th,self.ColorSet['blue'])
      self.screen.blit(text, [xtxt,ytxt])
      self.screen.blit(Rnd, [RndX,RndY])
      self.screen.blit(RndOver, [RndOverX,RndOverY])
      self.screen.blit(RndMax, [RndMaxX,RndMaxY])


#
# Display centered text on any part of the screen
#
   def DisplayCenteredText(self,Y,txt,fontsize,bgcolor=None,color=None,fontname=None):
      self.Logs.Log("WARNING","Using the deprecated method CScreen.DisplayCenteredText")
      bgcolor=self.ColorSet['grey'] if bgcolor==None else self.ColorSet[bgcolor]
      color=self.ColorSet['black'] if color==None else self.ColorSet[color]
      font = pygame.font.Font(fontname, int(fontsize))
      text = font.render(txt.encode("iso-8859-1",'replace') ,True, color)
      # Create a centered rectangle
      textRect = text.get_rect()
      # Center the rectangle
      textRect.centerx = self.screen.get_rect().centerx
      textRect.centery = Y
      self.screen.blit(text, textRect)
      pygame.display.flip()

#
# Show the player icon on the top right of the screen
#

   def DisplayPressPlayer(self,txt='Press Player button',color='red'):
      H = int(self.res['y'] / 10)
      W = int(self.res['x'])
      X = 0
      Y = int((self.res['y'] / 2) - (H / 2))
      pygame.draw.rect(self.screen, self.ColorSet[color], (X,Y,W,H), 0)
      Scaled = self.ScaleTxt(txt,W,H)
      font = pygame.font.Font(self.defaultfontpath, Scaled[0])
      text = font.render(txt, True, self.ColorSet['black'])
      self.screen.blit(text, [X+Scaled[1],Y+Scaled[2]])
      #self.DisplayCenteredText(self.res['y']/2,txt,int(self.res['x']/20))
      self.UpdateScreen()

#
# Simply update the screen (after multiple updates for example)
#
   def UpdateScreen(self):
      pygame.display.flip()

#
# Espeak vocal synthetiser (untested on windows)
#
   def Speech(self,text):
      try:         
         if self.Config.GetValue('SectionGlobals','espeakpath') and os.path.isfile(self.Config.GetValue('SectionGlobals','espeakpath')):
            try:
               espeakpath = self.Config.GetValue('SectionGlobals','espeakpath')
               volume = int(self.Config.GetValue('SectionGlobals','soundvolume'))
               pid = subprocess.Popen([espeakpath,"-a", "{}".format(volume), "-s","100","-v","fr","\"{}\"".format(text)])
            except Exception as e:
               self.Logs.Log("WARNING","Problem trying to use espeak : {}".format(e))
               return False
         else:
            return False
      except:
            self.Logs.Log("WARNING","Unable to find espeak binary on your system.")
            return False

#
# Play given sound. Search first in the home folder, then play default sound, or beep1 if not found.
#
   def PlaySound(self,filename='beep1',PlayDefIfNotFound=True,fileformat='ogg'):
      sound = False
      filetoplay = self.GetPathOfFile('sounds', '{}.{}'.format(filename,fileformat))
      if filetoplay != False:
         sound = pygame.mixer.Sound(filetoplay)
      elif PlayDefIfNotFound:
         self.Logs.Log("WARNING","Unable to load this audio file : {}.{}, playing default beep !".format(filename,fileformat))
         sound = pygame.mixer.Sound('sounds/beep1.ogg')
      # Play only if sound is set
      if sound:
         # Set volume to defined setting and play
         Volume = round(float(self.SoundVolume)/100,1)
         sound.set_volume(Volume)
         sound.play()
         return True
      else:
         return False

#
# Play player name at the begining of a round (priority : personnal sound / speech / beep)
#
   def SoundStartRound(self,Player):
      # Try to play User Sound (user.ogg in the .pydarts directory)
      UserSound = self.PlaySound(Player,False)
      # If it fail, try to generate sound with espeak
      if UserSound == False:
         UserSpeech=self.Speech(str(Player))
         if UserSpeech == False:
            self.PlaySound()

#
# Play Winner at the end of the Game (priority : personnal sound / speech / "you")
#
   def SoundEndGame(self,Player):
      self.PlaySound('winneris',False)
      pygame.time.wait(2000)
      UserSound = self.PlaySound(Player,False)
      if UserSound == False:
         UserSpeech=self.Speech(str(Player))
         if UserSpeech==False:
            self.PlaySound('you',False)
#
# Method to play sound for double, triple and bullseye
#
   def Sound4Touch(self,Touch):
      if Touch[1:] == "B":
         self.PlaySound('bullseye')
      elif Touch[:1] == 'D':
         self.PlaySound('double')
      elif Touch[:1] == 'T':
         self.PlaySound('triple')
      else:
         self.PlaySound()

#
# Check the right path of a requested file in prefered order : preference path, then pydarts path. return good path of False if path doesn't exists
#
   def GetPathOfFile(self,filefolder,filename):
      # Set path for user and pygame
      pathuser='{}/.pydarts/{}/{}'.format(os.path.expanduser('~'),filefolder,filename)
      pathpydarts='{}/{}'.format(filefolder,filename)
      # Check if file exists in user preferences path
      if os.path.isfile(pathuser):
         return pathuser
      # Else checks if exists in default pydatrs game path
      elif os.path.isfile(pathpydarts):
         return pathpydarts
      # Else it's a real problem ! Returns false
      else:
         return False

#
# Nice hit animation
#
   def NiceShot(self,msg='Nice Shot !'):
      # Image size
      ImgW=int(self.res['x']/3)
      ImgH=int(self.res['y']/8)
      # Image movement  step
      step = int(self.res['x']/10)
      # Time between to images
      time=1
      # Placement
      X = 0 - ImgW
      Y = int(self.res['y']/2.4)
      i1 = self.GetPathOfFile('images', 'dart1.png')
      i2 = self.GetPathOfFile('images', 'dart2.png')
      i1l=pygame.image.load(i1)
      i2l=pygame.image.load(i2)
      i1p=pygame.transform.scale(i1l,(ImgW,ImgH))
      i2p=pygame.transform.scale(i2l,(ImgW,ImgH))
      self.PlaySound('niceshot')
      if i1 and i2 != False:
         while X<int(self.res['x']-ImgW):
            X+=step
            self.DisplayBackground()
            self.screen.blit(i1p, (X,Y))
            pygame.display.flip()
            pygame.time.wait(time)
            self.DisplayBackground()
            self.screen.blit(i2p, (X,Y))
            pygame.display.flip()
            pygame.time.wait(time)
         self.InfoMessage([msg],3000,None,'middle','big')
      else:
         self.Logs.Log("ERROR","Unable to find required image for animation.")

#
# Display message for network version mismatch
#
   def VersionCheck(self,serverversion):
      if serverversion != pyDartsVersion:
         self.Logs.Log('ERROR','Version of client ({}) and server ({}) do not match. This is strongly discouraged ! Please upgrade !'.format(pyDartsVersion,serverversion))
         self.InfoMessage([self.Lang.lang('version-mismatch')],8000,None,'middle','big')
      else:
         self.Logs.Log('DEBUG','Version of client and server match. Continuing...')
         
#
# Draw board Methods
#
   def Drawtriple(self,AngleIndex,color=None):
      color=self.ColorSet['green'] if color==None else color
      radius_triple_out = int(min(self.res['y'],self.res['x'])/5.3)
      width_triple = min(int(self.res['y']/38),int(self.res['x']/38))
      arcRect = ((self.res['x']-(radius_triple_out*2))/2,(self.res['y'] - (radius_triple_out*2))/2,radius_triple_out*2,radius_triple_out*2)
      pygame.draw.arc(self.screen, color, arcRect, math.radians(18*6.5-18*(AngleIndex+1)), math.radians(18*6.5-18*AngleIndex), width_triple)
#
   def Drawdouble(self,AngleIndex,color=None):
      color=self.ColorSet['blue'] if color==None else color
      radius_double_out = int(min(self.res['y'],self.res['x'])/3.3)
      width_double = min(int(self.res['y']/35),int(self.res['x']/35))
      arcRect = ((self.res['x']-(radius_double_out*2))/2,(self.res['y'] - (radius_double_out*2))/2,radius_double_out*2,radius_double_out*2)
      pygame.draw.arc(self.screen, color, arcRect, math.radians(18*6.5-18*(AngleIndex+1)), math.radians(18*6.5-18*AngleIndex), width_double)
#
   def Drawsimple(self,AngleIndex,color=None):
      color=self.ColorSet['black'] if color==None else color
      radius_double_in = int(min(self.res['y'],self.res['x'])/3.65)
      radius_triple_in = int(min(self.res['y'],self.res['x'])/6)
      width_simple1 = min(int(self.res['y']/12),int(self.res['x']/12))
      width_simple2 = min(int(self.res['y']/8),int(self.res['x']/8))
      arcRect1 = ((self.res['x']-(radius_double_in*2))/2,(self.res['y'] - (radius_double_in*2))/2,radius_double_in*2,radius_double_in*2)
      arcRect2 = ((self.res['x']-(radius_triple_in*2))/2,(self.res['y'] - (radius_triple_in*2))/2,radius_triple_in*2,radius_triple_in*2)
      pygame.draw.arc(self.screen, color, arcRect1, math.radians(18*6.5-18*(AngleIndex+1)), math.radians(18*6.5-18*AngleIndex), width_simple1)
      pygame.draw.arc(self.screen, color, arcRect2, math.radians(18*6.5-18*(AngleIndex+1)), math.radians(18*6.5-18*AngleIndex), width_simple2)
#
   def Drawbull(self,Simple=False,Double=False,color=None):
      color=self.ColorSet['red'] if color==None and Double else color
      color=self.ColorSet['orange'] if color==None and Simple else color
      width_simple = min(int(self.res['y']/30),int(self.res['x']/30))
      width_double = min(int(self.res['y']/60),int(self.res['x']/60))
      radius_center_out = int(min(self.res['y'],self.res['x'])/22)
      radius_center_in = int(min(self.res['y'],self.res['x'])/50)
      if Simple:
         pygame.draw.circle(self.screen, color, (int(self.res['x']/2),int(self.res['y']/2)), radius_center_out, width_simple)
      if Double:
         pygame.draw.circle(self.screen, color, (int(self.res['x']/2),int(self.res['y']/2)), radius_center_in, width_double)
