'''-------------------------------------------------------------------------------
 Tool Name:   HydroSHEDStoStreamNetwork
 Source Name: HydroSHEDStoStreamNetwork.py
 Version:     ArcGIS 10.3
 License:     Apache 2.0
 Author:      Andrew Dohmann
 Updated by:  Andrew Dohmann
 Description: Produces 
 History:     Initial coding - 06/17/2016, version 1.0
 Updated:     Version 1.1, 06/20/2016, initial coding
-------------------------------------------------------------------------------'''
import ArcHydroTools
import arcpy
import os

class HydroSHEDStoStreamNetwork(object):
    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "HydroSHEDS to Stream Network"
        self.description = ("Processes DEM data to stream network")
        self.canRunInBackground = False
        self.category = "Workflows"

    def getParameterInfo(self):
        """Define parameter definitions"""
        File_GDB_Name = arcpy.Parameter(name="File_GDB_Name",
                                        displayName="File Geodatabase Name",
                                        direction="Input",
                                        parameterType="Required",
                                        datatype="GPString")

        File_GDB_Location = arcpy.Parameter(name="File_GDB_Location",
                                            displayName="File Geodatabase Location",
                                            direction="Input",
                                            parameterType="Required",
                                            datatype="DEFolder")
                                            
        Watershed_Boundary = arcpy.Parameter(name="Watershed_Boundary",
                                            displayName="Watershed Boundary",
                                            direction="Input",
                                            parameterType="Required",
                                            datatype="DEFeatureClass")

        Number_of_cells_to_define_stream = arcpy.Parameter(name="Number_of_cells_to_define_stream",
                                                           displayName="Number of cells to define stream",
                                                           direction="Input",
                                                           parameterType="Required",
                                                           datatype="GPLong")

        Output_Coordinate_System = arcpy.Parameter(name="Output_Coordinate_System",
                                                   displayName="Output Projected Coordinate System",
                                                   direction="Input",
                                                   parameterType="Required",
                                                   datatype="GPCoordinateSystem")
                                                   
        #SET DEFAULT TO EQUIDISTAN PROJECTION BECAUSE WE USE IT TO GET LENGTH/SLOPE                                           
        Output_Coordinate_System.value = "PROJCS['World_Equidistant_Cylindrical',GEOGCS['GCS_WGS_1984'" \
                                         ",DATUM['D_WGS_1984',SPHEROID['WGS_1984',6378137.0,298.257223563]]" \
                                         ",PRIMEM['Greenwich',0.0],UNIT['Degree',0.0174532925199433]]" \
                                         ",PROJECTION['Equidistant_Cylindrical'],PARAMETER['False_Easting',0.0]" \
                                         ",PARAMETER['False_Northing',0.0],PARAMETER['Central_Meridian',0.0]" \
                                         ",PARAMETER['Standard_Parallel_1',60.0],UNIT['Meter',1.0]]"
                                                           
        Input_DEM_Rasters = arcpy.Parameter(name="Input_DEM",
                                            displayName="Input DEM rasters",
                                            direction="Input",
                                            parameterType="Required",
                                            datatype="DERasterDataset",
                                            multiValue=True)

        Watershed_Flow_Direction_Rasters = arcpy.Parameter(name="Watershed_Flow_Direction_Rasters",
                                                           displayName="Watershed flow direction rasters",
                                                           direction="Input",
                                                           parameterType="Optional",
                                                           datatype="DERasterDataset",
                                                           multiValue=True)
                                                          
        params = [File_GDB_Name, File_GDB_Location, Watershed_Boundary,
                  Number_of_cells_to_define_stream, Output_Coordinate_System,
                  Input_DEM_Rasters, Watershed_Flow_Direction_Rasters]

        return params

    def isLicensed(self):
        """Set whether tool is licensed to execute."""
        return True

    def updateParameters(self, parameters):
        """Modify the values and properties of parameters before internal
        validation is performed.  This method is called whenever a parameter
        has been changed."""
        if parameters[0].altered:
            if not parameters[0].valueAsText.endswith(".gdb"):
                parameters[0].value = "{0}.gdb".format(parameters[0].valueAsText)
        return

    def updateMessages(self, parameters):
        """Modify the messages created by internal validation for each tool
        parameter.  This method is called after internal validation."""
        return

    def execute(self, parameters, messages):
        """The source code of the tool."""
        arcpy.env.overwriteOutput = True
        
        File_GDB_Name = parameters[0].valueAsText
        File_GDB_Location = parameters[1].valueAsText
        Watershed_Boundary = parameters[2].valueAsText
        Number_of_cells_to_define_stream = parameters[3].valueAsText
        Output_Coordinate_System = parameters[4].valueAsText
        Input_DEM_Rasters = parameters[5].valueAsText
        Watershed_Flow_Direction_Rasters = parameters[6].valueAsText        

        # Local variables:
        Path_to_GDB = os.path.join(File_GDB_Location, File_GDB_Name)
        Dataset = "Layers"
        Path_to_GDB_dataset = os.path.join(Path_to_GDB, Dataset)

        Coordinate_System = "GEOGCS['GCS_WGS_1984',DATUM['D_WGS_1984'," \
                            "SPHEROID['WGS_1984',6378137.0,298.257223563]]," \
                            "PRIMEM['Greenwich',0.0],UNIT['Degree',0.0174532925199433]];" \
                            "-400 -400 1000000000;-100000 10000;-100000 10000;" \
                            "8.98315284119522E-09;0.001;0.001;IsHighPrecision"
                            
        Buffer_Distance = "20 Kilometers"
        Watershed_Buffer = os.path.join(Path_to_GDB_dataset, "Watershed_Buffer")
        Output_Mosaic_Elevation_DEM = os.path.join(Path_to_GDB, "Mosaic_Elevation_DEM")
        Output_Elevation_DEM = os.path.join(Path_to_GDB, "Elevation_DEM")
        Output_Mosiac_Flow_Direction_Raster = os.path.join(Path_to_GDB, "Mosaic_Flow_Direction")
        Output_Flow_Direction_Raster = os.path.join(Path_to_GDB, "Flow_Direction")
        
        # Process: Create File GDB
        arcpy.CreateFileGDB_management(File_GDB_Location, File_GDB_Name, "CURRENT")

        # Process: Create Feature Dataset
        arcpy.CreateFeatureDataset_management(Path_to_GDB, Dataset, Coordinate_System)

        # Process: Buffer
        arcpy.Buffer_analysis(Watershed_Boundary, Watershed_Buffer, Buffer_Distance, 
                              "FULL", "ROUND", "NONE", "", "PLANAR")

        # Process: Mosaic To New Raster for DEM
        arcpy.MosaicToNewRaster_management(Input_DEM_Rasters, Path_to_GDB, "Mosaic_Elevation_DEM",
                                           "", "16_BIT_SIGNED", "", "1", "LAST", "FIRST")

        # Process: Extract by Mask for DEM
        arcpy.gp.ExtractByMask_sa(Output_Mosaic_Elevation_DEM, Watershed_Buffer, Output_Elevation_DEM)
        arcpy.Delete_management(Output_Mosaic_Elevation_DEM)

        if Watershed_Flow_Direction_Rasters:
            # Process: Mosaic To New Raster for Flow Direction
            arcpy.MosaicToNewRaster_management(Watershed_Flow_Direction_Rasters, Path_to_GDB, "Mosaic_Flow_Direction", 
                                               "", "16_BIT_SIGNED", "", "1", "LAST", "FIRST")

            # Process: Extract by Mask for Flow Direction
            arcpy.gp.ExtractByMask_sa(Output_Mosiac_Flow_Direction_Raster, Watershed_Buffer, Output_Flow_Direction_Raster)
            arcpy.Delete_management(Output_Mosiac_Flow_Direction_Raster)
        else:
            #generate flow direction raster
            ArcHydroTools.FlowDirection(Output_Elevation_DEM, Output_Flow_Direction_Raster)
        
        # Process: Flow Accumulation
        Output_Flow_Accumulation_Raster = os.path.join(Path_to_GDB, "Flow_Accumulation")
        ArcHydroTools.FlowAccumulation(Output_Flow_Direction_Raster, Output_Flow_Accumulation_Raster)

        # Process: Stream Definition
        Output_Str_Raster = os.path.join(Path_to_GDB, "Str")
        ArcHydroTools.StreamDefinition(Output_Flow_Accumulation_Raster, Number_of_cells_to_define_stream, Output_Str_Raster)
        
        # Process: Stream Segmentation
        Output_StrLnk_Raster = os.path.join(Path_to_GDB, "StrLnk")
        ArcHydroTools.StreamSegmentation(Output_Str_Raster, Output_Flow_Direction_Raster, Output_StrLnk_Raster)
        
        # Process: Catchment Grid Delineation
        Output_Cat = os.path.join(Path_to_GDB, "Cat")
        ArcHydroTools.CatchmentGridDelineation(Output_Flow_Direction_Raster, Output_StrLnk_Raster, Output_Cat)

        # Process: Catchment Polygon Processing
        Output_Catchment = os.path.join(Path_to_GDB_dataset, "Catchment")        
        ArcHydroTools.CatchmentPolyProcessing(Output_Cat, Output_Catchment)

        # Process: Drainage Line Processing
        Output_DrainageLine = os.path.join(Path_to_GDB_dataset, "DrainageLine")
        ArcHydroTools.DrainageLineProcessing(Output_StrLnk_Raster, Output_Flow_Direction_Raster, Output_DrainageLine)

        # Process: Add DrainLnID to Catchment
        arcpy.AddField_management(Output_Catchment, "DrainLnID", "LONG", "", "", "", "", "NULLABLE", "NON_REQUIRED", "")
        arcpy.JoinField_management(Output_Catchment, "HydroID", Output_DrainageLine, "GridID", "HydroID")
        arcpy.CalculateField_management(Output_Catchment, "DrainLnID", "[HydroID_1]", "VB", "")
        arcpy.DeleteField_management(Output_Catchment, "HydroID_1")
        
        # Process: Adjoint Catchment Processing
##        Output_Adjoint_Catchment = os.path.join(Path_to_GDB_dataset, "AdjointCatchment")        
##        ArcHydroTools.AdjointCatchment(Output_DrainageLine, Output_Catchment, Output_Adjoint_Catchment)

        # Process: Project
        Output_Projected_DrainageLine = os.path.join(Path_to_GDB, "Proj_DrainageLine")        
        arcpy.Project_management(Output_DrainageLine, Output_Projected_DrainageLine, Output_Coordinate_System)
        
        # Process: Add Surface Information
        arcpy.CheckOutExtension("3D")
        arcpy.AddSurfaceInformation_3d(Output_Projected_DrainageLine,Output_Elevation_DEM, "SURFACE_LENGTH;AVG_SLOPE")
        
        #CLEANUP
        arcpy.Delete_management(Output_DrainageLine)
        arcpy.Project_management(Output_Projected_DrainageLine, Output_DrainageLine, Coordinate_System)
        arcpy.Delete_management(Output_Projected_DrainageLine)
        arcpy.Delete_management(Watershed_Buffer)
        
        return