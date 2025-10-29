##### BEGIN GPL LICENSE BLOCK #####
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software Foundation,
#  Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# ##### END GPL LICENSE BLOCK #####

PMCversion = "2.0.0"

#   #   #   #   #   #   #   #   #   #
#     Global Variables & Modules    #
#   #   #   #   #   #   #   #   #   #

#   Import modules  #
import maya.cmds as mc
import maya.utils
import functools
import os, sys, copy
import json

try:
    from importlib import reload
except:
    pass


# ==================================================================================================

# load required plugins

def load_plugins(plugins):
    '''load plugins'''
    
    for plugin in plugins:
        if not mc.pluginInfo(plugin, q=1, l=1):
            try:
                mc.loadPlugin(plugin)
                mc.refresh(force=True)
                
            except:
                print("ERROR - could not load plugin :", plugin)


load_plugins(
    ['dx11Shader', 'shaderFXPlugin', 'fbxmaya', 'lookdevKit']
)


# ==================================================================================================

# new material setup functions

from .material import (
    arnold_material,
    octane_material,
    redshift_material,
    vray_material,
)

reload(arnold_material)
reload(octane_material)
reload(redshift_material)
reload(vray_material)

# ==================================================================================================

#   Global variables    #
internal =  False # Set True to run the internal version
SupportedEngines = {
    'Arnold':"arnold",
    # 'Mental Ray':"mentalray",
    'OctaneRender':"OctaneRender",
    'Redshift':"redshift",
    'V-Ray':"vray",
    # 'RenderMan':"renderManRIS"
}
EnginePlugins = {
    "Arnold": "mtoa",
    "OctaneRender": "OctanePlugin",
    "Redshift": "redshift4maya",
    "V-Ray": "vrayformaya"
}
mapDict = {}
matsFound = {}
settings = {}
nMats = 0
offset = 0
UVNodes = {}
progressBar = None
MaterialsListUIElements = []
previewImages = {}
settings["Platform"] = sys.platform
settings["MayaVersion"] = int(str(mc.about(v=True)).split(" ")[0])

# Disable material previews on Mac because MAC OS cannot scale images applied to the UI
if settings["Platform"] == 'darwin':
    settings["MaterialPreview"] = False
else:
    settings["MaterialPreview"] = True

# Create these global variables if they don't already exists
try:    MayaDefaultExceptionHook
except: MayaDefaultExceptionHook = maya.utils.formatGuiException

try:    PMC_PreviousPath
except: PMC_PreviousPath = None

try:    ThreadTest
except: ThreadTest = None


#   #   #   #   #   #   #   #   #   #
#           User Interface          #
#   #   #   #   #   #   #   #   #   #

# Create the window
def createUI():

    # Toggle our custom exception hook on
    TogglePMCExceptionHook(True)

    global settings, SupportedEngines

    if internal:
        global LightSetups
        global lightsetup
        windowID = "Internal Poliigon Material Converter (v"+str(PMCversion)+")"
    else:
        windowID = "Poliigon Material Converter (v"+str(PMCversion)+")"
    
    # Delete window if it already exists
    pID = windowID.replace(" ","_").replace("(","_").replace(".","_").replace(")","_")
    if mc.window(pID,q=True, exists=True):
        mc.deleteUI(pID)

    # Create the window
    window = mc.window(windowID, title=windowID, sizeable=False, mxb=False, rtf=False, width=300, h=470)

    #   -   -   -   UI Elements  -   -   -   #

    form = mc.formLayout(numberOfDivisions=100)
    #if settings["MayaVersion"] >= 2019:
    #    LFolderpathRow = mc.rowColumnLayout(adjustableColumn=1, numberOfColumns=4)
    #else:
    LFolderpathRow = mc.rowLayout(numberOfColumns=4, columnWidth3=(80, 75, 150), adjustableColumn=1, p=form, width=280)


    # Folder path
    if internal:
        rootSearch = mc.checkBox("root_search", label='Textures are located in a subfolder named "Generic_Files"', value=True, cc=functools.partial(InternalCheckboxUpdate, "Generic_Files"),p=form)
        settings["ROOT"] = rootSearch
    #    folderpathWidth = 175
    #else:
    #    folderpathWidth = 100

    folderpath = mc.textField('PMCfolderpath', width=100,height=25, bgc=[0.23,0.23,0.23], cc=updateFolderPath)


    # Use diffrent refresh icons depending on what maya version the user is running
    if settings["MayaVersion"] >= 2017:
        refrsh_icon = "QR_refresh.png"
    else:
        refrsh_icon = "clockwise.png"

    # Folderpath Buttons
    button_Tex = mc.iconTextButton( style='iconOnly', image1='fileOpen.png',ann="Open the file browser", width=22, height=22, bgc=[0.35,0.35,0.35], label='', command=functools.partial(texturesFolder, None), p=LFolderpathRow)
    button_reloadFolder = mc.iconTextButton( style='iconOnly', image1=refrsh_icon, ann="Refresh the selected folder", width=22, height=22, bgc=[0.35,0.35,0.35], label='', command=functools.partial(updateFolderPath, None), enable=False, p=LFolderpathRow)
    button_setDefDirLoc = mc.iconTextButton( style='iconOnly', image1='empty.png', ann="Set as the default path for loading materials", width=22, height=22, bgc=[0.35,0.35,0.35], label='', command=functools.partial(DefaultFolderPath, set=True), enable=False, p=LFolderpathRow)

    # Labels under the folderpath
    label_Path = mc.text('filepath', fn="smallObliqueLabelFont", align="left", label='Choose the root folder where the textures are stored. If multiple\ntexture sets are detected this script will auto-load those as well.', p=form)
    label_Mats = mc.text('foundT', label='', p=form)

    # Renderer
    renderer = mc.optionMenu(label='Renderer:', p=form, changeCommand=loadEngine)
    
    for engine in sorted(list(SupportedEngines.keys())) :
        mc.menuItem(engine.replace("-","")+"_mi", label=engine)

    # Batch All renderers option
    if internal:
        ball = mc.checkBox("use_all", label='All renderers', value=False, cc=functools.partial(InternalCheckboxUpdate, "All_Renderers"), p=form)

        # Light Setups
        lightsetup = mc.optionMenu(label='Light Setup', p=form)
        for setup in LightSetups:
            mc.menuItem(label=setup)
        open_folder = mc.iconTextButton( style='iconOnly', image1='fileOpen.png', width=19, height=19, command="os.startfile(os.path.join(mc.internalVar(usd=True), 'poliigon_material_converter', 'light_setups'))", bgc=[0.35,0.35,0.35], p=form)

    # Materials List
    SelectAll = mc.checkBox("PMC_select_all", label='Select All', value=False, enable=False, cc=functools.partial(PMC_SelectAllMaterials), p=form)

    paneLayout = mc.paneLayout( configuration='horizontal2', ps=[1,1,1], p=form)
    scrollLay = mc.scrollLayout("MaterialListScrollLayout", horizontalScrollBarThickness=0, verticalScrollBarThickness=0, width=200, height=80, backgroundColor=[0.2,0.2,0.2], p=paneLayout)
    form2 = mc.formLayout("MaterialsListForm",p=paneLayout, width=205, height=70)
    MaterialHelp = mc.text(label='Click on a material to select it', align="left", width=182, visible=False)
    MaterialName = mc.text(label='', align="left", width=182)#, fn="boldLabelFont")
    MaterialInfo = mc.text(label='', wordWrap=True, height=20, align="left", fn="smallObliqueLabelFont", width=182)
    button_browseTexture = mc.iconTextButton(style='iconOnly', image='search.png',ann="Browse for this material on Poliigon.com", enable=False, width=22, height=22, bgc=[0.35,0.35,0.35], label='', command=browseMissingMats)
    button_materialPreview = mc.symbolCheckBox(image='out_lambert.png',ann="Toggle on/off the preview icon", enable=False, value=settings["MaterialPreview"], width=22, height=22, bgc=[0.35,0.35,0.35], cc=PMC_ToggleMaterialPreview)
    Material_Icon = mc.iconTextStaticLabel(w=35, h=35, st='iconOnly', image='help.png', visible=False)
    #Material_ShaderPreview = mc.swatchDisplayPort(wh=(35, 35), visible=False, enable=False, rs=35, bgc=[0,0,0])

    MaterialsListLayout = mc.rowColumnLayout(numberOfColumns=1, p=scrollLay)


    # Advanced settings
    Advanced_Settings = mc.frameLayout(label='Advanced Settings', cll=True,cl=True, p=form2)
    Advanced_Settings_col = mc.columnLayout(rs=2, width=100, height=115,p=Advanced_Settings)
    if internal:
        AskName = mc.checkBox("ask_name", label='Ask for scene name', value=False)
        rewriteAscii = mc.checkBox("rewriteAscii", label='Rewrite ascii file',ann="Will rewrite the ascii file to not include e.g. Octane settings if Octane is not the selected renderer.", value=True)
    useAO = mc.checkBox("use_ao", label='Include Ambient Occlusion (AO) maps (if available)', value=True)
    useDISP = mc.checkBox("use_disp", label='Include Displacement maps (if available)', value=True)
    useBIT = mc.checkBox("use_16bit", label='Use 16 bit maps (if available)', value=True)
    useCONF = mc.checkBox("use_conform", label='Conform UV maps to image dimensions', value=False)
    usePREV = mc.checkBox("use_peview", label='Apply materials to preview spheres', value=False)


    # Convert & Apply Buttons
    button_Convert = mc.button(label="Load 0 Materials", command=convert, h=45, enable=False, p=form)
    button_applyMaterial = mc.button(label="Apply/Replace Selected Material",ann="Apply the selected material to the selected objects in the scene.",command=PMC_ApplyMaterialToSelectedObject, h=30, enable=False, p=form)


    # Save some UI Elements in a dict, if they need to be accessed later on.
    settings["folderpath"] = folderpath
    settings["button_reloadFolder"] = button_reloadFolder
    settings["button_setDefDirLoc"] = button_setDefDirLoc
    settings["label_Path"] = label_Path
    settings["label_Mats"] = label_Mats
    settings["renderer"] = renderer
    settings["SelectAll"] = SelectAll
    settings["button_applyMaterial"] = button_applyMaterial
    settings["button_Convert"] = button_Convert
    settings["MaterialsListLayout"] = MaterialsListLayout
    settings["MaterialHelp"] = MaterialHelp
    settings["MaterialName"] = MaterialName
    settings["MaterialInfo"] = MaterialInfo
    settings["button_browseTexture"] = button_browseTexture
    settings["button_materialPreview"] = button_materialPreview
    settings["MaterialIcon"] = Material_Icon
    settings["AO"] = useAO
    settings["DISP"] = useDISP
    settings["BIT"] = useBIT
    settings["CONF"]= useCONF
    settings["PREV"] = usePREV
    if internal:
        settings["Ball"] = ball
        settings["ASK_NAME"] = AskName
        settings["rewriteAscii"] = rewriteAscii


    #   -   -   -   Layout  -   -   -   #

    # Layout for the lower pane layout
    mc.formLayout(form2, edit=True, attachForm=[
        (Material_Icon, 'top', 0), (Material_Icon, 'left', 0),
        (MaterialHelp, 'top', 10), (MaterialHelp, 'left', 45),
        (MaterialName, 'top', 0), (MaterialName, 'left', 45),
        (MaterialInfo, 'top', 15), (MaterialInfo, 'left', 45),
        (button_materialPreview, 'top', 5),(button_materialPreview, 'right', 0),
        (button_browseTexture, 'top', 5),(button_browseTexture, 'right', 25),
        (Advanced_Settings, 'top', 45), (Advanced_Settings, 'left', 0),(Advanced_Settings, 'right', 0),
    ])

    if not internal:

        #   Default Layout   #

        window_height = 470
        window_width = 300

        mc.formLayout(form, edit=True, attachForm=[
            (LFolderpathRow, 'top', 15), (LFolderpathRow, 'left', 10), (LFolderpathRow, 'right', 10),

            (label_Path, 'top', 42), (label_Path, 'left', 10),
            (label_Mats, 'top', 50), (label_Mats, 'left', 10),
            (renderer, 'top', 77), (renderer, 'left', 10),
            (SelectAll, 'top', 113), (SelectAll, 'left', 10),
            (paneLayout , 'top', 130), (paneLayout , 'left', 9), (paneLayout , 'right', 9), (paneLayout , 'bottom', 75),

            (button_Convert, 'bottom', 30), (button_Convert, 'left', 0), (button_Convert, 'right', 0),
            (button_applyMaterial, 'bottom', 0), (button_applyMaterial, 'left', 0), (button_applyMaterial, 'right', 0),

        ])
    else:

        #   Internal Layout   #

        window_height = 560
        window_width = 340

        mc.formLayout( form, edit=True, attachForm=[
            (rootSearch, 'top', 10), (rootSearch, 'left', 10),
            (LFolderpathRow, 'top', 35), (LFolderpathRow, 'left', 10), (LFolderpathRow, 'right', 10),
            (label_Path, 'top', 63), (label_Path, 'left', 10),
            (label_Mats, 'top', 70), (label_Mats, 'left', 10),

            (renderer, 'top', 100), (renderer, 'left', 10),
            (ball, 'top', 102), (ball, 'left', 190),
            (lightsetup, 'top', 135), (lightsetup, 'left', 10),
            (open_folder, 'top', 135), (open_folder, 'left', 230),

            (SelectAll, 'top', 173), (SelectAll, 'left', 10),
            (paneLayout , 'top', 190), (paneLayout , 'left', 9), (paneLayout , 'right', 9), (paneLayout , 'bottom', 75),

            (button_Convert, 'bottom', 30), (button_Convert, 'left', 0), (button_Convert, 'right', 0),
            (button_applyMaterial, 'bottom', 0), (button_applyMaterial, 'left', 0), (button_applyMaterial, 'right', 0),
        ])


    #   -   -   -   Post Layout  -   -   -   #

    # Draw the window & rescale it
    mc.showWindow()
    mc.window(window, e=True, wh=(window_width,window_height))
    mc.window(window, e=True, sizeable=True)

    # If the user has a default folder saved, load it
    defaultPath = DefaultFolderPath(q=True)
    if defaultPath != "":
        getTextures(defaultPath)
        DefaultFolderPath(reverse=True)
    else:
        DefaultFolderPath(default=True)
        mc.iconTextButton(settings["button_setDefDirLoc"], e=True, enable=False)

    # Get the active render engine in maya and set it as default
    getEngine()

    # Toggle our custom exception hook off
    TogglePMCExceptionHook(False)


# Load plugin for active render engine, if not already loaded
def loadEngine(engine):
    """load engine plugin if not already"""
    
    if engine in EnginePlugins:
        plugin = EnginePlugins[engine]
        
        load_plugins([plugin])


# Get the active render engine and set it as default in the dropdown when opening the converter
def getEngine():
    # Make arnold default
    mc.optionMenu(settings["renderer"], sl=1, e=True)

    # Get the currently active render engine
    engine = mc.getAttr('defaultRenderGlobals.currentRenderer')

    for eng in SupportedEngines.keys() :
        # found = mc.renderer(SupportedEngines[eng], q=1, ex=1)
        
        # mc.menuItem(eng.replace("-","")+"_mi", e=True, label=eng, en=found)
        
        if engine == SupportedEngines[eng]:
            mc.optionMenu(settings["renderer"], e=True, v=eng)
    
    loadEngine(
        mc.optionMenu(settings["renderer"], q=True, v=True)
    )

    # Set the lightsetup to be at None by default
    if internal:
        global lightsetup
        mc.optionMenu(lightsetup, value="<None>", e=True)


# Update the label for the convert button
def updateUInmats():
    if nMats == 1: label = "Load 1 Material"
    else: label = "Load "+str(nMats)+" Materials"
    mc.button(settings["button_Convert"], e=True, label=label, enable=nMats)


