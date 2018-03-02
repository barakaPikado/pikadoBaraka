# -*- coding: utf-8 -*-
import os
import sys
#from . import CLogs
import serial# To detect serial port
import glob# used in FindSerialPort method
# Import library depending of python version
if sys.version[:1]=='2':
   import ConfigParser as configparser
elif sys.version[:1]=='3': 
   import configparser
# Internal Config file
from include.config import OrderedDartKeys

#
# Default values and default config file structure
#
ConfigList = {}

ConfigList['SectionAdvanced'] = {      'noserial':False, 
                                       'bypass-stats':False,
                                       'localplayers':False,
                                       'selectedgame':False,
                                       'gametype':False,
                                       'netgamename':False,
                                       'serverport':5005,
                                       'servername':'obilhaut.freeboxos.fr',
                                       'serveralias':False,
                                       'listen':'eth0',
                                       'mastertest':False,
                                       'clientpolltime':5,
                                       'animationduration':5,
                                       'forcecalibration':False
                                 }

ConfigList['SectionGlobals'] = {       'serialport':None,
                                       'serialspeed':9600,
                                       'blinktime':3000,
                                       'solo':2000,
                                       'releasedartstime':1800,
                                       'resx':1000,
                                       'resy':700,
                                       'fullscreen':0,
                                       'nbcol':6,
                                       'soundvolume':100,
                                       'colorset':'clear',
                                       'espeakpath':'/usr/bin/espeak',
                                       'debuglevel':2,
                                       'masterserver':'obilhaut.freeboxos.fr',
                                       'masterport':5006,
                                       'locale':False,
                                       'scoreonlogo':0
                                       }
ConfigList['SectionKeys'] = {
                                        's20':'',
                                        'd20':'',
                                        't20':'',
                                        's19':'',
                                        'd19':'',
                                        't19':'',
                                        's18':'',
                                        'd18':'',
                                        't18':'',
                                        's17':'',
                                        'd17':'',
                                        't17':'',
                                        's16':'',
                                        'd16':'',
                                        't16':'',
                                        's15':'',
                                        'd15':'',
                                        't15':'',
                                        's14':'',
                                        'd14':'',
                                        't14':'',
                                        's13':'',
                                        'd13':'',
                                        't13':'',
                                        's12':'',
                                        'd12':'',
                                        't12':'',
                                        's11':'',
                                        'd11':'',
                                        't11':'',
                                        's10':'',
                                        'd10':'',
                                        't10':'',
                                        's9':'',
                                        'd9':'',
                                        't9':'',
                                        's8':'',
                                        'd8':'',
                                        't8':'',
                                        's7':'',
                                        'd7':'',
                                        't7':'',
                                        's6':'',
                                        'd6':'',
                                        't6':'',
                                        's5':'',
                                        'd5':'',
                                        't5':'',
                                        's4':'',
                                        'd4':'',
                                        't4':'',
                                        's3':'',
                                        'd3':'',
                                        't3':'',
                                        's2':'',
                                        'd2':'',
                                        't2':'',
                                        's1':'',
                                        'd1':'',
                                        't1':'',
                                        'sb':'',
                                        'db':'',
                                        'playerbutton':'',
                                        'gamebutton':'',
                                        'backupbutton':''
                                       }
