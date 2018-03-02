#!/usr/bin/env python
# -*- coding: utf-8 -*-
#import config
from include.config import officialwebsite
import pygame
from pygame.locals import *
import serial
import sys
import glob
import time
#

####################
# New Fresh class that handle all input types at once
####################

class CInput():

   def __init__(self,Logs,Config,myDisplay):
      self.Logs=Logs
      self.shift=False
      self.clock = pygame.time.Clock()
      self.Config = Config
      self.Lang=None
      self.ConfigKeys=Config.ConfigFile['SectionKeys']
      self.last_click = 0
      self.myDisplay=myDisplay
      self.ser = False # Init serial connexion
      self.SerialBypass = bool(self.Config.GetValue('SectionAdvanced','noserial'))
     
####### SERIAL

   def Serial_Connect(self):
      # Check input serial port (if no param --noserial)
      if not self.SerialBypass:
         try:
            if self.Config.detectedserialport:
               serialport=self.Config.detectedserialport
            else:
               serialport=self.Config.GetValue('SectionGlobals','serialport')
            serialspeed = int(self.Config.GetValue('SectionGlobals','serialspeed'))
            self.ser = serial.Serial(serialport,serialspeed)
            self.Logs.Log("DEBUG","Successfully loaded serial port {} at speed {}".format(serialport,serialspeed))
         except Exception as e:
            self.Logs.Log("FATAL","Unable to load serial port : \"{}\". Common errors are : \n * Your board is not connected \n * Your config file is not set properly (pydarts.cfg in your home folder)\n * Your arduino driver is not installed properly (windows only)\n * You're not part of the dialout group (Linux only).\n -- Note : You can use --noserial argument to bypass serial connection.".format(self.Config.GetValue('SectionGlobals','serialport')))
            self.Logs.Log("DEBUG","Error was : {}".format(e))
            self.myDisplay.PlaySound('whatamess')
            self.myDisplay.InfoMessage([self.Lang.lang('serial-issue-1'),self.Lang.lang('serial-issue-2'),self.Lang.lang('serial-issue-3'),officialwebsite,self.Lang.lang('serial-issue-4')],None,None,'middle','big')
            sys.exit(2)
      else:
         self.Logs.Log("DEBUG","Serial connection bypass as requested. No need for a dart board mate !")
   #
   # Flush
   #
   def Serial_Flush(self):
      if not self.SerialBypass:
         try:
            self.ser.flushInput() #Flush Serial input values (prevent user to hit while prog sleeps)
         except:
            self.Logs.Log("DEBUG","Unable to flush input from serial port.")
      else:
         self.Logs.Log("DEBUG","Bypassing serial port flush")

   #
   # Read serial connection.
   #
   def Serial_Read(self,context=False):
      DartStroke = False
      KeyStroke = False
      # Listen on serial cx
      try:
         # This event (get) solve the bug on windows (waiting screen)
         #pygame.event.get()
         # Read into the serial buffer if there is somthing inside
         serdata=False
         try:
            serdata=self.ser.in_waiting()#pyserial v2.x
         except:
            pass
         try:
            serdata=self.ser.inWaiting()#pyserial v3.x
         except:
            pass
         if serdata: #Read only if there is something in the serial buffer (non-blocking mode)
            DartStroke=self.ser.read()
            DartStroke=DartStroke.decode(encoding='UTF-8')
      except Exception as e:
         print("Error {}".format(e))
      #print(DartStroke)
      # Find unique key in config dict. Returns uppercase (only if something has been hit on board)
      if DartStroke:
         for TheKey, TheConfig in self.ConfigKeys.items():
            if TheConfig == DartStroke:
               KeyStroke=TheKey.upper()
      # Debug Serial Input (only if something has been hit on board)
      if DartStroke and KeyStroke:
         self.Logs.Log("DEBUG","DEBUGINPUT : You hit \"{}\" which is associated to \"{}\" in your configuration file.".format(DartStroke,KeyStroke))
      elif DartStroke and KeyStroke==False:
         self.Logs.Log("DEBUG","You hit \"{}\" which doesn't exists in your configuration file.".format(DartStroke))
      # If asked to return KEY, else return VAL
      if context=='wizard':
         return DartStroke
      else:
         return KeyStroke
        
