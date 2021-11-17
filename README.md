## DATA ACQUISITION SYSTEM FOR HYBRID ELECTRONIC NOSE

### Introduction
I developed this software during my graduate years for my master thesis. 
I published a IEEE conference paper named "[A Hybrid E-nose System based on Metal Oxide Semiconductor Gas Sensors and Compact Colorimetric Sensors](https://ieeexplore.ieee.org/abstract/document/9495905)" using it. 
It is capable of acquiring both metal oxide gas sensor data and colorimetric sensors data at the same time, and storing the signals in terms of CSV files.

### HOW TO USE IT
First install [Git](https://git-scm.com/) and [Python Interpreter](https://www.python.org/) in your system.

Open the command prompt and move to the folder you want to work on this software and run
```
$ git clone https://github.com/aungkhantmaw64/hybrid-enose.git
```
Then go to hybrid-enose folder and run the following command in the command prompt to install required python packages to run this application. 
**Make sure you have added your python interpreter in the system path**.
```
$ pip install -r requirements.txt
```
Then run 
```
$ python main.py
```

This software's user interface is based on pyqt5 and main_window.ui is generated using QtCreator and required for rendering the GUI.
