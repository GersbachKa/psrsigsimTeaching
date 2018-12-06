'''
Implement some type of h5py data storage
Ways to do this:
1. Move components of bokeh_plot into this file. Have bokeh_plot return just
   the array. That way it can be stored in such a file (as I understand it)
   Have this file create the images and display them
2. Find a way to store a full bokeh.figure in a file

'''
#imports
import sys
sys.path.insert(0,'/home/kyle/GWA/NANOGrav/PsrSigSim/')
import psrsigsim as PSS
import numpy as np
import h5py

#Bokeh imports
from bokeh.io import curdoc, output_file, show
from bokeh.layouts import row, widgetbox
from bokeh.models import ColumnDataSource, Range1d
import bokeh.models.widgets as widgets
from bokeh.plotting import figure


#Constants for generating data
dm_range = (0.1,10.1)
dm_range_spacing = 5

#Default values for psr_dict
psr_dict = {}
psr_dict['f0'] = 1400                   #Central frequency
psr_dict['F0'] = 218                    #Pulsar spin freq
psr_dict['bw'] = 400                    #Bandwidth
psr_dict['Nf'] = 512                    #Frequency bins
psr_dict['ObsTime'] = 20                #Observation time
psr_dict['f_samp'] = 4                  #Sampling frequency
psr_dict['SignalType'] = "intensity"    #'intensity' which carries a Nf x Nt
#filterbank of pulses or 'voltage' which carries a 4 x Nt array of
#voltage vs. time pulses representing 4 stokes channels
psr_dict['dm'] = 0.1                     #Dispersion Measure Pescs/(CM^3)
# V_ISS -- Intersteller Scintilation Velocity
psr_dict['scint_bw'] =  15.6            #Scintilation Bandwidth
psr_dict['scint_timescale'] = 2630      #Scintilation Timescale
# pulsar -- pulsar name
# telescope -- telescope name(GBT or Arecibo)
psr_dict['freq_band'] = 1400            #Frequency band [327 ,430, 820, 1400, 2300]
# aperature -- aperature (m)
# area -- collecting area (m^2)
# Tsys -- system temp (K), total of receiver, sky, spillover, etc. (only needed for noise)
# name -- GBT or Arecibo
# tau_scatter -- scattering time (ms)
psr_dict['radiometer_noise'] =  False   #radiometer noise
psr_dict['data_type']='float32'            #
psr_dict['flux'] = 3
psr_dict['to_DM_Broaden'] = True

#Default values for Creating the plots
NumPulses = 1
startingPeriod = 1.0
start_time = (startingPeriod / psr_dict['F0']) *1000  #Getting start time in ms
start_bin = int((start_time)/TimeBinSize)
TimeBinSize = 0

fig = figure()


################################################################################
dmSlider = widgets.Slider(title="Dispersion Measure", value= 0.1,
                          start=dm_range[0], end=dm_range[1],
                          step=dm_range_spacing)

Exbutton = widgets.Button(label='Generate Filter Bank', button_type='success')

################################################################################

def updateData(attrname, old, new):
    showFilterBank(dmSlider.value)


def setup():

    #try:
    #    checkData()
    #except:
    #    genData()
    genData()
    showFirst()

def checkData():
    f=h5py.File('PsrTestFile.hdf5','r')
    f.close()

def buttonClick():
    print('Click')

def showFirst():
    f=h5py.File('PsrTestFile.hdf5','r')


    lis = DMList[str(dm_range[0])]
    fig = figure(title='Filter Bank',
                      x_range = Range1d(start_time,lis["stop_time"]),
                      y_range = Range1d(lis["first_freq"],lis["last_freq"]),
                      x_axis_label = 'Observation Time (ms)',
                      y_axis_label = 'Frequency (Mhz)',
                      tools="crosshair,pan,reset,wheel_zoom")

    nameString = 'dm' + str(dm_range[0])
    img = np.array(f.get(nameString))
    fig.image(image=[img], x=[0], y=[1400], dw=[lis["stop_time"]],
              dh=[lis["last_freq"]], palette='Plasma256')
    fig.plot_height = 700
    fig.plot_width = 700

    f.close()


def showFilterBank(dmVal):
    f=h5py.File('PsrTestFile.hdf5','r')

    lis = DMList[str(dmVal)]
    fig.y_range = Range1d(lis["first_freq"],lis["last_freq"])
    nameString = 'dm' + str(dmVal)
    img = np.array(f.get(nameString))
    fig.image(image=[img], x=[0], y=[1400], dw=[lis["stop_time"]],
              dh=[lis["last_freq"]], palette='Plasma256')
    f.close()


def genData():

    f=h5py.File('PsrTestFile.hdf5','a')

    #Generate DM data
    i=dm_range[0]
    #while i<=dm_range[1]:
    while i=0.1:
        #setup values
        nameString = 'dm' + str(i)
        psr_dict['dm'] = i
        s = PSS.Simulation(psr =  'J1713+0747' , sim_telescope= 'GBT',sim_ism= True, sim_scint= False, sim_dict = psr_dict)
        s.simulate()
        nBins_per_period = int(s.signal.MetaData.pulsar_period//s.signal.TimeBinSize)
        stop_bin = NumPulses*nBins_per_period
        stop_time = start_time + NumPulses * nBins_per_period * s.signal.TimeBinSize

        img = s.signal.signal[:,:stop_bin]

        valueDict = {}
        #valueDict['start_time'] = start_time
        print(stop_time)
        print(s.signal.first_freq)
        print(s.signal.last_freq)
        valueDict['stop_time'] = stop_time
        valueDict['first_freq'] = s.signal.first_freq
        valueDict['last_freq'] = s.signal.last_freq
        DMList[str(i)] = valueDict


        i+=dm_range_spacing
    f.close()



dmSlider.on_change('value', updateData)
Exbutton.on_click(buttonClick)
setup()

curdoc().add_root(row(dmSlider,Exbutton,fig))
