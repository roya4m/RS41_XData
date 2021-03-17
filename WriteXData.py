#####################################################################################################################
#
#       Module name      : WriteXData.py
#       Context          : Applicable with Vaisala MW41 Sounding System
#
#       Original release : 2021
#
#       12/03/2021 CNRM/GMEI/4M (AR) : Script to write XData frame to file
#       time + offset + InstrumentType + InstrumentNumber + SrvTime + GpsOffset + XData 
#
#####################################################################################################################

#####################################################################################################################
#
# Import required Python modules.
#
#####################################################################################################################


import clr
import System
import math
import sys
import imp
import datetime
from datetime import date, datetime, time, timedelta
from System import Array
from System import Type
from math import *
from System.IO import File, Path, Directory
from System.Globalization import CultureInfo

#################################################################################
#
# Referencies for required interfaces to the sounding system.
#
#################################################################################

clr.AddReference('IScripting')
clr.AddReference('SystemEvent')
clr.AddReference('DataTypes')
clr.AddReference('ILogService')

from Vaisala.Framework.Log import LogCategory
from Vaisala.Soundings.Framework import IExecutableScript
from Vaisala.Soundings.Framework import ISounding
from Vaisala.Soundings.Framework.DataTypes import SystemEvent
from Vaisala.Soundings.Framework.DataTypes import Oif92Parameters
from Vaisala.Soundings.Framework.DataTypes import Oif411Parameters
from Vaisala.Soundings.Framework.DataTypes import RS92SpecialSensorData
from Vaisala.Soundings.Framework.DataTypes import RawOzone
from Vaisala.Soundings.Framework.DataTypes import CalculatedOzone
from Vaisala.Soundings.Framework.DataTypes import OzoneResult
from Vaisala.Soundings.Framework.DataTypes import SurfaceObservations
from Vaisala.Soundings.Framework.DataTypes import AdditionalSensorData
from Vaisala.Soundings.Framework.DataTypes import OzoneInterfaceType
from Vaisala.Soundings.Framework.DataTypes.PTU import RawPtu
from Vaisala.Soundings.Framework.DataTypes.PTU import SynchronizedSoundingData


#####################################################################################################################
# Defines used in the script.
#####################################################################################################################

__Version__ = "2.4." + filter(str.isdigit, "$Revision: 28610 $")
__MissingData__ = -32768.0
__KelvinToC__ = 273.15
__MissingValue__ = "////////"
__ColumnSeparator__ = "\t"
__Columns__ = ["    time","offset","InstrumentType", "InstrumentNumber","SrvTime","GpsOffset","XData"]
__Units__ = ["    s","    s","/","/","    s","    s","Hz"]

OperatorIdValue = 'OBSERVER_NAME'
CommentValue = 'FREE_TEXT'

#################################################################################
#
# WriteXData class for implementing the script. 
# Note that file should be named same as executed class.
#
# Class should implement at least method defined by IExecutableScript interface.
#
#################################################################################

class WriteXData(IExecutableScript):
  """WriteXData example script
  
  In this script we receive notifications from sounding system and 
  write XData to the file when sounding is ongoing.
  The name of the XData file contains the launching time of the soundings 
  and the serial number of the radiosonde. 
  
  Command line options:
    -d <message destination> 
        Add new destination where report is distributed.
        Note that destination should be created in sounding system configuration.  
  """
  def __init__(self, args):
    """Initialize script
     
      Arguments:
      args -- Array of command line arguments.
    
    """
    
    self.LaunchTime = 0
    self.WriteDir = "C:\\data"
    self.Destinations = []
    self.WriteFile = "C:\\data\\xdata_test.txt"
    
    # Read command line options.
    i = 0
    while (i < len(args)) :
      if (args[i] == "-d") :
        i = i + 1
        if (i < len(args)) :
          self.Destinations.append(args[i])
      elif (args[i] == "-f") :
        i = i + 1
        if (i < len(args)) :
          self.WriteDir = args[i]
      i = i + 1
      
    dir = Path.GetDirectoryName(self.WriteDir)
    if not Directory.Exists(dir) :
      Directory.CreateDirectory(dir)
    # Order notifications of SystemEvent and SynchronizedSoundingData from Sounding system
    types = Array[Type]([clr.GetClrType(SystemEvent),clr.GetClrType(SynchronizedSoundingData),clr.GetClrType(AdditionalSensorData),
                         clr.GetClrType(RawPtu),clr.GetClrType(Oif411Parameters)])
                         #
    SoundingInterface.OrderNotifications(types)

  def get_SupportedScriptInterfaceVersion(self):
    return 3

  def get_Name(self):
    return "OzoneMain"

  def get_Description(self):
    return "Write XData frame to file when sounding is ongoing."


  def get_Author(self):
    return "@roya"


  def get_Version(self):
    return __Version__


  def HandleData(self, data):
    """ Handle sounding data.
    
    Arguments:
    data -- Sounding data
    
    """
    # Get method name to be called from data type.
    #method_name = 'handle_' + str(data.GetType().Name)
    #method = getattr(self, method_name)
    #method(data)
    
    # Get method to be called from data type.
    dataname = str(data.GetType().Name)
    if dataname == 'SystemEvent' :
      self.handle_SystemEvent(data)
    elif dataname == 'AdditionalSensorData' :
