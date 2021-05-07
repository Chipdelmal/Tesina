'''
Download ffmpeg https://github.com/BtbN/FFmpeg-Builds/releases

'''


import time
import _pickle as cPickle
import geopandas as gpd
import pandas as pd
from pyproj import  CRS
import bz2
from shapely.geometry import Point, Polygon
import math
import ffmpeg
import matplotlib.pyplot as plt
from os import path
import subprocess
import os


### VARIABLES ###
SHAPEFILE = "./shapefile/stp_gc_adg.shp"
POPULATIONS = "populations.csv"
CLUSTERS = "clusters.bz"
FRAMES_FOLDER = 'frames'
GENERATED_FRAMES = "./" + FRAMES_FOLDER +  "/"
SIM_URL = "./sim/E_0025000000_03_0000000000_0000000000_0000000000-HLT_0"
FILE_TYPE = "_sum.bz"
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
### PREPARE DATA####
crs = CRS('EPSG:4326')
centroids = []
coords = []
id = 1
file = 0

for cluster in clusters:
  
  if(file < 10):
    numFile = "0" + str(file)
  with bz2.open(SIM_URL + numFile + FILE_TYPE, "rb") as f:
      # Decompress data from file
      content = f.read()
  clusterProportion = cPickle.loads(content)
  file += 1

  days = len(clusterProportion.get("population"))
  
  arrH = []
  arrO = []
  arrP = []
  propH = 0
  propO = 0
  propP = 0
  
  for i in range(len(clusterProportion.get("population"))):
    propH = clusterProportion.get("population")[i][0] / clusterProportion.get("population")[i][2]
    propO = clusterProportion.get("population")[i][1] / clusterProportion.get("population")[i][2]
    propP = clusterProportion.get("population")[i][2]
    if propH < 0.3:
      propH = 0.3
    elif propH > 0.7:
      propH = 0.7

    if propO < 0.3:
      propO = 0.3
    elif propO > 0.7:
      propO = 0.7

    arrH.append(propH)
    arrO.append(propO)
    arrP.append(propP)

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
  coord = [id,centroidLon, centroidLat,pop,arrH,arrO,arrP]
  
  point = Point(centroidLon, centroidLat)
 
  centroids.append(point)
  coords.append(coord)
  id+=1

columns = ["id","lon", "lat", "popul", "propH", "propO","propP"]
df = pd.DataFrame(data=coords, columns=columns)
geo_centroids = gpd.GeoDataFrame(df, crs=crs, geometry=centroids)

#######################################
### PLOT ANIMATION MAP OF CLUSTERS ####

if not os.path.exists(FRAMES_FOLDER):
    os.makedirs(FRAMES_FOLDER)
fig, ax = plt.subplots(figsize=(15,15))
time_text = ax.text(7.2, 0.1,'0', fontsize=20)
aux = "000"

#Generate frames
for i in range(300):
  if(i > 9 and i < 100):
    aux = "00"
  elif(i > 99 and i < 1000):
    aux = "0"
  elif(i > 999):
    aux = ""
  name = "frame" + aux + str(i) + ".jpg"

  if(not path.exists(GENERATED_FRAMES + name)):
    map_shape.plot(ax = ax, alpha= 0.4, figsize=(20,15), edgecolor="gray", facecolor="white")
    s = [math.log2(geo_centroids.iloc[n].popul)*20 for n in range(len(geo_centroids))]
    colorsH = [[0.4, 0.2, 0.5, geo_centroids.iloc[n].propH[i]] for n in range(len(geo_centroids))]
    colorsO = [[0.8, 0.2, 0.5, geo_centroids.iloc[n].propO[i]] for n in range(len(geo_centroids))]

    geo_centroids.plot(ax = ax, markersize=s, c=colorsH, marker='H', label="Cluster")
    geo_centroids.plot(ax = ax, markersize=s, c=colorsO, marker='H', label="Cluster")
    time_text.set_text('Day: ' + str(i+1) )
    
    fig.savefig(GENERATED_FRAMES + name)

#Generate video
subprocess.call('ffmpeg -framerate 25 -i ' + GENERATED_FRAMES + 'frame%04d.jpg output.mp4', shell=True)
