'''

'''
#imports------------------------------------------------------------------------
import numpy as np
import h5py
import os

#Change this path to specify the location of the PsrSigSim
pssPath = '/home/kyle/GWA/NANOGrav/PsrSigSim/'
dataFilePath = 'PsrSigSim_TeachingApp/PsrTeachingData_V1.1.hdf5'

#Bokeh imports
from bokeh.io import curdoc, output_file, show
from bokeh.layouts import column, row, widgetbox, layout, Spacer
from bokeh.models import ColumnDataSource, Range1d, LinearColorMapper
import bokeh.models.widgets as widgets
from bokeh.plotting import figure

#Default values for psr_dict----------------------------------------------------
psr_dict = {}
psr_dict['f0'] = 1400                   #Central frequency
psr_dict['F0'] = 218                    #Pulsar spin freq
psr_dict['bw'] = 400                    #Bandwidth
psr_dict['Nf'] = 256                    #Frequency bins
psr_dict['ObsTime'] = 1000/psr_dict['F0']  #Observation time
psr_dict['f_samp'] = 0.08                #Sampling frequency
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
scSlider = widgets.Slider(title="Frequency (MHz)",value= scEnd ,start= scStart,
                          end=scEnd, step=scStep)

flSlider = widgets.Slider(title="Folding Frequency (Hz)", value=psr_dict['F0']/2,
                          start=psr_dict['F0']/4, end=psr_dict['F0']*3,
                          step=psr_dict['F0']*.01)




question1Group = widgets.RadioGroup(labels=["The plot would have 2 pulses with a larger Signal to Noise ratio",
                                    "The plot would have 1 pulse with a larger Signal to Noise ratio",
                                    "The plot would have 1 pulse with the same Signal to Noise ratio"]
                                    ,active=None)

question1Button = widgets.Button(label='Submit answer', button_type='success')

question2Group = widgets.RadioGroup(labels=["Lower frequencies arrive earlier than higher frequencies",
                                    "Higher frequencies arrive earlier than lower frequencies"],active=None)
question2Button = widgets.Button(label='Submit answer', button_type='success')

question3Group = widgets.RadioGroup(labels=["t > 1", "t = 1", "t < 1"],active=None)
question3Button = widgets.Button(label='Submit answer', button_type='success')

question4Group = widgets.RadioGroup(labels=["The pulse would have a lower peak with a 'tail' before the peak",
                                    "The pulse would have a lower peak with a 'tail' after the peak",
                                    "The pulse would have the same height of the peak with a 'tail' after the peak"],active=None)

question4Button = widgets.Button(label='Submit answer', button_type='success')



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
    grab_HTML()
    try:
        readData()
    except:
        genData()

def genData():
    try:
        import sys
        sys.path.insert(0,pssPath)
        import psrsigsim as PSS
    except:
        print("No PSS installed or location not specified")

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

    if(os.path.exists(dataFilePath)):
        os.remove(dataFilePath)

    f = h5py.File(dataFilePath,'w')

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
    f = h5py.File(dataFilePath,'r')

    dataString = 'DMData'
    DMFullData = np.array(f.get(dataString),copy=True)

    dataString = 'FLData'
    PreFoldingData = np.array(f.get(dataString),copy=True)

    dataString = 'SCData'
    ScatterData = np.array(f.get(dataString),copy=True)

    print('successfully read data')
    f.close()
    del f



#Bokeh Text boxes---------------------------------------------------------------


introPara = None
backgroundPara = None
foldPara = None
dmPara = None
ScatterPara = None
LastPara = None

def grab_HTML():
    global introPara
    global backgroundPara
    global foldPara
    global dmPara
    global ScatterPara
    global LastPara

    try:
        #Load all the HTML paragraphs as bokeh objects
        with open("PsrSigSim_TeachingApp/HTMLBits/introParagraph.html") as file:
            s = file.read()
            introPara = widgets.Div(text=s)

        with open("PsrSigSim_TeachingApp/HTMLBits/backgroundParagraph.html") as file:
            s = file.read()
            backgroundPara = widgets.Div(text=s)

        with open("PsrSigSim_TeachingApp/HTMLBits/foldingParagraph.html") as file:
            s = file.read()
            foldPara = widgets.Div(text=s)

        with open("PsrSigSim_TeachingApp/HTMLBits/dispersionParagraph.html") as file:
            s = file.read()
            dmPara = widgets.Div(text=s)

        with open("PsrSigSim_TeachingApp/HTMLBits/scatteringParagraph.html") as file:
            s = file.read()
            ScatterPara = widgets.Div(text=s)

        with open("PsrSigSim_TeachingApp/HTMLBits/endingParagraph.html") as file:
            s = file.read()
            LastPara = widgets.Div(text=s)

    except:
        print("HTML Files not found")
        exit()


setup() #------------------------------------------Reading/Genning Data---------

