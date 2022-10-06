# -*- coding: utf-8 -*-
"""
Created on Tue Jun 21 16:42:37 2022

@author: laplaud
"""

# Imports 
from GemmaeDetection import BinarizeStack, GetContours, FindChipPos
from AreaCurveFitting import fitAreaGrowth,fitOsmoChoc,selectR2s
from StatsFunctions import plotSig, Corr,TwowayANOVA

import matplotlib as mpl
import matplotlib.pyplot as plt
import seaborn as sns

from cycler import cycler

import numpy as np
import pandas as pd

from scipy.stats import ks_2samp, linregress

import os

import VallapFunc as vf

from IPython import get_ipython
get_ipython().run_line_magic('matplotlib', 'inline')

#%% Wrapper functions for binarization and Area fit

# 1. Area growth

# stringName : name of experiment, StackList : list of videos to analyze, Path : path to data,
# Scale : in µm/px, FPH : frames per hour, Delay : delay between imbibtion and experiments start
# R2Threshold : threshold for data validation based on R2 of fit, 
# Ori : Orientation of the chip Horizontal chip : H + direction of traps ('H>', 'H<', 'V^', 'Vv')
# ToDo : indicator of which sub-code to run 'BCF' -> Binarization, Contours & Fits
# 'B' -> Binarization only, 'CF' -> contours & fits only, 'F' -> Fits only

# Kwargs : 'showHist' (True/false) for function selectR2s, 'debuglist' (list of integers) 
# to choose the images to analyse for debug plots 'HSVrange' (list of two 1x3 tuples)
# binarization min and max threshold values for the three channels of HSV image 
# 'fitwindow' (time in hours) to choose the window after dormancy exit on which to fit 

def BinarizeAndFitArea(stringName,StackList,Path,Scale,FPH,Delay,R2Threshold,Ori,ToDo, **kwargs):
    
      
    DebugAll = False
    DebugPlots = False
    HSVrange = [(25, 25, 70),(60, 120,220)]
    ImgList = [0, 20, 40]
    fitwindow=15
    
    for key, value in kwargs.items(): 
        if key == 'debugAll':
            DebugAll = value
        elif key == 'debug':
            DebugPlots = value
        elif key == 'debuglist':
            ImgList = value 
        elif key == 'HSVrange':
            HSVrange = value
        elif key == 'fitwindow':
            fitwindow = value
        else:
            print('Unknown key : ' + key + '. Kwarg ignored.')
    
    if ToDo == 'BCF':
        DoBin = True
        DoCont = True
        DoFit = True
    elif ToDo == 'B':
        DoBin = True
        DoCont = False
        DoFit = False
    elif ToDo == 'CF':
        DoBin = False
        DoCont = True
        DoFit = True
    elif ToDo == 'F':
        DoBin = False
        DoCont = False
        DoFit = True
    else:
        raise NameError('ToDo variable is wrong')
    
    print('\n_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ ')
    print('\n- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - ')
    print('\n\nAnalyzing experiment : ' + stringName + '\n')
    
    # Binarization of stacks
    if DoBin:
        BinarizeStack(StackList, Path, Scale,debug = DebugAll, HSVrange = HSVrange, debuglist = ImgList)
        print('\n\n')
    
    if DoCont:
                
        # Computing contours from binary
        CD,GD = GetContours(StackList,Path, Scale,FPH, debug=DebugAll)

        # Saving all contours
        GD.to_csv(Path + '\\GlobalData' + stringName + '_AreaCont.csv',index_label = 'Ind')
        CD.to_csv(Path + '\\ContourData' + stringName + '_AreaCont.csv',index_label = 'Ind')
        print('\n\n')

    if DoFit:
        
        GD = pd.read_csv(Path + '\\GlobalData' + stringName + '_AreaCont.csv', index_col = 'Ind')
        CD = pd.read_csv(Path + '\\ContourData' + stringName + '_AreaCont.csv',index_col = 'Ind')
        print('\n\n')
        
        # Retrieve data on PPG position in chip 
        if os.path.exists(Path + '\ChipPositions.xlsx'):
            posinchip = pd.read_excel (Path + '\ChipPositions.xlsx', index_col='Name') 
            Rows = posinchip.loc[StackList].values[:,0]
        else:
            print('Finding PPGs position in chip...',end='')
            Rows = FindChipPos(StackList,Path,Ori)
            print('Done\n')
        print('\n\n')
        
        # Fitting area growth
        GD = fitAreaGrowth(StackList,Rows,GD,FPH,Delay, debugall = DebugAll, debug = DebugPlots,fitwindow = fitwindow)
        print('\n\n')

        # Sorting based on fit quality
        GD, CD, R2s, goodList = selectR2s(GD,CD,R2Threshold,stringName, showHist = DebugPlots)
        print('\n\n')
        
        # Saving sorted contour and fit data
        GD.to_csv(Path + '\\GlobalData' + stringName + '_AreaFit.csv',index_label = 'Ind')
        CD.to_csv(Path + '\\ContourData' + stringName + '_AreaFit.csv',index_label = 'Ind')
        print('\n\n')
    
    return

