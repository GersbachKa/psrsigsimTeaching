'''

'''
#imports------------------------------------------------------------------------
import sys
sys.path.insert(0,'/home/kyle/GWA/NANOGrav/PsrSigSim/')
import psrsigsim as PSS
import numpy as np
import h5py
import os


#Bokeh imports
from bokeh.io import curdoc, output_file, show
from bokeh.layouts import column, row, widgetbox, gridplot
from bokeh.models import ColumnDataSource, Range1d, LinearColorMapper
import bokeh.models.widgets as widgets
from bokeh.plotting import figure


#Default values for psr_dict----------------------------------------------------
psr_dict = {}
psr_dict['f0'] = 1400                   #Central frequency
psr_dict['F0'] = 218                    #Pulsar spin freq
psr_dict['bw'] = 400                    #Bandwidth
psr_dict['Nf'] = 512                    #Frequency bins
psr_dict['ObsTime'] = 1000/psr_dict['F0']  #Observation time
psr_dict['f_samp'] = 0.2                #Sampling frequency
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
dm_range_spacing = 0.25
NumPulses = 1 #Don't change this. A bunch of stuff uses variables that depend on
#this being 1
startingPeriod = 0
start_time = (startingPeriod / psr_dict['F0']) *1000  #Getting start time in ms
TimeBinSize = (1.0/psr_dict['f_samp']) * 0.001
start_bin = int((start_time)/TimeBinSize)
stop_time = (((1 / psr_dict['F0']) *1000) * NumPulses) + start_time
# start_time + however many pulses times the pulsar period in ms
stop_bin =int((stop_time)/TimeBinSize)
first_freq = psr_dict['f0']-(psr_dict['bw']/2)
last_freq = psr_dict['f0']+(psr_dict['bw']/2)

foldingAdditionFactor = 0.1
FL_tau_scatter =0.005
FL_f0 = 1150
FL_bw = 1700
FL_Nf = 34     #Using using 34, the Bandwidth will make integers for steps in the slider

FL_dm = 0.001
FL_flux = 80


DMFullData = None
DM_list = list(np.arange(dm_range[0],dm_range[1]+dm_range_spacing,step=dm_range_spacing))

ScatterData = None

PreFoldingData = None


################################################################################
dmSlider = widgets.Slider(title="Dispersion Measure", value= 0,
                          start=dm_range[0], end=dm_range[1],
                          step=dm_range_spacing)

scStep = FL_bw/FL_Nf #Span of frequencies to one bin
scStart = FL_f0 - (FL_bw/2) + (scStep/2) #Middle of the lowest frequency bin
scEnd = FL_f0 + (FL_bw/2) - (scStep/2) #Middl6e of the highest frequency bin
scSlider = widgets.Slider(title="Central Frequency",value= scStart  ,start= scStart,
                          end=scEnd, step=scStep)

flSlider = widgets.Slider(title="Folding Frequency", value=psr_dict['F0'],
                          start=psr_dict['F0']/2, end=psr_dict['F0']*2,
                          step=psr_dict['F0']*.05)

Exbutton = widgets.Button(label='Unused Button for now', button_type='success')

################################################################################


def updateDMData(attrname, old, new):
    idx = DM_list.index(dmSlider.value)
    DMsrc.data = dict(image=[DMFullData[idx,:,:]],x=[start_time],y=[first_freq])

def updateSCData(attrname, old, new):
    a = int((scSlider.value - scStart)/scStep)
    SCsrc.data = dict(x=np.linspace(0,1,ScatterData.shape[1]),
                                 y=ScatterData[a,:])

def updateFLData(attrname, old, new):
    postFold = calcFold(flSlider.value)
    FLsrc.data = dict(x=np.linspace(0,1,postFold.shape[0]),
                                 y=postFold)

def workingCalfFold(freq):
    foldingPeriod = (1.0/freq)*1000 #Given a frequency, what is the period
    foldingBin = int(foldingPeriod/TimeBinSize) #length of period in terms of time binss
    totalNum = PreFoldingData.shape[0] * PreFoldingData.shape[1] #Total Datapoints
    height = int(totalNum / foldingBin) + 1 #Given the folding frequency, this would be how many times we fold
    PostFoldingData = np.copy(PreFoldingData)
    PostFoldingData.resize(foldingBin,height) #Resizing to the given specs
    PostFoldingData = np.sum(PostFoldingData,axis=1) #summing the data points along the folded axis

def calcFold(freq):
    foldingPeriod = (1.0/freq)*1000 #Given a frequency, what is the period
    foldingBin = int(foldingPeriod/TimeBinSize) #length of period in terms of time binss
    totalNum = PreFoldingData.size #Total Datapoints
    height = int(totalNum / foldingBin) + 1 #Given the folding frequency, this would be how many times we fold
    PostFoldingData = np.array(PreFoldingData, copy=True)
    print(PostFoldingData.shape)
    PostFoldingData.resize(foldingBin,height) #Resizing to the given specs
    PostFoldingData.sum(axis=1) #summing the data points along the folded axis
    return np.copy(PostFoldingData)

def setup():
    try:
        readData()
    except:
        genData()



def buttonClick():
    print('Click')


