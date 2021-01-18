# -*- coding: utf-8 -*-
"""
Created on Mon Jan 18 11:22:54 2021

@author: Valentin Laplaud

The purpose of this code is to test a first way of analyzing video of water droplet
splashing in a marchantia cups. It is based on the first test experiment performed 
the 14 jan 2021

It will use image analysis done with 'Analyze Particles' in imageJ, with one text file 
per drop to analyze
"""


import matplotlib.pyplot as plt  # Plotting functions
import numpy as np # Handling numbers
import statistics as st # mean median and stuff
import math as mt # math functions
import seaborn as sb # for swarmplot

# Path to data
P = r'D:\Users\Valentin Laplaud\PostDoc\Data\21.01.14_PremiereGouttes\Analysis'

FrameRate = 10 # in frame per millisecond 
Scale = 1 # in mn/px (here no scale where done)

CupsList = ['C1_75cm_1'] # list of cups analyzed



for s in CupsList:
    
    ## Impact analysis
    ImpactFilename = P + '\\' + s + '-Impact_results.txt'
    
    F = open(ImpactFilename,'r') # Open file for reading
    lines = F.readlines() # Read all lines of the file
    
    # find the columns with X and Y values and Slice number
    NameVect = lines[0].split('\t') 
    nX = NameVect.index("X")
    nY = NameVect.index("Y")
    try:
        nS = NameVect.index("Slice")
    except:
        nS = NameVect.index("Slice\n") # if last column
        
    XposI = [] # X position of impacting drop
    YposI = [] # Y position of impacting 
    SliceI = [] # Slice list for impacting drop    
        
    # loops over images
    for l in lines[1:]:
        XposI.append(float(l.split('\t')[nX]))
        YposI.append(float(l.split('\t')[nY]))
        SliceI.append(float(l.split('\t')[nS]))
        
        
    YposI = np.max(YposI) - YposI   
    TimeI = np.divide(SliceI,FrameRate) # in milliseconds
    
    VertSpeedI = np.divide(np.diff(YposI),np.diff(TimeI))*Scale
    # vertical impact speed in mm/s
    
    MeanVertSpeedI = st.mean(VertSpeedI)
    
    # Plotting position in time with mean speed
      
    plt.figure()
    plt.title('Impact drop vertical position in time (mean speed = ' + str(abs(round(MeanVertSpeedI,1))) + ' px/ms)') 
    plt.xlabel('Time (ms)')
    plt.ylabel('Vertical position (px)')
    plt.plot(TimeI,YposI,'o-')
    plt.savefig(P + '\\' + s +'_FigYPos_Impact.png',dpi=300)
    
    
    ## Ejection analysis
    DropList = ['D1']
    for d in DropList:
        EjectionFilename = P + '\\' + s + '-Ejection-' + d + '_results.txt'
        
        F = open(EjectionFilename,'r') # Open file for reading
        lines = F.readlines() # Read all lines of the file
    
        # find the columns with X and Y values and Slice number
        NameVect = lines[0].split('\t') 
        nX = NameVect.index("X")
        nY = NameVect.index("Y")
        try:
            nS = NameVect.index("Slice")
        except:
            nS = NameVect.index("Slice\n") # if last column
        
        XposE = [] # X position of impacting drop
        YposE = [] # Y position of impacting 
        SliceE = [] # Slice list for impacting drop
            
        # loops over images
        for l in lines[1:]:
            XposE.append(float(l.split('\t')[nX]))
            YposE.append(float(l.split('\t')[nY]))
            SliceE.append(float(l.split('\t')[nS]))
      
        YposE = np.max(YposE) - YposE
        TimeE = np.divide(SliceE,FrameRate) # in milliseconds
        TimeEAxis = TimeE[0:-1]+np.diff(TimeE)/2-TimeE[0]
        
        VertSpeedE = np.divide(np.diff(YposE),np.diff(TimeE))*Scale
        HorzSpeedE = np.divide(np.diff(XposE),np.diff(TimeE))*Scale
            
        
        MeanVertSpeedE = st.mean(VertSpeedE)
        MeanHorzSpeedE = st.mean(HorzSpeedE)
        
        # Plotting position in time with mean speed
          
        plt.figure()
        plt.title('Ejected drop ' +d + ' vertical position in time (mean speed = ' + str(abs(round(MeanVertSpeedE,1))) + ' px/ms)') 
        plt.xlabel('Time (ms)')
        plt.ylabel('Vertical position (px)')
        plt.plot(TimeE,YposE,'o-')
        plt.savefig(P + '\\' + s + '-' + d +'_FigYPos_Ejection.png',dpi=300) 
        
        plt.figure()
        plt.title('Ejected drop ' +d + ' Horizontal position in time (mean speed = ' + str(abs(round(MeanHorzSpeedE,1))) + ' px/ms)') 
        plt.xlabel('Time (ms)')
        plt.ylabel('Horizontal position (px)')
        plt.plot(TimeE,XposE,'o-')
        plt.savefig(P + '\\' + s + '-' + d +'_FigXPos_Ejection.png',dpi=300) 