#
# Start of Config Class
#
class CConfig:
   def __init__(self,Args,Logs):
      self.userpath=os.path.expanduser('~')
      self.pathdir='{}/.pydarts'.format(self.userpath)
      self.pathfile='{}/pydarts.cfg'.format(self.pathdir)
      self.defaultserialport='/dev/ttyACM0'#In case of problem detecting serial port
      self.Args=Args
      self.Logs=Logs # Init logs
      self.ConfigList = ConfigList # Copy into object the value of default config
      self.ConfigFile = {} # Copy in Local variable the value of the config file
      config=self.Args.GetParamValue2('config')
      self.detectedserialport = False
      if config:
         self.Logs.Log("DEBUG","Using alternative config file {}".format(self.Args.GetParamValue2('config')))
         self.pathfile="{}/{}".format(self.pathdir,self.Args.GetParamValue2('config'))


   #
   # Try to detect available port
   #
   def FindSerialPort(self):
      """ Lists serial port names
         :raises EnvironmentError:
            On unsupported or unknown platforms
         :returns:
            A list of the serial ports available on the system
      """
      if sys.platform.startswith('win'):
         ports = ["COM{}".format(i + 1) for i in range(256)]
      elif sys.platform.startswith('linux') or sys.platform.startswith('cygwin'):
         # this excludes your current terminal "/dev/tty"
         ports = glob.glob('/dev/tty[A-Za-z0-9]*')
      elif sys.platform.startswith('darwin'):
         ports = glob.glob('/dev/tty.*')
      else:
         self.Logs.Log("WARNING","Unsupported operating system... Unable to detect serial port format.")
      #
      result = []
      for port in ports:
         try:
            s = serial.Serial(port,'9600')
            s.close()
            result.append(port)
         except Exception as e:
            pass
      # Add eventually the command line suggestion of the config file value
      try:
         if self.GetValue('SectionGlobals','serialport'):
            result.append(self.GetValue('SectionGlobals','serialport'))
      except:
         pass
      # Remove duplicates
      result=list(set(result))
      if len(result)>1:
         self.Logs.Log("DEBUG", "We found multiple port suitable for pydarts : {}.".format(result))
         ret=result
      elif len(result)==1:
         self.Logs.Log("DEBUG", "Great ! We found only one suitable serial port : {}. We will use it in your freshly created config file !".format(result))
         ret=result
      else:
         self.Logs.Log("WARNING","Sorry dude... We found no suitable serial port... Please double check and adapt your config file.".format(result))
         ret=[self.defaultserialport]
      self.detectedserialport=ret
        

#
# Check if the config file exists and if not, create it
#
   def CheckConfigFile(self):
      self.configfileexists = True
      """
      self.detectedserialport = False
      # Always try to detect all available serial ports
      try:
         self.detectedserialport=self.FindSerialPort()
      except Exception as e:
         self.Logs.Log("ERROR","Unable to load serial port lookup method")
         self.Logs.Log("DEBUG","Error was : {}".format(e))
      """
      # Create config folder in profile if necessary
      if not os.path.isfile(self.pathfile):
         self.Logs.Log("WARNING","Creating folder {}".format(self.pathdir))
         if not os.path.exists(self.pathdir):
            os.makedirs(self.pathdir)
         self.configfileexists = False
      else:
         self.Logs.Log("DEBUG","Config file {} exists. We use it so...".format(self.pathfile))

