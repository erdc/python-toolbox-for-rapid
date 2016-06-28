'''-------------------------------------------------------------------------------
 Tool Name:   CreateMuskingumXfile
 Source Name: CreateMuskingumXfile.py
 Version:     ArcGIS 10.3
 License:     Apache 2.0
 Author:      Andrew Dohmann and Alan Snow
 Updated by:  Andrew Dohmann
 Description: Produces 
 History:     Initial coding - 06/27/2016, version 1.0
 Updated:     Version 1.1, 06/27/2016, initial coding
-------------------------------------------------------------------------------'''
import arcpy
import csv
import os
import time

class CreateMuskingumXfile(object):
    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "Create Muskingum X file"
        self.description = ("Creates the Muskingum X file for RAPID")
        self.canRunInBackground = False
        self.category = "Calibration"

    def getParameterInfo(self):
        """Define parameter definitions"""
        rapid_out_folder = arcpy.Parameter(name = 'RAPID Output Folder',
                                           displayName = 'rapid_out_folder',
                                           datatype = 'DEFolder',
                                           parameterType = 'Required',
                                           direction = 'Input')
                                            
        input_Drainage_Lines = arcpy.Parameter(name="input_Drainage_Lines",
                                         displayName="Input Drainage Lines",
                                         direction="Input",
                                         parameterType="Required",
                                         datatype="GPFeatureLayer")
        input_Drainage_Lines.filter.list = ['Polyline']

        Default_x = arcpy.Parameter(name="Default_x",
                                    displayName="Default x value",
                                    direction="Input",
                                    parameterType="Required",
                                    datatype="GPDouble")
        Default_x.value = "0.3"
         
        Input_Reservoir = arcpy.Parameter(name = 'Reservoir Input',
                                           displayName = 'Input_Reservoirs',
                                           datatype = 'GPFeatureLayer',
                                           parameterType = 'Optional',
                                           direction = 'Input')
        Input_Reservoir.filter.list = ['Polygon']

        params = [rapid_out_folder, 
                  input_Drainage_Lines, 
                  Default_x, 
                  Input_Reservoir]

        return params

    def isLicensed(self):
        """Set whether tool is licensed to execute."""
        return True

    def updateParameters(self, parameters):
        """Modify the values and properties of parameters before internal
        validation is performed.  This method is called whenever a parameter
        has been changed."""

    def updateMessages(self, parameters):
        """Modify the messages created by internal validation for each tool
        parameter.  This method is called after internal validation."""
        return

    def execute(self, parameters, messages):
        """The source code of the tool."""
        
        rapid_out_folder = parameters[0].valueAsText
        Drainage_Lines = parameters[1].valueAsText
        Default_x = parameters[2].valueAsText
        Input_Reservoir = parameters[3].valueAsText

        # Process: Muskingum x  
        #check to see if a Muskingum x already exists
        fieldList = arcpy.ListFields(Drainage_Lines, "Musk_x")
        fieldCount = len(fieldList)
        if (fieldCount >= 1):
            date = time.strftime("%m_%d_%Y")
            Musk_x = "Musk_x_%s" %date
        else:
            Musk_x = "Musk_x"
        
        if Input_Reservoir:
            #Determine if drainageline intersects rservoir
            #create feature class where reservoirs and drainagelines intersect #"in_memory"
            Reservoir_Drainagelines = os.path.join(os.path.dirname(Drainage_Lines), "Reservoir_Drainagelines")
            inFeatures = [Drainage_Lines, Input_Reservoir]
            arcpy.Intersect_analysis(in_features=inFeatures, out_feature_class=Reservoir_Drainagelines, join_attributes="ALL", cluster_tolerance="-1 Unknown", output_type="INPUT")
            arcpy.AddField_management(Reservoir_Drainagelines, Musk_x, "DOUBLE", "", "", "", "", "NULLABLE", "NON_REQUIRED", "")
            #field "Musk_x" set to 0.0 if drainageline intersects with reservoir
            arcpy.CalculateField_management(Reservoir_Drainagelines, Musk_x, "0.0", "PYTHON", "")
            arcpy.JoinField_management(Drainage_Lines, "HydroID", Reservoir_Drainagelines, "HydroID", Musk_x)
            #changes muckingum x to Default_x if musk_x = null
            with arcpy.da.UpdateCursor(Drainage_Lines,
                                       [Musk_x]) as cursor:
                for row in cursor:
                    if row[0] != 0.0:
                        row[0] = Default_x
                        cursor.updateRow(row)
            
            # Delete cursor and row objects to remove locks on the data
            del row
            del cursor
                    
            # deletes Intersect with Drainage Line and Reservoir
            arcpy.Delete_management(Reservoir_Drainagelines)
        else:
            #Add default field to file
            arcpy.AddField_management(Drainage_Lines, Musk_x, "DOUBLE", "", "", "", "", "NULLABLE", "NON_REQUIRED", "")
            arcpy.CalculateField_management(Drainage_Lines, Musk_x, Default_x, "PYTHON", "")
        
        #generate file 
        out_muskingum_x_file = os.path.join(rapid_out_folder, "x.csv")
        ##make a list of all of the fields in the table
        field_names = ['HydroID', Musk_x]
        with open(out_muskingum_x_file,'wb') as csvfile:
            connectwriter = csv.writer(csvfile, dialect='excel')
            for row in sorted(arcpy.da.SearchCursor(Drainage_Lines, field_names)):
                connectwriter.writerow([row[1]])

        
        return