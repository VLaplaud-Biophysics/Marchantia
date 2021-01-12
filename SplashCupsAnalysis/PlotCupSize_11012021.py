"""
This code is a first code in python. 
As a test it plots size of SplashCups measured in imageJ from images 
made on the 11th of january 2021
"""


import matplotlib.pyplot as plt  # Plotting functions
import numpy as np # Handling numbers
import seaborn  # for swarmplot

# Path to data
P = r'd:\Users\Valentin Laplaud\PostDoc\Data\21.01.11_ObservationCorbeilles\MesureCorbeilles_11012021'


# Different thalli

T_list = ['1', '2', '3', '4']

xGrouping = [] # Major elipse axis grouping
Major = [] # Major elipse axis
Minor = [] # Minor elipse axis
    
# Loops over Thalli
for s in T_list:
    Filename = P + '\Thalle_' + s + '\FitElipseResults.txt' # Name of file to open
    F = open(Filename,'r') # Open file
    lines = F.readlines() # Read all lines of the file

    # find the columns with Major and Minor axis values
    NameVect = lines[0].split('\t') 
    nMaj = NameVect.index("Major")
    nMin = NameVect.index("Minor")
    

    # loops over cups measurements
    for l in lines[1:]:
        xGrouping.append(s)
        Major.append(float(l.split('\t')[nMaj]))
        Minor.append(float(l.split('\t')[nMin]))
        
        
MeanAxis = [X/2 for X in [sum(x) for x in zip(Major, Minor)]]
        
    
plt.figure(1)
plt.xlabel('Thallus')
plt.ylabel('Major elipse axis length (mm)')
seaborn.swarmplot(xGrouping,Major)

plt.figure(2)
plt.xlabel('Thallus')
plt.ylabel('Minor elipse axis length (mm)')
seaborn.swarmplot(xGrouping,Minor)

plt.figure(3)
plt.xlabel('Thallus')
plt.ylabel('Mean axis length (mm)')
seaborn.swarmplot(xGrouping,MeanAxis)
    