# After loading a material, set the icon to confirm.png
def setLoadedIcon(matName):
    for element in MaterialsListUIElements:
        if "matButtonID_" in element:
            # If the name of the just loaded material matches a button label, switch that icon to confirm.png
            if matName == mc.iconTextButton(element, q=True, label=True):
                IconID = "matIconID_"+element.split("_")[-1]
                mc.iconTextButton(IconID, e=True, image="confirm.png")
                mc.checkBox(element.replace("matButtonID", "matCheckboxID"), e=True, value=False)
                if matName == mc.text(settings["MaterialName"], q=True, label=True):
                    updateMaterialInfo(IconID)


# Populate the material list with all of the materials found
def populateMaterialList():
    global matsFound
    global MaterialsListUIElements
    
    # Clear all of the current materials in the list
    if MaterialsListUIElements != []:
        for item in MaterialsListUIElements:
            if "matButtonID" not in item:
                try:
                    # We've had some reports where this fails, so placed in a try catch for now.
                    # 'Poliigon_Material_Converter__v1_3_8_|formLayout662|paneLayout2|MaterialListScrollLayout|rowColumnLayout27|matRowID_1' not found.
                    mc.deleteUI(item)
                except:
                    pass

    # Useful variables
    SelectionHighlightColor = [0.4, 0.4, 0.4]#[.32,.52,.65]#
    light_grey = [.8,.8,.8]
    MaterialsListUIElements = []
    AllMaterials = mc.ls(mat=True)
    LoadedMaterials = []
    i=1


    #   -   -    Valid Materials    -   -   #

    for workflow in matsFound:
        for res in matsFound[workflow]:
            for matn in sorted(list(matsFound[workflow][res].keys())):
                missingmat = False

                if matn not in mapDict.get(workflow, {}).get(res, {}):
                    missingmat = True

                # If material is valid, add it to the list.
                if not missingmat:
                    materialName = (matn+"_"+res+"_"+workflow).replace("__", "_")

                    # If a materialwith the same name already exists in the maya file, mark as loaded.
                    if materialName in AllMaterials:
                        icon='confirm.png'
                        checkboxValue = True
                    else:
                        checkboxValue = False
                        icon='empty.png'

                    # Create the row, icon, checkbox & button.
                    mc.checkBox(settings["SelectAll"], e=True, value=False) #=True) Don't select all by default
                    rowLayout = mc.rowLayout("matRowID_"+str(i), numberOfColumns=3 ,p=settings["MaterialsListLayout"], w=362)
                    icon = mc.iconTextButton("matIconID_"+str(i), style='iconOnly', image1=icon, width=15, height=15, label='', command=functools.partial(updateMaterialInfo, "matIconID_"+str(i)), ann="", p=rowLayout, bgc=SelectionHighlightColor, ebg=False)
                    checkbox = mc.checkBox("matCheckboxID_"+str(i), label="", h=15,ann="",cc=functools.partial(updateMaterialsList, "matCheckboxID_"+str(i), workflow, matn, res), value=checkboxValue, p=rowLayout)
                    button = mc.iconTextButton("matButtonID_"+str(i), style="textOnly", label=materialName,h=15, align="left",command=functools.partial(updateMaterialInfo, "matIconID_"+str(i)),dcc=functools.partial(isolateSelected, "matIconID_"+str(i), workflow, matn, res), bgc=SelectionHighlightColor, ebg=False, p=rowLayout, olc=light_grey)
                    MaterialsListUIElements.append(rowLayout)
                    MaterialsListUIElements.append(button)

                    # If material is the current selected one, update the material info
                    if mc.iconTextButton("matIconID_"+str(i),q=True, image=True) == "confirm.png":
                        updateMaterialsList(checkbox, workflow, matn, res, None)
                        LoadedMaterials.append(workflow+matn+res)

                    i+=1


    #   -   -    Invalid Materials    -   -   #

    for workflow in matsFound:
        for res in matsFound[workflow]:
            for matn in sorted(list(matsFound[workflow][res].keys())):
                checkboxValue = True
                enable = True
                ann=""
                materialName = (matn+"_"+res+"_"+workflow).replace("__", "_")
                
                dcc = functools.partial(isolateSelected, "matIconID_"+str(i), workflow, matn, res)

                # !!! THIS SEEMS WRONG, HAVE A LOOK AT IT LATER !!!
                # IF material has been loaded & invalid, don't dispaly it at all?!?!?!?
                if workflow+matn+res in LoadedMaterials:
                    pass
                else:
                    if matn not in mapDict.get(workflow, {}).get(res, {}):
                        for mat in MissingMaterials:
                            if matn in mat and res in mat:
                                ann = mat.replace(matn+"_"+res+" - ", "")
                                icon = 'caution.png'
                                mc.checkBox(settings["SelectAll"], e=True, value=False)
                                break
                        checkboxValue = False

                # If material is invalid, Create the Row, Icon, Checkbox & Button
                if not checkboxValue:
                    rowLayout = mc.rowLayout("matRowID_"+str(i), numberOfColumns=3 ,p=settings["MaterialsListLayout"], w=262)
                    icon = mc.iconTextButton("matIconID_"+str(i), style='iconOnly', image1=icon, width=15, height=15, label='', command=functools.partial(updateMaterialInfo, "matIconID_"+str(i)), ann=ann, p=rowLayout, bgc=SelectionHighlightColor, ebg=False)
                    checkbox = mc.checkBox("matCheckboxID_"+str(i), label="", h=15,ann=ann,cc=functools.partial(updateMaterialsList, "matCheckboxID_"+str(i), workflow, matn, res), value=checkboxValue, enable=enable, p=rowLayout)
                    button = mc.iconTextButton("matButtonID_"+str(i), style="textOnly",ann=ann, label=materialName,h=15, align="left",command=functools.partial(updateMaterialInfo, "matIconID_"+str(i)),dcc=dcc, bgc=SelectionHighlightColor, ebg=False, p=rowLayout)
                    MaterialsListUIElements.append(rowLayout)
                    MaterialsListUIElements.append(button)
                    i+=1


# Button: Apply selected material to selected objects.
def PMC_ApplyMaterialToSelectedObject(self=None):
    # Get the material from the name in the UI
    materialName = mc.text(settings["MaterialName"], q=True, label=True)
    mat = mc.ls(materialName, mat=True)
    
    if mat == []:
        mc.confirmDialog(t="Warning", icn="warning", b="OK", m="Material "+materialName+" could no be found.")
        return
    if len(mc.ls(sl=True, tr=True)) > 0:
        # Apply the material to the selected objects
        if mc.objExists(mat[0]+'_MIX') : mc.hyperShade(a=mat[0]+'_MIX')
        else : mc.hyperShade(a=mat[0])
        
        if mc.nodeType(mat[0]) in ['aiStandardSurface'] :
            pAlpha = len(mc.listConnections(mat[0]+'.opacityR'))
            pSSS = len(mc.listConnections(mat[0]+'.subsurfaceColor'))
            if pAlpha and pSSS :
                for pObj in mc.ls(sl=True, tr=True) :
                    try : mc.setAttr(pObj+'.aiOpaque', 0)
                    except : pass
    else:
        # No objects were selected, return a warning
        mc.confirmDialog(t="Warning", icn="warning", b="OK", m="No objects selected.")


# Update the material info bar with the currently selected material.
def updateMaterialInfo(IconID, self=None):
    TogglePMCExceptionHook(True)

    global settings

    # Get all of the ID's
    checkboxID = IconID.replace("matIconID", "matCheckboxID")
    buttonID = IconID.replace("matIconID", "matButtonID")
    RowID = IconID.replace("matIconID", "matRowID")

    label = mc.iconTextButton(buttonID, q=True, label=True)
    ann = mc.checkBox(checkboxID, q=True, ann=True)

    # Check if material contains a warning. (invalid material)
    if ann == "":
        mc.text(settings["MaterialHelp"], e=True, visible=True, label=label)
        mc.text(settings["MaterialName"], e=True, label=label, visible=False)
    else:
        mc.text(settings["MaterialHelp"], e=True, visible=False)
        mc.text(settings["MaterialName"], e=True, label=label, visible=True)

    # Enable the browse texture on poliigon.com button
    mc.iconTextButton(settings["button_browseTexture"], e=True, enable=True)

    # Disable material previews on MAC
    if settings["Platform"] != "darwin":
        mc.symbolCheckBox(settings["button_materialPreview"], e=True, enable=True)

    # Update material info
    mc.text(settings["MaterialInfo"], e=True, label=ann)
    icon = mc.iconTextButton(IconID, q=True, image=True)
    mc.button(settings["button_applyMaterial"], e=True, enable=(icon == "confirm.png"))

    # Un-Hightlight previous selection
    for ID in range(1,int(len(MaterialsListUIElements)/2)+1):
        mc.iconTextButton("matButtonID_"+str(ID), e=True, ebg=False)
        mc.rowLayout("matRowID_"+str(ID), e=True, bgc=[0.2,0.2,0.2])

    # Hightlight selected material in the list
    mc.iconTextButton(buttonID, e=True, ebg=True)
    backgroundColor = mc.iconTextButton(buttonID, q=True, bgc=True)
    mc.rowLayout(RowID, e=True, bgc=backgroundColor)

    # Update the material preview
    if settings["MaterialPreview"]:
        icon = None

        # Check if there are any previews
        MatName = label.split("_")[0]
        if MatName in previewImages:
            for type in ["_Sphere", "_Cube", "_Flat"]:
                if type in previewImages[MatName]:
                    icon = previewImages[MatName][type]
                    break

        # No previews found, use the color map instead.
        else:
            for workflow in matsFound:
                for res in matsFound[workflow]:
                    for matn in matsFound[workflow][res]:
                        if matn+"_"+res == label and "COL_" in matsFound[workflow][res][matn]:
                            icon=matsFound[workflow][res][matn]["COL_"]
                            break
        # Update the icon
        mc.iconTextStaticLabel(settings["MaterialIcon"], e=True, image=icon)

        # OLD CODE, CAN BE REMOVED.
        #else:
            # Material has been loaded, use display a material preview instead
            # Check if material exists
            #materials = mc.ls(mat=True)
            #if label in materials:
            #    mc.swatchDisplayPort(settings["Material_ShaderPreview"], e=True, sn=label, visible=True, enable=True)
            #    mc.iconTextStaticLabel(settings["MaterialIcon"], e=True, visible=False)

    else:
        # Material previews are disabled, use the list icon instead.
        mc.iconTextStaticLabel(settings["MaterialIcon"], e=True, image=icon)

    # Update currently selected material
    settings["CurrentID"] = IconID

    TogglePMCExceptionHook(False)


# Add or remove a material from the mapDict (The list refered to when pressing the convert button)
def updateMaterialsList(CheckboxID, workflow, mat, res, self=None):
    TogglePMCExceptionHook(True)

    global mapDict
    global nMats

    # Get the value from the checkbox
    checkboxValue = mc.checkBox(CheckboxID, q=True, value=True)

    # Add the material to the list
    if checkboxValue:
        mapDict[workflow][res][mat] = matsFound[workflow][res][mat]
        nMats += 1

    # Remove the material from the list
    else:
        try:
            del mapDict[workflow][res][mat]
        except:
            pass
        nMats -= 1

    updateUInmats()

    TogglePMCExceptionHook(False)


# Select and Deselct all of the materials in the materials list
def PMC_SelectAllMaterials(value):
    TogglePMCExceptionHook(True)
    global nMats
    i=1

    # Loop through all of the checkboxes
    for workflow in matsFound:
        if workflow != "METALNESS":
            for res in matsFound[workflow]:
                for mat in matsFound[workflow][res]:

                    # Update the checkbox value
                    mc.checkBox("matCheckboxID_"+str(i), e=True, value=value)

                    # Select All, add all materials to the list which is referd to when converting.
                    if value:
                        mapDict[workflow][res][mat] = matsFound[workflow][res][mat]
                        nMats = i

                    # Deselect All, remove all materials from the list which is referd to when converting.
                    else:
                        if mat in mapDict.get(workflow, {}).get(res, {}):
                            del mapDict[workflow][res][mat]
                        nMats = 0

                    i+=1

    updateUInmats()

    TogglePMCExceptionHook(False)


# Open the selected material in the webbrowser
def browseMissingMats():
    mat = mc.text(settings["MaterialName"], q=True, label=True)
    try:
        import webbrowser
        import re
    except:
        return False
    # Construct the URL based on the material name
    url = mat.split('_')[0]
    url = re.sub("(?<=[a-z])(?=[A-Z])", "-", url)
    url = re.sub("(?<=[a-z])(?=[0-9])", "-", url)
    url = 'https://www.poliigon.com/texture/' + url
    url = url.lower()
    webbrowser.open(url, new=2)

    return True


# Command for double clicking a material in the list: Select only that one.
def isolateSelected(IconID, workflow, matn, res, self=None):
    PMC_SelectAllMaterials(False)
    mc.checkBox(settings["SelectAll"], e=True, value=False)
    checkboxID = IconID.replace("matIconID_", "matCheckboxID_")
    mc.checkBox(checkboxID, e=True, value=True)
    updateMaterialsList(checkboxID, workflow, matn, res)
    updateMaterialInfo(IconID)


# Toggle on/off the material previews
def PMC_ToggleMaterialPreview(value):
    settings["MaterialPreview"] = value
    updateMaterialInfo(settings["CurrentID"])


# Get or Set the default folder path, or change icon of the button.
# q         = Query the currently saved filepath
# set       = Save current filepath as default
# reverese  = Apply the reverse icon to the button
# default   = Apply the default icon to the button
def DefaultFolderPath(q=False, set=False, reverse=False, default=False):

    # Check if the settings file exists, if so read the current data
    if q or set:
        import json
        fileSettings = os.path.join(mc.internalVar(usd=True), 'poliigon_material_converter', 'Settings.json')
        if os.path.exists(fileSettings):
            with open(fileSettings) as file:
                fileSettingsData = json.load(file)
        else:
            fileSettingsData = {"DefaultFolderPath":""}

    # Query the currently saved filepath
    if q:
        return fileSettingsData["DefaultFolderPath"]

    # Save current filepath as default
    elif set:
        if fileSettingsData["DefaultFolderPath"] == mc.textField(settings["folderpath"], q=True, text=True):
            DefaultFolderPath(default=True)
            fileSettingsData["DefaultFolderPath"] = ""
            updateFolderPath("")
            mc.iconTextButton(settings["button_setDefDirLoc"], e=True, enable=False)
            mc.iconTextButton(settings["button_reloadFolder"], e=True, enable=False)
        else:
            fileSettingsData["DefaultFolderPath"] = mc.textField(settings["folderpath"], q=True, text=True)
            reverse = True

        # Write data to file
        try:
            with open(fileSettings, 'w') as file:
                json.dump(fileSettingsData, file)
        except:
            pass

    # Apply the reverse icon to the button
    if reverse:
        icon = os.path.join(mc.internalVar(userBitmapsDir=True), 'poliigon_pathRevert.png')
        mc.iconTextButton(settings["button_setDefDirLoc"], e=True, ann="Remove this custom path for loading textures", image=icon, enable=True)

    # Apply the default icon to the button
    elif default:
        icon = os.path.join(mc.internalVar(userBitmapsDir=True), 'poliigon_pathSave.png')
        mc.iconTextButton(settings["button_setDefDirLoc"], e=True, ann="Set as default path for loading texture", image=icon, enable=True)


# Executes whenever the folderpath textfield is changed manually
def updateFolderPath(folderPath):

    # if None, Refresh the currently given root directory
    if folderPath == None:
        folderPath = mc.textField(settings["folderpath"], q=True, text=True)

    if folderPath == '':
        mc.textField(settings["folderpath"], e=True, text="")

    # Check if Dir exists
    if not os.path.isdir(folderPath) and folderPath != '':
        msg = folderPath + "\nis not a directory on your device. Please make sure the path is correct."
        mc.confirmDialog(t="Invalid path", icn="warning", b="OK", m=msg)
        mc.iconTextButton(settings["button_reloadFolder"], e=True, enable=False)
        mc.iconTextButton(settings["button_setDefDirLoc"], e=True, enable=False)
        return

    # Get the textures in given root folder
    TogglePMCExceptionHook(True)
    getTextures(folderPath)

    getEngine()