#Folding question---------------------------------------------------------------
question1Para = widgets.Div(text="""<h3>Question 1</h3>
                                   <p>Shown to the right is a plot of folded data at double the true period of a pulsar (i.e. the x-axis is 2 periods long).
                                   If you were to change that folding period to match the period of the pulsar, what would the plot look like?</p>""")

question1RightPara = widgets.Div(text="""<h3>Correct!</h3>
                                        <p>When folded at the correct period, the two pulses that are visible overlap and become one pulse that sticks out farther from
                                        the noise (larger Signal to Noise ratio).</p>""")

question1WrongPara1 = widgets.Div(text="""<h3>Not quite.</h3>
                                        <p>Would there still be two pulses visible if this plot is over two periods, and it's asking for a single period?</p>""")

question1WrongPara2 = widgets.Div(text="""<h3>Close.</h3>
                                        <p>If the same amount of noise is present for all folding periods, would two pulses overlapping cause a difference in the signal?</p>""")
#-------------------------------------------------------------------------------
#Dispersion question------------------------------------------------------------
question2Para = widgets.Div(text="""<h3>Question 2</h3>
                                   <p>To the right is a filterbank plot of a pulsar with a Dispersion Measure(DM) of 0 pc/cm<sup>3</sup>.
                                   Without any dispersion, the entire pulse arrives at the same time.
                                   If, instead, the pulsar had a DM of 7 pc/cm<sup>3</sup>, what which frequencies would arrive first?</p>""")

question2RightPara = widgets.Div(text="""<h3>Correct!</h3>""")

question2WrongPara1 = widgets.Div(text="""<h3>Getting there.</h3>
                                        <p>Pay careful attention to the equation in the background section. What is the sign on the frequency?</p>""")


#-------------------------------------------------------------------------------
#Dispersion question 2----------------------------------------------------------
question3Para = widgets.Div(text="""<h3>Question 3</h3>
                                   <p>If the highest frequency arrives at time t=0 and the lowest frequency arrives at a time t=2,
                                   when would the middle frequency arrive?</p>""")

question3RightPara = widgets.Div(text="""<h3>Correct!</h3>
                                        <p>Because of the 1 / f <sup>2</sup> dependence, the middle frequency would arrive before t=1</p>""")
question3WrongPara1 = widgets.Div(text="""<h3>Not quite.</h3>
                                        <p>What is the time dependence on frequency in this case?</p>""")
question3WrongPara2 = widgets.Div(text="""<h3>Almost.</h3>
                                        <p>What is the time dependence on frequency in this case?</p>""")
#-------------------------------------------------------------------------------
#Scattering question------------------------------------------------------------
question4Para = widgets.Div(text="""<h3>Question 4</h3>
                                   <p>To the right is a plot of a pulse profile from a pulsar at a high frequency with scattering effects that are negligible at this frequency.
                                   If you were to lower the frequency to show the effects of this scattering, what would the pulse look like?</p>""")

question4RightPara = widgets.Div(text="""<h3>Correct!</h3>
                                        <p>Because the overall energy is the same, having a tail would mean that the peak would need to decrease.
                                        The tail is after the peak due to the scattered light taking a longer path than the non-scattered.</p>
                                        <p>*Note: Due to the 1 / f <sup>4</sup> dependence, things at anything but the lowest frequencies look nearly identical</p>""")
question4WrongPara1 = widgets.Div(text="""<h3>Not quite.</h3>
                                        <p>What happens to the path length of the light that gets scattered versus non-scattered</p>""")
question4WrongPara2 = widgets.Div(text="""<h3>Almost.</h3>
                                        <p>Think about the conservation of energy.
                                        If a single pulse is spread over more distance, what would happen to the peak?</p>""")
#-------------------------------------------------------------------------------



#Bokeh Dispersion Figure--------------------------------------------------------

DMCM = LinearColorMapper(palette="Plasma256", low=0.0025, high=10)

DMsrc = ColumnDataSource( data=dict(image=[DMFullData[0,:,:]],x=[start_time],y=[first_freq]) )


DMfig = figure(title='Filter Bank',
             x_range = Range1d(0,1),
             y_range = Range1d(first_freq,last_freq),
             x_axis_label = 'Phase',
             y_axis_label = 'Frequency (MHz)',
             tools = "crosshair,pan,reset,wheel_zoom")

DMfig.image(source = DMsrc,image='image',x='x', y='y',# image=[DMFullData[1,:,:]]
          dw=(stop_time-start_time), dh=(last_freq - first_freq),
          color_mapper = DMCM)

DMfig.plot_height = 500
DMfig.plot_width = 500

DMinputs = widgetbox(dmSlider)

#-------------------------------------------------------------------------------
#Bokeh Scattering Figure--------------------------------------------------------
SCsrc = ColumnDataSource(data=dict(x=np.linspace(0,1,ScatterData.shape[1]),
                             y=ScatterData[-1,:]))