# 2. Osmotic chocs

# stringName : name of experiment, StackList : list of videos to analyze, Path : path to data,
# Scale : in µm/px, FPH : frames per hour, R2Threshold : threshold for data validation based on R2 of fit, 
# Ori : Orientation of the chip Horizontal chip : H + direction of traps ('H>', 'H<', 'V^', 'Vv')
# ToDo : indicator of which sub-code to run 'BCF' -> Binarization, Contours & Fits
# 'B' -> Binarization only, 'CF' -> contours & fits only, 'F' -> Fits only

# Kwargs : 'showHist' (True/false) for function selectR2s, 'debuglist' (list of integers) 
# to choose the images to analyse for debug plots 'HSVrange' (list of two 1x3 tuples)
# binarization min and max threshold values for the three channels of HSV image 
# 'FitIntervalComp/Rel (list of two ints) Images corresponding to times between 
# which to fit compression/relaxation

def BinarizeAndFitOsChoc(stringName,StackList,Path,Scale,FPH,R2Threshold,Ori,ToDo, **kwargs):
    
    
    showHist = False
    DebugPlots = False
    HSVrange = [(25, 25, 70),(60, 120,220)]
    ImgList = [0, 20, 40]
    FitIntervalComp = [0,25]
    FitIntervalRel = [25,55]
    TstartComp = 3
    TstartRel = 9
    RelValidation = True
    
    for key, value in kwargs.items(): 
        if key == 'showHist':
            showHist = value
        elif key == 'debug':
            DebugPlots = value
        elif key == 'debuglist':
            ImgList = value 
        elif key == 'HSVrange':
            HSVrange = value
        elif key == 'FitIntervalComp':
            FitIntervalComp = value
        elif key == 'FitIntervalRel':
            FitIntervalRel = value
        elif key == 'TstartComp':
            TstartComp = value
        elif key == 'TstartRel':
            TstartRel = value
        elif key == 'RelValidation':
            RelValidation = value
        else:
            print('Unknown key : ' + key + '. Kwarg ignored.')
    
    if ToDo == 'BCF':
        DoBin = True
        DoCont = True
        DoFit = True
    elif ToDo == 'B':
        DoBin = True
        DoCont = False
        DoFit = False
    elif ToDo == 'CF':
        DoBin = False
        DoCont = True
        DoFit = True
    elif ToDo == 'F':
        DoBin = False
        DoCont = False
        DoFit = True
    else:
        raise NameError('ToDo variable is wrong')
    
    print('\n\n\n' + stringName + '\n\n')
    
    # Binarization of stacks
    if DoBin:
        BinarizeStack(StackList, Path, Scale,debug = DebugPlots, HSVrange = HSVrange, debuglist = ImgList)
    
    if DoCont:
                
        # Computing contours from binary
        CD,GD = GetContours(StackList,Path, Scale,FPH, debug=DebugPlots)
        
        # Saving all contours
        GD.to_csv(Path + '\\GlobalData' + stringName + '_AreaCont.csv',index_label = 'Ind')
        CD.to_csv(Path + '\\ContourData' + stringName + '_AreaCont.csv',index_label = 'Ind')
        
        print('Contour saved')

    if DoFit:
        
        # Retrieve data on PPG position in chip 
        if os.path.exists(Path + '\ChipPositions.xlsx'):
            posinchip = pd.read_excel (Path + '\ChipPositions.xlsx', index_col='Name') 
            Rows = posinchip.loc[StackList].values[:,0]
        else:
            print('Finding PPGs position in chip...',end='')
            Rows = FindChipPos(StackList,Path,Ori)
            print('Done\n')
        print('\n\n')
        
        GD = pd.read_csv(Path + '\\GlobalData' + stringName + '_AreaCont.csv', index_col = 'Ind')
        CD = pd.read_csv(Path + '\\ContourData' + stringName + '_AreaCont.csv',index_col = 'Ind')
        
        GD = fitOsmoChoc(StackList,Rows,CD,GD,FPH,FitIntervalComp[0],FitIntervalComp[1],TstartComp,FitIntervalRel[0],FitIntervalRel[1],TstartRel,debug = DebugPlots)
        
        # Selecting only good R2s for both compand rel, could be changed in the future for more general plots
        GD, CD, R2s, goodList = selectR2s(GD, CD, R2Threshold, stringName,showHist=showHist)
        if RelValidation:
            GD, CD, R2s, goodList = selectR2s(GD, CD, R2Threshold, stringName,showHist=showHist,key = 'fitR2rel')
        
        # Saving sorted contour and fit data
        GD.to_csv(Path + '\\GlobalData' + stringName + '_AreaFit.csv',index_label = 'Ind')
        CD.to_csv(Path + '\\ContourData' + stringName + '_AreaFit.csv',index_label = 'Ind')
    
    return