# BUTTON: Browse for root directory (Folder Icon)
# Task: Open a file browser and let the user locate the desired folder.
def texturesFolder(self):
    TogglePMCExceptionHook(True)

    # Prompt a file dialog and ask for the folder that contains the textures
    if PMC_PreviousPath != None:
        folderPath = mc.fileDialog2(ds=1, fm=3, cap="Textures Folder", dir=PMC_PreviousPath)
    else:
        folderPath = mc.fileDialog2(ds=1, fm=3, cap="Textures Folder")

    # None = The user closed the window or pressed cancel
    if folderPath == None:
        TogglePMCExceptionHook(False)
        return False

    folderPath = folderPath[0]

    mapDict = getTextures(folderPath)


# Get all of the poliigon textures from the selcted folder (+ all subfolders)
def getTextures(Path):
    global folderPath
    global settings
    global mapDict
    global nMats
    global PMC_PreviousPath
    
    mc.waitCursor(st=1)

    # Make sure the folder path text field is updated
    folderPath = Path
    PMC_PreviousPath = folderPath
    mc.textField(settings['folderpath'], edit=True, text=folderPath)

    # For internal, if Generic_Files = True, add the subfolder Generic_Files to the path
    if internal:
        if mc.checkBox(settings["ROOT"], q=True, v=True):
            folderPath = os.path.join(folderPath, "Generic_Files")

    # Get all polligon textures from the folder and place them in a dict

    global OBJlist
    global previewImages
    previewImages = {}
    OBJlist = []
    mapDict = {}
    previewTypes = ["_cube", "_flat", "_sphere", "_cylinder", "_fabric", "_preview1"]
    supportedMaps = ["COL_", "AO_", "DISP_", "EMISSION_", "FUZZ_", "GLOSS_", "NRM_", "NRM16_", "DISP16_", "REFL_", "ROUGHNESS_", "ALPHAMASKED_", "MASK_", "TRANSLUCENCY_", "TRANSMISSION_", "SSS_", "METALNESS_"]
    supportedExtentions = ['.exr', '.jpg', '.jpeg', '.png', '.tif', '.tiff']
    supportedSizes = ['256', '512', '1K', '2K', '3K', '4K', '6K', '8K', '12K', '16K', '18K', 'HIRES']
    if internal:
        supportedExtentions += ['.obj', '.fbx']
    
    # new convention
    
    supportedMapsNew = [
        'AmbientOcclusion',
        'BaseColor',
        'BaseColorOpacity',
        'Displacement',
        'Emission',
        'Hdri',
        'Metallic',
        'Normal',
        'Opacity',
        'Roughness',
        'ScatteringColor',
        'SheenColor',
        'Translucency',
        'Transmission',
    ]
    
    tex_mapping = {
        'AO_': 'AmbientOcclusion',
        'COL_': 'BaseColor',
        'ALPHAMASKED_': 'BaseColorOpacity',
        'DISP_': 'Displacement',
        'DISP16_': 'Displacement',
        'EMISSION_': 'Emission',
        'METALNESS_': 'Metallic',
        'NRM_': 'Normal',
        'NRM16_': 'Normal',
        'MASK_': 'Opacity',
        'ROUGHNESS_': 'Roughness',
        'SSS_': 'ScatteringColor',
        'FUZZ_': 'SheenColor',
        'TRANSLUCENCY_': 'Translucency',
        'TRANSMISSION_': 'Transmission',
    }
    
    def get_mat_name(fname):
        if '_Mat_' in fname:
            return fname.split('_Mat_')[0]
        else :
            Map = get_tex_map(fname)
            
            if Map is not None:
                return fname.split("_"+Map)[0]
        return None
    
    def get_tex_map(fname):
        for m in supportedMaps+supportedMapsNew:
            if "_"+m in fname:
                return m
        return None
    
    def get_tex_size(file):
        dir_name = os.path.basename(os.path.dirname(file))
        fname,ext = os.path.splitext(os.path.basename(file))
        Map = get_tex_map(fname)
        for s in supportedSizes:
            if s == dir_name or s in fname.split('_'):
                return s
        if Map in supportedMapsNew:
            return ""
        return None
    
    def get_tex_workflow(fname, Map):
        if fname.endswith("SPECULAR") :
            return "SPECULAR"
        elif fname.endswith("METALNESS") :
            return "METALNESS"
        elif Map in supportedMapsNew :
            return "METALLIC"
        return "DIALECTRIC"
    
    # Search the directory for textures and models
    for root, dirs, files in os.walk(folderPath):
        for name in files:
            fname,ext = os.path.splitext(name)
            
            if ext not in supportedExtentions:
                continue
            
            MatName = get_mat_name(fname)
            
            # Check if it's a preview
            prev = [prev for prev in previewTypes if fname.lower().endswith(prev)]
            if len(prev) :
                if MatName not in previewImages:
                    previewImages[MatName] = {}
                previewImages[MatName][prev[0]] = os.path.join(root, name)
                continue
            
            file = str(os.path.join(root, name))
            Map = get_tex_map(fname)
            workflow = get_tex_workflow(fname, Map)
            
            # METALNESS to METALLIC
            if workflow == 'METALNESS':
                Map = tex_mapping.get(Map, Map)
            if Map in supportedMapsNew:
                workflow = 'METALLIC'
            
            res = get_tex_size(file)
            if res is None:
                continue
            
            # print(name)
            # print(fname,ext)
            # print(file)
            # print(MatName)
            # print(Map)
            # print(workflow)
            
            # If a model is found, add it to the obj list (internal only)
            if internal:
                if ext in ['.obj', '.fbx', '.FBX']:
                    OBJlist.append(os.path.join(root, name))
            
            # Check if the filename contains a keyword from supportedMaps, if so we can assume it's a poliigon texture
            
            if Map is not None:
                # Get some info about the texture, such as material name & resolution
                # Poliigon's naming convention: MaterialName_MapType_Resolution_Workflow.FileExtention
                # Example:
                # WoodenPlanks001_COL_3K.jpg
                # MetalWorn003_NRM_1K_SPECULAR.png (workflow only applies when it's a metal material)
                
                # Add workflow to dict
                mapDict.setdefault(workflow, {})
                
                # Add res to dict
                mapDict[workflow].setdefault(res, {})
                
                # Add material to dict
                mapDict[workflow][res].setdefault(MatName, {})
                
                # Add texture path to dict
                if Map not in mapDict[workflow][res][MatName]:
                    try :
                        mapDict[workflow][res][MatName][Map] = file
                    except :
                        try :
                            mapDict[workflow][res][MatName][Map] = (file).encode('utf-8')
                        except : pass

                # The dict may end up looking something like this:
                # {"DIALECTRIC":{
                #    "3K":{
                #        "WoodenPlanks001":{
                #            "COL_" : "C:\WoodenPlanks001_COL_4K.jpg"
                #            "GLOSS_" : "C:\WoodenPlanks001_GLOSS_4K.jpg"
                #            "REFL_" : "C:\WoodenPlanks001_REFL_4K.jpg"
                #            "NRM_" : "C:\WoodenPlanks001_NRM_4K.jpg"
                #        }
                #    }
                #}}

    # print(json.dumps(mapDict, indent=2))

    # Save a full list of all the materials found.
    global matsFound
    matsFound = copy.deepcopy(mapDict)

    # Check all of the materials if they're valid
    mapDict, nMats = checkTextures(mapDict)

    # Update the UI to let the user know how many materials were found
    mc.text(settings["label_Path"], edit=True, label='')
    mc.iconTextButton(settings["button_reloadFolder"], e=True, enable=True)

    # Add all of the found materials to the UI list.
    populateMaterialList()

    # Update UI

    # Enable/disable features depending on how many materials where found.
    if len(MaterialsListUIElements)/2 == 1:
        enable=True
        msg = "1 material found."
    elif len(MaterialsListUIElements)/2 > 0:
        enable=True
        msg = str(len(MaterialsListUIElements)/2) + " materials found."
    else:
        enable=False
        msg = "No materials found."

    mc.text(settings["MaterialHelp"], e=True, visible=enable, label="Click on a material to select it")
    mc.text(settings["MaterialName"], e=True, visible=enable, label="")
    mc.text(settings["MaterialInfo"], e=True, visible=enable, label="")
    mc.iconTextStaticLabel(settings["MaterialIcon"], e=True, visible=enable, image="help.png")
    mc.checkBox(settings["SelectAll"], e=True, enable=enable)
    mc.iconTextButton(settings["button_browseTexture"], e=True, enable=False)
    mc.symbolCheckBox(settings["button_materialPreview"], e=True, enable=False)
    mc.button(settings["button_applyMaterial"], e=True, enable=False)

    # Update the UI to display number of materials found
    mc.text(settings["label_Mats"], edit=True, label=msg)

    # If there was only one material found, select it by default
    if len(MaterialsListUIElements)/2 == 1:
        updateMaterialInfo("matIconID_1")

    # Update the Convert button
    updateUInmats()

    # Update the save default folder path button
    if DefaultFolderPath(q=True) == mc.textField(settings["folderpath"], q=True, text=True):
        DefaultFolderPath(reverse=True)
    else:
        DefaultFolderPath(default=True)
    if folderPath == "":
        mc.iconTextButton(settings["button_setDefDirLoc"], e=True, enable=False)

    TogglePMCExceptionHook(False)
    
    mc.waitCursor(st=0)
    
    PMC_SelectAllMaterials(False)
    
    return mapDict


# Check for any invalid materials, if found give the user a warning prompt
def checkTextures(mapDict):
    if internal:
        global OBJlist
    # Each material must contain at least 4 of the required maps
    requiredMaps = ["COL_", "GLOSS_", "REFL_", "NRM_"]
    requiredMapsMetallic = ["BaseColor", "Metallic", "Normal", "Roughness"]
    nMats = 0
    global MissingMaterials
    MissingMaterials = []
    MatsToRemove = []
    for workflow in mapDict:
        if workflow not in ["METALNESS", "METALLIC"]:
            for res in mapDict[workflow]:
                for mat in mapDict[workflow][res]:
                    # Get list of missing required maps
                    MissingMaps = [
                        m for m in requiredMaps
                        if m not in mapDict[workflow][res][mat]
                    ]

                    # If one or more required maps were missing from the material, add it to the incomplete materials list
                    if len(MissingMaps) > 0:
                        mapstr = ""
                        for Map in MissingMaps:
                            mapstr += Map+", "
                        MissingMaterials.append(mat+"_"+res + " - MISSING MAPS: "+mapstr[:-2]+"")
                        MatsToRemove.append([workflow, res, mat])
                    else:
                        nMats+=1 # Count how many valid materials have been found.
            
        elif workflow == "METALLIC":
            for res in mapDict[workflow]:
                for mat in mapDict[workflow][res]:
                    # Get list of missing required maps
                    MissingMaps = [
                        m for m in requiredMapsMetallic
                        if m not in mapDict[workflow][res][mat]
                    ]
                    
                    # If one or more required maps were missing from the material, add it to the incomplete materials list
                    if len(MissingMaps) > 0:
                        mapstr = ", ".join(MissingMaps)
                        MissingMaterials.append(mat+"_"+res + " - MISSING MAPS: "+mapstr)
                        MatsToRemove.append([workflow, res, mat])
                    else:
                        nMats+=1 # Count how many valid materials have been found.

    # Check for textures using the metalness workflow, and warn users
    if "METALNESS" in mapDict:
        for res in mapDict["METALNESS"]:
            for mat in mapDict["METALNESS"][res]:
                try:
                    # Check if it has an specular version too, then we don't have to warn
                    mapDict["SPECULAR"][res][mat]
                except:
                    MissingMaterials.append(mat+"_"+res + " - METALNESS WORKFLOW (Download the SPECULAR WORKFLOW)")

    # Remove invalid materials from the dictionary
    for MatInfo in MatsToRemove:
        del mapDict[MatInfo[0]][MatInfo[1]][MatInfo[2]]
    if "METALNESS" in mapDict:
        del mapDict["METALNESS"]

    return mapDict, nMats


#   #   #   #   #   #   #   #   #   #
#       Converting to Engines       #
#   #   #   #   #   #   #   #   #   #


# BUTTON: CONVERT!
# TASK:
# Create materials out of all the valid texture sets
# if internal: Also import models, save out the scenes + option to batch all engines
def convert(self, prompt=True):

    TogglePMCExceptionHook(True)

    global settings
    global nMats
    global offset
    global UVNodes
    UVNodes = {}
    offset = ((nMats/2.0)*-1)

    Engine = mc.optionMenu(settings["renderer"], q=True, value=True)

    found = mc.renderer(SupportedEngines[Engine], q=1, ex=1)
    if not found:
        mc.confirmDialog(t="Error", icn="error", b="OK", m=Engine+" renderer not found.\n\nPlease check that the relevant Plugin\nis installed and loaded.")
        return False

    # If there are no materials to convert, return
    if nMats == 0:
        if not prompt:
            return False
        
        if "Choose the root folder" in mc.text(settings["label_Path"], q=True, label=True):
            mc.confirmDialog(t="Warning", icn="warning", b="OK", m='A folder has not been set.\nPlease select the root folder where the textures you want to load are stored.')
            return False
        else:
            mc.confirmDialog(t="Warning", icn="warning", b="OK", m="No materials were found. Please make sure that the selected \"Textures folder\" contains at least one complete material.\n\nNote that a complete material consists of these four map types:\nCOL, GLOSS, REFL, NRM.")
            return False


    # If multiple models are found, ask what to name the maya scene, or if the option ask_name = True (internal only)
    if internal:
        global ImportedLights
        global SavePath
        global folderPath
        global SceneName
        global OBJlist
        ImportedLights = False

        if len(OBJlist) > 1 or mc.checkBox(settings["ASK_NAME"], q=True, v=True):
            result = mc.promptDialog(title='Name Scene',message='Enter Name:',button=['OK', 'Cancel'],defaultButton='OK',cancelButton='Cancel',dismissString='Cancel')
            SceneName = mc.promptDialog(query=True, text=True)
            if mc.checkBox(settings["ROOT"], q=True, v=True):
                SavePath = os.path.join(folderPath, "..", "Maya", SceneName+"_")
            else:
                SavePath = os.path.join(folderPath,"Maya", SceneName+"_")
        else:
            SceneName = os.path.basename(OBJlist[0])
            SceneName = os.path.splitext(SceneName)[0]
            if mc.checkBox(settings["ROOT"], q=True, v=True):
                SavePath = os.path.join(folderPath, "..", "Maya", SceneName+"_")
            else:
                SavePath = os.path.join(folderPath,"Maya", SceneName+"_")

    # Check if we should run a batch on all the renderers
    batchAll = False
    if internal:
        batchAll = mc.checkBox(settings["Ball"], q=True, v=True)
    
    # Batch all render engines
    if batchAll:
        mc.optionMenu(settings["renderer"], value="Arnold", e=True)
        r = CreateArnoldMat()
        SaveFile('Arnold')
        ImportedLights = False
        UVNodes = {}
        r = True
        if not r:
            mc.confirmDialog(t="ERROR", m="Failed to create the Arnold materials, please make sure that Mental Ray is installed correctly.", b="OK", icn="critical")
        mc.optionMenu(settings["renderer"], value="Redshift", e=True)
        r = createRedshiftMat()
        SaveFile('Redshift')
        ImportedLights = False
        UVNodes = {}
        if not r:
            mc.confirmDialog(t="ERROR", m="Failed to create the Redshift materials, please make sure that Redshift is installed correctly.", b="OK", icn="critical")
        mc.optionMenu(settings["renderer"], value="V-Ray", e=True)
        r = createVrayMat()
        SaveFile('Vray')
        ImportedLights = False
        UVNodes = {}
        if not r:
            mc.confirmDialog(t="ERROR", m="Failed to create the Vray materials, please make sure that Vray is installed correctly.", b="OK", icn="critical")
        mc.optionMenu(settings["renderer"], value="OctaneRender", e=True)
        r = createOctaneMat()
        SaveFile('Octane')
        ImportedLights = False
        UVNodes = {}
        if not r:
            mc.confirmDialog(t="ERROR", m="Failed to create the Octane materials, please make sure that Octane is installed correctly.", b="OK", icn="critical")
        response = True
    else:
        # Create the materials for the selected render engine
        if Engine == "Arnold":
            response = CreateArnoldMat()
            if internal: SaveFile('Arnold')
        elif Engine == 'Mental Ray':
            response = CreateMentalRayMat()
            if internal: SaveFile('MentalRay')
        elif Engine == 'Redshift':
            response = createRedshiftMat()
            if internal: SaveFile('Redshift')
        elif Engine == 'V-Ray':
            response = createVrayMat()
            if internal: SaveFile('Vray')
        elif Engine == "OctaneRender":
            response = createOctaneMat()
            if internal: SaveFile('Octane')
        elif Engine == "RenderMan":
            response = createRendermanMat()
            if internal: SaveFile('RenderMan')

    # Close the progress bar window.
    if not internal:
        global progressBar
        progressBar.closeWindow()

    # Deselct all of the materials in the list.
    PMC_SelectAllMaterials(False)
    mc.checkBox(settings["SelectAll"], e=True, value=False)
    updateUInmats()

    TogglePMCExceptionHook(False)
    
    if prompt:
        # create a message box once the converter is done and let the user know how it went
        if response:
            mc.confirmDialog(t="Success", m="All materials loaded successfully.", b="OK")
        else:
            mc.confirmDialog(t="ERROR", m="Failed to create the materials, please make sure that the selected renderer is installed correctly.", b="OK", icn="critical")