#
# Create and fill config file
#
   def WriteConfigFile(self,NewKeys):
      self.defaultconfig= ( "[SectionGlobals]\n"
                            "### Serial configuration - GNU/Linux exemple : /dev/ttyACM0 - Windows example : COM3) - Default 9600 bauds\n"
                            "serialport:{}\n".format(self.detectedserialport))
      self.defaultconfig+=(
                            "#serialspeed:9600\n\n"
                            "### Blink time of main information (ms) (good is 3000)\n"
                            "#blinktime:3000\n"
                            "### Wait between player in ms - (Solo Option - put to 0 disable it - good is 10000)\n"
                            "#solo:2000\n"
                            "### Time to release darts safely after a hit on player button (good is 1000-3000)\n"
                            "#releasedartstime:1800\n"
                            "### Screen resolution - if fullscreen is set to 1, resolution is bypassed\n"
                            "#resx:1000\n"
                            "#resy:700\n"
                            "#fullscreen:0\n"
                            "### How many columns in tab without BULL's eye. Will be moved to a game setting, a day.\n"
                            "#nbcol:6\n"
                            "### Default sound volume (percent)\n"
                            "#soundvolume:100\n"
                            "### Color set (bright|dark)|yourown\n"
                            "#colorset:bright\n"
                            "### Espeak path (to use voice synthesis - example on linux : /usr/bin/espeak)\n"
                            "#espeakpath:/usr/bin/espeak\n"
                            "### Debug level : 1=Debug|2=Warnings|3=Errors|4=Fatal Errors (Default 2)\n"
                            "#debuglevel:2\n"
                            "### Master Server : the server which can host Game List\n"
                            "#masterserver:obilhaut.freeboxos.fr\n"                         
                            "#masterport:5006\n"
                            "### Localization (en_GB, fr_FR, de_DE, es_ES, ...)\n"
                            "#locale:en_GB\n"
                            "### Score display on logo instead of normal display (0/1)\n"
                            "#scoreonlogo:0\n"
                            "\n"
                            "### SectionKeys store mandatory configuration linked to your arduino configuration. Check wiki online in any doubt.\n")

      self.defaultconfig+=("[SectionKeys]\n")
      for key in OrderedDartKeys:
         try:
            self.defaultconfig+=("{}:{}\n".format(key.upper(),NewKeys[key]))
         except:
            pass
      self.defaultconfig+=(
                            "\n"
                            "[SectionAdvanced]\n"
                            "### You can test pydarts without any dart board connected, using this option : \n"
                            "#noserial:0\n"
                            "### If you do not want the stats to be updated, please use this option : \n"
                            "#bypass-stats:0\n"
                            "#mastertest:0\n"
                            "### Frequency in second for the client to poll the server for players names\n"
                            "#clientpolltime:5\n"
                            ""
                             )
      file = open(self.pathfile, 'w')
      file.write(self.defaultconfig)
      file.close()
#
# Read a section of the config file
#
   def ReadConfigFile(self,Section):
      Config = configparser.ConfigParser()
      self.Logs.Log("DEBUG","Working on section {} of your config file.".format(Section))
      try:
         Config.read(self.pathfile)
      except:
         self.Logs.Log("FATAL","Your config file {} contain errors. Correct them or rename this file (it will be regenerated).".format(self.pathfile))
         exit (1)
      try:
         options = Config.options(Section) # Try to loads options from config file
      except Exception as e:
         if Section in self.ConfigList:#Warn only if the requested section is part of the config
            self.Logs.Log("WARNING","Your config file does not contain a section named {}.".format(Section))
         else:
            self.Logs.Log("DEBUG","Don't forget that you may create section named {} to customize pyDarts".format(Section))
         self.ConfigFile[Section]={} # Create empty config values even if the section does not exists
         return False
      DictOptions={}
      for option in options:
         try:
            DictOptions[option] = Config.get(Section, option)
         except Exception as e:
            self.Logs.Log("ERROR","Configuration issue with this option : {}".format(option))
            self.Logs.Log("DEBUG","Error was : {}".format(e))
            DictOptions[option] = None

      # Store in local object
      self.ConfigFile[Section]=DictOptions

      # Return options
      return DictOptions

#
#  Return value for an option (first search CLI args, then config file, then search default value) 
#  Break if option is required, return false otherwise
#

   def GetValue(self,Section,v,req=True):
      if v==None or Section==None:
         return False
      else:
         if self.Args.GetParamValue2(v):
            #self.Logs.Log("DEBUG","Using cli config value for {}={}".format(v,self.Args.GetParamValue2(v)))
            return self.Args.GetParamValue2(v)
         elif v in self.ConfigFile[Section]:
            #self.Logs.Log("DEBUG","Using config file value for {}:{}".format(v,self.ConfigFile[Section][v]))
            return self.ConfigFile[Section][v]
         elif v in self.ConfigList[Section]:
            #self.Logs.Log("WARNING","Using default config value for {}:{}".format(v,self.ConfigList[Section][v]))
            return self.ConfigList[Section][v]
         elif req:
            self.Logs.Log("FATAL","Error getting required config value {}. No command line, no config found, no default. Abort".format(v))
            sys.exit(1)
         else:
            return False
   # Specific config (comma separated values
   def GetPlayersNames(self):
      PlayersNames = self.GetValue('SectionAdvanced','localplayers')
      if PlayersNames:
         return PlayersNames.split(',')
      else:
         return False