SCfig = figure(title='Scattering Demo',
               x_range = Range1d(0,1),
               y_range = Range1d(0,1),
               x_axis_label = 'Phase',
               y_axis_label = 'Pulse Intensity',
               tools = "crosshair,pan,reset,wheel_zoom")

SCfig.line(source = SCsrc, x='x', y='y',)
SCfig.plot_height = 500
SCfig.plot_width = 500

SCinputs = widgetbox(scSlider)

#-------------------------------------------------------------------------------
#Bokeh Folding Figure-----------------------------------------------------------
calcFold(psr_dict['F0']/2)

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

FLinputs = widgetbox(flSlider)

#-------------------------------------------------------------------------------




#Folding Question---------------------------------------------------------------
latest_answer1 = None
def updateQuestion1():
    global latest_answer1
    response = int(question1Group.active)
    lay = l.children[3].children[0].children[0]
    if(response != latest_answer1):
        if(response == 0):
            #Display wrong answer message 1
            lay.children[3]=question1WrongPara1
        elif(response == 2):
            #Display wrong answer message 2
            lay.children[3]=question1WrongPara2
        else:
            #Remove the answering and place the widget
            lay.children[2]=question1RightPara
            lay.children[3]=flSlider
    else:
        #Same response, do nothing
        pass
#-------------------------------------------------------------------------------
#Dispersion Question---------------------------------------------------------------
latest_answer2 = None
def updateQuestion2():
    global latest_answer2
    response = int(question2Group.active)
    lay = l.children[5].children[0].children[0]
    if(response != latest_answer2):
        if(response == 0):
            #Display wrong answer message 1
            lay.children[3]=question2WrongPara1
        else:
            #Remove the answering and place the widget
            lay.children[2]=question2RightPara
            lay.children[3]=question3Para
            lay.children[4]=question3Group
            lay.children[5]=question3Button
    else:
        #Same response, do nothing
        pass

#-------------------------------------------------------------------------------
#Dispersion Question 2----------------------------------------------------------
latest_answer3 = None
def updateQuestion3():
    global latest_answer3
    response = int(question3Group.active)
    lay = l.children[5].children[0].children[0]
    if(response != latest_answer3):
        if(response == 0):
            #Display wrong answer message 1
            lay.children[6]=question3WrongPara1
        elif(response == 1):
            #Display wrong answer message 2
            lay.children[6]=question3WrongPara2
        else:
            #Remove the answering and place the widget
            lay.children[5]=question3RightPara
            lay.children[6]=dmSlider
    else:
        #Same response, do nothing
        pass

#-------------------------------------------------------------------------------
#Scattering Question---------------------------------------------------------------
latest_answer4 = None
def updateQuestion4():
    global latest_answer4
    response = int(question4Group.active)
    lay = l.children[8].children[0].children[0]
    if(response != latest_answer4):
        if(response == 0):
            #Display wrong answer message 1
            lay.children[3]=question4WrongPara1
        elif(response == 2):
            #Display wrong answer message 2
            lay.children[3]=question4WrongPara2
        else:
            #Remove the answering and place the widget
            lay.children[2]=question4RightPara
            lay.children[3]=scSlider
    else:
        #Same response, do nothing
        pass

#-------------------------------------------------------------------------------


dmSlider.on_change('value', updateDMData)
scSlider.on_change('value', updateSCData)
flSlider.on_change('value', updateFLData)

question1Button.on_click(updateQuestion1)
question2Button.on_click(updateQuestion2)
question3Button.on_click(updateQuestion3)
question4Button.on_click(updateQuestion4)


foldColumn = column(children=[question1Para,question1Group,question1Button,Spacer(height=5)],sizing_mode='scale_width')
foldColumn.width = 750
foldColumn.height = 500
foldingActivity = row(children=[foldColumn,FLfig],sizing_mode='scale_width')

dispersionActivity = row(children=[column(children=
                      [question2Para,question2Group,question2Button,Spacer(height=1),Spacer(height=1),Spacer(height=1),Spacer(height=1)],sizing_mode='scale_width'),
                      DMfig],sizing_mode='scale_width')

scatteringActivity = row(children=[column(children=
                      [question4Para,question4Group,question4Button,Spacer(height=5)],sizing_mode='scale_width'),
                      SCfig],sizing_mode='scale_width')



layoutList = [
            [introPara],
            [backgroundPara],
            [foldPara],
            [foldingActivity], #i=3
            [dmPara],
            [dispersionActivity], #i=5
            [row(children=[Spacer(height=40)])],
            [ScatterPara],
            [scatteringActivity], #i=8
            [LastPara]
           ]

l = layout(layoutList,sizing_mode='scale_width')

curdoc().add_root(l)
curdoc().title = "PsrSigSim Teaching Tool"