def getColorSpace():
    """Gets the color space for the file node

    Determines if 'scene-linear Rec 709/sRGB' color space is in the list
    of available color spaces, since it must have been renamed to
    'scene-linear Rec.709-sRGB' in Maya 2022
    """
    colorSpacesToCheck = ['scene-linear Rec 709/sRGB', 'scene-linear Rec.709-sRGB', 'sRGB'] # In order of preference
    colorSpaceNames = mc.colorManagementPrefs(q=True, inputSpaceNames=True)

    if colorSpacesToCheck[0] in colorSpaceNames:
        return colorSpacesToCheck[0]
    elif colorSpacesToCheck[1] in colorSpaceNames:
        return colorSpacesToCheck[1]
    else:
        return colorSpacesToCheck[-1]


# Create the arnold materials
def CreateArnoldMat():
    global settings
    global progressBar

    # Create a progress bar
    if not internal:
        progressBar = PMC_ProgressBar()
        progressBar.createWindow()

    for workflow in mapDict:
        if workflow != "METALNESS": # METALNESS has been removed in the checkTextures, so this check is not needed
            for res in mapDict[workflow]:
                for matn in mapDict[workflow][res]:

                    matName = (matn+"_"+res+"_"+workflow).replace("__", "_")
                    sys.stdout.write('\nLoading material ' + matName + "...")

                    if internal:
                        matInfo2 = mapDict[workflow][res][matn]
                        matInfo = CreateFolder(mapDict[workflow][res][matn], matn, 'Arnold') # Create the folder setup
                        mc.setAttr("defaultRenderGlobals.currentRenderer", "arnold", type="string") # Set Arnold as render engine
                    else:
                        matInfo = mapDict[workflow][res][matn]
                        progressBar.updateBar(matName)
                    
                    # -----------------------------------------------------------------------------------------------------
                    
                    # metallic -> new convention
                    
                    if workflow == "METALLIC":
                        mat_class = arnold_material.ArnoldMaterial(matName)
                        
                        mat = mat_class.build_material(workflow, matInfo)
                        
                        setLoadedIcon(matName)
                        
                        continue
                    
                    # -----------------------------------------------------------------------------------------------------
                    
                    if "ALPHAMASKED_" in matInfo :
                        matInfo["COL_"] = matInfo["ALPHAMASKED_"]
                    
                    pOldVersion = 0
                    # Create the material
                    mat = ""
                    if "aiStandardSurface" in mc.allNodeTypes() :
                        mat = mc.shadingNode("aiStandardSurface", asShader=True)
                    elif "aiStandard" in mc.allNodeTypes() :
                        mat = mc.shadingNode("aiStandard", asShader=True)
                        pOldVersion = 1
                    else:
                        # Could not create the material, Arnold is most likely not installed
                        return False

                    if "unknown" in mat:
                        # Something went wrong with creating the material. Shading node is most likely missing.
                        mc.delete(mat)
                        return False
                    mat = mc.rename(mat, matName)

                    colorSpace = getColorSpace()

                    # COLOR & AO -----------------------------------------------------------------------------------------------------
                    
                    if pOldVersion :
                        ColNode = CreateFileNode(mat, matInfo["COL_"], matName+"_COL", "color", False, False, False, mat)[0]
                    elif "AO_" in matInfo and mc.checkBox(settings["AO"], q=True, v=True):
                        # AO map exists
                        CompNode = mc.shadingNode("aiComposite", asTexture=True)
                        CreateFileNode(CompNode, matInfo["AO_"], matName+"_AO", "A", False, False, False, mat)
                        ColNode = CreateFileNode(CompNode, matInfo["COL_"], matName+"_COLOR", "B", False, False, False, mat)[0]
                        mc.connectAttr(CompNode+".outColor", mat+".baseColor")
                        mc.setAttr(CompNode+".operation",19)
                    else:
                        # No AO map found, only load the color
                        ColNode = CreateFileNode(mat, matInfo["COL_"], matName+"_COL", "baseColor", False, False, False, mat)[0]

                    # REFL (Specular Color) -----------------------------------------------------------------------------------------------------
                    
                    ReflCCNode = None
                    ReflAdjustmentFloat = mc.shadingNode("aiUserDataFloat", asUtility=True)#, asTexture=True)
                    ReflAdjustmentFloat = mc.rename(ReflAdjustmentFloat, matName+"_REFL_ADJUST")
                    if workflow != "SPECULAR":
                        if pOldVersion :
                            ReflCCNode = CreateFileNode(mat, matInfo["REFL_"], matName+"_REFL", "KsColor", True, True, False, mat)[2]
                        else :
                            ReflCCNode = CreateFileNode(mat, matInfo["REFL_"], matName+"_REFL", "specularColor", True, True, False, mat)[2]
                            mc.setAttr(ReflAdjustmentFloat+".default",.6)
                            for Channel in ["R", "G", "B"]:
                                mc.connectAttr(ReflAdjustmentFloat+".outValue", ReflCCNode+".multiply"+Channel)
                    else:
                        ReflMultiplyNode = mc.shadingNode("aiMultiply", asUtility=True)#, asTexture=True)
                        ReflMultiplyNode = mc.rename(ReflMultiplyNode, matName+"_Multiply")
                        CreateFileNode(ReflMultiplyNode, matInfo["REFL_"], matName+"_REFL", "input1", False, False, False, mat)
                        if pOldVersion :
                            mc.connectAttr(ReflMultiplyNode+".outColor", mat+".KsColor")
                        else :
                            mc.setAttr(ReflAdjustmentFloat+".default",1)
                            mc.connectAttr(ReflMultiplyNode+".outColor", mat+".specularColor")
                            for Channel in ["R", "G", "B"]:
                                mc.connectAttr(ReflAdjustmentFloat+".outValue", ReflMultiplyNode+".input2"+Channel)

                    # GLOSS (Roughness) -----------------------------------------------------------------------------------------------------
                    
                    if pOldVersion :
                        GlossNode, GlossOutputNode, GlossCCNode = CreateFileNode(mat, matInfo["GLOSS_"], matName+"_GLOSS", None, True, True, True, mat)
                        mc.connectAttr(GlossCCNode+".outColorR", mat+".specularRoughness")
                    else :
                        GlossNode, GlossOutputNode, GlossCCNode = CreateFileNode(mat, matInfo["GLOSS_"], matName+"_GLOSS", "specularRoughness", True, True, True, mat)
                    mc.setAttr(GlossNode+".colorSpace", colorSpace, type="string")
                    #GlossAdjustmentFloat = mc.shadingNode("aiUserDataFloat", asUtility=True)#, asTexture=True)
                    #GlossAdjustmentFloat = mc.rename(GlossAdjustmentFloat, matName+"_GLOSS_ADJUST")
                    #mc.setAttr(GlossAdjustmentFloat+".default",1)
                    #for Channel in ["R", "G", "B"]:
                    #    mc.connectAttr(GlossAdjustmentFloat+".outValue", GlossCCNode+".multiply"+Channel)

                    # Normals -----------------------------------------------------------------------------------------------------
                    
                    if not pOldVersion :
                        NRMNode = mc.shadingNode("aiNormalMap", asTexture=True)
                        mc.connectAttr(NRMNode+".outValue", mat+".normalCamera")
                        if "NRM16_" in matInfo and mc.checkBox(settings["BIT"], q=True, v=True):
                            NormalNode = CreateFileNode(NRMNode, matInfo["NRM16_"], matName+"_NORMALS", "input", True, False, False, mat)[0]
                        else:
                            NormalNode = CreateFileNode(NRMNode, matInfo["NRM_"], matName+"_NORMALS", "input", True, False, False, mat)[0]
                        mc.setAttr(NormalNode+".colorSpace", colorSpace, type="string")
                        mc.rename(NRMNode, matName+"_NORMAL_MAP")

                    # Transmission -----------------------------------------------------------------------------------------------------
                    
                    if pOldVersion :
                        pass
                    elif "TRANSMISSION_" in matInfo:
                        if settings["MayaVersion"] > 2017:
                            CreateFileNode(mat, matInfo["TRANSMISSION_"], matName+"_TRANSMISSION", "transmission", True, False, True, mat)
                        else:
                            CreateFileNode(mat, matInfo["TRANSMISSION_"], matName+"_TRANSMISSION", "transmission", False, False, True, mat)
                        mc.connectAttr(ColNode+".outColor", mat+".transmissionColor")


                    # Alphamasked -----------------------------------------------------------------------------------------------------
                    
                    if "ALPHAMASKED_" in matInfo:
                        for c in ["R","G","B"]:
                            mc.connectAttr(ColNode+".outAlpha", mat+".opacity.opacity"+c)

                    # SSS -----------------------------------------------------------------------------------------------------
                    
                    if "SSS_" in matInfo:
                        if pOldVersion :
                            pNode = CreateFileNode(mat, matInfo["SSS_"], matName+"_SSS", "KsssColor", False, False, False, mat)[0]
                        else :
                            pNode = CreateFileNode(mat, matInfo["SSS_"], matName+"_SSS", "subsurfaceColor", False, False, False, mat)[0]
                            
                            mc.setAttr(mat+".subsurface", 0.1)
                            mc.setAttr(mat+".subsurfaceScale", 0.1)
                            try: mc.setAttr(mat+".subsurfaceType", 0)
                            except : pass
                            
                            #ToFloatNode = mc.shadingNode("aiColorToFloat", asTexture=True)
                            #mc.connectAttr(pNode+".outColor", ToFloatNode+".input")
                            #ToFloatNode = mc.rename(ToFloatNode, matName+"_SSS_ToFloat")
                            #mc.connectAttr(ToFloatNode+".outValue", mat+".subsurface")
                            
                            mc.setAttr(mat+".caustics", 1)
                            mc.setAttr(mat+".exitToBackground", 1)

                    # Displacement -----------------------------------------------------------------------------------------------------
                    
                    if pOldVersion :
                        pass
                    elif mc.checkBox(settings["DISP"], q=True, v=True) and ("DISP_" in matInfo or ("DISP16_" in matInfo and mc.checkBox(settings["BIT"], q=True, v=True))):
                        ShadingEngine = mc.sets(renderable=True, noSurfaceShader=True, empty=True, name=matName+"_SG")
                        mc.connectAttr(mat+".outColor",ShadingEngine+".surfaceShader")
                        DispNode = mc.shadingNode("displacementShader", asShader=True)
                        mc.connectAttr(DispNode+".displacement",ShadingEngine+".displacementShader")
                        mc.setAttr(DispNode+".scale", .2)
                        mc.setAttr(DispNode+".aiDisplacementPadding", 1)
                        if "DISP16_" in matInfo and mc.checkBox(settings["BIT"], q=True, v=True):
                            DispFileNode = CreateFileNode(DispNode, matInfo["DISP16_"], matName+"_DISPLACEMENT", None, False, False, False, mat)[0]
                        else:
                            DispFileNode = CreateFileNode(DispNode, matInfo["DISP_"], matName+"_DISPLACEMENT", None, False, False, False, mat)[0]
                        mc.setAttr(DispFileNode+".colorSpace", colorSpace, type="string")
                        mc.connectAttr(DispFileNode+".outColor.outColorR",DispNode+".displacement")
                        DispNode = mc.rename(DispNode, matName+"_DISPLACEMENT_NODE")

                    # General Settings -----------------------------------------------------------------------------------------------------
                    
                    if not pOldVersion :
                        mc.setAttr(mat+".base", 1)
                        if workflow != "SPECULAR":
                            mc.setAttr(mat+".specularIOR", 1.65)
                        else:
                            mc.setAttr(mat+".specularIOR", 100)

                    # Load the model corresponding to the material
                    if internal:
                        models = loadObj(mat, matn)
                        if models != False:
                            for model in models:
                                if "TRANSMISSION_" in matInfo:
                                    shapeNode = mc.listRelatives(model, shapes=True)[0]
                                    mc.setAttr(shapeNode+".aiOpaque", 0)

                    # Create preview spheres
                    previewSphere(mat, matInfo)

                    setLoadedIcon(matName)
    return True


