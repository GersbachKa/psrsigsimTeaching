import sys
sys.path.insert(0,'/home/kyle/GWA/NANOGrav/PsrSigSim/')
import psrsigsim as PSS
import numpy as np
import h5py
import json
import os


def genDMs(DMDict,hash):
    DMFullData = []
    psr_dict = DMDict['dm_psr_dict']
    i = DMDict['dm_range'][0]
    while i <= DMDict['dm_range'][1]:
        if(i==0):
            psr_dict['dm']=.0001
        else:
            psr_dict['dm']=i

        psr = PSS.Simulation(psr =  None , sim_telescope= 'GBT',
                             sim_ism= None, sim_scint= None,
                             sim_dict = psr_dict)
        psr.init_signal()
        psr.init_pulsar()
        psr.init_ism()
        psr.pulsar.gauss_template(peak=.5)
        psr.simulate()
        curData = psr.signal.signal[:,DMDict['start_bin']:DMDict['stop_bin']]
        curData = np.roll(curData, -1*(int(psr.ISM.time_delays[-1] / DMDict['TimeBinSize'])),1)
        DMFullData.append(curData)
        i+=DMDict['dm_range_spacing']

    #Check if file exists
    if(os.path.exists('PsrSigSim_TeachingApp/SimData/DMData.hdf5')):
        os.remove('PsrSigSim_TeachingApp/SimData/DMData.hdf5')

    f = h5py.File('PsrSigSim_TeachingApp/SimData/DMData.hdf5','w')
    DMFullData = np.array(DMFullData)
    f.create_dataset('DMData', data=DMFullData)
    f.create_dataset('DMhash', data=hash)
    f.close()


def genFold(foldDict,hash):
    FoldingData = []
    psr = PSS.Simulation(psr =  None , sim_telescope= 'GBT',
                             sim_ism= None, sim_scint= None,
                             sim_dict = foldDict['fold_psr_dict'])
    psr.init_signal()
    psr.init_pulsar()
    psr.init_ism()
    psr.pulsar.gauss_template(peak=.5)
    psr.init_telescope()
    psr.simulate()
    currentData = psr.obs_signal + foldDict['fold_signalMultiplier']*psr.signal.signal
    FoldingData = np.copy((currentData[:,foldDict['start_bin']:foldDict['stop_bin']]))#Removed Swapaxes
    FoldingData = np.reshape(FoldingData,(np.size(FoldingData)))

    #check if file exists
    if(os.path.exists('PsrSigSim_TeachingApp/SimData/FoldData.hdf5')):
        os.remove('PsrSigSim_TeachingApp/SimData/FoldData.hdf5')

    f = h5py.File('PsrSigSim_TeachingApp/SimData/FoldData.hdf5','w')
    FoldingData = np.array(FoldingData)
    f.create_dataset('FoldData', data=FoldingData)
    f.create_dataset('Foldhash', data=hash)
    f.close()


def genScatter(scatterDict,hash):
    ScatteringData = []
    psr = PSS.Simulation(psr =  None , sim_telescope= 'GBT',
                             sim_ism= None, sim_scint= None,
                             sim_dict = scatterDict['scatter_psr_dict'])
    psr.init_signal()
    psr.init_pulsar()
    psr.init_ism()
    psr.pulsar.gauss_template(peak=.25)
    psr.init_telescope()
    psr.simulate()
    ScatteringData = psr.pulsar.profile

    if(os.path.exists('PsrSigSim_TeachingApp/SimData/ScatterData.hdf5')):
        os.remove('PsrSigSim_TeachingApp/SimData/ScatterData.hdf5')

    f = h5py.File('PsrSigSim_TeachingApp/SimData/ScatterData.hdf5','w')
    ScatteringData = np.array(ScatteringData)
    f.create_dataset('ScatterData', data=ScatteringData)
    f.create_dataset('Scatterhash', data=hash)
    f.close()
