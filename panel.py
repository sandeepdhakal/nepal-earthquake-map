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

from bokeh.models.widgets.tables import NumberFormatter

# %%
gv.extension("bokeh")
hv.extension("bokeh")
pn.extension("tabulator")

# %%
nepal = gpd.read_parquet("data/nepal.parq")
quakes = gpd.read_parquet("data/quakes.parq")

# %%
last_date = quakes.index.max().date()
earliest_date = quakes.index.min().date()
date_slider = pn.widgets.DateRangeSlider(
    name="Date Range",
    start=earliest_date,
    end=last_date,
    value=(earliest_date, last_date),
    width=800,
)

hover_tooltips = [
    ("Date", "@{time}{%F}"),
    ("Magnitude: ", "@mag"),
    ("Depth: ", "@depth kms"),
]

mag_range = (quakes["mag"].min(), quakes["mag"].max())


def plot_quakes(date_range):
    dates = [pd.Timestamp(x, tz="UTC") for x in date_range]
    data = quakes.loc[dates[0] : dates[1]]
    quake_table.value = data[["mag", "depth", "latitude", "longitude"]]
    return (
        gv.Points(
            data,
            kdims=["longitude", "latitude"],
            vdims=["mag", "depth", "time"],
        )
        .opts(hover_tooltips=hover_tooltips)
        .redim.range(mag=mag_range)
    )


quake_points = pn.bind(plot_quakes, date_range=date_slider)
points = hv.DynamicMap(quake_points)

quake_table = pn.widgets.Tabulator(
    quakes[["mag", "depth", "latitude", "longitude"]],
    show_index=True,
    selectable=False,
    sortable={
        "mag": True,
        "depth": True,
        "longitude": False,
        "latitude": False,
    },
    formatters={
        "mag": NumberFormatter(format="0.00"),
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

point_layout = pn.Column(
    gvts.CartoLight
    * map.opts(
        alpha=0.1,
        width=800,
        height=500,
        xaxis=None,
        yaxis=None,
        active_tools=["pan", "wheel_zoom"],
        default_tools=["pan", "wheel_zoom", "hover"],
    )
    * points.opts(
        size=(2 ** gv.dim("mag")) / 4,
        cmap="OrRd",
        tools=["hover"],
        toolbar="above",
        hover_tooltips=hover_tooltips,
        color="mag",
        colorbar=True,
    ),
    date_slider,
)

table_layout = pn.Column(quake_table)
app = pn.FlexBox(point_layout, table_layout, sizing_mode="stretch_both")

# %%
app.servable()