# Create Mental Ray material
def CreateMentalRayMat():
    global progressBar

    # Create a progressBar
    if not internal:
        progressBar = PMC_ProgressBar()
        progressBar.createWindow()

    for workflow in mapDict:
        if workflow != "METALNESS":
            for res in mapDict[workflow]:
                for matn in mapDict[workflow][res]:

                    matName = (matn+"_"+res).replace("__", "_")
                    sys.stdout.write('\nLoading material ' + matName + "...")

                    if internal:
                        matInfo2 = mapDict[workflow][res][matn]
                        matInfo = CreateFolder(mapDict[workflow][res][matn], matn, 'MentalRay')
                        mc.setAttr("defaultRenderGlobals.currentRenderer", "mentalRay", type="string")
                    else:
                        matInfo = mapDict[workflow][res][matn]
                        progressBar.updateBar(matName)
                    
                    if "ALPHAMASKED_" in matInfo :
                        matInfo["COL_"] = matInfo["ALPHAMASKED_"]

                    # Create the material
                    try:
                        mat = mc.shadingNode("mia_material_x", asShader=True)
                    except:
                        return False
                    if "unknown" in mat:
                        mc.delete(mat)
                        return False
                    mat = mc.rename(mat, matName)

                    colorSpace = getColorSpace()

                    # COLOR and AO
                    if "AO_" in matInfo and mc.checkBox(settings["AO"], q=True, v=True):
                        CompNode = mc.shadingNode("layeredTexture", asTexture=True)
                        CreateFileNode(CompNode, matInfo["AO_"], matName+"_AO", "inputs[0].color", False, False, False, mat)
                        COLNode = CreateFileNode(CompNode, matInfo["COL_"], matName+"_COLOR", "inputs[1].color", False, False, False, mat)[0]
                        mc.setAttr(CompNode+".inputs[0].blendMode", 6)
                        mc.connectAttr(CompNode+".outColor", mat+".diffuse")
                        CompNode = mc.rename(CompNode, matName+"_COL_AO_MULTIPLY")
                    else:
                        COLNode = CreateFileNode(mat, matInfo["COL_"], matName+"_COLOR", "diffuse", False, False, False, mat)[0]


                    # REFLECTION
                    if workflow != "SPECULAR":
                        CreateFileNode(mat, matInfo["REFL_"], matName+"_REFL", "refl_color", False, True, False, mat)
                        mc.setAttr(mat+".brdf_fresnel", True)
                    else:
                        CreateFileNode(mat, matInfo["REFL_"], matName+"_REFL", "refl_color", False, False, False, mat)
                        mc.setAttr(mat+".brdf_fresnel", False)
                        mc.setAttr(mat+".brdf_0_degree_refl", 1)

                    # GLOSS
                    if workflow != "SPECULAR":
                        GlossOutput = CreateFileNode(mat, matInfo["GLOSS_"], matName+"_GLOSS", None, False, False, False, mat)[0]
                        GlossOutput = GlossOutput+".outColorR"
                        #mc.setAttr(GlossNode+".colorSpace", colorSpace, type="string")
                    else:
                        if False:
                            GlossOutput = CreateFileNode(mat, matInfo["GLOSS_"], matName+"_GLOSS", None, True, False, False, mat)[1]
                            for axis in ["X", "Y", "Z"]:
                                mc.setAttr(GlossOutput+".colGamma"+axis, 0.454)
                            GlossOutput = GlossOutput+".outColorR"
                        else:
                            GlossOutput = CreateFileNode(mat, matInfo["GLOSS_"], matName+"_GLOSS", None, False, False, False, mat)[0]
                            GCNode = mc.shadingNode("gammaCorrect", asTexture=True)
                            mc.connectAttr(GlossOutput+".outColor", GCNode+".value")
                            for axis in ["X", "Y", "Z"]:
                                mc.setAttr(GCNode+".gamma"+axis, 0.454)
                            GlossOutput = GCNode+".outValueX"
                    mc.connectAttr(GlossOutput, mat+".refl_gloss")

                    # NORMALS
                    BumpNode = mc.shadingNode("bump2d", asTexture=True)
                    mc.setAttr(BumpNode+".bumpInterp", 1)
                    mc.setAttr(BumpNode+".bumpDepth", 0)
                    if "NRM16_" in matInfo and mc.checkBox(settings["BIT"], q=True, v=True):
                        NRMNode = CreateFileNode(BumpNode, matInfo["NRM16_"], matName+"_NRM", None, False, False, False, mat)[0]
                    else:
                        NRMNode = CreateFileNode(BumpNode, matInfo["NRM_"], matName+"_NRM", None, False, False, False, mat)[0]
                    mc.connectAttr(NRMNode+".outAlpha", BumpNode+".bumpValue")
                    mc.connectAttr(BumpNode+".outNormal", mat+".standard_bump")
                    mc.rename(BumpNode, matName+"_Bump2D")

                    # Displacement
                    if mc.checkBox(settings["DISP"], q=True, v=True) and ("DISP_" in matInfo or ("DISP16_" in matInfo and mc.checkBox(settings["BIT"], q=True, v=True))):
                        ShadingEngine = mc.sets(renderable=True, noSurfaceShader=True, empty=True, name=matName+"_SG")
                        mc.connectAttr(mat+".message",ShadingEngine+".miMaterialShader")
                        mc.connectAttr(mat+".message",ShadingEngine+".miShadowShader")
                        mc.connectAttr(mat+".message",ShadingEngine+".miPhotonShader")
                        DispNode = mc.shadingNode("displacementShader", asShader=True)
                        mc.connectAttr(DispNode+".displacement",ShadingEngine+".displacementShader")
                        mc.setAttr(DispNode+".scale", 0.25)
                        if "DISP16_" in matInfo and mc.checkBox(settings["BIT"], q=True, v=True):
                            DispFileNode = CreateFileNode(DispNode, matInfo["DISP16_"], matName+"_DISPLACEMENT", None, False, False, False, mat)[0]
                        else:
                            DispFileNode = CreateFileNode(DispNode, matInfo["DISP_"], matName+"_DISPLACEMENT", None, False, False, False, mat)[0]
                        mc.setAttr(DispFileNode+".colorSpace", colorSpace, type="string")
                        mc.connectAttr(DispFileNode+".outColor.outColorR",DispNode+".displacement")
                        DispNode = mc.rename(DispNode, matName+"_DISPLACEMENT_NODE")

                    # Transmission
                    if "TRANSMISSION_" in matInfo:
                        mc.connectAttr(GlossOutput, mat+".refr_gloss")
                        if settings["MayaVersion"] > 2017:
                            CreateFileNode(mat, matInfo["TRANSMISSION_"], matName+"_TRANSMISSION", "transparency", False, False, True, mat)
                        else:
                            TransmissionNode = CreateFileNode(mat, matInfo["TRANSMISSION_"], matName+"_TRANSMISSION", None, False, False, False, mat)[0]
                            mc.connectAttr(TransmissionNode+".outColorR", mat+".transparency")

                    # ALPHAMAKSED
                    if "ALPHAMASKED_" in matInfo:
                        if settings["MayaVersion"] > 2016:
                            MathNode = mc.shadingNode("colorMath", asTexture=True)
                            if "unknown" in MathNode:
                                mc.delete(MathNode)
                                mc.connectAttr(COLNode+".outAlpha", mat+".cutout_opacity")
                            else:
                                ReverseNode = mc.shadingNode("reverse", asTexture=True)
                                mc.connectAttr(COLNode+".outAlpha", ReverseNode+".inputY")
                                mc.setAttr(COLNode+".alphaIsLuminance", True)
                                AlphaNode = CreateFileNode(ReverseNode, matInfo["COL_"], matName+"_ALPHA", None, False, False, False, mat)[0]
                                mc.connectAttr(AlphaNode+".outAlpha", ReverseNode+".inputX")
                                mc.setAttr(MathNode+".operation", 1)
                                for alpha in [("X", "B", 50),("Y", "A", 30)]:
                                    CCNode = mc.shadingNode("colorCorrect", asTexture=True)
                                    mc.connectAttr(ReverseNode+".output.output"+alpha[0], CCNode+".inAlpha")
                                    mc.setAttr(CCNode+".alphaGamma", alpha[2])
                                    mc.connectAttr(CCNode+".outAlpha", MathNode+".alpha"+alpha[1])
                                mc.connectAttr(MathNode+".outAlpha", mat+".cutout_opacity")
                        else:
                            mc.connectAttr(COLNode+".outAlpha", mat+".cutout_opacity")


                    # General Settings
                    mc.setAttr(mat+".reflectivity", 1)

                    # load objs
                    if internal:
                        loadObj(mat, matn)

                    # Create the preview spheres
                    previewSphere(mat, matInfo)

                    setLoadedIcon(matName)

    return True


# Create the redshift materials
def createRedshiftMat():
    global progressBar

    # Create a progress bar
    if not internal:
        progressBar = PMC_ProgressBar()
        progressBar.createWindow()

    for workflow in mapDict:
        if workflow != "METALNESS":
            for res in mapDict[workflow]:
                for matn in mapDict[workflow][res]:

                    matName = (matn+"_"+res+"_"+workflow).replace("__", "_")
                    sys.stdout.write('\nLoading material ' + matName + "...")

                    if internal:
                        matInfo2 = mapDict[workflow][res][matn]
                        matInfo = CreateFolder(mapDict[workflow][res][matn], matn, 'Redshift')
                        mc.setAttr("defaultRenderGlobals.currentRenderer", "redshift", type="string")
                    else:
                        matInfo = mapDict[workflow][res][matn]
                        progressBar.updateBar(matName)
                    
                    # -----------------------------------------------------------------------------------------------------
                    
                    # metallic -> new convention
                    
                    if workflow == "METALLIC":
                        mat_class = redshift_material.RedshiftMaterial(matName)
                        
                        mat = mat_class.build_material(workflow, matInfo)
                        
                        setLoadedIcon(matName)
                        
                        continue
                    
                    # -----------------------------------------------------------------------------------------------------
                    
                    if "ALPHAMASKED_" in matInfo :
                        matInfo["COL_"] = matInfo["ALPHAMASKED_"]

                    # Create material
                    mat = mc.shadingNode("RedshiftMaterial", asShader=True)
                    if "unknown" in mat:
                        mc.delete(mat)
                        return False
                    mat = mc.rename(mat, matName)

                    colorSpace = getColorSpace()
                    
                    # COLOR and AO
                    if "SSS_" not in matInfo and "AO_" in matInfo and mc.checkBox(settings["AO"], q=True, v=True):
                        CompNode = mc.shadingNode("RedshiftColorLayer", asTexture=True)

                        # Redshift's Color Layer was added in v2.5.21
                        if "unknown" in CompNode:
                            mc.delete(CompNode)

                            # Create a multiply divide node instead
                            CompNode = mc.shadingNode("multiplyDivide", asTexture=True)
                            CreateFileNode(CompNode, matInfo["AO_"], matName+"_AO", "input1", False, False, False, mat)
                            ColNode = CreateFileNode(CompNode, matInfo["COL_"], matName+"_COLOR", "input2", False, False, False, mat)[0]
                            mc.connectAttr(CompNode+".output", mat+".diffuse_color")

                        else:
                            # Make use of the redshift color layer node
                            CreateFileNode(CompNode, matInfo["AO_"], matName+"_AO", "layer1_color", False, False, False, mat)
                            ColNode = CreateFileNode(CompNode, matInfo["COL_"], matName+"_COLOR", "base_color", False, False, False, mat)[0]
                            mc.setAttr(CompNode+".layer1_blend_mode", 4)
                            mc.connectAttr(CompNode+".outColor", mat+".diffuse_color")

                        CompNode = mc.rename(CompNode, matName+"_COL_AO_MULTIPLY")

                    else:
                        ColNode = CreateFileNode(mat, matInfo["COL_"], matName+"_COLOR", "diffuse_color", False, False, False, mat)[0]


                    ReflAdjustNode = mc.shadingNode("multiplyDivide", asTexture=True)
                    ReflAdjustNode = mc.rename(ReflAdjustNode, matName+"_REFL_ADJUST")
                    mc.connectAttr(ReflAdjustNode+".output", mat+".refl_color")
                    # REFLECTION
                    if workflow != "SPECULAR":
                        CreateFileNode(ReflAdjustNode, matInfo["REFL_"], matName+"_REFL", "input1", False, True, False, mat)
                        for Axis in ["X", "Y", "Z"]:
                            mc.setAttr(ReflAdjustNode+".input2"+Axis, 0.6)
                    else:
                        CreateFileNode(ReflAdjustNode, matInfo["REFL_"], matName+"_REFL", "input1", False, False, False, mat)
                        mc.setAttr(mat+".refl_ior", 0)


                    GlossAdjustNode = mc.shadingNode("multiplyDivide", asTexture=True)
                    GlossAdjustNode = mc.rename(GlossAdjustNode, matName+"_GLOSS_ADJUST")
                    mc.connectAttr(GlossAdjustNode+".output.outputX", mat+".refl_roughness")


                    # GLOSS
                    GlossNode = CreateFileNode(GlossAdjustNode, matInfo["GLOSS_"], matName+"_GLOSS", "input1", False, True, False, mat)[0]
                    mc.setAttr(GlossNode+".colorSpace", colorSpace, type="string")
                    #mc.connectAttr(GlossNode+".outColor.outColorR", mat+".refl_roughness")


                    # NORMALS
                    BumpNode = mc.shadingNode("RedshiftBumpMap", asUtility=True)
                    # Set type to Tangent Space Normals, this is only available in the newer versions of Redshift
                    try:
                        mc.setAttr(BumpNode+".inputType", 1)
                        oldMethod = False
                    except:
                       oldMethod = True
                       mc.delete(BumpNode)

                    if not oldMethod:
                        mc.setAttr(BumpNode+".scale", 1) # Set the normals scale
                        if "NRM16_" in matInfo and mc.checkBox(settings["BIT"], q=True, v=True):
                            NrmNode = CreateFileNode(BumpNode, matInfo["NRM16_"], matName+"_NRM", "input", False, False, False, mat)[0]
                        else:
                            NrmNode = CreateFileNode(BumpNode, matInfo["NRM_"], matName+"_NRM", "input", False, False, False, mat)[0]
                        mc.setAttr(NrmNode+".colorSpace", colorSpace, type="string")
                        #mc.setAttr(NrmNode+".colorSpace",'Raw', type="string")
                        BumpNode = mc.rename(BumpNode, matName+"_BumpNode")
                        mc.connectAttr(BumpNode+".out", mat+".bump_input")

                    else:
                        # User is running an older version of Redshift, use this older method to load in the Normals
                        BumpNode = mc.shadingNode("RedshiftNormalMap", asTexture=True)
                        if "NRM16_" in matInfo and mc.checkBox(settings["BIT"], q=True, v=True):
                            mc.setAttr(BumpNode+".tex0", matInfo["NRM16_"], type="string")
                        else:
                            mc.setAttr(BumpNode+".tex0", matInfo["NRM_"], type="string")
                        mc.connectAttr(BumpNode+".outDisplacementVector", mat+".bump_input")
                        BumpNode = mc.rename(BumpNode, matName+"_NORMALS")


                    # Conform UVMap for NRM node
                    if mc.checkBox(settings["CONF"], q=True, v=True):
                        global UVNodes
                        UVNode = UVNodes[mat]
                        mc.connectAttr(UVNode+".repeatUV.repeatU", BumpNode+".repeats.repeats0")
                        mc.connectAttr(UVNode+".repeatUV.repeatV", BumpNode+".repeats.repeats1")

                    # Displacement
                    if mc.checkBox(settings["DISP"], q=True, v=True) and ("DISP_" in matInfo or ("DISP16_" in matInfo and mc.checkBox(settings["BIT"], q=True, v=True))):
                        ShadingEngine = mc.sets(renderable=True, noSurfaceShader=True, empty=True, name=matName+"_SG")
                        mc.connectAttr(mat+".outColor",ShadingEngine+".surfaceShader")
                        DispNode = mc.shadingNode("RedshiftDisplacement", asUtility=True)
                        mc.setAttr(DispNode+".scale", 0.25)
                        mc.connectAttr(DispNode+".out",ShadingEngine+".rsDisplacementShader")
                        if "DISP16_" in matInfo and mc.checkBox(settings["BIT"], q=True, v=True):
                            DispFileNode = CreateFileNode(DispNode, matInfo["DISP16_"], matName+"_DISPLACEMENT", "texMap", False, False, False, mat)[0]
                        else:
                            DispFileNode = CreateFileNode(DispNode, matInfo["DISP_"], matName+"_DISPLACEMENT", "texMap", False, False, False, mat)[0]
                        mc.setAttr(DispFileNode+".colorSpace", colorSpace, type="string")
                        DispNode = mc.rename(DispNode, matName+"_DISPLACEMENT_NODE")

                    # Alphamasked
                    if "ALPHAMASKED_" in matInfo:
                        for c in ["R","G","B"]:
                            mc.connectAttr(ColNode+".outAlpha", mat+".opacity_color.opacity_color"+c)

                    # SSS
                    if "SSS_" in matInfo:
                        mc.setAttr(mat+".ms_amount", 0.4)
                        mc.setAttr(mat+".ms_radius_scale", 1)
                        CreateFileNode(mat, matInfo["SSS_"], matName+"_SSS", "ms_color0", False, False, False, mat)
                        mc.setAttr(mat+".ms_weight0", 1)
                        mc.setAttr(mat+".ms_radius0", 2)
                        
                        SSSNode = CreateFileNode(mat, matInfo["SSS_"], matName+"_SSS1", "ms_amount", False, False, False, mat, pOut='outAlpha')[0]
                        try :
                            mc.connectAttr(':defaultColorMgtGlobals.cme', SSSNode+'.cme')
                            mc.connectAttr(':defaultColorMgtGlobals.cfe', SSSNode+'.cmcf')
                            mc.connectAttr(':defaultColorMgtGlobals.cfp', SSSNode+'.cmcp')
                            mc.connectAttr(':defaultColorMgtGlobals.wsn', SSSNode+'.ws')
                        except : pass
                        mc.setAttr(SSSNode+".colorSpace", colorSpace, type='string')

                    # Transmission
                    if "TRANSMISSION_" in matInfo:
                        TransmissionNode = CreateFileNode(mat, matInfo["TRANSMISSION_"], matName+"_TRANSMISSION", None, False, False, False, mat)[0]
                        mc.connectAttr(TransmissionNode+".outAlpha", mat+".refr_weight")
                        mc.connectAttr(ColNode+".outColor", mat+".refr_color")
                        mc.setAttr(mat+".refr_absorption_scale", 1)
                        mc.setAttr(mat+".energyCompMode", 0)


                    # General Settings
                    mc.setAttr(mat+".refl_brdf", 1)
                    # Load models
                    if internal:
                        models = loadObj(mat, matn)
                        if models != False:
                            for model in models:
                                shapeNode = mc.listRelatives(model, shapes=True)[0]
                                mc.setAttr(shapeNode+".rsEnableDisplacement", True)

                    # Create the preview spherers
                    sphere = previewSphere(mat, matInfo)
                    if sphere:
                        shapeNode = mc.listRelatives(sphere, shapes=True)[0]
                        mc.setAttr(shapeNode+".rsEnableDisplacement", True)

                    setLoadedIcon(matName)

    return True


