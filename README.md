RS41_XData
===========================================================

Radiosonde RS41 has a serial interface designed for addtional sensor (XData interface). This interface reads data from additional sensors to transfer it in a digital format. The radiosonde transmits the addional sensor information together with the traditional measurement from the radiosonde (position and thermodynamic information) to the ground equipment. 

Tools here are a supplementary way of handling XData interface with RS41 radiosonde for people to monitor the data from an additional sensor during the sounding. 

How to use it?
---------------

Many information to handle additional sensor measurement with Vaisala systems can be found in the Radiosonde RS41 Additional Sensor Interface Documentation. 

The script WriteXData.py is an example of a script that can be used to write XData frame from additional sensor to file. This script must be uploaded to the software. To upload a script, please follow the user documentation from Vaisala. 

Once updated, this script will write files in the directory 'C:\data\'. 

XDATA protocol
---------------
More information on the XDATA protocol can be found here: 
* https://www.esrl.noaa.gov/gmd/ozwv/wvap/sw.html
* https://www.esrl.noaa.gov/gmd/aftp/user/jordan/iMet-1-RSB%20Radiosonde%20XDATA%20Daisy%20Chaining.pdf


Trouble shooting
---------
See the Memo files


Contacts
---------
  * Axel Roy (CNRM): axel.roy@meteo.fr

Licence
--------
This tools is used under Microsoft Public License (Ms-PL).
