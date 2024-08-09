from datetime import date

import geopandas as gpd
import pandas as pd
from pandas.tseries.offsets import DateOffset


def parse_seismo_data(csv_file):
    quakes = pd.read_csv(csv_file, usecols=[0, 1, 2, 3, 4])

    quakes["datetime"] = pd.to_datetime(
        quakes["Date"] + " " + quakes["Time"], format="mixed", dayfirst=True
    )
    quakes = quakes.drop(columns=["Date", "Time"])

    last_5_years = quakes["datetime"] >= (date.today() + DateOffset(years=-5))
    quakes = quakes[last_5_years]
    quakes = gpd.GeoDataFrame(
        quakes, geometry=gpd.points_from_xy(quakes["Longitude"], quakes["Latitude"])
    )
    return quakes


def parse_usgs_data(csv_file, nepal_bounds):
    quakes = pd.read_csv(
        csv_file,
        parse_dates=["time"],
        dtype={
            "latitude": "float32",
            "longitude": "float32",
            "depth": "float32",
            "mag": "float32",
        },
    )

    quakes = gpd.GeoDataFrame(
        quakes,
        geometry=gpd.points_from_xy(quakes["longitude"], quakes["latitude"]),
        crs=nepal.crs,
    )

    # nepal's borders
    quakes = quakes[quakes.within(nepal_bounds.loc[0, "geometry"])]
    return (
        quakes.set_index(pd.DatetimeIndex(quakes["time"]))
        .drop(columns="time")
        .sort_index()
    )


if __name__ == "__main__":
    nepal = gpd.read_parquet("data/nepal.parq")
    nepal_bounds = nepal.dissolve()

    quakes = parse_usgs_data("data/quakes-usgs.csv", nepal_bounds)
    quakes.to_parquet("data/quakes.parq")