# Create the Vray materials
def createVrayMat():
    global progressBar

    # Create a progress bar
    if not internal:
        progressBar = PMC_ProgressBar()
        progressBar.createWindow()

    for workflow in mapDict:
        if workflow != "METALNESS":
            for res in mapDict[workflow]:
                for matn in mapDict[workflow][res]:

                    matName = (matn+"_"+res+"_"+workflow).replace("__", "_")
                    sys.stdout.write('\nLoading material ' + matName + "...")

                    if internal:
                        matInfo2 = mapDict[workflow][res][matn]
                        matInfo = CreateFolder(mapDict[workflow][res][matn], matn, 'Vray')
                        mc.setAttr("defaultRenderGlobals.currentRenderer", "vray", type="string")
                    else:
                        matInfo = mapDict[workflow][res][matn]
                        progressBar.updateBar(matName)
                    
                    # -----------------------------------------------------------------------------------------------------
                    
                    # metallic -> new convention
                    
                    if workflow == "METALLIC":
                        mat_class = vray_material.VrayMaterial(matName)
                        
                        mat = mat_class.build_material(workflow, matInfo)
                        
                        setLoadedIcon(matName)
                        
                        continue
                    
                    # -----------------------------------------------------------------------------------------------------
                    
                    if "ALPHAMASKED_" in matInfo and ("MASK_" not in matInfo or "SSS_" not in matInfo) :
                        matInfo["COL_"] = matInfo["ALPHAMASKED_"]

                    # Create the material
                    pFastSSS = 0
                    if "SSS_" in matInfo :
                        mat = mc.shadingNode("VRayFastSSS2", asShader=True)
                        if "unknown" in mat :
                            mc.delete(mat)
                        else :
                            pFastSSS = 1
                    
                    if not pFastSSS :
                        mat = mc.shadingNode("VRayMtl", asShader=True)
                        if "unknown" in mat:
                            mc.delete(mat)
                            return False
                    mat = mc.rename(mat, matName)

                    colorSpace = getColorSpace()
                    
                    # COLOR and AO ---------------------------------------------------------------------------------------------------------------
                    
                    if "AO_" in matInfo and mc.checkBox(settings["AO"], q=True, v=True) and not pFastSSS :
                        CompNode = mc.shadingNode("layeredTexture", asTexture=True)
                        CreateFileNode(CompNode, matInfo["AO_"], matName+"_AO", "inputs[0].color", False, False, False, mat)
                        COLNode = CreateFileNode(CompNode, matInfo["COL_"], matName+"_COLOR", "inputs[1].color", False, False, False, mat)[0]
                        mc.setAttr(CompNode+".inputs[0].blendMode", 6)
                        mc.connectAttr(CompNode+".outColor", mat+".diffuseColor")
                        CompNode = mc.rename(CompNode, matName+"_COL_AO_MULTIPLY")
                    else:
                        COLNode = CreateFileNode(mat, matInfo["COL_"], matName+"_COLOR", None, False, False, False, mat)[0]
                        if pFastSSS :
                            mc.connectAttr(COLNode+".outColor", mat+".diffuseTex")
                        else :
                            mc.connectAttr(COLNode+".outColor", mat+".diffuseColor")
                    
                    ReflAdjustNode = mc.shadingNode("multiplyDivide", asTexture=True)
                    ReflAdjustNode = mc.rename(ReflAdjustNode, matName+"_REFL_ADJUST")
                    
                    
                    # Refelection ---------------------------------------------------------------------------------------------------------------
                    
                    if workflow != "SPECULAR":
                        REFLNode = CreateFileNode(ReflAdjustNode, matInfo["REFL_"], matName+"_REFL", "input1", False, True, False, mat)[0]
                        for Axis in ["X", "Y", "Z"]:
                            mc.setAttr(ReflAdjustNode+".input2"+Axis, 0.6)
                    else:
                        REFLNode = CreateFileNode(ReflAdjustNode, matInfo["REFL_"], matName+"_REFL", "input1", False, False, False, mat)[0]
                        try : mc.setAttr(mat+".fresnelIOR", 0)
                        except : pass
                    
                    if pFastSSS :
                        mc.setAttr(REFLNode+".invert", True)
                        mc.connectAttr(ReflAdjustNode+".output", mat+".reflection")
                    else :
                        mc.connectAttr(ReflAdjustNode+".output", mat+".reflectionColor")
                    
                    
                    # Gloss ---------------------------------------------------------------------------------------------------------------
                    
                    GlossAdjustNode = mc.shadingNode("multiplyDivide", asTexture=True)
                    GlossAdjustNode = mc.rename(GlossAdjustNode, matName+"_GLOSS_ADJUST")
                    
                    GlossNode = CreateFileNode(GlossAdjustNode, matInfo["GLOSS_"], matName+"_GLOSS", "input1", False, False, False, mat)[0]
                    mc.setAttr(GlossNode+".colorSpace", colorSpace, type="string")
                    
                    if pFastSSS :
                        mc.connectAttr(GlossAdjustNode+".output.outputX", mat+".glossiness")
                    else :
                        mc.connectAttr(GlossAdjustNode+".output.outputX", mat+".reflectionGlossiness")
                    
                    
                    # NORMALS ---------------------------------------------------------------------------------------------------------------
                    
                    if "NRM16_" in matInfo and mc.checkBox(settings["BIT"], q=True, v=True):
                        NRMNode = CreateFileNode(mat, matInfo["NRM16_"], matName+"_NORMALS", "bumpMap", False, False, False, mat)[0]
                    else:
                        NRMNode = CreateFileNode(mat, matInfo["NRM_"], matName+"_NORMALS", "bumpMap", False, False, False, mat)[0]
                    mc.setAttr(NRMNode+".colorSpace", colorSpace, type="string")
                    mc.setAttr(mat+".bumpMapType", 1)
                    
                    
                    # Alphamasked ---------------------------------------------------------------------------------------------------------------
                    
                    if "ALPHAMASKED_" in matInfo and not pFastSSS :
                        for channel in ["R","G","B"]:
                            mc.connectAttr(COLNode+".outAlpha", mat+".opacityMap"+channel)
                    
                    # Transmission ---------------------------------------------------------------------------------------------------------------
                    
                    if "TRANSMISSION_" in matInfo and not pFastSSS :
                        CreateFileNode(mat, matInfo["TRANSMISSION_"], matName+"_TRANSMISSION", "refractionColor", False, False, False, mat)
                        mc.connectAttr(GlossNode+".outAlpha", mat+".refractionGlossiness")
                        mc.connectAttr(COLNode+".outColor", mat+".fogColor")
                        mc.setAttr(mat+".fogBias", 10)
                    
                    
                    # Displacement ---------------------------------------------------------------------------------------------------------------
                    
                    if ("DISP_" in matInfo or ("DISP16_" in matInfo and mc.checkBox(settings["BIT"], q=True, v=True))) and mc.checkBox(settings["DISP"], q=True, v=True) and not pFastSSS :
                        ShadingEngine = mc.sets(renderable=True, noSurfaceShader=True, empty=True, name=matName+"_SG")
                        mc.connectAttr(mat+".outColor",ShadingEngine+".surfaceShader")
                        DispNode = mc.shadingNode("displacementShader", asShader=True)
                        DispNode = mc.rename(DispNode, matName+"_DisplacementShader")
                        mc.connectAttr(DispNode+".displacement",ShadingEngine+".displacementShader")
                        if "DISP16_" in matInfo and mc.checkBox(settings["BIT"], q=True, v=True):
                            DispFileNode = CreateFileNode(DispNode, matInfo["DISP16_"], matName+"_DISPLACEMENT", None, False, False, False, mat)[0]
                        else:
                            DispFileNode = CreateFileNode(DispNode, matInfo["DISP_"], matName+"_DISPLACEMENT", None, False, False, False, mat)[0]
                        mc.setAttr(DispFileNode+".colorSpace", colorSpace, type="string")
                        mc.connectAttr(DispFileNode+".outColor.outColorR",DispNode+".displacement")
                        mc.setAttr(DispFileNode+".colorGain", 0.25,0.25,0.25, type="double3")
                    
                    
                    # SSS ---------------------------------------------------------------------------------------------------------------
                    
                    if "SSS_" in matInfo :
                        SSSNode, SSSOut = CreateFileNode(mat, matInfo["SSS_"], matName+"_SSS", None, False, False, False, mat)
                        if pFastSSS :
                            mc.connectAttr(SSSNode+".outColor", mat+".subsurfaceColor")
                            mc.connectAttr(SSSNode+".outColor", mat+".scatterRadiusColor")
                            
                            SSSNode1, SSSOut1 = CreateFileNode(mat, matInfo["SSS_"], matName+"_SSS1", None, False, False, False, mat)
                            mc.setAttr(SSSNode1+'.invert', 1)
                            mc.connectAttr(SSSNode1+".outAlpha", mat+".diffuseAmount")
                        else :
                            mc.connectAttr(SSSNode+".outColor", mat+".fogColor")
                            mc.setAttr(mat+".refractionColor", 0.0392,0.0392,0.0392, type="double3")
                            mc.setAttr(mat+".refractionGlossiness", 0)
                            mc.setAttr(mat+".fogMult", 10)
                            mc.setAttr(mat+".sssOn", True)
                        
                        if "ALPHAMASKED_" in matInfo and "MASK_" in matInfo :
                            mat = mc.rename(mat, matName+'_SSS')
                            
                            matB = mc.shadingNode("VRayBlendMtl", asShader=True, name=matName)
                            matO = mc.shadingNode("VRayMtl", asShader=True, name=matName+'_Opacity')
                            mat2S = mc.shadingNode("VRayMtl2Sided", asShader=True, name=matName+'_2Sided')
                            
                            mc.setAttr(matO+".opacityMap", 0, 0, 0, type='double3')
                            
                            pSG = mc.sets(renderable=True, noSurfaceShader=True, empty=True, name=matName+"_SG")
                            mc.connectAttr(matB+".outColor",pSG+".surfaceShader")
                            
                            mc.connectAttr(mat+'.outColor', mat2S+'.backMaterial', f=1)
                            mc.connectAttr(mat+'.outColor', mat2S+'.frontMaterial', f=1)
                            mc.connectAttr(mat2S+'.outColor', matB+'.coat_material_0', f=1)
                            mc.connectAttr(matO+'.outColor', matB+'.base_material', f=1)
                            
                            MASKNode, MASKOut = CreateFileNode(matB, matInfo["MASK_"], matName+"_MASK", 'blend_amount_0', False, False, False, matB)
                            
                            mc.select(matB)
                    
                    
                    # General Settings ---------------------------------------------------------------------------------------------------------------
                    if pFastSSS :
                        pass
                    else :
                        mc.setAttr(mat+".brdfType", 3)
                        mc.setAttr(mat+".reflectOnBackSide", True)
                        mc.setAttr(mat+".lockFresnelIORToRefractionIOR", False)
                        mc.setAttr(mat+".affectShadows", True)

                    # Load the models
                    if internal:
                        model = loadObj(mat, matn)

                    # Create the preview spheres
                    previewSphere(mat, matInfo)

                    setLoadedIcon(matName)

    return True


