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
from bokeh.layouts import column, row, widgetbox, layout
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
PostFoldingData = None

################################################################################
dmSlider = widgets.Slider(title="Dispersion Measure", value= 0,
                          start=dm_range[0], end=dm_range[1],
                          step=dm_range_spacing)

scStep = FL_bw/FL_Nf #Span of frequencies to one bin
scStart = FL_f0 - (FL_bw/2) + (scStep/2) #Middle of the lowest frequency bin
scEnd = FL_f0 + (FL_bw/2) - (scStep/2) #Middl6e of the highest frequency bin
scSlider = widgets.Slider(title="Central Frequency (MHz)",value= scStart  ,start= scStart,
                          end=scEnd, step=scStep)

flSlider = widgets.Slider(title="Folding Frequency (Hz)", value=psr_dict['F0'],
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
    calcFold(flSlider.value)
    FLsrc.data = dict(x=np.linspace(0,1,PostFoldingData.shape[0]),
                                 y=PostFoldingData)

def calcFold(freq):
    global PostFoldingData
    PostFoldingData = None
    foldBin = int((1.0/freq)*1000/TimeBinSize) #length of period in terms of time bins
    height = int(PreFoldingData.size/foldBin)
    temp = np.copy(PreFoldingData)
    temp = np.resize(temp,(height,foldBin))
    PostFoldingData = np.sum(temp,axis=0)


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
    PreFoldingData = np.copy((currentData[:,start_bin:stop_bin]))#Removed Swapaxes
    PreFoldingData = np.reshape(PreFoldingData,(np.size(PreFoldingData)))
    #Deep copy of the data with swapped axis

    #Scattering
    global ScatterData
    psr.pulsar.gauss_template(peak=.25)
    psr.simulate()

    ScatterData = psr.pulsar.profile

    if(os.path.exists('PsrSigSim_TeachingApp/PsrTeachingData.hdf5')):
        os.remove('PsrSigSim_TeachingApp/PsrTeachingData.hdf5')

    f = h5py.File('PsrSigSim_TeachingApp/PsrTeachingData.hdf5','w')

    dataString = 'DMData'
    DMFullData = np.array(DMFullData)
    f.create_dataset(dataString, data=DMFullData)

    dataString = 'FLData'
    f.create_dataset(dataString, data=PreFoldingData)

    dataString = 'SCData'
    f.create_dataset(dataString, data=ScatterData)

    f.close()
    del f


def readData():
    global DMFullData
    global PreFoldingData
    global ScatterData
    f = h5py.File('PsrSigSim_TeachingApp/PsrTeachingData.hdf5','r')

    dataString = 'DMData'
    DMFullData = np.array(f.get(dataString),copy=True)

    dataString = 'FLData'
    PreFoldingData = np.array(f.get(dataString),copy=True)

    dataString = 'SCData'
    ScatterData = np.array(f.get(dataString),copy=True)

    print('successfully read data')
    f.close()
    del f


setup()
#Bokeh Text boxes---------------------------------------------------------------

introPara = widgets.Div(text="""<h1 style="text-align: center;"><img src="PsrSigSim_TeachingApp/static/UWBLogo.jpg" width="100" height="100"> <img src="PsrSigSim_TeachingApp/static/NANOGravLogo.png" width="200" height="100"></h1>
                                <h1 style="text-align: center;"><strong>Pulsar Signal Simulator Teaching Tool</strong></h1>
                                <p style="text-align: center;"><strong>Created by Kyle Gersbach &amp; Dr. Jeff Hazboun</strong></p>
                                <p style="text-align: center;">Members of the Key Gravitational Wave Astronomy Research Group</p>
                                <p style="text-align: center;">&nbsp;</p>
                                <p>This tool is designed to help those who wish to get a basic understanding of how and why NANOGrav and other Pulsar Timing Arrays conduct data analysis. This application was built using the <a href="https://github.com/PsrSigSim/PsrSigSim">Pulsar Signal Simulator</a> as well as the <a href="https://bokeh.pydata.org/en/latest/">Bokeh</a> plotting and interactive tools. This application is still in development. If you have any suggestions or issues, please email me at: <a href="mailto:Gersbach.KA@gmail.com">Gersbach.KA@gmail.com</a></p>
                                <p>&nbsp;</p>""",
                                )

backgroundPara = widgets.Div(text="""<h3>Background</h3>
                                     <p>For background information to understand the following activities, I suggest reading up on the following websites as the explinations they give will be much better than what I can currently give</p>
                                     <p><a href="https://www.cv.nrao.edu/course/astr534/Pulsars.html">https://www.cv.nrao.edu/course/astr534/Pulsars.html</a></p>
                                     <p><a href="http://www.jb.man.ac.uk/distance/frontiers/pulsars/section4.html">http://www.jb.man.ac.uk/distance/frontiers/pulsars/section4.html</a></p>
                                     <p><a href="http://astronomy.swin.edu.au/cms/astro/cosmos/p/Pulsar+Dispersion+Measure">http://astronomy.swin.edu.au/cms/astro/cosmos/p/Pulsar+Dispersion+Measure</a></p>
                                     <p>&nbsp;</p>""",
                                     )

foldPara = widgets.Div(text="""<h3>Folding</h3>
                               <p>If you were to simply point your radio telescope towards a known pulsar, you would see nothing but noise. The only way to actually see these pulsars is to use the process called Folding. Folding is the process of taking a large amount of data, over a long time period and, with some defined period <strong>T</strong>, we break the data into chunks all with that same time period <strong>T</strong>. Then add all of the segments at the same part of the phase together, sort of like the picture below:</p>
                               <p style="text-align: center;">&nbsp;<img src="PsrSigSim_TeachingApp/static/Folding.png" width="300" height="300"></p>
                               <p>Notice how the data beforehand looks as if its just completely random, however, if you were to fold the data with the same period as the pulsar you are observing, you notice that the pulse from that pulsar finally become visible. However, if you were to fold the data with the wrong period, you might not see it at all. This is because the location of the pulse on the graph shifts between folds, making it harder to detect.&nbsp;</p>
                               <p>In this activity, you can move around the slider to adjust the frequency of which you are folding. This frequency corresponds to the period of which you fold through the&nbsp;<strong>T=1/F&nbsp;</strong>relation.&nbsp;The length of the period will change how long "phase" represents on the x-axis. A higher frequency means that the phase occupies a shorter amount of time and vice versa. You should notice that with a frequency of&nbsp;<strong>218 Hz</strong> the pulse is very much visible, as this is the frequency of the simulated pulsar. You might also see that at multiples and fractions of that frequency (i.e. <strong>109 Hz and 436 Hz</strong>)<strong>&nbsp;</strong>the pulse(s) is actually still visible, this is due to the harmonics of the pulse and can help lead you to the correct value when searching, where the biggest difference between signal and noise exists.</p>
                               <p>&nbsp;</p>""",
                               )

dmPara = widgets.Div(text="""<h3>Dispersion</h3>
                             <p>Dispersion is another effect that we must remove when looking for a pulsar. Dispersion is an effect where lower frequencies from a pulsar get delayed more than higher frequencies. The amount of delay is dependent on the amount of material (Free Electrons) between the pulsar and the observer (also called the Interstellar Medium or ISM), as well as the frequencies being observed. The value of the Dispersion Measure is given by the following equation:</p>
                             <p style="text-align: center;">&nbsp;<img src="PsrSigSim_TeachingApp/static/DispersionEquation.png" width="300" height="150"></p>
                             <p>In this next activity, you can manually change the dispersion measure and view the resulting plot of Frequency versus Time where higher frequencies are on the top. Do note that when the pulse seems to wander off of one side of the graph and appear on the other, this would actually be from a trailing pulse that came before the current pulse. This means that you could potentially be seeing 3 or more pulses all at the same time, just at different frequencies.</p>
                             <p>&nbsp;</p>""",
                             )

ScatterPara = widgets.Div(text="""<h3>Scattering</h3>
                                  <p>Scattering is yet another effect that a pulse from a pulsar can go through. This is primarily caused by a section of a pulse that was initially not directed at the observer, but the refraction from the Interstellar Medium causes those sections to be redirected towards Earth. In the same way light bends as it enters a new medium, like a cup of water, light also gets refracted by the Interstellar Medium. Due to the differing lengths that sections of the pulse travels, the resulting observations can generate a tail often called a scattering tail. This diagram helps to explain why the pulse can have a tail:</p>
                                  <p style="text-align: center;">&nbsp;<img src="PsrSigSim_TeachingApp/static/Scattering.png" width="800" height="300"></p>
                                  <p>Because this phenomenon is frequency dependent, lower frequencies are affected by it more than higher frequencies, the following activity shows that with lower frequencies you see this tail on the end of the pulsar, while at higher frequencies the pulse is much more gaussian. Keep in mind that this is what a scattering tail would look like in a perfect world, and our observations look much messier.</p>
                                  <p>&nbsp;</p>""",
                                  )

LastPara = widgets.Div(text="""<p style="text-align: center;">This work was partially funded by Grant 1430284 through the NSF NANOGrav Physics Frontiers Center.</p>
                               <p style="text-align: center;"><img src="PsrSigSim_TeachingApp/static/NSFLogo.png" width="185" height="150"></p>""",
                               )


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
calcFold(psr_dict['F0'])

FLsrc = ColumnDataSource(data=dict(x = np.linspace(0,1,PostFoldingData.shape[0]),
                             y = PostFoldingData ) )

FLfig = figure(plot_width = 400, plot_height = 400,
              #x_range = Range1d(start_time,stop_time),
              y_range = Range1d(0,20),
              x_axis_label = 'Phase',
              y_axis_label = 'Pulse Intensity',
              tools = "crosshair,pan,reset,wheel_zoom")

FLfig.line(source = FLsrc, x='x', y='y',)
FLfig.plot_height = 500
FLfig.plot_width = 500
FLfig.yaxis.major_label_text_font_size = '0pt'

#-------------------------------------------------------------------------------

dmSlider.on_change('value', updateDMData)
scSlider.on_change('value', updateSCData)
flSlider.on_change('value', updateFLData)
#Exbutton.on_click(buttonClick)

DMinputs = widgetbox(dmSlider)

SCinputs = widgetbox(scSlider)

FLinputs = widgetbox(flSlider)

l = layout([
            [introPara],
            [backgroundPara],
            [foldPara],
            [FLinputs,FLfig],
            [dmPara],
            [DMinputs,DMfig],
            [ScatterPara],
            [SCinputs,SCfig],
            [LastPara]
           ],sizing_mode='scale_width')

curdoc().add_root(l)
curdoc().title = "PsrSigSim Teaching Tool"
