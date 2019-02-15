#Bokeh Imports
from bokeh.io import curdoc, output_file, show
from bokeh.layouts import column, row, widgetbox, layout
from bokeh.models import ColumnDataSource, Range1d, LinearColorMapper
import bokeh.models.widgets as widgets
from bokeh.plotting import figure

import numpy as np
import HTMLbits as hb

PreFoldingData = None
PostFoldingData = None

def main(all_dictionaries,FoldData,DMData,ScatterFullData):

    DMFullData = DMData
    dm_range = all_dictionaries['dm_constants']['dm_range']
    dm_range_spacing = all_dictionaries['dm_constants']['dm_range_spacing']
    DM_list = list(np.arange(dm_range[0],dm_range[1]+dm_range_spacing,step=dm_range_spacing))

    ScatterData = ScatterFullData

    global PreFoldingData
    global PostFoldingData

    PreFoldingData = FoldData
    PostFoldingData = None


    dmSlider = widgets.Slider(title="Dispersion Measure", value= 0,
                              start=dm_range[0], end=dm_range[1],
                              step=dm_range_spacing)

    scatterDict = all_dictionaries['scatter_constants']['scatter_psr_dict']
    scStep = scatterDict['bw']/scatterDict['Nf'] #Span of frequencies to one bin
    scStart = scatterDict['f0'] - (scatterDict['bw']/2) + (scStep/2) #Middle of the lowest frequency bin
    scEnd = scatterDict['f0'] + (scatterDict['bw']/2) - (scStep/2) #Middle of the highest frequency bin
    scSlider = widgets.Slider(title="Central Frequency (MHz)",value= scStart  ,start= scStart,
                              end=scEnd, step=scStep)

    foldingDict = all_dictionaries['fold_constants']['fold_psr_dict']
    flSlider = widgets.Slider(title="Folding Frequency (Hz)", value=foldingDict['F0'],
                              start=foldingDict['F0']/2, end=foldingDict['F0']*2,
                              step=foldingDict['F0']*.05)


    #Update Fuctions------------------------------------------------------------

    def updateDMData(attrname, old, new):
        idx = DM_list.index(dmSlider.value)
        DMsrc.data = dict(image=[DMFullData[idx,:,:]],
                          x=[all_dictionaries['dm_constants']['start_time']],
                          y=[all_dictionaries['dm_constants']['first_freq']])

    def updateSCData(attrname, old, new):
        a = int((scSlider.value - scStart)/scStep)
        SCsrc.data = dict(x=np.linspace(0,1,ScatterData.shape[1]),y=ScatterData[a,:])

    def updateFLData(attrname, old, new):
        calcFold(flSlider.value)
        FLsrc.data = dict(x=np.linspace(0,1,PostFoldingData.shape[0]),y=PostFoldingData)

    def calcFold(freq):
        #global PostFoldingData
        PostFoldingData = None
        foldBin = int((1.0/freq)*1000/(all_dictionaries['fold_constants']['TimeBinSize'])) #length of period in terms of time bins
        height = int(PreFoldingData.size/foldBin)
        temp = np.copy(PreFoldingData)
        temp = np.resize(temp,(height,foldBin))
        PostFoldingData = np.sum(temp,axis=0)
        print(type(PostFoldingData))



    #Bokeh Dispersion Figure--------------------------------------------------------

    DMCM = LinearColorMapper(palette="Plasma256", low=0.0025, high=10)

    DMsrc = ColumnDataSource(data=dict(image=[DMFullData[0,:,:]],
                             x=[all_dictionaries['dm_constants']['start_time']],
                             y=[all_dictionaries['dm_constants']['first_freq']]))


    DMfig = figure(title='Filter Bank',
                 x_range = Range1d(all_dictionaries['dm_constants']['start_time'],
                                   all_dictionaries['dm_constants']['stop_time']),
                 y_range = Range1d(all_dictionaries['dm_constants']['first_freq'],
                                   all_dictionaries['dm_constants']['last_freq']),
                 x_axis_label = 'Observation Time (ms)',
                 y_axis_label = 'Frequency (MHz)',
                 tools = "crosshair,pan,reset,wheel_zoom")

    DMdw = all_dictionaries['dm_constants']['stop_time'] - all_dictionaries['dm_constants']['start_time']
    DMdh = all_dictionaries['dm_constants']['last_freq'] - all_dictionaries['dm_constants']['first_freq']
    DMfig.image(source = DMsrc,image='image',x='x', y='y',# image=[DMFullData[1,:,:]]
              dw=(DMdw), dh=(DMdh),
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
    calcFold(all_dictionaries['fold_constants']['fold_psr_dict']['F0'])


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
                [hb.introPara],
                [hb.backgroundPara],
                [hb.foldPara],
                [FLinputs,FLfig],
                [hb.dmPara],
                [DMinputs,DMfig],
                [hb.ScatterPara],
                [SCinputs,SCfig],
                [hb.LastPara]
               ],sizing_mode='scale_width')

    curdoc().add_root(l)
    curdoc().title = "PsrSigSim Teaching Tool"
