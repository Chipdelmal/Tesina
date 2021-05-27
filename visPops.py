import pandas as pd
import matplotlib.pyplot as plt
from shapely.geometry import Point, Polygon
import bz2
import _pickle as cPickle
import math
import geopandas as gpd
from pyproj import  CRS

### VARIABLES ###
SHAPEFILE = "./shapefile/stp_gc_adg.shp"
POPULATIONS = "populations.csv"
CLUSTERS = "clusters.bz"

#################
### READ FILES ###
#MAP
map_shape = gpd.read_file(SHAPEFILE)
#POPULATIONS
populations = pd.read_csv(POPULATIONS) 

#CLUSTERS
with bz2.open(CLUSTERS, "rb") as f:
    # Decompress data from file
    content = f.read()
clusters = cPickle.loads(content)

####################
### PREPARE DATA ###

#Generate dataframe of populations
points = [Point(xy) for xy in zip(populations["lon"], populations["lat"])]
crs = CRS('EPSG:4326')
geo_populations = gpd.GeoDataFrame(populations, crs=crs, geometry=points)

centroids = []
coordinates = []
id = 0

for cluster in clusters:
  acumLon = 0
  acumLat = 0
  pop = 0
  
  for population in cluster:
    point = populations.iloc[population]
    acumLon += point.lon
    acumLat += point.lat
    pop += point["pop"]
  
  centroidLon=acumLon/len(cluster)
  centroidLat=acumLat/len(cluster)
  coordinate = [id,centroidLon, centroidLat,pop]
  point = Point(centroidLon, centroidLat)
  centroids.append(point)
  coordinates.append(coordinate)
  id+=1

#Generate dataframe of clusters
columns = ["id","lon", "lat", "population"]
df = pd.DataFrame(data=coordinates, columns=columns)
geo_centroids = gpd.GeoDataFrame(df, crs=crs, geometry=centroids)

### PLOT MAP OF POPULATIONS AND CLUSTERS ###
fig, ax = plt.subplots(figsize=(15,15))
map_shape.plot(ax = ax, alpha= 0.4, figsize=(20,15), edgecolor="lightgray", facecolor="lightgray")
geo_populations.plot(ax = ax, markersize=20, color=(0.4, 0.2, 0.5, 0.2), marker="o", label="Population")
pointLabel = 0
for i in range(len(populations)):
  point = populations.iloc[i]
  plt.text(point["lon"], point["lat"], str(pointLabel), color=(0.7, 0.2, 0.5, 0.2), fontsize=6)
  pointLabel += 1
geo_centroids.plot(ax = ax, markersize=60, color="steelblue", marker="X", label="Cluster")

for coordinate in coordinates:
  plt.text(coordinate[1], coordinate[2], coordinate[0], color="black", fontsize=8)



plt.legend(prop={'size': 10}, loc="upper left")
plt.show()
############################################