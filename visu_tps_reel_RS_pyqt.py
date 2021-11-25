#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue May 18 15:22:24 2021

@author: roya
"""
from pyqtgraph.Qt import QtGui, QtCore
import pyqtgraph as pg

## Switch to using white background and black foreground
pg.setConfigOption('background', 'w')
pg.setConfigOption('foreground', 'k')

import numpy as np
import pandas as pd
import glob
import os


#global variable
global dirOut
dirOut = "C:\data\*"

## pour test --> indiquer le dossier contenant les données 
#(fichier XData et fichier RawData): 
#dirOut = "/home/roya/ktrm/BALLON_LIBRE/sonde_surfusion/2021_11_23/"


### conversion hexadecimale twc:
def xdata_ftwc(char):
    return int(char[2:6], base=16)/1000

### conversion hexadecimale slwc:
def xdata_fslwc(char):
    return int(char[6:10], base=16)/1000


# Recherche du fichier en cours d'écriture (le plus récent dans le répertoire) :
def latest_file(listFile):
    return max(listFile, key=os.path.getctime)

def read_xdata(File):
    print(File)
    data = pd.read_csv(File,sep=' ',skiprows=3,header=None,na_values='-32768.00')
    # freq oscillation en Hz
    
    data[8] = data[7].apply(xdata_ftwc)
    data[9] = data[7].apply(xdata_fslwc)
    data.columns = ['date', 'time', 'offset', 'InstrumentType',\
        'InstrumentNumber', 'SrvTime','GpsOffset', 'XDataHex','twc_frequency','slwc_frequency']
    data.index = pd.to_datetime(data['date'] + ' ' + data['time'])
    data['timestamp'] = data.index.values.astype(np.int64) // 10 ** 9
    data.fillna(np.nan,inplace=True)
    return data

def read_ptu(File):
    print(File)
    data = pd.read_csv(File,sep=' ',skiprows=2,na_values='-32768.00')        
    data.columns = ['SrvDate', 'SrvTime','pressure', 'temperature',\
                    'humidity', 'windDirection', 'windSpeed', 'v', 'u', \
                    'altitude', 'longitude', 'latitude', 'ascentRate']
    for col in ['pressure', 'temperature','humidity', 'windDirection', \
                'windSpeed', 'v', 'u','altitude', 'longitude', 'latitude',\
                'ascentRate'] :
        data[col] = pd.to_numeric(data[col], errors = 'coerce')
    data.index = pd.to_datetime(data['SrvDate'] + ' ' + data['SrvTime'])
    data['timestamp'] = data.index.values.astype(np.int64) // 10 ** 9
    data.fillna(np.nan,inplace=True)
    return data



def read_ptu(File):
    print(File)
    # astuce pour lire le fichier meme si la trame n'est pas complète.
    # la trame n'est pas complète tant que la sonde n'a pas reçu une trame GPS
    # pour la première fois.
    # --- 
    # i = nb de ligne a passer avant de trouver une trame complète, défaut a 2 
    # pour sauter l'entete.
    i = 2
    result = None
    while result is None:
        try :
            data = pd.read_csv(File,sep=' ',skiprows=i,na_values='-32768.00',header=None)      
            result = 'ok'
        except pd.errors.ParserError: 
            i = i + 1
    # fin lecture
    
    data.columns = ['SrvDate', 'SrvTime','pressure', 'temperature',\
                    'humidity', 'windDirection', 'windSpeed', 'v', 'u', \
                    'altitude', 'longitude', 'latitude', 'ascentRate']
    for col in ['pressure', 'temperature','humidity', 'windDirection', \
                'windSpeed', 'v', 'u','altitude', 'longitude', 'latitude',\
                'ascentRate'] :
        data[col] = pd.to_numeric(data[col], errors = 'coerce')
    data.index = pd.to_datetime(data['SrvDate'] + ' ' + data['SrvTime'])
    data['timestamp'] = data.index.values.astype(np.int64) // 10 ** 9
    data.fillna(np.nan,inplace=True)
    return data

def updatePlots():
    global xdatafile, ptufile, ptr, p1,c1, p2, c2, p3, c3, p4, c4, p5, c5, p6, c6, p7, c7, p8, c8
    df_xdata = read_xdata(xdatafile)
    df_ptu = read_ptu(ptufile)
    c1.setData(df_ptu.timestamp,df_ptu.temperature)
    c2.setData(df_ptu.timestamp,df_ptu.humidity)
    c3.setData(df_ptu.timestamp,df_ptu.pressure)
    c4.setData(df_ptu.timestamp,df_ptu.windSpeed)
    c8.setData(df_ptu.timestamp,df_ptu.windDirection)
    c5.setData(df_ptu.longitude,df_ptu.latitude)
    c6.setData(df_xdata.timestamp,df_xdata.twc_frequency)
    c7.setData(df_xdata.timestamp,df_xdata.slwc_frequency)    
    if ptr == 0:
        p1.enableAutoRange('y', False)  
        p2.enableAutoRange('y', False)
        p3.enableAutoRange('y', False)
        p4.enableAutoRange('y', False)
        p5.enableAutoRange('xy', False)
        p6.enableAutoRange('y', False)
        p7.enableAutoRange('y', False) 
        p8.enableAutoRange('y', False) 
    ptr += 1



# initilisation: 
ListFilePtu = glob.glob(dirOut+"Raw*")
ListFileXdata = glob.glob(dirOut+"XData*")
ptufile = latest_file(ListFilePtu)
xdatafile = latest_file(ListFileXdata)
print(ptufile)
print(xdatafile)
ptr = 0        
df_xdata = read_xdata(xdatafile)
df_ptu = read_ptu(ptufile)
# -----------------------------------------------------
app = pg.mkQApp("Radiosonde Example")
#mw = QtGui.QMainWindow()
#mw.resize(800,800)
win = pg.GraphicsLayoutWidget(show=True, title="Life stream RS examples")
win.resize(1000,600)
win.setWindowTitle('Radiosonde Example')
# Enable antialiasing for prettier plots
pg.setConfigOptions(antialias=True)
# Pressure
p3 = win.addPlot(title="Pressure",axisItems = {'bottom': pg.DateAxisItem()})
c3 = p3.plot(df_ptu.timestamp,df_ptu.pressure,pen=(0,0,0))
p3.setLabel('left', 'Pressure', units='hPa')
p3.setLabel('bottom', 'Time')
p3.showGrid(x=True, y=True)
# temperature
p1 = win.addPlot(title="Temperature",axisItems = {'bottom': pg.DateAxisItem()})
c1 = p1.plot(df_ptu.timestamp,df_ptu.temperature,pen=(0,0,0))
p1.setLabel('left', 'Temperature', units='K')
p1.setLabel('bottom', 'Time')
p1.showGrid(x=True, y=True)
# windspeed
p4 = win.addPlot(title="Wind Speed",axisItems = {'bottom': pg.DateAxisItem()})
c4 = p4.plot(df_ptu.timestamp,df_ptu.windSpeed,pen=(0,0,0))
p4.setLabel('left', 'Wind Speed', units='m/s')
p4.setLabel('bottom', 'Time')
p4.showGrid(x=True, y=True)
# windDirection
p8 = win.addPlot(title="Wind Direction",axisItems = {'bottom': pg.DateAxisItem()})
c8 = p8.plot(df_ptu.timestamp,df_ptu.windDirection,pen=(0,0,0))
p8.setLabel('left', 'Wind Speed', units='°')
p8.setLabel('bottom', 'Time')
p8.showGrid(x=True, y=True)
win.nextRow()

#humidity 
p2 = win.addPlot(title="Humidity",axisItems = {'bottom': pg.DateAxisItem()})
c2 = p2.plot(df_ptu.timestamp,df_ptu.humidity,pen=(0,0,0))
p2.setLabel('left', 'Humidity', units='%')
p2.setLabel('bottom', 'Time')
p2.showGrid(x=True, y=True)
## frequency of the TWC
p6 = win.addPlot(title="Frequency TWC",axisItems = {'bottom': pg.DateAxisItem()})
c6 = p6.plot(df_xdata.timestamp,df_xdata.twc_frequency,pen=(0,0,0))
p6.setLabel('left', 'Frequency', units='Hz')
p6.setLabel('bottom', 'Time')
p6.showGrid(x=True, y=True)
## frequency of the SLWC
p7 = win.addPlot(title="Frequency SLWC",axisItems = {'bottom': pg.DateAxisItem()})
c7 = p7.plot(df_xdata.timestamp,df_xdata.slwc_frequency,pen=(0,0,0))
p7.setLabel('left', 'Frequency', units='Hz')
p7.setLabel('bottom', 'Time')
p7.showGrid(x=True, y=True)
# position of the radiosonde
p5 = win.addPlot(title="Position")
c5 = p5.plot(df_ptu.longitude,df_ptu.latitude,pen=(0,0,0))
p5.setLabel('left', 'Latitude', units='°')
p5.setLabel('bottom', 'Longitude', units='°')
p5.showGrid(x=True, y=True)

# Update Plot every 1000 ms
timer = QtCore.QTimer()
timer.timeout.connect(updatePlots)
timer.start(1000)


if __name__ == '__main__':
    pg.mkQApp().exec_()

































