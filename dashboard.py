# ---
# jupyter:
#   jupytext:
#     cell_markers: '"""'
#     text_representation:
#       extension: .py
#       format_name: percent
#       format_version: '1.3'
#       jupytext_version: 1.16.4
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
# nepal = gpd.read_parquet('s3://nepal-in-data/quakes/nepal.parq')
# quakes = gpd.read_parquet('s3://nepal-in-data/quakes/quakes.parq')

nepal = gpd.read_parquet("data/nepal.parq")
quakes = gpd.read_parquet("data/quakes.parq")

# %%
slider_stylesheet = """
:host {
    top: -75px !important;
    width: 300px;
    left: 20px;
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


# %%
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

# %%
table_stylesheet = """
:host {
    flex: 1 0 30%;
}
.tabulator-cell {
    font-size: 14px;
}
"""

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
        "time": "Date/Time",
        "mag": "Mag.",
        "depth": "Depth (km)",
        "longitude": "Long",
        "latitude": "Lat",
    },
    theme="bulma",
    layout='fit_data',
    stylesheets=[table_stylesheet],
)

# %%
map = gv.Polygons(nepal, vdims=[])

plot =  (
    map.opts(
        alpha=0.1,
        xaxis=None,
        yaxis=None,
        active_tools=["pan", "wheel_zoom"],
        default_tools=["pan", "wheel_zoom", "hover"],
        data_aspect=1,
        responsive='width',
    )
    * points.opts(
        size=(2 ** gv.dim("mag")) / 4,
        cmap="OrRd",
        toolbar="above",
        color="mag",
        colorbar=True,
        data_aspect=1,
        responsive='width',
    ).redim.range(mag=mag_range)
)
map_css = """
:host {
    flex: 2 1 65%;
}
"""
plot_layout = pn.layout.Column(plot, date_slider, stylesheets=[map_css])

# %%
flex_css = """
@media screen and (max-width: 1200px) {
  div[id^="flexbox"] {
    flex-flow: column !important;
  }
}
"""
layout = pn.layout.FlexBox(plot_layout, quake_table, stylesheets=[flex_css])

# %%
template = pn.template.MaterialTemplate(
    site="",
    title="Earthquakes in Nepal",
    sidebar=[],
    main=[layout]
)
template.servable()

# %%