#%% Data visualisation function for growth and osmotic chocs quantifications

# 1. Comparison of growth quantifications between different experiments

# GDs : list of dataframe global data for experiments to analyse, Labels : list of 
# labels for each experiment, colors list of colors to plot, P : path for figure saving,
# Title : Name of the conditions plot (appears in figure titles)

# Kwargs : 'showcurve/box/hist' (True/False) to choose the different graphs displayed,
# 'indiplots' : (True/False) plot individual area curves, 'nbins' : (integer) 
# number of bins in histograms, 'stats' ('ranksum' or None) choose type of stats done 
# 'sigpairs' (list of 2-lists of integers) if specified, will only do significance 
# tests between selected data sets

def compareGrowth(GDs, Labels, colors,P, Title, **kwargs):

    showcurve = False
    showbox = False
    showhist = False
    nbins = 20
    AllSigs = True
    IndividualPlots = False
    stats = 'ranksum'
    groupcat = None
    diffcat = None
    NimgMax = '24h'
    
    for key, value in kwargs.items(): 
        if key == 'showcurve':
            showcurve = value 
        elif key == 'showbox':
            showbox = value
        elif key == 'showhist':
            showhist = value
        elif key == 'nbins':
            nbins = value
        elif key == 'sigpairs':
            sigpairs = value
            AllSigs = False
        elif key == 'indiplots' :
            IndividualPlots = value
        elif key == 'stats' :
            stats = value
        elif key == 'groupcat' :
            groupcat = np.array(value)
        elif key == 'diffcat' :
            diffcat = np.array(value)
        elif key == 'NimgMax' :
            if (value == '24h') | (value == 'max'):
                NimgMax = value 
            else:
                raise ValueError('Wrong value for NimgMax ! Allowed : ''24h'' or ''max'' ')
                
        else:
            print('Unknown key : ' + key + '. Kwarg ignored.')
    
    # Colors
    colorcycle = [plt.get_cmap('gist_rainbow')(1. * i/len(GDs)) for i in range(len(GDs))]
    mpl.rcParams['axes.prop_cycle'] = cycler(color=colorcycle)
         
    # check existence of figure folder, if absent, create it
    if not os.path.exists(P + '\\AreaGrowth'):
            os.mkdir(P + '\\AreaGrowth') # create folder
            
    ## Data grouping if ANOVA : 
    if stats == 'ANOVA':
        cats = np.unique(groupcat)
        newGDs = [None]*len(cats)
        for s,ss in zip(cats,range(len(cats))):
            pos = np.argwhere(groupcat==s)
            PD = pd.DataFrame(data=None)
            for i in pos:
                PD = PD.append(GDs[i[0]])
            newGDs[ss] = PD[:]
    else:
        newGDs = GDs[:]
    
    ######### Curves of evolution ##########
    
    fig2,ax2 = plt.subplots(dpi = 250,facecolor='black')
    fig2.suptitle(Title + ' - Area vs. time')
    plt.xlabel('Time (min)')
    plt.ylabel('Area (mm²)')
    
    fig3,ax3 = plt.subplots(dpi = 250,facecolor='black')
    fig3.suptitle(Title + ' - Norm Area vs. time')
    plt.xlabel('Time (min)')
    plt.ylabel('Area (normalized)')
    
    """  fig10,ax10 = plt.subplots(dpi = 250,facecolor='black')
    fig10.suptitle(Title + ' - Area vs. aligned time')
    plt.xlabel('Time (min)')
    plt.ylabel('Area (mm²)')
    
    fig11,ax11 = plt.subplots(dpi = 250,facecolor='black')
    fig11.suptitle(Title + ' - Norm Area vs. aligned time')
    plt.xlabel('Time (min)')
    plt.ylabel('Area (normalized)')"""
    
    for GD,lab,i in zip(newGDs,Labels,range(len(GDs))):
        
        StackList = np.unique(GD.index)
           
        if NimgMax == 'max':
            nimgmax = GD['Img'].max() # number of images (duration) to plot for growth curve
        else:
            nimgmax = 49 # 24h
        
        if IndividualPlots:
            fig1,ax1 = plt.subplots(dpi = 250,facecolor='black')
            fig1.suptitle(lab + ' - Area vs. time')
            plt.xlabel('Time (min)')
            plt.ylabel('Area (mm²)')
            for s in StackList:
                ax1.plot(GD.loc[s,'Img']*30,GD.loc[s,'Area'],label=s,lw=1)
            plt.legend(prop={'size': 5})

        # number of ppgs and label
        nPPG = len(GD.loc[GD['Img'] == 0])
        lab = lab + ' - n = ' + str(nPPG)
        
        # Computing mean area over all gemmae for each image
        MeanA = np.empty(nimgmax)
        MeanTime = np.empty(nimgmax)
        StdA = np.empty(nimgmax)

        for im in range(nimgmax):

            MeanA[im] = GD.loc[GD['Img'] == im,'Area'].to_numpy().mean()
            MeanTime[im] = im*30
            StdA[im] = GD.loc[GD['Img'] == im,'Area'].to_numpy().std()
        
        nppg = len(GD.loc[GD['Img'] == 0,'Area'].to_numpy())

        ax2.errorbar(MeanTime,MeanA,yerr=StdA/np.sqrt(nppg), capsize=3,label=lab,color = colors[i])
        ax3.errorbar(MeanTime,MeanA/MeanA[0],yerr=StdA/MeanA[0]/np.sqrt(nppg), capsize=3,label=lab,color = colors[i])
        
    plt.figure(fig2.number)
    plt.legend(prop={'size': 8})
    fig2.savefig(P + '\\AreaGrowth\\' + Title + '_AreaCurve.png')
    if not showcurve:
        plt.close(fig2)

    plt.figure(fig3.number)
    plt.legend(prop={'size': 8})
    fig3.savefig(P + '\\AreaGrowth\\' + Title + '_NormAreaCurve.png')
    if not showcurve:
        plt.close(fig3)


    ######### Parameters of fit ###########
    
      
    fig4,ax4 = plt.subplots(dpi = 250,facecolor='black')
    fig4.suptitle(Title + ' - Growth start time')
    plt.ylabel('T start (hours)')
      
    fig5,ax5 = plt.subplots(dpi = 250,facecolor='black')
    fig5.suptitle(Title + ' - Growth caracteristic time')
    plt.ylabel('Tau growth (hours)')
    
    fig6,ax6 = plt.subplots(dpi = 250,facecolor='black') 
    fig6.suptitle(Title + ' - Starting area') 
    plt.ylabel('Starting area from fit (mm²)') 

    fig16,ax16 = plt.subplots(dpi = 250,facecolor='black')
    fig16.suptitle(Title + ' - Initial growth increase')
    plt.ylabel('Growth at Tstart (%)')
    
    if len(newGDs) == 2:
        # Histogram for distribution comparison
        fig7,ax7 = plt.subplots(dpi = 250,figsize = (5,3.5),facecolor='black')
        fig7.suptitle(Title + ' - Growth caracteristic times')
        plt.xlabel('Tau growth (hours)')
        plt.ylabel('PDF')

        fig8,ax8 = plt.subplots(dpi = 250,figsize = (5,3.5),facecolor='black')
        fig8.suptitle(Title + ' - Growth start time')
        plt.xlabel('T start (min)')
        plt.ylabel('PDF')
        
        fig9,ax9 = plt.subplots(dpi = 250,figsize = (5,3.5),facecolor='black')
        fig9.suptitle(Title + ' - Growth caracteristic times')
        plt.xlabel('Tau growth (hours) - median aligned')
        plt.ylabel('PDF')

        fig10,ax10 = plt.subplots(dpi = 250,figsize = (5,3.5),facecolor='black')
        fig10.suptitle(Title + ' - Growth start time')
        plt.xlabel('T start (min) - median aligned')
        plt.ylabel('PDF')
    
    tdebs= [None]*len(newGDs)
    taus= [None]*len(newGDs)
    captdeb= [None]*len(newGDs)
    captau= [None]*len(newGDs)
    medtdeb= [None]*len(newGDs)
    medtau= [None]*len(newGDs)    
    
    Area0 = [None]*len(newGDs) 
    capArea0 = [None]*len(newGDs) 
    medArea0 = [None]*len(newGDs) 
    
    AreaStart = [None]*len(newGDs)
    capAreaStart = [None]*len(newGDs)
    medAreaStart = [None]*len(newGDs)
    
    grouping = []
    labs = []
    
    for GD,lab,i in zip(newGDs,Labels,range(len(newGDs))):
        
        # number of ppgs and label
        nPPG = len(GD.loc[GD['Img'] == 0])
        lab = lab + 'n = ' + str(nPPG)
        labs = np.append(labs,lab)
        
        # Retrieve data
        tdebs[i] = GD.loc[GD['Img'] == 0, 'tdeb']/60
        taus[i] = GD.loc[GD['Img'] == 0, 'Tau']/60          
        Area0[i] = GD.loc[GD['Img'] == 0, 'A0fit'] 
        AreaStart[i] = GD.loc[GD['Img'] == 0, 'GrowthAtStart_flat']*100
        
        
        # swarmplots
        grouping = np.append(grouping,np.ones(len(tdebs[i]))*i)


        plotprops = {'color':'white'}
        boxprops = {'color':'white','facecolor':colors[i]}
        
         
        bp4 = ax4.boxplot(tdebs[i], positions = [i], labels = [lab],patch_artist = True, boxprops=boxprops, capprops =plotprops,
                    showfliers = False,whiskerprops=plotprops,medianprops =plotprops)
        
        bp5 = ax5.boxplot(taus[i], positions = [i], labels = [lab],patch_artist = True, boxprops=boxprops, capprops =plotprops,
                    showfliers = False,whiskerprops=plotprops,medianprops =plotprops)
        
        bp6 = ax6.boxplot(Area0[i], positions = [i], labels = [lab],patch_artist = True, boxprops=boxprops, capprops =plotprops, 
            showfliers = False,whiskerprops=plotprops,medianprops =plotprops) 
        
        bp26 = ax16.boxplot(AreaStart[i], positions = [i], labels = [lab],patch_artist = True, boxprops=boxprops, capprops =plotprops,
                    showfliers = False,whiskerprops=plotprops,medianprops =plotprops)
    
        captdeb[i] = bp4['caps'][1].get_ydata(orig=True)[0]
        captau[i] = bp5['caps'][1].get_ydata(orig=True)[0]
        capArea0[i] = bp6['caps'][1].get_ydata(orig=True)[0] 
        capAreaStart[i] = bp26['caps'][1].get_ydata(orig=True)[0]
        medtdeb[i] = bp4['medians'][0].get_ydata(orig=True)[0]
        medtau[i] = bp5['medians'][0].get_ydata(orig=True)[0]
        medArea0[i] = bp6['medians'][0].get_ydata(orig=True)[0] 
        medAreaStart[i] = bp26['medians'][0].get_ydata(orig=True)[0]
        
        if len(newGDs) == 2:
        
            ax7.hist(taus[i], nbins, density=True, facecolor=colors[i], alpha=0.5)
            ax8.hist(tdebs[i], nbins, density=True, facecolor=colors[i], alpha=0.5)
            ax9.hist(taus[i]-np.median(taus[i]), nbins, density=True, facecolor=colors[i], alpha=0.5)
            ax10.hist(tdebs[i]-np.median(tdebs[i]), nbins, density=True, facecolor=colors[i], alpha=0.5)

            
    sns.swarmplot(x=grouping,y=pd.concat(tdebs),color = 'white', size=2, ax = ax4)
    sns.swarmplot(x=grouping,y=pd.concat(taus),color = 'white', size=2, ax = ax5)
    sns.swarmplot(x=grouping,y=pd.concat(Area0),color = 'white', size=2, ax = ax6) 
    sns.swarmplot(x=grouping,y=pd.concat(AreaStart),color = 'white', size=2, ax = ax16)
    
    ax4.set_xticklabels(labs)
    ax5.set_xticklabels(labs)
    ax6.set_xticklabels(labs) 
    ax16.set_xticklabels(labs)

    if len(newGDs) == 2:
        # Distribution comparison with two-sample kolmogorov smirnov test
        statsTau, pTau =  ks_2samp(taus[0],taus[1])
        ax7.set_title('KS test - p = ' + str(round(pTau*1000)/1000))
        fig7.tight_layout()
        
        statsTdeb, pTdeb =  ks_2samp(tdebs[0],tdebs[1])
        ax8.set_title('KS test - p = ' + str(round(pTdeb*1000)/1000))
        fig8.tight_layout()
        
        statsTau, pTau =  ks_2samp(taus[0]-np.median(taus[0]),taus[1]-np.median(taus[1]))
        ax9.set_title('KS test - p = ' + str(round(pTau*1000)/1000))
        fig9.tight_layout()
        
        statsTdeb, pTdeb =  ks_2samp(tdebs[0]-np.median(tdebs[0]),tdebs[1]-np.median(tdebs[1]))
        ax10.set_title('KS test - p = ' + str(round(pTdeb*1000)/1000))
        fig10.tight_layout()
        
    if not showhist:
        plt.close(fig7)
        plt.close(fig8)
        plt.close(fig9)
        plt.close(fig10)
    
    steptdeb = np.max(captdeb)*0.125
    steptau = np.max(captau)*0.125
    stepArea0 = np.max(capArea0)*0.125 
    stepAreaStart = np.max(capAreaStart)*0.125
    
    fullsteptdeb = 0
    fullsteptau = 0
    fullstepArea0 = 0 
    fullstepAreaStart = 0
    
    hmaxtdeb = np.max(captdeb)
    hmaxtau = np.max(captau)
    hmaxArea0 = np.max(capArea0) 
    hmaxAreaStart = np.max(capAreaStart)
    
    if stats=='ranksum':
        if AllSigs:
            for i in range(len(newGDs)-1):
                for j in range(i+1,len(newGDs)):

                    fullsteptdeb = plotSig(ax4,hmaxtdeb,steptdeb,fullsteptdeb,tdebs[i],tdebs[j],i,j)

                    fullsteptau = plotSig(ax5,hmaxtau,steptau,fullsteptau,taus[i],taus[j],i,j)
                    
                    fullstepArea0 = plotSig(ax6,hmaxArea0,stepArea0,fullstepArea0,Area0[i],Area0[j],i,j) 

                    fullstepAreaStart = plotSig(ax16,hmaxAreaStart,stepAreaStart,fullstepAreaStart,AreaStart[i],AreaStart[j],i,j)
                    
        else:
            for i,j in sigpairs:

                fullsteptdeb = plotSig(ax4,hmaxtdeb,steptdeb,fullsteptdeb,tdebs[i],tdebs[j],i,j)

                fullsteptau = plotSig(ax5,hmaxtau,steptau,fullsteptau,taus[i],taus[j],i,j)
 
                fullstepArea0 = plotSig(ax6,hmaxArea0,stepArea0,fullstepArea0,Area0[i],Area0[j],i,j) 

                fullstepAreaStart = plotSig(ax16,hmaxAreaStart,stepAreaStart,fullstepAreaStart,AreaStart[i],AreaStart[j],i,j)

                
 
 
    if stats=='ranksum':
        fig4.savefig(P + '\\AreaGrowth\\' + Title + '_Tstart.png')
        fig5.savefig(P + '\\AreaGrowth\\'+ Title +  '_TauGrowth.png')
        fig6.savefig(P + '\\AreaGrowth\\'+ Title +  '_StartingArea.png') 
        fig16.savefig(P + '\\AreaGrowth\\'+ Title +  '_InitialGrowth.png')
        if not showbox:
            plt.close(fig5)
            plt.close(fig4)
            plt.close(fig6)
            plt.close(fig16)
        return  
    elif stats == 'ANOVA':
        for v,med,fig,ax,dat in zip(['tdeb','Tau','A0fit','GrowthAtStart_flat'],[medtdeb,medtau,medArea0,medAreaStart],[fig4,fig5,fig6,fig16],[ax4,ax5,ax6,ax16],
                                    [pd.concat(tdebs),pd.concat(taus),pd.concat(Area0),pd.concat(AreaStart)]):

            res = TwowayANOVA(v,diffcat,groupcat,GDs);

            pDC = res.loc['C(Date)','PR(>F)']
            pGC = res.loc['C(Condition)','PR(>F)']

            ax.set_title('Date significativity (ANOVA) : p = ' + str(round(pDC*1000)/1000))
            ax.plot([0.3, 0.7],[np.mean(med), np.mean(med)],'-w')
            ax.text(0.5,np.mean(med)*1.1,'p = ' + str(round(pGC*1000)/1000), ha='center',fontsize='small')
            
            ax.set_ylim([np.min(dat)-np.abs(0.3*np.min(dat)), 1.5*np.percentile(dat,90)])
            
            
    
    else:
        if not showbox:
            plt.close(fig5)
            plt.close(fig4)
            plt.close(fig6) 
            plt.close(fig16)
            return
        else:
            return