#### KEYBOARD & MOUSE (from pygame)
# Context can be different, dependanding from where this method is used. So far : 'menus' or 'game' or 'editing'
#
   def KbdAndMouse(self,ktype, specials, context=None):
      keypressed = ""
      realkey=-1      
      double_click_duration=500
      clicktype=False
      events = pygame.event.get()
      for event in events:
         if event.type == pygame.QUIT:
            self.Logs.Log("DEBUG","Please exit any network game before killing pyDarts :)")
            if context=='game':
               return 'GAMEBUTTON'
            else:
               return 'escape'
         # Case of Key UP
         if event.type == KEYUP:
            if pygame.key.name(event.key) == 'left shift':
               self.shift=False
         # Case of key PRESSED
         if event.type == KEYDOWN:
            #self.clock.tick(30)
            keyname = pygame.key.name(event.key)
            unicodekey = event.dict['unicode']
            if len(keyname)==1 and unicodekey!='':
               keycouple = self.RealKey(unicodekey,context)
            else:
               keycouple = self.RealKey(keyname,context)
            realkey = keycouple[1]# Get pydarts translation of key
            realtype = keycouple[0]# Get pydarts translation of key type (alpha, fx, num, etc...)
            #print("Key analysis : original {}, translated as {} in unicode and {} in pydarts key".format(keyname,unicodekey,realkey))
            if realkey in specials:# return special key if allowed
               return realkey
            elif realtype in ktype:# Return standard key if allowed/expected
               return realkey
         # Case of MOUSE BUTTON PRESSED
         if event.type == pygame.MOUSEBUTTONDOWN:
            #on click
            self.clock.tick(30)
            self.diff = self.clock.get_time()
            if self.diff <= double_click_duration:
               clicktype='double-click'
               #self.clock.tick()
               #self.last_click = 0
            else:
               clicktype='single-click'
               #self.last_click = self.now
         if clicktype:
            keycouple = self.RealKey(clicktype,context)
            realkey = keycouple[1]# Get pydarts translation of key
            realtype = keycouple[0]# Get pydarts translation of key type (alpha, fx, num, etc...)
            if realkey in specials:
               return realkey
      # Everything above failed, return -1 (0 is a valid char)
      return -1


   def ListenInputs(self,ktype=['num','alpha','fx','arrows'], specials = ['enter','tab','backspace','left shift','escape','space','double-click','single-click'] ,WaitFor=[], context='menus'):
      SerialInput = False
      pyGameInput = -1
      while True:
         pygame.time.wait(5)# A few ms to reduce cpu...
         # First try to read serial
         if not self.SerialBypass:
            SerialInput = self.Serial_Read(context)
         # If serial returns false, try to read keyboard
         if not SerialInput:
            pyGameInput = self.KbdAndMouse(ktype,specials,context)
         # If any input return anything, exit from loop
         if pyGameInput!=-1:
            self.Logs.Log("DEBUG","Input debug : {}".format(pyGameInput))
         # Return Serial input if expected (or if nothing expected)
         if (SerialInput and WaitFor==[]) or (SerialInput in WaitFor):
            return SerialInput
         # Return pyGame input if expected (or if nothing expected)
         if (pyGameInput!=-1 and WaitFor==[]) or (pyGameInput in WaitFor):
            return pyGameInput


