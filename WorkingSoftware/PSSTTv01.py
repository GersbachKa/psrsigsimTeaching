'''
Implement some type of h5py data storage
Ways to do this:
1. Move components of bokeh_plot into this file. Have bokeh_plot return just
   the array. That way it can be stored in such a file (as I understand it)
   Have this file create the images and display them
2. Find a way to store a full bokeh.figure in a file

'''
#imports------------------------------------------------------------------------
import sys
sys.path.insert(0,'/home/kyle/GWA/NANOGrav/PsrSigSim/')
import psrsigsim as PSS
import numpy as np
import h5py


#Bokeh imports
from bokeh.io import curdoc, output_file, show
from bokeh.layouts import column, row, widgetbox
from bokeh.models import ColumnDataSource, Range1d
import bokeh.models.widgets as widgets
from bokeh.plotting import figure


#Default values for psr_dict----------------------------------------------------
psr_dict = {}
psr_dict['f0'] = 1400                   #Central frequency
psr_dict['F0'] = 218                    #Pulsar spin freq
psr_dict['bw'] = 400                    #Bandwidth
psr_dict['Nf'] = 512                    #Frequency bins
psr_dict['ObsTime'] = 4*1000/psr_dict['F0']  #Observation time
psr_dict['f_samp'] = 0.1                #Sampling frequency
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
psr_dict['data_type']='float32'         #Was int8
psr_dict['flux'] = 3
psr_dict['to_DM_Broaden'] = False


#Constants for generating data--------------------------------------------------
dm_range = (0,10)
dm_range_spacing = 0.5
NumPulses = 1
startingPeriod = 2.0
start_time = (startingPeriod / psr_dict['F0']) *1000  #Getting start time in ms
TimeBinSize = (1.0/psr_dict['f_samp']) * 0.001
start_bin = int((start_time)/TimeBinSize)
stop_time = (((1 / psr_dict['F0']) *1000) * NumPulses) + start_time
# start_time + however many pulses times the pulsar period in ms
stop_bin =int((stop_time)/TimeBinSize)
first_freq = psr_dict['f0']-(psr_dict['bw']/2)
last_freq = psr_dict['f0']+(psr_dict['bw']/2)
FullData = None
DM_list = list(np.arange(dm_range[0],dm_range[1],step=dm_range_spacing))
################################################################################
dmSlider = widgets.Slider(title="Dispersion Measure", value= 0,
                          start=dm_range[0], end=dm_range[1],
                          step=dm_range_spacing)

Exbutton = widgets.Button(label='Unused Button for now', button_type='success')

################################################################################


def updateDMData(attrname, old, new):
    idx = DM_list.index(dmSlider.value)
    src.data = dict(image=[FullData[idx,:,:]],x=[start_time],y=[first_freq])

def setup():
    try:
        readData()
    except:
        genData()


def buttonClick():
    print('Click')


def genData():
    global FullData
    FullData = []
    i = dm_range[0]
    while i<=dm_range[1]:
        psr_dict['dm']=i
        psr = PSS.Simulation(psr =  'J1713+0747' , sim_telescope= 'GBT',sim_ism= True, sim_scint= False, sim_dict = psr_dict)
        psr.simulate()
        FullData.append(psr.signal.signal[:,start_bin:stop_bin])
        print(psr.signal.TimeBinSize)
        print('DM is ',i)
        i+=dm_range_spacing

    f = h5py.File('PsrDMData.hdf5','w')
    dataString = 'Data'
    FullData = np.array(FullData)
    f.create_dataset(dataString, data=FullData)
    f.close()


def readData():
    global FullData
    f = h5py.File('PsrDMData.hdf5','r')
    dataString = 'Data'
    FullData = np.array(f.get(dataString))
    print('successfully read data')
    f.close()


setup()
#Bokeh Figure-------------------------------------------------------------------

src = ColumnDataSource(data=dict(image=[FullData[0,:,:]],x=[start_time],y=[first_freq]))


fig = figure(title='Filter Bank',
             x_range = Range1d(start_time,stop_time),
             y_range = Range1d(first_freq,last_freq),
             x_axis_label = 'Observation Time (ms)',
             y_axis_label = 'Frequency (MHz)',
             tools = "crosshair,pan,reset,wheel_zoom")

fig.image(source = src,image='image',x='x', y='y',# image=[FullData[1,:,:]]
          dw=(stop_time-start_time), dh=(last_freq - first_freq),
          palette = 'Plasma256')

fig.plot_height = 600
fig.plot_width = 600
#-------------------------------------------------------------------------------

dmSlider.on_change('value', updateDMData)
Exbutton.on_click(buttonClick)

inputs = widgetbox(dmSlider,Exbutton)

curdoc().add_root(row(inputs,fig))
curdoc().title = "DM Variation"