# 2. Comparison of hydromechanical properties

# GDs : list of dataframe global data for experiments to analyse, Labels : list of 
# labels for each experiment, colors list of colors to plot, P : path for figure saving,
# Title : Name of the conditions plot (appears in figure titles)

# Kwargs : 'showbox/hist' (True/False) to choose the different graphs displayed,
# 'stats' ('ranksum' or None) choose type of stats done 
# 'sigpairs' (list of 2-lists of integers) if specified, will only do significance 
# tests between selected data sets

def compareHydroMech(GDs, Labels, colors,P, Title, **kwargs):

    showbox = False
    showhist = False
    AllSigs = True
    stats = 'ranksum'
    
    for key, value in kwargs.items(): 
        if key == 'showbox':
            showbox = value
        elif key == 'showhist':
            showhist = value
        elif key == 'sigpairs':
            sigpairs = value
            AllSigs = False
        elif key == 'stats' :
            stats = value
        else:
            print('Unknown key : ' + key + '. Ewarg ignored.')
         
    # check existence of figure folder, if absent, create it
    if not os.path.exists(P + '\\Hydromechanics'):
            os.mkdir(P + '\\Hydromechanics') # create folder
    
        
    ### Regroup data
    Es= [None]*len(GDs)
    Ecomps= [None]*len(GDs)
    Lcomps= [None]*len(GDs)
    Erels= [None]*len(GDs)
    Lrels= [None]*len(GDs)
    
    for GD,lab,i in zip(GDs,Labels,range(len(GDs))):
        
        # Retrieve data
        Es[i] = GD.loc[GD['Img'] == 0, 'E']
        Ecomps[i] = GD.loc[GD['Img'] == 0, 'Ecomp']
        Lcomps[i] = GD.loc[GD['Img'] == 0, 'TauFlux'] 
        Erels[i] = GD.loc[GD['Img'] == 0, 'Erel']
        Lrels[i] = GD.loc[GD['Img'] == 0, 'TauFluxRel']  
        
        fig0,ax0,cap,med = vf.boxswarmplot(Title + '\n\nElastic bulk modulus comparison for ' + lab,'E (MPa)',
                                           [Ecomps[i],Erels[i]],[colors[i],colors[i]],['Ecomp','Erel'])

        plotSig(ax0,np.max(cap),np.max(cap)*0.125,0,Ecomps[i],Erels[i],0,1)
        
        fig0.tight_layout() 
        fig0.savefig(P + '\\Hydromechanics\\' + lab + '_EComp-Rel.png')
        
        fig01,ax01,cap,med = vf.boxswarmplot(Title + '\n\nTauFlux comparison for ' + lab,'Tau (min-1)',
                                           [Lcomps[i],Lrels[i]],[colors[i],colors[i]],['TauFlux_comp','TauFlux_rel'])

        plotSig(ax01,np.max(cap),np.max(cap)*0.125,0,Lcomps[i],Lrels[i],0,1)
        
        fig01.tight_layout()
        fig0.savefig(P + '\\Hydromechanics\\' + lab + '_Tflux-Rel.png')
        
        
        if showhist:
            fig00, ax00 = plt.subplots(dpi=300)
            ax00.hist(np.divide(Erels[i],Ecomps[i]), facecolor=colors[i]) # ,density = True
            fig00.suptitle('Median : ' + str(np.round(np.divide(Erels[i],Ecomps[i]).median()*100)/100) + 
                           ' - Mean : ' + str(np.round(np.divide(Erels[i],Ecomps[i]).mean()*100)/100))
            ax00.set_xlabel('Erel/Ecomp')
            ax00.set_ylabel('Count')
            fig00.savefig(P + '\\Hydromechanics\\' + lab + '_EComp-Rel_Dist.png')
            
            
            fig00, ax00 = plt.subplots(dpi=300)
            ax00.hist(Es[i], facecolor=colors[i],bins=20) # ,density = True
            fig00.suptitle('Bulk elastic moduli of WT gemmae')
            ax00.set_xlabel('E (MPa)')
            ax00.set_ylabel('Count')
            # ax00.set_xlim(right=1.5)
            fig00.savefig(P + '\\Hydromechanics\\' + lab + '_E_Dist.png')
            

            linreg = linregress(Ecomps[i],Erels[i])

            g = sns.jointplot(x=Ecomps[i],y=Erels[i],kind='reg',color = colors[i],height = 12)
            g.ax_joint.set_xlabel('E compression (MPa)',fontsize = 25)
            g.ax_joint.set_ylabel('E relaxation (MPa)',fontsize = 25)
            g.ax_joint.tick_params(axis='both', labelsize=20)
            g.ax_joint.legend([f"S = {linreg.slope:.2f}",
                               f"CC = {linreg.rvalue:.3f}\nP = {linreg.pvalue:.3f}"],
                              fontsize='xx-large')
            
            fig001, ax001 = plt.subplots(dpi=300)
            ax001.hist(np.divide(Lrels[i],Lcomps[i]), facecolor=colors[i]) # ,density = True
            fig001.suptitle('Median : ' + str(np.round(np.divide(Lrels[i],Lcomps[i]).median()*100)/100) + 
                           ' - Mean : ' + str(np.round(np.divide(Lrels[i],Lcomps[i]).mean()*100)/100))
            ax001.set_xlabel('TfluxRel/Tflux')
            ax001.set_ylabel('Count')
            fig001.savefig(P + '\\Hydromechanics\\' + lab + '_TauFluxComp-Rel_Dist.png')
        
    ### plot
    fig1,ax1,capEcomp,medEcomp = vf.boxswarmplot(Title + '\n\nElastic bulk modulus (compression)','Ecomp (MPa)',Ecomps,colors,Labels[:])
    fig10,ax10,capErel,medErel = vf.boxswarmplot(Title + '\n\nElastic bulk modulus (relaxation)','Erel (MPa)',Erels,colors,Labels[:])
    fig11,ax11,capE,medE = vf.boxswarmplot(Title + '\n\nElastic bulk modulus (mean)','E (MPa)',Es,colors,Labels[:])
    fig2,ax2,capLcomp,medLcomp = vf.boxswarmplot(Title + '\n\nTauFlux (compression)','Tau_Comp (min-1)',Lcomps,colors,Labels[:])
    fig20,ax20,capLrel,medLrel = vf.boxswarmplot(Title + '\n\nTauFlux (relaxation)','Tau_Rel (min-1)',Lrels,colors,Labels[:])       


    ### stats
    fullstepE = 0
    fullstepEcomp = 0
    fullstepLcomp = 0
    fullstepErel = 0
    fullstepLrel = 0
    
    if stats=='ranksum':
        if AllSigs:
            for i in range(len(GDs)-1):
                for j in range(i+1,len(GDs)):

                    fullstepEcomp = plotSig(ax1,np.max(capEcomp),np.max(capEcomp)*0.125,fullstepEcomp,Ecomps[i],Ecomps[j],i,j)
                    fullstepE = plotSig(ax11,np.max(capE),np.max(capE)*0.125,fullstepE,Es[i],Es[j],i,j)
                    fullstepErel = plotSig(ax10,np.max(capErel),np.max(capErel)*0.125,fullstepErel,Erels[i],Erels[j],i,j)
                    fullstepLcomp = plotSig(ax2,np.max(capLcomp),np.max(capLcomp)*0.125,fullstepLcomp,Lcomps[i],Lcomps[j],i,j)
                    fullstepLrel = plotSig(ax20,np.max(capLrel),np.max(capLrel)*0.125,fullstepLrel,Lrels[i],Lrels[j],i,j)

        else:
            for i,j in sigpairs:

                    fullstepEcomp = plotSig(ax1,np.max(capEcomp),np.max(capEcomp)*0.125,fullstepEcomp,Ecomps[i],Ecomps[j],i,j)
                    fullstepE = plotSig(ax11,np.max(capE),np.max(capE)*0.125,fullstepE,Es[i],Es[j],i,j)
                    fullstepErel = plotSig(ax10,np.max(capErel),np.max(capErel)*0.125,fullstepErel,Erels[i],Erels[j],i,j)
                    fullstepLcomp = plotSig(ax2,np.max(capLcomp),np.max(capLcomp)*0.125,fullstepLcomp,Lcomps[i],Lcomps[j],i,j)
                    fullstepLrel = plotSig(ax20,np.max(capLrel),np.max(capLrel)*0.125,fullstepLrel,Lrels[i],Lrels[j],i,j)

    fig1.tight_layout()
    fig2.tight_layout()
    fig10.tight_layout()
    fig20.tight_layout()
    fig11.tight_layout()
    

    if stats=='ranksum':
        fig1.savefig(P + '\\Hydromechanics\\' + Title + '_Ecomp.png')
        fig2.savefig(P + '\\Hydromechanics\\'+ Title +  '_TauFluxComp.png')
        fig10.savefig(P + '\\Hydromechanics\\' + Title + '_Erel.png')
        fig20.savefig(P + '\\Hydromechanics\\'+ Title +  '_TauFluxrel.png')
        fig11.savefig(P + '\\Hydromechanics\\' + Title + '_E.png')
        if not showbox:
            plt.close(fig2)
            plt.close(fig1)
        return    
    else:
        if not showbox:
            plt.close(fig2)
            plt.close(fig1)
            return
        else:
            return