def genData():
    #Dispersion Measure
    print("Generating Data \nThis should take less than a minute...")
    global DMFullData
    DMFullData = []
    i = dm_range[0]
    while i<=dm_range[1]:
        if(i==0):
            psr_dict['dm']=.001
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
        curData = psr.signal.signal[:,start_bin:stop_bin*NumPulses]
        curData = np.roll(curData, -1*(int(psr.ISM.time_delays[-1] / TimeBinSize)),1)
        DMFullData.append(curData)
        i+=dm_range_spacing

    #Folding
    global PreFoldingData
    psr_dict['tau_scatter'] = FL_tau_scatter
    psr_dict['f0'] = FL_f0
    psr_dict['bw'] = FL_bw
    psr_dict['Nf'] = FL_Nf
    psr_dict['dm'] = FL_dm
    psr_dict['radiometer_noise'] =  True
    psr_dict['flux'] = FL_flux
    psr_dict['to_Scatter_Broaden_exp'] = True

    psr = PSS.Simulation(psr =  None , sim_telescope= 'GBT',
                             sim_ism= None, sim_scint= None,
                             sim_dict = psr_dict)
    psr.init_signal()
    psr.init_pulsar()
    psr.init_ism()
    psr.pulsar.gauss_template(peak=.5)
    psr.init_telescope()
    psr.simulate()
    currentData = psr.obs_signal + foldingAdditionFactor*psr.signal.signal
    PreFoldingData = np.copy(np.swapaxes(currentData[:,start_bin:stop_bin],0,1))
    #Deep copy of the data with swapped axis

    #Scattering
    global ScatterData
    psr.pulsar.gauss_template(peak=.25)
    psr.simulate()

    ScatterData = psr.pulsar.profile

    f = h5py.File('PsrTeachingData.hdf5','w')

    dataString = 'DMData'
    DMFullData = np.array(DMFullData)
    f.create_dataset(dataString, data=DMFullData)

    dataString = 'FLData'
    f.create_dataset(dataString, data=PreFoldingData)

    dataString = 'SCData'
    f.create_dataset(dataString, data=ScatterData)

    f.close()


def readData():
    global DMFullData
    global PreFoldingData
    global ScatterData
    f = h5py.File('PsrTeachingData.hdf5','r')

    dataString = 'DMData'
    DMFullData = np.array(f.get(dataString))

    dataString = 'FLData'
    PreFoldingData = np.array(f.get(dataString))

    dataString = 'SCData'
    ScatterData = np.array(f.get(dataString))

    print('successfully read data')
    f.close()


setup()
#Bokeh Text boxes---------------------------------------------------------------
firstp = widgets.Div(text="""This is some intro text explaining what this first plot isself.""",
             width=1000, height=100)

secondp = widgets.Div(text="""This is some more text explaining what this second plot is""",
             width=1000, height=100)

thirdp = widgets.Div(text="""The same thing, but this time I'm <a href="http://nanograv.org/">Linking</a> something in it""",
             width=1000, height=100)



#-------------------------------------------------------------------------------
#Bokeh Dispersion Figure--------------------------------------------------------

DMCM = LinearColorMapper(palette="Plasma256", low=0.0025, high=10)

DMsrc = ColumnDataSource(data=dict(image=[DMFullData[0,:,:]],x=[start_time],y=[first_freq]))


DMfig = figure(title='Filter Bank',
             x_range = Range1d(start_time,stop_time),
             y_range = Range1d(first_freq,last_freq),
             x_axis_label = 'Observation Time (ms)',
             y_axis_label = 'Frequency (MHz)',
             tools = "crosshair,pan,reset,wheel_zoom")

DMfig.image(source = DMsrc,image='image',x='x', y='y',# image=[DMFullData[1,:,:]]
          dw=(stop_time-start_time), dh=(last_freq - first_freq),
          color_mapper = DMCM)

DMfig.plot_height = 500
DMfig.plot_width = 500

#-------------------------------------------------------------------------------
#Bokeh Scattering Figure--------------------------------------------------------

SCsrc = ColumnDataSource(data=dict(x=np.linspace(0,1,ScatterData.shape[1]),
                             y=ScatterData[0,:]))

SCfig = figure(title='Scattering Demo',
               x_range = Range1d(0,1),
               y_range = Range1d(0,1),
               x_axis_label = 'Phase',
               y_axis_label = 'Pulse Intensity',
               tools = "crosshair,pan,reset,wheel_zoom")

SCfig.line(source = SCsrc, x='x', y='y',)
SCfig.plot_height = 500
SCfig.plot_width = 500

#-------------------------------------------------------------------------------
#Bokeh Folding Figure-----------------------------------------------------------

postFold = calcFold(psr_dict['F0'])
FLsrc = ColumnDataSource(data=dict(x=np.linspace(0,1,postFold.shape[0]),
                             y= postFold) )

FLfig = figure(plot_width = 400, plot_height = 400,
              #x_range = Range1d(start_time,stop_time),
              y_range = Range1d(0,20),
              x_axis_label = 'Phase',
              y_axis_label = 'Pulse Intensity',
              tools = "crosshair,pan,reset,wheel_zoom")

FLfig.line(source = FLsrc, x='x', y='y',)
FLfig.plot_height = 500
FLfig.plot_width = 500


#-------------------------------------------------------------------------------

dmSlider.on_change('value', updateDMData)
scSlider.on_change('value', updateSCData)
flSlider.on_change('value', updateFLData)
#Exbutton.on_click(buttonClick)

DMinputs = widgetbox(dmSlider)

SCinputs = widgetbox(scSlider)

FLinputs = widgetbox(flSlider)

grid = gridplot([
                [firstp],
                [FLinputs,FLfig],
                [secondp],
                [DMinputs,DMfig],
                [thirdp],
                [SCinputs,SCfig]
                ])

curdoc().add_root(grid)
curdoc().title = "PsrSigSim Teaching Tool"
