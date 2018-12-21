import numpy as np

from bokeh.io import curdoc
from bokeh.layouts import column
from bokeh.models import ColumnDataSource, Slider
from bokeh.plotting import figure

N = 100

x_ = np.linspace(0, 10, 200)
y_ = np.linspace(0, 10, 200)
z_ = np.linspace(0, 10, N)

x, y, z = np.meshgrid(x_, y_, z_, indexing='xy')

data = np.sin(x+z)*np.cos(y)

source = ColumnDataSource(data=dict(image=[data[:, :, 0]]))

p = figure(x_range=(0, 10), y_range=(0, 10))
p.image(image='image', x=0, y=0, dw=10, dh=10, source=source, palette="Spectral11")

slider = Slider(start=0, end=(N-1), value=0, step=1, title="Frame")

def update(attr, old, new):
    source.data = dict(image=[data[:, :, slider.value]])

slider.on_change('value', update)

curdoc().add_root(column(p, slider))
