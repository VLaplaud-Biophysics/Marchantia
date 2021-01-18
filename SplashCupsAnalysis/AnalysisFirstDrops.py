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
# import math as mt # math functions
import seaborn  # for swarmplot

# Path to data
P = r'd:\Users\Valentin Laplaud\PostDoc\Data\21.01.14_PremiereGouttes\Analysis'

FrameRate = 10000 # in frame per second 

CupsList = ['C1_75cm_1'] # list of cups analyzed

XposI = [] # X position of impacting drop
YposI = [] # Y position of impacting 
SliceI = [] # Slice list for impacting drop

for s in CupsList:
    ImpactFilename = P + '\'' + s + '-Impact_results.txt'
    
    F = open(Filename,'r') # Open file for reading
    lines = F.readlines() # Read all lines of the file
    
    # find the columns with X and Y values and Slice number
    NameVect = lines[0].split('\t') 
    nX = NameVect.index("X")
    nY = NameVect.index("Y")
    nS = NameVect.index("Slice")
    
    # loops over images
    for l in lines[1:]:
        XposI.append(float(l.split('\t')[nX]))
        YposI.append(float(l.split('\t')[nY]))
        SliceI.append(float(l.split('\t')[nS]))
    
    
    DropList = ['D1']
    for d in DropList:
        EjectionFilename = P + '\'' + s + '-Ejection-' + d + '_results.txt'