#        elif dataname == 'AdditionalSensorData' and __Is_Oif411_Module__:
      self.handle_AdditionalSensorData(data)

  def handle_SystemEvent(self, event):
    """ Handle sounding system events.
    
    Arguments:
    event -- Sounding system event
    
    """

    if event.EventName == "ReadyForRelease":
    #if event.EventName == "SoundingCreated":
      self.SoundingStart()
    elif event.EventName == "SoundingCompleted":
      self.SoundingEnd()
      # Done -> exit
      SoundingInterface.StopScript()
      sys.exit(0)

  def SoundingStart(self):
    """Clear XData file and write new header to it.

    """

    # SoundingInterface object is provided by sounding system to the script.
    # Object provides ISounding interface methods.
    self.RadiosondeId = SoundingInterface.GetRadiosonde().ID
    soundingInfo = SoundingInterface.GetSoundingInformation()
    self.StartTime = soundingInfo.SoundingStartTime
    # Launchtime corresponds to the interval btw "start time" and "balloon released"
    self.LaunchTime = soundingInfo.LaunchTime
    time_delta = timedelta(seconds = round(self.LaunchTime))
    # Convert. into a python Datetime object and incrementation of time
    self.StartDatetime = datetime(self.StartTime.Year, self.StartTime.Month, 
                                  self.StartTime.Day, self.StartTime.Hour,
                                  self.StartTime.Minute, self.StartTime.Second)
    self.ReleaseDatetime = self.StartDatetime + time_delta
    self.WriteFile = self.WriteDir + "\\XData_" +  self.StartDatetime.strftime('%Y%m%d%H%M%S')  + "_" + self.RadiosondeId + ".txt" 
    xdataFile = open(self.WriteFile, "w")
    header = __ColumnSeparator__.join(__Columns__)
    xdataFile.write(header + "\n")
    header = __ColumnSeparator__.join(__Units__)
    xdataFile.write(header + "\n")
    xdataFile.close()
    SoundingInterface.Log(LogCategory.info, "Writing XData to " + self.WriteFile)

  def SoundingEnd(self) :
    """Write sounding status to file."""

    soundingInfo = SoundingInterface.GetSoundingInformation()
    xdataFile = open(self.WriteFile, "a")
    comments = SoundingInterface.GetSoundingMetadata(CommentValue)
    if (comments) :
        xdataFile.write("Comments: " + comments + "\n")
    xdataFile.close()
    self.SendToDestinations()

  def SendToDestinations(self) :
    """Send created file to defined destinations.
    """

    if File.Exists(self.WriteFile) and len(self.Destinations) > 0 :
      msgfile = open(self.WriteFile, "rb")
      report = msgfile.read()
      msgfile.close()
      SoundingInterface.Log(LogCategory.info, "Sending to destinations " + str(self.Destinations))
      SoundingInterface.SendReport("XDATA", report, Array[str](self.Destinations))

  def handle_AdditionalSensorData(self, xdata):
  #def handle_SynchronizedSoundingData(self, xdata):
    
    """ Handle RS41 X-data events and write XData to file when it is received as event.
    
    Arguments:
    xdata -- additional sensor data
    """
    toFile = open(self.WriteFile, "a")
    
    #line = self.FormatLine(xdata.RadioRxTime,xdata.XData)
    line = self.FormatLine(xdata.RadioRxTime,xdata.MeasurementOffset,
                           xdata.InstrumentType,xdata.InstrumentNumber,
                           xdata.DataSrvTime,xdata.GpsTimeOffset,xdata.XData)
    
    toFile.write(line + "\n")
    toFile.close()

  def FormatLine(self, rxTime, measurementoffset, instrumenttype, instrumentnumber, datasrvtime, gpstimeoffset, xdata) :

    """Returns one level data as string.
    """

    columns = []
    if (rxTime == __MissingData__) :
        columns.append(__MissingValue__)
    else :
       time = round(rxTime, 2) 
       columns.append("%s" % time)
    if (measurementoffset == __MissingData__) :
        columns.append(__MissingValue__)
    else :
        columns.append("%s" % measurementoffset)
    if (instrumenttype == __MissingData__) :
        columns.append(__MissingValue__)
    else :
        columns.append("%s" % instrumenttype)
    if (instrumentnumber == __MissingData__) :
        columns.append(__MissingValue__)
    else :
        columns.append("%s" % instrumentnumber)
    if (datasrvtime == __MissingData__) :
        columns.append(__MissingValue__)
    else :
        columns.append("%s" % datasrvtime)
    if (gpstimeoffset == __MissingData__) :
        columns.append(__MissingValue__)
    else :
        columns.append("%s" % gpstimeoffset)
    if (xdata == __MissingData__) :
        columns.append(__MissingValue__)
    else :
        columns.append("%s" % xdata)
    return __ColumnSeparator__.join(columns)

  def CreateReport(self):
    """ Create XData report from current sounding.
    """

    self.SoundingStart()
    for xdata in SoundingInterface.GetAdditionalSensorData() :
      self.handle_AdditionalSensorData(xdata)
    self.SoundingEnd()
