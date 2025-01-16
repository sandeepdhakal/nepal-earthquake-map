"""A dashboard to visualise the most recent earthquakes in Nepal."""

import datetime
import urllib.parse

import colorcet as cc  # noqa: F401
import geopandas as gpd
import geoviews as gv
import holoviews as hv
import pandas as pd
import panel as pn
from bokeh.models import HoverTool
from bokeh.models.widgets.tables import NumberFormatter

hv.extension("bokeh")
pn.extension("tabulator")
pn.extension(design="material")

pn.extension(
    defer_load=True,
    loading_spinner="dots",
    loading_indicator=True,
    throttled=True,
    # loading_color="#0000ff",
)

nepal = gpd.read_parquet("data/nepal.parq").dissolve()
nepal = nepal.dissolve()

bounds = nepal.bounds
minx, miny, maxx, maxy = bounds.iloc[0].to_numpy()

CATALOG_URL = "https://earthquake.usgs.gov/fdsnws/event/1/query.geojson"
params = {
    "starttime": "2010-10-07",
    "endtime": str(datetime.date.today()),
    "maxlatitude": maxy,
    "minlatitude": miny,
    "maxlongitude": maxx,
    "minlongitude": minx,
    "minmagnitude": 3,
    "eventtype": "earthquake",
    "orderby": "time",
}
columns = ["mag", "place", "time", "geometry", "depth"]

url = f"{CATALOG_URL}?{urllib.parse.urlencode(params)}"
quakes = gpd.read_file(url, columns=columns)

nepal_buffer = nepal.to_crs(epsg=3857).buffer(20000).to_crs(epsg=4326)
quakes = quakes[quakes.within(nepal_buffer.loc[0])]

quakes["time"] = pd.to_datetime(quakes["time"], unit="ms").dt.tz_localize(
    tz="Asia/Kathmandu",
)
quakes = quakes.set_index("time").sort_index()

quakes["longitude"] = quakes["geometry"].x
quakes["latitude"] = quakes["geometry"].y
quakes = quakes.drop(columns="geometry")

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
    sizing_mode="stretch_width",
    stylesheets=[slider_stylesheet],
)

mag_range = (quakes["mag"].min(), quakes["mag"].max())

table_stylesheet = """
:host {
    flex: 1 0 30%;
}
.tabulator-cell {
    font-size: 14px;
}
"""

quake_table = pn.widgets.Tabulator(
    quakes[["mag", "latitude", "longitude"]],
    show_index=True,
    page_size=10,
    selectable=False,
    sortable={
        "mag": True,
        "longitude": False,
        "latitude": False,
    },
    formatters={
        "mag": NumberFormatter(format="0.0"),
        "longitude": NumberFormatter(format="0.00"),
        "latitude": NumberFormatter(format="0.00"),
    },
    editors={"mag": None, "longitude": None, "latitude": None},
    titles={
        "time": "Date/Time",
        "mag": "Mag.",
        "longitude": "Long",
        "latitude": "Lat",
    },
    theme="bulma",
    layout="fit_data",
    stylesheets=[table_stylesheet],
)


def plot_quakes(date_range):
    """Plot the earthquakes within the `date_range` datetime range."""
    dates = [pd.Timestamp(x, tz="UTC") for x in date_range]
    data = quakes.loc[dates[0] : dates[1]]
    quake_table.value = data[["mag", "latitude", "longitude"]]

    hover_tool = HoverTool(
        tooltips=[
            ("Date", "@time{%d %b %Y %I:%M %p}"),
            ("Magnitude: ", "@mag{0.0}"),
            ("Place", "@place"),
        ],
        formatters={"@time": "datetime"},
    )

    # idea for datetime based colourbar thanks to https://stackoverflow.com/a/59271373
    data = data.reset_index()
    # use 'time_color' for the colorbar, since the colors need to be a float or int
    data["time_color"] = data.index.to_series()
    cbar_opts = {
        "major_label_overrides": data["time"].dt.strftime("%Y-%m-%d").to_dict(),
        "major_label_text_align": "left",
    }

    return gv.Points(
        data,
        kdims=["longitude", "latitude"],
        vdims=["mag", "time", "time_color", "place"],
    ).opts(
        tools=[hover_tool],
        size=(2 ** gv.dim("mag")) / 4,
        cmap="viridis",
        color="time_color",
        fill_alpha=0.5,
        colorbar=True,
        colorbar_opts=cbar_opts,
        toolbar="above",
    )


quake_points = pn.bind(plot_quakes, date_range=date_slider)
points = hv.DynamicMap(quake_points)

nepal_map = gv.Path(nepal).opts(color="black")

plot = nepal_map.opts(
    # alpha=0.1,
    xaxis=None,
    yaxis=None,
    active_tools=["pan", "wheel_zoom"],
    default_tools=["pan", "wheel_zoom"],
    data_aspect=1,
    responsive="width",
) * points.opts(
    data_aspect=1,
    responsive="width",
).redim.range(mag=mag_range)
map_css = """
:host {
    flex: 2 1 65%;
}
"""
plot_layout = pn.layout.Column(plot, date_slider, stylesheets=[map_css])

flex_css = """
@media screen and (max-width: 1200px) {
  div[id^="flexbox"] {
    flex-flow: column !important;
  }
}
"""
layout = pn.layout.FlexBox(plot_layout, quake_table, stylesheets=[flex_css])

template = pn.template.MaterialTemplate(
    site="",
    title="Earthquakes in Nepal",
    sidebar=[],
    main=[layout],
)
template.servable()