# Create the Octane materials
def createOctaneMat():
    global progressBar

    # Create a progress bar
    if not internal:
        progressBar = PMC_ProgressBar()
        progressBar.createWindow()

    global settings
    for workflow in mapDict:
        if workflow != "METALNESS":
            for res in mapDict[workflow]:
                for matn in mapDict[workflow][res]:

                    matName = (matn+"_"+res+"_"+workflow).replace("__", "_")
                    sys.stdout.write('\nLoading material ' + matName + "...")

                    if internal:
                        matInfo2 = mapDict[workflow][res][matn]
                        matInfo = CreateFolder(mapDict[workflow][res][matn], matn, 'Octane')
                        mc.setAttr("defaultRenderGlobals.currentRenderer", "OctaneRender", type="string")
                    else:
                        matInfo = mapDict[workflow][res][matn]
                        progressBar.updateBar(matName)
                    
                    # -----------------------------------------------------------------------------------------------------
                    
                    # metallic -> new convention
                    
                    if workflow == "METALLIC":
                        mat_class = octane_material.OctaneMaterial(matName)
                        
                        mat = mat_class.build_material(workflow, matInfo)
                        
                        setLoadedIcon(matName)
                        
                        continue
                    
                    # -----------------------------------------------------------------------------------------------------
                    
                    if "ALPHAMASKED_" in matInfo :
                        matInfo["COL_"] = matInfo["ALPHAMASKED_"]

                    # Create material
                    mat = mc.shadingNode("octaneGlossyMaterial", asShader=True)
                    if "unknown" in mat:
                        mc.delete(mat)
                        return False
                    mat = mc.rename(mat, matName)

                    # Shading Engine
                    ShadingEngine = mc.sets(renderable=True, noSurfaceShader=True, empty=True, name=matName+"_SG")
                    mc.connectAttr(mat+".outColor",ShadingEngine+".surfaceShader")

                    try: # BRDF model wasn't avaliable in earlier versions of Octane
                        mc.setAttr(mat+".BrdfModel", 0)
                        if 'plant' not in matn.lower() : mc.setAttr(mat+".BrdfModel", 2)
                    except:
                        pass

                    # if a Transmission map is detected, create a second specular material
                    if "TRANSMISSION_" in matInfo:
                        Specmat = mc.shadingNode("octaneSpecularMaterial", asShader=True)
                        if "unknown" in Specmat:
                            mc.delete(mat)
                            mc.delete(Specmat)
                            return False
                        Specmat = mc.rename(Specmat, matName+"_SPECULAR")
                        mat = mc.rename(mat, matName+"_GLOSSY")

                    # Conform UV Maps
                    UVScaleNode = mc.shadingNode("octaneScaleTransform", asTexture=True)
                    UVScaleNode = mc.rename(UVScaleNode, matName+"_UVScale")
                    if mc.checkBox(settings["CONF"], q=True, v=True):
                        UVTexNode = mc.shadingNode("file", asTexture=True)
                        mc.setAttr(UVTexNode+".fileTextureName", matInfo["COL_"], type="string")
                        width, height = mc.getAttr(UVTexNode+".outSize")[0]
                        if width != height:
                            if height > width:
                                mc.setAttr(UVScaleNode+".ScaleX", float(width)/height)
                            else:
                                mc.setAttr(UVScaleNode+".ScaleY", float(height)/width)
                        mc.delete(UVTexNode)

                    # COLOR & AO
                    if "AO_" in matInfo and mc.checkBox(settings["AO"], q=True, v=True):
                        MultiplyNode = mc.shadingNode("octaneMultiplyTexture", asTexture=True)
                        MultiplyNode = mc.rename(MultiplyNode, matName+"_COL_AO_MULTIPLY")
                        createOctaneFileNode(MultiplyNode, matInfo["AO_"], matName+"_AO", "Texture1", False, UVScaleNode)
                        ColNode = createOctaneFileNode(MultiplyNode, matInfo["COL_"], matName+"_COLOR", "Texture2", False, UVScaleNode)
                        mc.connectAttr(MultiplyNode+".outTex", mat+".Diffuse")
                    else:
                        ColNode = createOctaneFileNode(mat, matInfo["COL_"], matName+"_COLOR", "Diffuse", False, UVScaleNode)


                    # Reflection
                    ReflAdjustNode = mc.shadingNode("octaneMultiplyTexture", asTexture=True)
                    ReflAdjustNode = mc.rename(ReflAdjustNode, matName+"_REFL_ADJUST")
                    mc.connectAttr(ReflAdjustNode+".outTex", mat+".Specular")
                    mc.octane(texfpin=(ReflAdjustNode+".Texture1", 1))
                    if workflow != "SPECULAR":
                        ReflNode = createOctaneFileNode(ReflAdjustNode, matInfo["REFL_"], matName+"_REFLECTION", "Texture1", True, UVScaleNode)
                        mc.octane(texfpin=(ReflAdjustNode+".Texture2", 0.6))
                        if "TRANSMISSION_" in matInfo:
                            mc.connectAttr(ReflNode+".outTex", Specmat+".Reflection")
                        mc.setAttr(mat+".Index", 1.6)
                    else:
                        ReflNode = createOctaneFileNode(ReflAdjustNode, matInfo["REFL_"], matName+"_REFLECTION", "Texture1", False, UVScaleNode)
                        mc.octane(texfpin=(ReflAdjustNode+".Texture2", 1))
                        mc.setAttr(mat+".Index", 1)
                        if "TRANSMISSION_" in matInfo:
                            mc.connectAttr(ReflNode+".outTex", Specmat+".Reflection")

                    # Gloss
                    GlossMultiplyNode = mc.shadingNode("octaneMultiplyTexture", asTexture=True)
                    GlossMultiplyNode = mc.rename(GlossMultiplyNode, matName+"_GLOSS_ADJUST")
                    mc.octane(texfpin=(GlossMultiplyNode+".Texture1", 1))
                    mc.octane(texfpin=(GlossMultiplyNode+".Texture2", 1))
                    mc.connectAttr(GlossMultiplyNode+".outTex", mat+".Roughness")
                    GlossNode = createOctaneFileNode(GlossMultiplyNode, matInfo["GLOSS_"], matName+"_GLOSS", "Texture1", False, UVScaleNode)
                    mc.setAttr(GlossNode+".Gamma", 1)
                    mc.setAttr(GlossNode+".Invert", True)
                    if "TRANSMISSION_" in matInfo:
                        mc.connectAttr(GlossNode+".outTex", Specmat+".Roughness")#CCGlossNode+".outTex"


                    # Normals
                    if "NRM16_" in matInfo and mc.checkBox(settings["BIT"], q=True, v=True):
                        NRMNode = createOctaneFileNode(mat, matInfo["NRM16_"], matName+"_NORMALS", "Normal", False, UVScaleNode)
                    else:
                        NRMNode = createOctaneFileNode(mat, matInfo["NRM_"], matName+"_NORMALS", "Normal", False, UVScaleNode)

                    # Displacement
                    if mc.checkBox(settings["DISP"], q=True, v=True) and ("DISP_" in matInfo or ("DISP16_" in matInfo and mc.checkBox(settings["BIT"], q=True, v=True))):
                        DispNode = mc.shadingNode("octaneDisplacementNode", asTexture=True)
                        mc.setAttr(DispNode+".Height", .1)
                        mc.setAttr(DispNode+".Offset", .5)
                        mc.connectAttr(DispNode+".outDisp", mat+".Displacement")
                        if "DISP16_" in matInfo and mc.checkBox(settings["BIT"], q=True, v=True):
                            DispFileNode = createOctaneFileNode(DispNode, matInfo["DISP16_"], matName+"_DISPLACEMENT", "Texture", False, UVScaleNode)
                        else:
                            DispFileNode = createOctaneFileNode(DispNode, matInfo["DISP_"], matName+"_DISPLACEMENT", "Texture", False, UVScaleNode)
                        mc.setAttr(DispFileNode+".Gamma", 1)
                        DispNode = mc.rename(DispNode, matName+"_DISPLACEMENT_NODE")

                    # Alphamasked
                    if "ALPHAMASKED_" in matInfo:
                        AlphaNode = mc.shadingNode("octaneAlphaImageTexture", asTexture=True)
                        mc.setAttr(AlphaNode+".File", matInfo["ALPHAMASKED_"], type="string")
                        mc.connectAttr(AlphaNode+".outTex", mat+".Opacity")
                        mc.connectAttr(UVScaleNode+".outTransform", AlphaNode+".Transform")
                        mc.rename(AlphaNode, matName+"_ALPHA")

                    # SSS
                    if "SSS_" in matInfo:
                        Specmat = mc.shadingNode("octaneSpecularMaterial", asShader=True)
                        mc.setAttr(Specmat+".Index", 1)
                        createOctaneFileNode(Specmat, matInfo["SSS_"], matName+"_SSS", "Transmission", False, UVScaleNode)
                        mc.octane(texcpin=(Specmat+".Reflection", 0, 0, 0))
                        mc.octane(texfpin=(Specmat+".Roughness", 0))
                        ScatteringMedium = mc.shadingNode("octaneScatteringMedium", asTexture=True)
                        mc.connectAttr(ScatteringMedium+".outMedium", Specmat+".Medium")
                        mc.setAttr(ScatteringMedium+".Scale", 3)
                        mc.octane(texfpin=(ScatteringMedium+".Absorption", 1))
                        mc.octane(texfpin=(ScatteringMedium+".Scattering", 0.1))
                        ScatteringMedium = mc.rename(ScatteringMedium, matName+"_ScatteringMedium")
                        
                        Mixmat = mc.shadingNode("octaneMixMaterial", asShader=True)
                        mc.connectAttr(Specmat+".outMaterial", Mixmat+".Material1")
                        mc.connectAttr(mat+".outMaterial", Mixmat+".Material2")
                        mc.octane(texfpin=(Mixmat+".Amount", 0.2))
                        
                        SSSNode = createOctaneFileNode(Mixmat, matInfo["SSS_"], matName+"_SSS1", "Amount", False, UVScaleNode)
                        mc.setAttr(SSSNode+".Gamma", 1.0)
                        
                        mc.rename(mat, matName+"_GLOSSY")
                        mat = mc.rename(Mixmat, matName)
                        #Mixmat = mc.rename(Mixmat, matName+"_MIX")
                        Specmat = mc.rename(Specmat, matName+"_SPECULAR")
                        
                        if "ALPHAMASKED_" in matInfo and "MASK_" in matInfo :
                            pFloatTex = mc.shadingNode("octaneFloatTexture", asShader=True, name=matName+"_Roughness")
                            mc.setAttr(pFloatTex+".Value", 0.1)
                            mc.connectAttr(pFloatTex+".outTex", Specmat+'.Roughness')

                    # Transmission
                    if "TRANSMISSION_" in matInfo:
                        # Create a mix material
                        Mixmat = mc.shadingNode("octaneMixMaterial", asShader=True)
                        #mc.connectAttr(TransmissionMap+".outTex", Mixmat+".Amount")
                        mc.connectAttr(Specmat+".outMaterial", Mixmat+".Material1")
                        mc.connectAttr(mat+".outMaterial", Mixmat+".Material2")
                        Mixmat = mc.rename(Mixmat, matName+"_MIX")
                        
                        TransmissionMap = createOctaneFileNode(Mixmat, matInfo["TRANSMISSION_"], matName+"_TRANSMISSION", "Amount", False, UVScaleNode)
                        mc.connectAttr(ColNode+".outTex", Specmat+".Transmission")
                        mc.connectAttr(NRMNode+".outTex", Specmat+".Normal")
                        mc.setAttr(Specmat+".FakeShadows", True)
                        
                        mat = Mixmat

                    # Load the models
                    if internal:
                        model = loadObj(mat, matn)

                    # Create the preview spherers
                    previewSphere(mat, matInfo)
                    
                    mc.select(mat)

                    setLoadedIcon(matName)

    return True


# Create the Renderman materials
def createRendermanMat():
    global settings
    global progressBar

    # Create a progress bar
    if not internal:
        progressBar = PMC_ProgressBar()
        progressBar.createWindow()

    for workflow in mapDict:
        if workflow != "METALNESS":
            for res in mapDict[workflow]:
                for matn in mapDict[workflow][res]:

                    matName = (matn+"_"+res).replace("__", "_")
                    sys.stdout.write('\nLoading material ' + matName + "...")

                    # Renderman is not supported in internal atm, but leave it here incase we want to support it in the future
                    if internal:
                        matInfo2 = mapDict[workflow][res][matn]
                        matInfo = CreateFolder(mapDict[workflow][res][matn], matn, 'Octane')
                        mc.setAttr("defaultRenderGlobals.currentRenderer", "OctaneRender", type="string")
                    else:
                        matInfo = mapDict[workflow][res][matn]
                        progressBar.updateBar(matName)
                    
                    if "ALPHAMASKED_" in matInfo :
                        matInfo["COL_"] = matInfo["ALPHAMASKED_"]

                    # Create material
                    mat = mc.shadingNode("PxrSurface", asShader=True)
                    if "unknown" in mat:
                        mc.delete(mat)
                        return False
                    mat = mc.rename(mat, matName)

                    colorSpace = getColorSpace()

                    mc.setAttr(mat+".specularModelType", 1)
                    # Some properties that'll differ depending if it's a metal or not
                    if workflow == "SPECULAR":
                        mc.setAttr(mat+".specularFresnelShape", 0)
                    else:
                        mc.setAttr(mat+".specularFresnelMode", 1)


                    # Color & AO
                    if "AO_" in matInfo and mc.checkBox(settings["AO"], q=True, v=True):
                        # AO map exists
                        CompNode = mc.shadingNode("layeredTexture", asTexture=True)
                        CreateFileNode(CompNode, matInfo["AO_"], matName+"_AO", "inputs[0].color", False, False, False, mat)
                        ColNode = CreateFileNode(CompNode, matInfo["COL_"], matName+"_COLOR", "inputs[1].color", False, False, False, mat)[0]
                        mc.setAttr(CompNode+".inputs[0].blendMode", 6)
                        mc.connectAttr(CompNode+".outColor", mat+".diffuseColor")
                        CompNode = mc.rename(CompNode, matName+"_COL_AO_MULTIPLY")
                    else:
                        # No AO map found, only load the color
                        ColNode = CreateFileNode(mat, matInfo["COL_"], matName+"_COL", "diffuseColor", False, False, False, mat)[0]


                    # Reflection (invert if it's non metallic)
                    if workflow == "SPECULAR":
                        ReflNode = CreateFileNode(mat, matInfo["REFL_"], matName+"_REFL", "specularEdgeColor", False, False, False, mat)[0]
                    else:
                        ReflNode = CreateFileNode(mat, matInfo["REFL_"], matName+"_REFL", "specularEdgeColor", False, True, False, mat)[0]

                    # Gloss
                    GlossNode = CreateFileNode(mat, matInfo["GLOSS_"], matName+"_GLOSS", None, False, True, False, mat)[0]
                    mc.setAttr(GlossNode+".colorSpace", colorSpace, type="string")
                    mc.connectAttr(GlossNode+".outColor.outColorR", mat+".specularRoughness")


                    # NORMALS
                    nrmMap = mc.shadingNode("PxrNormalMap", asTexture=True)
                    nrmMap = mc.rename(nrmMap, matName+"_PxrNRM")
                    mc.connectAttr(nrmMap+".resultN", mat+".bumpNormal")

                    if "NRM16_" in matInfo and mc.checkBox(settings["BIT"], q=True, v=True):
                        # Load the 16bit nrm map
                        nrmNode = CreateFileNode(nrmMap, matInfo["NRM16_"], matName+"_NRM16", "inputRGB", False, False, False, mat)[0]
                    else:
                        # Renderman can't handle 8bit jpgs as nrm maps, solved by inserting a gamma node inbetween.
                        nrmGammaNode = mc.shadingNode("gammaCorrect", asTexture=True)
                        nrmGammaNode = mc.rename(nrmGammaNode, matName+"_gammaCorrectNRM")
                        nrmNode = CreateFileNode(nrmGammaNode, matInfo["NRM_"], matName+"_NRM", "value", False, False, False, mat)[0]
                        mc.connectAttr(nrmGammaNode+".outValue", nrmMap+".inputRGB")
                        for channel in ["X", "Y", "Z"]:
                            mc.setAttr(nrmGammaNode+".gamma"+channel, 2.2)

                    mc.setAttr(nrmNode+".colorSpace", colorSpace, type="string")
                    mc.setAttr(nrmMap+".orientation", 0)


                    # DISPLACEMENT
                    if mc.checkBox(settings["DISP"], q=True, v=True) and ("DISP_" in matInfo or ("DISP16_" in matInfo and mc.checkBox(settings["BIT"], q=True, v=True))):
                        ShadingEngine = mc.sets(renderable=True, noSurfaceShader=True, empty=True, name=matName+"_SG")
                        DispNode = mc.shadingNode("PxrDisplace", asShader=True)
                        DispNode = mc.rename(DispNode, matName+"_PxrDISP")
                        mc.connectAttr(DispNode+".outColor", ShadingEngine+".displacementShader")
                        mc.connectAttr(mat+".outColor", ShadingEngine+".surfaceShader")
                        mc.setAttr(DispNode+".dispAmount", 0.1)
                        if "DISP16_" in matInfo and mc.checkBox(settings["BIT"], q=True, v=True):
                            dispFileNode = CreateFileNode(mat, matInfo["DISP16_"], matName+"_DISP16", None, False, False, False, mat)[0]
                        else:
                            dispFileNode = CreateFileNode(mat, matInfo["DISP_"], matName+"_DISP", None, False, False, False, mat)[0]
                        mc.setAttr(dispFileNode+".colorSpace", colorSpace, type="string")
                        mc.connectAttr(dispFileNode+".outColor.outColorR", DispNode+".dispScalar")

                    # Alphamasked
                    if "ALPHAMASKED_" in matInfo:
                        mc.connectAttr(ColNode+".outAlpha", mat+".presence")

                    # Load the models
                    if internal:
                        model = loadObj(mat, matn)

                    # Create the preview spherers
                    previewSphere(mat, matInfo)

                    setLoadedIcon(matName)

    return True


#   #   #   #   #   #   #   #   #   #
#        Creating File nodes        #
#   #   #   #   #   #   #   #   #   #


# Create an octane image texture
def createOctaneFileNode(mat, fname, name, connection, invert, UVScaleNode):
    Node = mc.shadingNode("octaneImageTexture", asTexture=True)
    mc.setAttr(Node+".File", fname, type="string")
    mc.setAttr(Node+".Invert", invert)
    if connection != None:
        mc.connectAttr(Node+".outTex", mat+"."+connection)
    Node = mc.rename(Node, name)
    mc.connectAttr(UVScaleNode+".outTransform", Node+".Transform")
    return Node


# Create a file node and load the texture into it
def CreateFileNode(mat, fname, name, connection, cc, invert, convert, fullMat, pOut='outColor'):
    Engine = mc.optionMenu(settings["renderer"], q=True, value=True)
    Node = mc.shadingNode("file", asTexture=True)
    output = Node + "."+pOut
    outputNode = Node
    mc.setAttr(Node+".fileTextureName", fname, type="string")
    UVNode = connectUVNode(Node, fullMat)
    if cc:
        if Engine == "Arnold":
            try :
                CCNode = mc.shadingNode("aiColorCorrect", asTexture=True)
                mc.connectAttr(Node+"."+pOut, CCNode+".input")
            except :
                CCNode = mc.shadingNode("colorCorrect", asTexture=True)
                mc.connectAttr(Node+"."+pOut, CCNode+".inColor")
        else:
            CCNode = mc.shadingNode("colorCorrect", asTexture=True)
            mc.connectAttr(Node+"."+pOut, CCNode+".inColor")
        CCNode = mc.rename(CCNode, name+"_CC")
        outputNode = CCNode
        output = CCNode + "."+pOut
    if invert:
        if Engine == "Arnold":
            try :
                mc.setAttr(CCNode+".invert", True)
            except :
                pass
        else:
            mc.setAttr(Node+".invert", True)
    if convert:
        try :
            ToFloatNode = mc.shadingNode("aiColorToFloat", asTexture=True)
            mc.connectAttr(output, ToFloatNode+".input")
            ToFloatNode = mc.rename(ToFloatNode, name+"_ToFloat")
            outputNode = ToFloatNode
            output = ToFloatNode+".outValue"
        except :
            pass
    if connection != None:
        mc.connectAttr(output, mat+"."+connection)
    Node = mc.rename(Node, name)
    if cc and Engine == "Arnold":
        return(Node, outputNode, CCNode)
    return(Node, outputNode)