#### COMMON

   #
   # Function to get key and type from current state
   # 
   def RealKey(self,keypressed,context):
      if (keypressed == "&" and self.shift) or keypressed=="[1]" or keypressed=="1":
         kvalue = 1
         ktype = 'num'
      elif (keypressed == "world 73" and self.shift) or keypressed=="[2]" or keypressed=="2":
         kvalue = 2
         ktype = 'num'
      elif (keypressed == "\"" and self.shift) or keypressed=="[3]" or keypressed=="3":
         kvalue = 3
         ktype = 'num'
      elif (keypressed == "'" and self.shift) or keypressed=="[4]" or keypressed=="4":
         kvalue = 4
         ktype = 'num'
      elif (keypressed == "(" and self.shift) or keypressed=="[5]" or keypressed=="5":
         kvalue = 5
         ktype = 'num'
      elif (keypressed == "-" and self.shift) or keypressed=="[6]" or keypressed=="6":
         kvalue = 6
         ktype = 'num'
      elif (keypressed == "world 72" and self.shift) or keypressed=="[7]" or keypressed=="7":
         kvalue = 7
         ktype = 'num'
      elif (keypressed == "_" and self.shift) or keypressed=="[8]" or keypressed=="8":
         kvalue = 8
         ktype = 'num'
      elif (keypressed == "world 71" and self.shift) or keypressed=="[9]" or keypressed=="9":
         kvalue = 9
         ktype = 'num'
      elif (keypressed == "world 64" and self.shift) or keypressed=="[0]" or keypressed=="0":
         kvalue = 0
         ktype = 'num'
      elif (keypressed == "=" and self.shift) or keypressed=="[+]":
         kvalue = '+'
         ktype = 'math'
      elif (keypressed == "*" and self.shift==False) or keypressed=="[*]":
         kvalue = '*'
         ktype = 'math'
      elif (keypressed == "-" and self.shift==False) or keypressed=="[-]":
         kvalue = '-'
         ktype = 'math'
      elif (keypressed == ":" and self.shift) or keypressed=="[/]":
         kvalue = '/'
         ktype = 'math'
      elif (keypressed == "world 64" and self.shift) or keypressed=="[0]" or keypressed=="0":
         kvalue = 0
         ktype = 'math'
      elif (keypressed == ";" and self.shift) or keypressed==".":
         kvalue = '.'
         ktype = 'alpha'
      elif keypressed == "down" or keypressed == "up" or keypressed == "right" or keypressed == "left":
         kvalue = keypressed
         ktype = 'arrows'
      elif keypressed == 'escape' and context=='game': # In-game context, escape means ABORT
         kvalue='GAMEBUTTON'
         ktype='special'
      elif keypressed == 'escape': # All others context, it means 'escape'
         kvalue=keypressed
         ktype = 'special'
      elif keypressed == 'space' and context=='game': # In-game context, space means NEXT PLAYER
         kvalue='PLAYERBUTTON'
         ktype='special'
      elif keypressed == 'space': # All other context, space means 'space'
         kvalue=keypressed
         ktype='special'
      elif keypressed == 'enter' or keypressed=='return': # Enter and Return are comfunded volontarily
         kvalue='enter'
         ktype='special'
      elif keypressed == 'tab':
         kvalue=keypressed
         ktype='special'
      elif keypressed == 'backspace':
         kvalue=keypressed
         ktype='special'
      elif keypressed == 'b' and context=='game': # In-game, 'b' means 'BACKUPTURN'
         kvalue='BACKUPBUTTON'
         ktype='special'
      elif keypressed == 'f' and context=='editing':
         kvalue='f'
         ktype='alpha'
      elif (keypressed == 'f' or keypressed=='double-click'): # Everywhere else, 'f' and double-click means "Fullscreen"
         kvalue='TOGGLEFULLSCREEN'
         ktype='special'
      elif keypressed == 'left shift':
         kvalue=keypressed
         ktype='special'
         self.shift=True #Enable Shift !
      # Other special chars, need to be at the end (based on length)
      elif (len(keypressed)== 2 or len(keypressed)==3) and keypressed[:1] == "f": # Detect Fx keys
         kvalue = keypressed
         ktype = 'fx'
      elif len(keypressed)== 1:# Detect any other key (simple alpha keys)
         kvalue = keypressed
         ktype = 'alpha'
      else:
         kvalue=None
         ktype=None
      return [ktype,kvalue]
      
