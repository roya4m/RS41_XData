########################################################################
#
#      Copyright (c) Vaisala Group 2015. All rights reserved.
#
#      The terms "Vaisala" and "Vaisala Group" are defined as
#      "Vaisala Oyj and all its subsidiaries".
#
#       Module name      : Ozone report script
#       Context          : Applicable with Vaisala MW41 Sounding System
#
#       Original release : 2015
#       27/06/2018 CNRM/GMEI/4M (DT) : Script for reporting raw data (radiosonde location + PTU)
#       14/11/2018 CNRM/GMEI/4M (DT+AR) : Update for the 2.9 version of MW41
#
########################################################################

import clr
import sys
from System import Array
from System import Type
from System import DateTime
from System.IO import Directory
from System.Globalization import CultureInfo
from math import *

clr.AddReference('IScripting')
clr.AddReference('SystemEvent')
clr.AddReference('DataTypes')
clr.AddReference('ILogService')
from Vaisala.Soundings.Framework import IExecutableScript
from Vaisala.Soundings.Framework import ISounding
from Vaisala.Soundings.Framework.DataTypes import SystemEvent
from Vaisala.Soundings.Framework.DataTypes.GPS import GPSResult
from Vaisala.Soundings.Framework.DataTypes.GPS import WindSolutionStatus
from Vaisala.Soundings.Framework.DataTypes.PTU import RawPtu


CommentValue = 'FREE_TEXT'

class NewRawData(IExecutableScript):
  """ Writes raw data location + PTU to the file. Reporting is started when radiosonde is ready for release.

  Note! When using this script GPSResult distribution should be enabled in MW41.

  Command line options:
    -f <directory path> 
        Directory where where location file is written.
        Files are named as RadiosondeLocation_[yyyyMMddHHmmss].txt.
  """
  import sys
  LineEnd = "\r\n"
  MissingData = -32768
  Version = "1.1." + filter(str.isdigit, "$Revision: 0 $")
  RadioResetTime = None
  LatestLocation = None
  LatestRawPTU = None
  WriteDir = "C:\\data"
  
  def __init__(self, args):
    i = 0    
    while (i < len(args)) :
      if (args[i] == "-f") :
        i = i + 1
        if (i < len(args)) :
          self.WriteDir = args[i]
      i = i + 1

    if not Directory.Exists(self.WriteDir) :
      Directory.CreateDirectory(self.WriteDir)
      
    # Order notifications from Sounding system
    types = Array[Type]([clr.GetClrType(SystemEvent),
                         clr.GetClrType(GPSResult),
                         clr.GetClrType(RawPtu)])
    SoundingInterface.OrderNotifications(types)

  def get_SupportedScriptInterfaceVersion(self):
    return 3

  def get_Name(self):
    return "Radiosonde location + PTU"

  def get_Description(self):
    return "Script for reporting raw data (radiosonde location + PTU)."

  def get_Author(self):
    return "@Vaisala"

  def get_Version(self):
    return self.Version

  def HandleData(self, data):
    """ Handle sounding data.
    
    Arguments:
    data -- Sounding data
    
    """
    
    method_name = 'handle_' + str(data.GetType().Name)
    method = getattr(self, method_name)
    method(data)

  def handle_SystemEvent(self, event):
    """ Handle sounding system events.
    
    Arguments:
    event -- Sounding system event
    
    """
    
    if event.EventName == "ReadyForRelease":
        self.Start()
    elif event.EventName == "SoundingCompleted":
        self.Stop()
        # Done -> exit
        SoundingInterface.StopScript()
        sys.exit(0)
 
  def Start(self):
    """ Start reporting radiosonde location """

    self.RadiosondeId = SoundingInterface.GetRadiosonde().ID
    soundingInfo = SoundingInterface.GetSoundingInformation()
    self.RadioResetTime = soundingInfo.RadioResetTime
    self.WriteFile = self.WriteDir + "\\RawData_" +  soundingInfo.SoundingStartTime.ToString("yyyyMMddHHmmss", CultureInfo.InvariantCulture)  + "_" + self.RadiosondeId + ".txt"
    self.CleanFile()