# Create and connect a UV node into the file node
# If a UV node already exists, use that one
def connectUVNode(Node, mat):
    global UVNodes
    if mat not in UVNodes:
        global settings
        UVNode = mc.shadingNode("place2dTexture", asUtility=True)
        UVNode = mc.rename(UVNode, mat+"_UV")
        UVNodes[mat] = UVNode
        if mc.checkBox(settings["CONF"], q=True, v=True):
            width, height = mc.getAttr(Node+".outSize")[0]
            if width != height:
                if height > width:
                    mc.setAttr(UVNode+".repeatU", float(height)/width)
                else:
                    mc.setAttr(UVNode+".repeatV", float(width)/height)
    else:
        UVNode = UVNodes[mat]
    for connect in [".coverage", ".translateFrame", ".rotateFrame", ".mirrorU", ".mirrorV", ".stagger", ".wrapU", ".wrapV",
     ".repeatUV", ".offset", ".noiseUV", ".vertexUvOne", ".vertexUvTwo", ".vertexUvThree", ".vertexCameraOne"]:
        mc.connectAttr(UVNode+connect, Node+connect)
    mc.connectAttr(UVNode+".outUV", Node+".uv")
    mc.connectAttr(UVNode+".outUvFilterSize", Node+".uvFilterSize")
    return UVNode


# Create the preview spheres
def previewSphere(mat, matInfo):
    global settings
    global offset
    if mc.checkBox(settings["PREV"], q=True, v=True):
        Engine = mc.optionMenu(settings["renderer"], q=True, value=True)
        sphere, sphereShape = mc.polySphere(n="PreviewSphere_"+mat, r=2, sh=32, sa=64)
        mc.setAttr(sphere+".translateX", (offset*5)+2.5)
        mc.select(sphere, r=True)
        mc.hyperShade(a=mat)
        offset+=1
        if "ALPHAMASKED_" in matInfo:
            if Engine == "Arnold":
                mc.setAttr(sphere+".aiOpaque", False)
        return sphere
    return False


#   #   #   #   #   #   #   #   #   #
#        Internal Operations        #
#   #   #   #   #   #   #   #   #   #


# Update UI when some features are turned on/off (Internal Only)
def InternalCheckboxUpdate(checkbox, self=None):

    # If all renderers is True, disable the selection of a specific renderer
    if checkbox == "All_Renderers":
        if mc.checkBox(settings["Ball"], q=True, value=True):
            mc.optionMenu(settings["renderer"], enable=False, e=True)
        else:
            mc.optionMenu(settings["renderer"], enable=True, e=True)

# Get all of the maya files in the light_setups folder and place them in the light setup dropdown (Internal Only)
def getLightsetups():
    global LightSetups
    SCRIPT_PATH = os.path.join(mc.internalVar(usd=True), 'poliigon_material_converter', 'light_setups')

    # Check if dir exists, otherwise create it
    if not os.path.exists(SCRIPT_PATH):
        os.makedirs(SCRIPT_PATH)
        return False

    # Search the root for any maya files
    for root, dirs, files in os.walk(SCRIPT_PATH):
        for name in files:
            if os.path.splitext(name)[1] in ['.mb', '.ma']:
                LightSetups[name] = os.path.join(root, name)
    LightSetups["<None>"] = None


# Load the models (internal only)
def loadObj(mat, matn):
    global OBJlist
    for obj in OBJlist:
        # Check if there's a model with the same name as the material, if so, load that one
        if matn == os.path.basename(obj).split('.')[0]:

            prevMats = mc.ls(mat=True)
            imported_models = mc.file(obj, i=True, rnn=True) # import the fbx/obj file
            postMats = mc.ls(mat=True)
            models = []
            Imported_materials = mc.ls(imported_models, mat=True)
            print ("Imported Mats:")
            print (Imported_materials)
            # Compare material's before and after import to delete any materials that was imported
            deletedMats = []
            for temp_mat in postMats:
                if temp_mat not in prevMats:
                    mc.delete(temp_mat)
                    deletedMats.append(temp_mat)
                    print ("Deleting")
                    print (temp_mat)

            print ("Pre")
            print (prevMats)
            print ("Post")
            print (postMats)
            # Get the transform nodes for each model
            for ob in imported_models:
                if ob not in deletedMats:
                    if mc.objectType(ob) == "transform":
                        models.append(ob)

            # Go through each model and do some settings
            for model in models:
                # If the model was imported from an .obj, scale it up 100 units
                if "obj" == os.path.basename(obj).split('.')[1]:
                    for axis in ["X", "Y", "Z"]:
                        mc.setAttr(model+".scale"+axis, 100)

                # Freeze scale & rotations
                mc.makeIdentity(model, apply=True, s=1, r=1)

                # Apply the material to the model
                mc.select(model[1:], r=True)
                mc.hyperShade(a=mat)
            return models
    return False


# Create the folder where the maya file + textures will be saved (internal only)
def CreateFolder(matInfo, matn, engineName):
    global settings
    global SavePath
    from shutil import copyfile

    # get the folderpath, where to save the textures etc.
    if mc.checkBox(settings["ROOT"], q=True, v=True):
        folderPath = os.path.join(SavePath+engineName)
    else:
        folderPath = os.path.join(SavePath+engineName)

    # Create the dir
    if not os.path.isdir(folderPath):
        os.makedirs(folderPath)


    # Copy textures into the new folder & Create a new mapdict with relative filepaths
    matInfot = {}
    for texture in matInfo:
        texturePath = matInfo[texture]
        texName =  os.path.split(texturePath)[1]
        newTexturePath = os.path.join(folderPath, texName)
        copyfile(texturePath, newTexturePath)
        matInfot.update({texture:texName})

    # Import the light setup
    global lightsetup
    global LightSetups
    global ImportedLights
    if not ImportedLights:
        lightsetup_S = mc.optionMenu(lightsetup, q=True, value=True)
        if lightsetup_S != "<None>":
            fpath = LightSetups[lightsetup_S]
            mc.file(new=True, force=True)
            mc.file(fpath, o=True) # i=True
        ImportedLights = True

    return matInfot


# Save out the maya file and create a new one (internal only)
def SaveFile(engineName):
    global SavePath
    global SceneName

    # Create the folderpath were to save the file
    if mc.checkBox(settings["ROOT"], q=True, v=True):
        folderPath = os.path.join(SavePath+engineName)
    else:
        folderPath = os.path.join(SavePath+engineName)
    MayaFP = os.path.join(folderPath, SceneName+"_"+engineName+".ma")

    # Save file
    mc.file(rename=MayaFP)
    mc.file(save=True, type="mayaAscii")


    # Tell the file it's not been modified, to avoid any problems with creating the new file.
    #mc.file(modified=False)

    # Create a new file
    mc.file(newFile=True, force=True)



    if mc.checkBox(settings["rewriteAscii"], q=True, v=True):
        # Rewrite the file to unwanted info
        RewriteSourceFile(MayaFP, engineName)


# Internal Only
# When saving a Maya file with a plugin enabled, it saves unwated data in the file
# This causes errors later on when trying to open the file without plugin installed.
# RewriteSourceFile() Will read the ascii file and remove the unwanted data.
def RewriteSourceFile(filepath, engine):
    # Read file
    file = open(filepath, 'r+')
    content = file.readlines()
    newFileContent = ""
    checkIfNextLineContinue = None

    # Check each line if it should be removed or not
    for line in content:
        doNotAdd = False
        if checkIfNextLineContinue !=  None:
            if (checkIfNextLineContinue in line and "createNode " not in line) or line == "\n":
                doNotAdd = True
            else:
                checkIfNextLineContinue = None

        # Remove Vray data
        if engine != 'Vray' and 'fileInfo "vrayBuild"' in line:
            doNotAdd = True

        # Remove Octane data
        if engine != 'Octane':
            if '-dataType "oct' in line:
                doNotAdd = True
            if 'createNode octaneSettings -n "octaneSettings";' in line:
                doNotAdd = True
                checkIfNextLineContinue = "\t"
            if '" -ln "oct' in line:
                doNotAdd = True
                checkIfNextLineContinue = '\t\t'
            if "Octane" in line:
                doNotAdd = True
            if 'setAttr ".octoslc"' in line:
                doNotAdd = True

        # Remove Arnold data
        if engine != "Arnold":
            if 'requires "mtoa"' in line:
                doNotAdd = True
                checkIfNextLineContinue = "\t"
            elif 'setAttr ".ai_translator"' in line:
                doNotAdd = True
            elif 'setAttr ".ai_opaque" no;' in line:
                doNotAdd = True

        if not doNotAdd:
            newFileContent += line

    # Clear file of current content
    file.seek(0)
    file.truncate()

    # Write new content to file
    file.write(newFileContent)

    # Close File
    file.close()


#   #   #   #   #   #   #   #   #   #
#       Custom Error messages       #
#   #   #   #   #   #   #   #   #   #


# Toggle ON/OFF our custom exception hook
def TogglePMCExceptionHook(state):
    if state:
        maya.utils.formatGuiException = PMCExceptionHook
    else:
        maya.utils.formatGuiException = MayaDefaultExceptionHook


# Custom exception hook to catch any uncaught errors and display
# them to the user in a text box.
def PMCExceptionHook(etype, value, tb, detail=2):
    # Start by turning off the custom exception hook incase anything below would
    # throw an error, to make sure it doesn't get stuck in a loop.
    TogglePMCExceptionHook(False)

    # Close the progress bar
    global progressBar
    try:progressBar.closeWindow()
    except:pass

    msg = maya.utils._formatGuiException(etype, value, tb, 2)

    # Create the UI and display the message
    ErrorMsgDisplay(msg)

    return maya.utils._formatGuiException(etype, value, tb, 3)


# Window to display any uncaught errors
# The purpose of this is to make it easy for the user to copy paste
# the errors and send them to the support team.
# An idea would be to make an automatic send button
def ErrorMsgDisplay(msg):
    windowID = "ERROR"

    # Append some relevant info to the error message

    # Get the plugin version of the renderer the user was trying to convert too
    if "renderer" in settings:
        Engine = mc.optionMenu(settings["renderer"], q=True, value=True)
        PluginNames = {
            'Arnold':'mtoa',
            'Mental Ray':'Mayatomr',
            'OctaneRender':'OctanePlugin',
            'Redshift':'redshift4maya',
            'RenderMan':'RenderMan_for_Maya',
            'V-Ray':'vrayformaya'
        }
        try:
            PluginVersion = mc.pluginInfo(PluginNames[Engine], query=True, version=True)
        except:
            PluginVersion = " (version unknown)."
    else:
        # Might be none if the error occurs before the var renderer has been defined.
        Engine = "undefined"
        PluginVersion = ""

    SysInfo = 'Tool: Poliigon Material Converter v' + PMCversion +\
    '\nMaya: ' + str(mc.about(version=True)) +\
    '\nRenderer: ' + Engine + ' ' + PluginVersion +\
    '\nOS: ' + sys.platform

    # Create the final message
    msg = SysInfo + '\n' + msg

    # Delete the window if it already exists
    if mc.window(windowID.replace(" ","_"),q=True, exists=True):
        mc.deleteUI(windowID.replace(" ","_"))

    # Create the window
    window = mc.window(windowID, title=windowID, wh=(470,360), sizeable=True, maximizeButton=False)

    form = mc.formLayout(numberOfDivisions=100)

    # UI Elements
    labelTextR1 = mc.text(label='Oops, looks like you\'ve encountered an error.\nPlease copy the message below and send it to:', align="left")
    label_mail = mc.text(label='support@poliigon.com', align="left", font="boldLabelFont", w=130)
    ErrorMsg = mc.scrollField(editable=False, wordWrap=False, text=msg, w=50, h=50, ann="Commands:\nCtrl + A = Select All\nCtrl + C = Copy")
    sendMail = mc.button(label="Send", w=100, h=35, command=functools.partial(sendErrorEmail,msg, window), ann="Send this erorr message anonymously to the developers, Requires an internet connection.")
    buttonDismiss = mc.button(label="Dismiss", w=100, h=35, command=functools.partial(closeWindow, window), ann="Close this error window.")

    # Layout
    mc.formLayout( form, edit=True, attachForm=[
        (labelTextR1, 'top', 15), (labelTextR1, 'left', 10),
        (label_mail, 'top', 28), (label_mail, 'left', 255),
        (ErrorMsg, 'top', 50), (ErrorMsg, 'left', 10), (ErrorMsg, 'right', 10), (ErrorMsg, 'bottom', 50),
        (sendMail, 'bottom', 10), (sendMail, 'left', 10),
        (buttonDismiss, 'bottom', 10), (buttonDismiss, 'right', 10),
    ])

    # Draw the window
    mc.showWindow()


# Send an email with the error report
def sendErrorEmail(msg, window, self):
    # Import urllib
    try:
        import urllib2, urllib
    except:
        return False

    # I'm currently redirecting the mails through my nilssoderman.com server.
    # Though we might want to setup something similar on the poliigon.com server
    request_url = r"https://www.nilssoderman.com/cgi-bin/FormMail.pl"
    data = urllib.urlencode({
    'subject': 'Error: Maya Poliigon Material Converter v'+PMCversion,
    'Message': msg,
    'recipient': 'error@nilssoderman.com'
    })

    # Make the request and send the email
    req = urllib2.Request(request_url, data)
    try:
        # Try to send the mail, might fail if there is not internet connection or incase there would be any problem with the server.
        # Wait 10 seconds before returning false, there's so little data sent that 10 sec should be more than enough.
        urllib2.urlopen(req, timeout = 10)
        sent = True
    except:
        # Failed to send the email, most likely due to connection issues
        sent = False
    if sent:
        # Inform the user that the message has been sent
        mc.confirmDialog(t="Sent", m="Error message was successfully sent.", b="OK")
        closeWindow(window, None)
    else:
        mc.confirmDialog(t="Error: Failed to send message.", m="Message could not be sent, please check your internet connection.\nOr copy the message and send it manually to poliigon.com.", b="OK", icn="critical")


#   #   #   #   #   #   #   #   #   #
#              MISC                 #
#   #   #   #   #   #   #   #   #   #


# Progress bar
class PMC_ProgressBar():

    # Variables
    MaterialName = None
    progressBar = None
    window = None

    # Draw the UI
    def createWindow(self):
        # Remove window if it already exists
        self.window = "PMC_Progress_Bar"

        if mc.window(self.window, q=True, exists=True):
            try:
                mc.deleteUI(mc.window(self.window))
            except:
                pass
        
        if not mc.window(self.window, q=True, exists=True):
            # Create the window
            mc.window(self.window, title="Loading Materials...", sizeable=False, wh=(160,50), mxb=False)

            # UI Elements
            mc.columnLayout()
            mc.text('PMC_Progressbar_Loading', label="Loading...", fn="boldLabelFont", width=160, height=25)
            mc.progressBar('PMC_Progressbar', maxValue=nMats, width=160)

        # Show the window and resize it correctly
        mc.showWindow(self.window)
        mc.window(self.window, e=True, wh=(160,50))

    # Update the % as well as the name of the material currently beeing loaded
    def updateBar(self, matName):
        mc.text('PMC_Progressbar_Loading', label="Loading: "+matName, e=True)
        mc.progressBar('PMC_Progressbar', edit=True, step=1)

    # Close the window
    def closeWindow(self):
        try:
            mc.deleteUI(self.window)
        except:
            pass


# Close a window, This really doesn't need to be it's own def...
def closeWindow(windowID, self):
    mc.deleteUI(windowID)


# Called when the script runs
def main(ih = internal):
    global internal
    internal = ih
    if internal:
        global OBJlist
        OBJlist = []
        global lightsetup
        lightsetup = None
        global LightSetups
        LightSetups = {"<None>":None}
        global ImportedLights
        ImportedLights = False
        global SavePath
        SavePath = ""
        global folderPath
        folderPath = ""
        global SceneName
        SceneName = ""
        getLightsetups()
    createUI()


if __name__=='__main__':
    main()
