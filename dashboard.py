# ---
# jupyter:
#   jupytext:
#     cell_markers: '"""'
#     text_representation:
#       extension: .py
#       format_name: percent
#       format_version: '1.3'
#       jupytext_version: 1.16.1
#   kernelspec:
#     display_name: NepQuakes
#     language: python
#     name: nep-quakes
# ---

# %%
import colorcet as cc  # noqa: F401
import geopandas as gpd
import geoviews as gv
import geoviews.tile_sources as gvts
import holoviews as hv
import pandas as pd
import panel as pn

from bokeh.models import HoverTool
from bokeh.models.widgets.tables import NumberFormatter

# %%
# gv.extension("bokeh")
hv.extension("bokeh")
pn.extension("tabulator")
pn.extension(design="material")

# %%
nepal = gpd.read_parquet("data/nepal.parq")
quakes = gpd.read_parquet("data/quakes.parq")

# %%
slider_stylesheet = """
:host {
    top: -75px !important;
}
"""

last_date = quakes.index.max().date()
earliest_date = quakes.index.min().date()
date_slider = pn.widgets.DateRangeSlider(
    name="Date Range",
    start=earliest_date,
    end=last_date,
    value=(earliest_date, last_date),
    sizing_mode='stretch_width',
    stylesheets=[slider_stylesheet],
)

info = pn.pane.Alert(f"**{len(quakes)}** earthquakes recorded between {earliest_date:%F} and {last_date:%F}")

mag_range = (quakes["mag"].min(), quakes["mag"].max())

def plot_quakes(date_range):
    dates = [pd.Timestamp(x, tz="UTC") for x in date_range]
    data = quakes.loc[dates[0] : dates[1]]
    quake_table.value = data[["mag", "depth", "latitude", "longitude"]]

    hover_tool = HoverTool(tooltips=[
        ("Date", "@time{%d %b %Y %I:%M %p}"),
        ("Magnitude: ", "@mag{0.0}"),
        ("Depth: ", "@depth{0.00} kms"),
    ],
  formatters={'@time': 'datetime'})
    return (
        gv.Points(
            data,
            kdims=["longitude", "latitude"],
            vdims=["mag", "depth", "time"],
        ).opts(tools=[hover_tool])
    )


quake_points = pn.bind(plot_quakes, date_range=date_slider)
points = hv.DynamicMap(quake_points)

quake_table = pn.widgets.Tabulator(
    quakes[["mag", "depth", "latitude", "longitude"]],
    show_index=True,
    page_size=10,
    selectable=False,
    sortable={
        "mag": True,
        "depth": True,
        "longitude": False,
        "latitude": False,
    },
    formatters={
        "mag": NumberFormatter(format="0.0"),
        "depth": NumberFormatter(format="0.00"),
        "longitude": NumberFormatter(format="0.00"),
        "latitude": NumberFormatter(format="0.00"),
    },
    editors={"mag": None, "depth": None, "longitude": None, "latitude": None},
    titles={
        "mag": "Magnitude",
        "depth": "Depth (km)",
        "longitude": "Longitude",
        "latitude": "Latitude",
    },
)

map = gv.Polygons(nepal, vdims=[])

plot =  (
    gvts.CartoLight
    * map.opts(
        alpha=0.1,
        responsive=True,
        xaxis=None,
        yaxis=None,
        active_tools=["pan", "wheel_zoom"],
        default_tools=["pan", "wheel_zoom", "hover"],
    )
    * points.opts(
        size=(2 ** gv.dim("mag")) / 4,
        cmap="OrRd",
        toolbar="above",
        color="mag",
        colorbar=True,
    ).redim.range(mag=mag_range)
)

plot_pane = pn.Column(
    plot,
    pn.Row(pn.Spacer(width=50), date_slider, info, pn.Spacer(width=50)),
    sizing_mode='stretch_both'
)

table_layout = pn.Column(quake_table)
app = pn.FlexBox(plot_pane, table_layout, sizing_mode="stretch_both")
pn.template.MaterialTemplate(site="", title="Earthquakes in Nepal", main=[app]).servable()#, raw_css=[CSS]).servable()