# 3. Comparison and correlation between growth and mechanicas parameters

def GOC_Comp(GD_Growths,GD_OCs,ParamGrowth,ParamOC,labelsGrowth,labelsOC,Titles,colors, **kwargs):
    
    PlotFits = False
    
    for key,value in kwargs.items():
        if key == 'PlotFits':
            PlotFits= value
        else:
            print('Unknown key : ' + key + '. Kwarg ignored.')
    
    fullData = pd.DataFrame(data=None, columns=ParamOC+ParamGrowth)
    GDs = []
    
    for (GD_Growth,GD_OC) in zip(GD_Growths,GD_OCs) :
        
        ListGrowth = np.unique(GD_Growth.index)
        ListChoc = np.unique(GD_OC.index)
        CommonList = set.intersection(set(ListGrowth), set(ListChoc))

        print('n = ' + str(len(CommonList)))

        DataFit = GD_OC.loc[(GD_OC['Img']==0),['Img']+ParamOC].loc[CommonList]
        DataGrowth = GD_Growth.loc[(GD_Growth['Img']==0),ParamGrowth].loc[CommonList]
        Data = DataFit.join(DataGrowth) 
        
        Data['GrowthSlope_FromExp'] = GD_OC.loc[(GD_OC['Img']==0),'A0Rel']/GD_Growth.loc[(GD_Growth['Img']==0),'Tau']
        Data['GrowthSlope_FromGR'] = GD_OC.loc[(GD_OC['Img']==0),'A0Rel']*GD_Growth.loc[(GD_Growth['Img']==0),'GR_end']
        
        fullData = fullData.append(Data, ignore_index=True)
        
        GDs.append(Data.copy(deep=True))
    
    GDs.insert(0,fullData.copy(deep=True))
    
    columns = ParamGrowth+ParamOC
    
    Corr(GDs,['Pooled'] + Titles,columns = columns,columnslabels = labelsGrowth+labelsOC,PlotFits = PlotFits,colors=colors)
   