#    self.WriteLine("");
#    self.WriteLine("Radiosonde: " + self.RadiosondeId)
#    self.WriteLine("");
    self.WriteLine("Date Time P T RH DD FF V U Height Lon Lat VV")
    
  def Stop(self):
    """ Stop reporting radiosonde location """
    soundingInfo = SoundingInterface.GetSoundingInformation()
    rawFile = open(self.WriteFile, "a")
    comments = SoundingInterface.GetSoundingMetadata(CommentValue)
    if (comments) :
      edtFile.write("Comments: " + comments + "\n")
    rawFile.close()

  def handle_GPSResult(self, location):
    """ Update latest location """
    
    if self.RadioResetTime != None :
      # MW41 updates GPS results. Here we are using unfiltered GPS results.
      if self.LatestLocation == None or location.RadioRxTime > self.LatestLocation.RadioRxTime :
        self.LatestLocation = location
        self.WriteDataLine()
    
  def handle_RawPtu(self, RawPTU):
    """ Update latest RawPTU """
    
    if self.RadioResetTime != None :
      # MW41 updates RawPTU results. Here we are using unfiltered RawPTU results.
      if self.LatestRawPTU == None or RawPTU.RadioRxTime > self.LatestRawPTU.RadioRxTime :
        self.LatestRawPTU = RawPTU
        self.WriteDataLine()

  def WriteDataLine(self):
    """ Write data line to output file """
    
    if self.LatestRawPTU != None and self.LatestLocation != None and \
       round(self.LatestRawPTU.RadioRxTime,0) == round(self.LatestLocation.RadioRxTime,0) :

      # Date and time
      date = self.RadioResetTime.AddSeconds(self.LatestRawPTU.RadioRxTime)
      row = date.ToString("yyyy-MM-dd HH:mm:ss", CultureInfo.InvariantCulture)
      # Pression
      if self.LatestRawPTU.IsPressureOk == False :
        row += " %.2f" % (self.MissingData)
      else :
        row += " %.2f" % (self.LatestRawPTU.Pressure)
      # Temperature
      if self.LatestRawPTU.IsTemperatureOk == False :
        row += " %.2f" % (self.MissingData)
      else :
        row += " %.2f" % (self.LatestRawPTU.Temperature)
      # Humidity (RS41 : T-corrected humidity)
      if self.LatestRawPTU.IsHumidityOk == False :
        row += " %.2f" % (self.MissingData)
      else :
        row += " %.2f" % (self.LatestRawPTU.Humidity1)

     # GPS data
      if self.LatestLocation.Status == WindSolutionStatus.Autonomous or \
         self.LatestLocation.Status == WindSolutionStatus.Differential :
        u = self.LatestLocation.WindEast
        v = self.LatestLocation.WindNorth
        if u != self.MissingData and v != self.MissingData:
          dd = atan2(-u,-v) * 180/pi
          if dd <= 0:
            dd += 360
          ff = sqrt(u*u + v*v)
        else:
          dd = self.MissingData
          ff = self.MissingData
        # Wind direction
        row += " %.0f" % (dd)
        # Wind speed
        row += " %.2f" % (ff)
        # Wind speed, north component (Filtered north wind)
        row += " %.2f" % (v)
        # Wind speed, east component (Filtered east wind)
        row += " %.2f" % (u)
        # Geometric height from sea level
        row += " %.0f" % (self.LatestLocation.GeometricHeightFromSeaLevel)
         # Longitude (Position WGS84 coordinates)
        row += " %.6f" % (self.LatestLocation.PositionWgs84.Longitude)
        # Latitude (Position WGS84 coordinates)
        row += " %.6f" % (self.LatestLocation.PositionWgs84.Latitude)

      # Ascent rate
      row += " %.2f" % (self.LatestRawPTU.AscentRate)

      wFile = open(self.WriteFile, "ab")
      wFile.write(row + self.LineEnd)
      wFile.close()  

  def CleanFile(self):
    """ Write empty output file """

    wFile = open(self.WriteFile, "wb")
    wFile.write('')
    wFile.close()  

  def WriteLine(self, line):
    """ Write line to output file """

    wFile = open(self.WriteFile, "ab")
    wFile.write(line + self.LineEnd)
    wFile.close()  
 
