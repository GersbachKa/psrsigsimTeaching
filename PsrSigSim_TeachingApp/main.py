'''
1. Import bokeh                             *
2. Check if data has been generated         *
3a. If not, import the data Generation      *
3b. Generate the data, and a checksum       *
4. Grab the data from the data files        *
5. Display values
'''


#Imports ----------------------------------------------------------------------
import numpy as np
import hashlib
import h5py
import json
import os

import showBokeh


all_dictionaries = None
DMFullData = None
FoldFullData = None
ScatterFullData = None



def loadData():
    #Attempt to get constants from JSON file
    global all_dictionaries
    try:
        with open('PsrSigSim_TeachingApp/dataGenerationConstants.json','r') as fileIn:
            all_dictionaries=json.load(fileIn)
    except:
        print("Cannot find dataGenerationConstants.json file. If you do not have it, you can find it on GitHub")
        exit()

    #Calculating the observation times for each
    all_dictionaries['dm_constants']['dm_psr_dict'].update({
        'ObsTime':(1000 / all_dictionaries['dm_constants']['dm_psr_dict']['F0'])
    })

    all_dictionaries['fold_constants']['fold_psr_dict'].update({
        'ObsTime':(1000 / all_dictionaries['fold_constants']['fold_psr_dict']['F0'])
    })

    all_dictionaries['scatter_constants']['scatter_psr_dict'].update({
        'ObsTime':(1000 / all_dictionaries['scatter_constants']['scatter_psr_dict']['F0'])
    })

    #Calculating the values used by Bokeh
    fillInBokehValues()


    #Attempt to get datafiles from HDF5
    _load_DMData()
    _load_FoldData()
    _load_ScatterData()




def _load_DMData():
    global all_dictionaries
    global DMFullData

    #get hashes from all_dictionaries
    DM_const_hash = str(all_dictionaries['dm_constants'])
    DM_const_hash = hashlib.md5(str.encode(DM_const_hash)).hexdigest()

    try:
        file1 = h5py.File("PsrSigSim_TeachingApp/SimData/DMData.hdf5",'r')
        DMhash = np.array2string(file1.get('DMhash'))[1:-1]
        if(DMhash!=DM_const_hash):
            #Not a match, need to regenerate
            raise Exception('DMhash did not match')
        else:
            #They match, no generation required
            DMFullData = np.array(file1.get("DMData"),copy=True)

    except:
        #File not found. need to generate
        import dataGenerator
        dataGenerator.genDMs(all_dictionaries['dm_constants'],DM_const_hash)
        DMFullData = np.array(file1.get("DMData"),copy=True)




def _load_FoldData():
    global all_dictionaries
    global FoldFullData

    Fold_const_hash = str(all_dictionaries['fold_constants'])
    Fold_const_hash = hashlib.md5(str.encode(Fold_const_hash)).hexdigest()

    #For folding
    try:
        file1 = h5py.File("PsrSigSim_TeachingApp/SimData/FoldData.hdf5",'r')
        Foldhash = np.array2string(file1.get('Foldhash'))[1:-1]
        if(Foldhash!=Fold_const_hash):
            #Not a match, need to regenerate
            raise Exception('Foldhash did not match')
        else:
            #They match, no generation required
            FoldFullData = np.array(file1.get("FoldData"),copy=True)

    except:
        #File not found. need to generate
        import dataGenerator
        dataGenerator.genFold(all_dictionaries['fold_constants'],Fold_const_hash)
        FoldFullData = np.array(file1.get("FoldData"),copy=True)




