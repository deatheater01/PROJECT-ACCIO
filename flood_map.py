#Import required ArcGis and ArcPy modules
import arcpy, arcinfo
import os
import glob
import arcgisscripting
import urllib

from arcpy import env
from arcpy.sa import *

# Set your workspace
arcpy.env.workspace = r"C:\DisasterMapping\FAULT "

# Check requirements
arcpy.CheckOutExtension("spatial")
arcpy.CheckOutExtension("3D")

#Turn on Overwrite
arcpy.env.overwriteOutput = True

folderName = "Result1"
path = arcpy.env.workspace + "\\" + folderName

def makeFolder (folderName, path):
    path = arcpy.env.workspace + "\\" + folderName
    if os.path.exists(path):
        folderName = raw_input("Please choose a name: ")
        path = arcpy.env.workspace + "\\" + folderName
        makeFolder(folderName, path)
        
    else:  
        os.mkdir(path, 0777)
        print "Folder \"%s\" created." %folderName

makeFolder(folderName, path)

All_Infrastructures = arcpy.env.workspace + "\Local_Variables" + r"\All_Infrastructures.shp"
#NLCD to be updated to Dec 2018 edition once it's compiled
NLCD_2016 = arcpy.env.workspace + "\Local_Variables" + r"\nlcd_2016_landcover_2016_edition_2017_10_10.img"          
Lspop2014 = arcpy.env.workspace + "\Local_Variables" + r"\Lspop2014"
WaterMask_tif = arcpy.env.workspace + "\Local_Variables" + r"\WaterMask.tif"
NDWI_SignatureFile = arcpy.env.workspace + "\Local_Variables" + r"\ndwi_sigfil.gsg"
print "Setting Outputs..."
mosaic_b3 = arcpy.env.workspace + "\mosaic_b3.tif"
mosaic_b5 = arcpy.env.workspace + "\mosaic_b5.tif"
mosaic_b9 = arcpy.env.workspace + "\mosaic_b9.tif"
CloudMask = arcpy.env.workspace + "\CloudMask"
C3 = arcpy.env.workspace + "\C3"
C5 = arcpy.env.workspace + "\C5"
TOA_mosaic_b3 = arcpy.env.workspace + "\TOA_mosaic_b3"
TOA_mosaic_b5 = arcpy.env.workspace + "\TOA_mosaic_b5"
B3 = arcpy.env.workspace + "\B3"
B5 = arcpy.env.workspace + "\B5"
NDWI = arcpy.env.workspace + "\NDWI"
MLClass_NDWI = arcpy.env.workspace + "\MLClass_NDWI.tif"
Output_confidence_raster = ""
WaterMaskClip_tif = path + "\\" + "WaterMaskClip.tif"
Reclass_watermask_tif = arcpy.env.workspace + "\Reclass_watermask.tif"
Reclass_MLClass_NDWI_tif = arcpy.env.workspace + "\Reclass_MLClass_NDWI.tif"
NDWI_Extracted_WMask_tif = arcpy.env.workspace + "\NDiWI_Extracted_WMask.tif"
Flood_Water_tif = path + "\\" + "Flood_Water.tif"
Landscan_Clp = arcpy.env.workspace + "\Landscan_Clp"
FloodMap_ExtentPolygon_shp = arcpy.env.workspace + "\FloodMap_ExtentPolygon.shp"
NLCD_Clp = arcpy.env.workspace + "\NLCD_Clp"
NLCD_Ag_Clp = arcpy.env.workspace + "\\" + "\NLCD_Ag_Clp"
Flooded_Lscan = path + "\\" + "Flooded_Lscan"
Flooded_Ag = path + "\\" + "Flooded_Ag"
Infra_Feature = arcpy.env.workspace + "\Infra_Feature"
Flooded_Infra = path + "\\" + "Flooded_Infra"
Infrastructure_Clp_shp = arcpy.env.workspace + "\\" + "\Infrastructure_Clp.shp"


#The segment below is where you specify the region. The input is to be modified in the code itself in the "..." below. Please refer LansatProductIdentifier image in the project 
Band3 = glob.glob(arcpy.env.workspace + r"\LC80*\*B3.tif")
Band5 = glob.glob(arcpy.env.workspace + r"\LC80*\*B5.tif")
Band9 = glob.glob(arcpy.env.workspace + r"\LC80*\*B9.tif")

for mosaic3 in iter(Band3):
    band = mosaic3[-5]
    print " "
    print "Mosaicking band 3..."
    
    arcpy.MosaicToNewRaster_management(Band3, arcpy.env.workspace, "mosaic_b" + band + ".tif", "#", "16_BIT_UNSIGNED", "#", "1", "MAXIMUM", "FIRST")
    break

for mosaic5 in iter(Band5):
    band = mosaic5[-5]
    PR = mosaic5[-25:-19]
    print "Mosaicking band 5..."
    
    arcpy.MosaicToNewRaster_management(Band5, arcpy.env.workspace, "mosaic_b" + band + ".tif", "#", "16_BIT_UNSIGNED", "#", "1", "MAXIMUM", "FIRST")
    break

for mosaic5 in iter(Band5):
    print "Mosaicking band 9..."
    print " "
    arcpy.MosaicToNewRaster_management(Band9, arcpy.env.workspace, "mosaic_b9.tif", "#", "16_BIT_UNSIGNED", "#", "1", "MAXIMUM", "FIRST")
    break

print "Reclassifying B9..."

arcpy.gp.Reclassify_sa(mosaic_b9, "Value", "0 1;0 5325 1", CloudMask, "NODATA")

print "Extracting Clouds from B3..."
arcpy.gp.ExtractByMask_sa(mosaic_b3, CloudMask, C3)

print "Extracting Clouds from B5..."
arcpy.gp.ExtractByMask_sa(mosaic_b5, CloudMask, C5)

print "Converting B3 to TOA..."
arcpy.gp.RasterCalculator_sa("\"C3\" * (2.0000E-5) + (-0.10000)", TOA_mosaic_b3)
                             
print "Removing negative values TOA B3..."
arcpy.gp.RasterCalculator_sa("Con(\"TOA_mosaic_b3\" < 0,0,\"TOA_mosaic_b3\")", B3)

print "Converting B5 to TOA..."                             
arcpy.gp.RasterCalculator_sa("\"C5\" * (2.0000E-5) + (-0.10000)", TOA_mosaic_b5)

print "Removing negative values TOA B5..."
arcpy.gp.RasterCalculator_sa("Con(\"TOA_mosaic_b5\" < 0,0,\"TOA_mosaic_b5\")", B5)

print "Performing NDWI..."
arcpy.gp.RasterCalculator_sa("Float(\"B3\" - \"B5\") / Float(\"B3\" + \"B5\")", NDWI)

print " "
print " "
print "Data Processing Complete!"
print " "
print " "

print "Performing Maximum Likelihood Classification..."
print " "
print " "
arcpy.gp.MLClassify_sa(NDWI, NDWI_SignatureFile, MLClass_NDWI, "0.0", "EQUAL", "", Output_confidence_raster)

print "Data Analysis Pt. 1 - Maximum Likelihood Classification Complete!"
print " "
print " "

print "Getting Raster Domain..."
arcpy.RasterDomain_3d(mosaic_b3, FloodMap_ExtentPolygon_shp, "POLYGON")

print "Clipping Water Mask..."
arcpy.gp.ExtractByMask_sa(WaterMask_USA_tif, FloodMap_ExtentPolygon_shp, WaterMaskClip_tif)

print "Reclassifying NDWI Classification..."
arcpy.gp.Reclassify_sa(MLClass_NDWI, "Value", "1 0;1 151 1", Reclass_MLClass_NDWI_tif, "DATA")

print "Reclassifying Water Mask..."
arcpy.gp.Reclassify_sa(path + "\\" + "WaterMaskClip.tif", "Value", "0 NODATA;1 2;2 1", Reclass_watermask_tif, "DATA")

print "Subtracting Water Mask from NDWI Classification..."
arcpy.gp.RasterCalculator_sa("\"Reclass_watermask.tif\" - \"Reclass_MLClass_NDWI.tif\"", NDWI_Extracted_WMask_tif)

print "Identifying Flood Water..."
print " "
print " "
arcpy.gp.Reclassify_sa(NDWI_Extracted_WMask_tif, "Value", "2 1", Flood_Water_tif, "NODATA")

print "Data Analysis Pt. 2 - Flood Extent Map Complete"
print "Your final product 'Flood_Water' is located within %s." %path
print " "
print " "

print "Clipping Landscan..."
arcpy.gp.ExtractByMask_sa(Lspop2014, FloodMap_ExtentPolygon_shp, Landscan_Clp)

print "Extracting Flooded Landscan by water mask..."
arcpy.gp.ExtractByMask_sa(Landscan_Clp, Flood_Water_tif, Flooded_Lscan)

print "Clipping Infrastructures..."
arcpy.Clip_analysis(All_Infrastructures, FloodMap_ExtentPolygon_shp, Infrastructure_Clp_shp, "")

print "Converting Infrastructures from a feature to a raster..."
arcpy.FeatureToRaster_conversion(Infrastructure_Clp_shp, "STRUCTURE", Infra_Feature, "0.002")

print "Extracting Flooded Infrastructure by mask..."
print " "
print " "
arcpy.gp.ExtractByMask_sa(Infra_Feature, Flood_Water_tif, Flooded_Infra)

print "Clipping NLCD..."
arcpy.gp.ExtractByMask_sa(NLCD_2016, FloodMap_ExtentPolygon_shp, NLCD_Clp)

print "Reclassify NLCD data..."
arcpy.gp.Reclassify_sa(NLCD_Clp, "Value", "81 1;82 2", NLCD_Ag_Clp, "NODATA")

print "Extracting Flooded NLCD by water mask..."
arcpy.gp.ExtractByMask_sa(NLCD_Ag_Clp, Flood_Water_tif, Flooded_Ag)


print "Data Analysis Pt. 3 - Flood Impact Map Complete"
print "Results is located within %s." %path