def _load_ScatterData():
    global all_dictionaries
    global ScatterFullData

    Scatter_const_hash = str(all_dictionaries['scatter_constants'])
    Scatter_const_hash = hashlib.md5(str.encode(Scatter_const_hash)).hexdigest()

    try:
        file1 = h5py.File("PsrSigSim_TeachingApp/SimData/ScatterData.hdf5",'r')
        Scatterhash = np.array2string(file1.get('Scatterhash'))[1:-1]
        if(Scatterhash!=Scatter_const_hash):
            #Not a match, need to regenerate
            raise Exception('Scatterhash did not match')
        else:
            #They match, no generation required
            ScatterFullData = np.array(file1.get("ScatterData"),copy=True)

    except:
        #File not found. need to generate
        import dataGenerator
        dataGenerator.genScatter(all_dictionaries['scatter_constants'],Scatter_const_hash)
        ScatterFullData = np.array(file1.get("ScatterData"),copy=True)




def fillInBokehValues():
    global all_dictionaries
    #DM variations
    dm_TimeBinSize = (1.0/ all_dictionaries['dm_constants']['dm_psr_dict']['f_samp']) * 0.001
    dm_start_time = 0
    dm_stop_time = (1.0/all_dictionaries['dm_constants']['dm_psr_dict']['F0']) * 1000

    dm_start_bin = 0
    dm_stop_bin = int(dm_start_time/dm_TimeBinSize)

    _dmBandwidth = all_dictionaries['dm_constants']['dm_psr_dict']['bw']
    dm_first_freq = all_dictionaries['dm_constants']['dm_psr_dict']['f0'] - (_dmBandwidth/2)
    dm_last_freq = dm_first_freq + _dmBandwidth

    all_dictionaries['dm_constants'].update({
            'TimeBinSize':dm_TimeBinSize,
            'start_time':dm_start_time,
            'stop_time':dm_stop_time,
            'start_bin':dm_start_bin,
            'stop_bin':dm_stop_bin,
            'first_freq':dm_first_freq,
            'last_freq':dm_last_freq
            })

    #Folding
    fold_TimeBinSize = (1.0/ all_dictionaries['fold_constants']['fold_psr_dict']['f_samp']) * 0.001
    fold_start_time = 0
    fold_stop_time = (1.0/all_dictionaries['fold_constants']['fold_psr_dict']['F0']) * 1000

    fold_start_bin = 0
    fold_stop_bin = int(fold_start_time/fold_TimeBinSize)

    _foldBandwidth = all_dictionaries['fold_constants']['fold_psr_dict']['bw']
    fold_first_freq = all_dictionaries['fold_constants']['fold_psr_dict']['f0'] - (_foldBandwidth/2)
    fold_last_freq = fold_first_freq + _foldBandwidth

    all_dictionaries['fold_constants'].update({
            'TimeBinSize':fold_TimeBinSize,
            'start_time':fold_start_time,
            'stop_time':fold_stop_time,
            'start_bin':fold_start_bin,
            'stop_bin':fold_stop_bin,
            'first_freq':fold_first_freq,
            'last_freq':fold_last_freq
            })

    #Scattering
    scatter_TimeBinSize = (1.0/ all_dictionaries['scatter_constants']['scatter_psr_dict']['f_samp']) * 0.001
    scatter_start_time = 0
    scatter_stop_time = (1.0/all_dictionaries['scatter_constants']['scatter_psr_dict']['F0']) * 1000

    scatter_start_bin = 0
    scatter_stop_bin = int(scatter_start_time/scatter_TimeBinSize)

    _scatterBandwidth = all_dictionaries['scatter_constants']['scatter_psr_dict']['bw']
    scatter_first_freq = all_dictionaries['scatter_constants']['scatter_psr_dict']['f0'] - (_scatterBandwidth/2)
    scatter_last_freq = scatter_first_freq + _scatterBandwidth

    all_dictionaries['scatter_constants'].update({
            'TimeBinSize':scatter_TimeBinSize,
            'start_time':scatter_start_time,
            'stop_time':scatter_stop_time,
            'start_bin':scatter_start_bin,
            'stop_bin':scatter_stop_bin,
            'first_freq':scatter_first_freq,
            'last_freq':scatter_last_freq
            })


loadData()
showBokeh.main(all_dictionaries,FoldFullData,DMFullData,ScatterFullData)
