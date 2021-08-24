## Classes

<dl>
<dt><a href="#DzBridgeAutoWeight">DzBridgeAutoWeight</a></dt>
<dd></dd>
<dt><a href="#DzBridgeExporter">DzBridgeExporter</a></dt>
<dd></dd>
<dt><a href="#DzBridgeDialog">DzBridgeDialog</a></dt>
<dd></dd>
<dt><a href="#DzBridgeEnvironment">DzBridgeEnvironment</a></dt>
<dd></dd>
<dt><a href="#DzBridgeFigure">DzBridgeFigure</a></dt>
<dd></dd>
<dt><a href="#DzBridgeHelpers">DzBridgeHelpers</a></dt>
<dd></dd>
<dt><a href="#DzBridgeMorphs">DzBridgeMorphs</a></dt>
<dd></dd>
<dt><a href="#DzBridgePose">DzBridgePose</a></dt>
<dd></dd>
<dt><a href="#DzBridgeScene">DzBridgeScene</a></dt>
<dd></dd>
<dt><a href="#DzBridgeSubdivision">DzBridgeSubdivision</a></dt>
<dd></dd>
<dt><a href="#DzBridgeWriter">DzBridgeWriter</a></dt>
<dd></dd>
</dl>

<a name="DzBridgeAutoWeight"></a>

## DzBridgeAutoWeight
**Kind**: global class  

* [DzBridgeAutoWeight](#DzBridgeAutoWeight)
    * [new DzBridgeAutoWeight(sRootPath)](#new_DzBridgeAutoWeight_new)
    * [.getActiveMorphs(oNode)](#DzBridgeAutoWeight+getActiveMorphs) ⇒ <code>DzNode</code>
    * [.zeroOutMorphs(oActiveMorphs)](#DzBridgeAutoWeight+zeroOutMorphs)
    * [.returnMorphValues(oActiveMorphs)](#DzBridgeAutoWeight+returnMorphValues)
    * [.transferWeights(oSource, oTarget)](#DzBridgeAutoWeight+transferWeights) ⇒ <code>Boolean</code>
    * [.findingPropsToWeight(oSource, oParent)](#DzBridgeAutoWeight+findingPropsToWeight)
    * [.weightObjects(oBaseNode)](#DzBridgeAutoWeight+weightObjects)

<a name="new_DzBridgeAutoWeight_new"></a>

### new DzBridgeAutoWeight(sRootPath)
Used to weight non-skinned geometry on Nodes with a skeleton


| Param | Type |
| --- | --- |
| sRootPath | <code>String</code> | 

<a name="DzBridgeAutoWeight+getActiveMorphs"></a>

### dzBridgeAutoWeight.getActiveMorphs(oNode) ⇒ <code>DzNode</code>
Object : Helper function to deselect everything in the scene.

**Kind**: instance method of [<code>DzBridgeAutoWeight</code>](#DzBridgeAutoWeight)  
**Returns**: <code>DzNode</code> - Contains all the active morphs on the node given with its property and value  

| Param | Type | Description |
| --- | --- | --- |
| oNode | <code>DzNode</code> | a given figure that has morphs |

<a name="DzBridgeAutoWeight+zeroOutMorphs"></a>

### dzBridgeAutoWeight.zeroOutMorphs(oActiveMorphs)
Void: Applys the default values of the morphs that are active

**Kind**: instance method of [<code>DzBridgeAutoWeight</code>](#DzBridgeAutoWeight)  

| Param | Type | Description |
| --- | --- | --- |
| oActiveMorphs | <code>Object</code> | All the active morphs found on the specific figure. |

<a name="DzBridgeAutoWeight+returnMorphValues"></a>

### dzBridgeAutoWeight.returnMorphValues(oActiveMorphs)
Void: Applys the user input values of the morphs that are active

**Kind**: instance method of [<code>DzBridgeAutoWeight</code>](#DzBridgeAutoWeight)  

| Param | Type | Description |
| --- | --- | --- |
| oActiveMorphs | <code>Object</code> | All the active morphs found on the specific figure. |

<a name="DzBridgeAutoWeight+transferWeights"></a>

### dzBridgeAutoWeight.transferWeights(oSource, oTarget) ⇒ <code>Boolean</code>
Bool : Runs Transfer Utility and return if it was a success or not.

**Kind**: instance method of [<code>DzBridgeAutoWeight</code>](#DzBridgeAutoWeight)  
**Returns**: <code>Boolean</code> - Returns if the DzTransferUtility was a success or not  

| Param | Type | Description |
| --- | --- | --- |
| oSource | <code>DzNode</code> | Source Figure used to get the weights |
| oTarget | <code>DzNode</code> | Target prop which is unweighted and needs auto-weights |

<a name="DzBridgeAutoWeight+findingPropsToWeight"></a>

### dzBridgeAutoWeight.findingPropsToWeight(oSource, oParent)
Void: Cycles through the Children of the Parents and does loop for Auto-Weights

**Kind**: instance method of [<code>DzBridgeAutoWeight</code>](#DzBridgeAutoWeight)  

| Param | Type | Description |
| --- | --- | --- |
| oSource | <code>DzNode</code> | Source Figure used to get the weights |
| oParent | <code>DzNode</code> | Parent Figure used for find the Children |

<a name="DzBridgeAutoWeight+weightObjects"></a>

### dzBridgeAutoWeight.weightObjects(oBaseNode)
Void: Used to run the Auto-Weight logic, This is Destructive and break user's scene

**Kind**: instance method of [<code>DzBridgeAutoWeight</code>](#DzBridgeAutoWeight)  

| Param | Type | Description |
| --- | --- | --- |
| oBaseNode | <code>DzNode</code> | The Top Node of the hierachy |

<a name="DzBridgeExporter"></a>

## DzBridgeExporter
**Kind**: global class  

* [DzBridgeExporter](#DzBridgeExporter)
    * [new DzBridgeExporter(sDazBridgeName, sScriptPath, oBridgeScene)](#new_DzBridgeExporter_new)
    * [.sDazBridgeName](#DzBridgeExporter+sDazBridgeName) : <code>String</code>
    * [.sRootPath](#DzBridgeExporter+sRootPath) : <code>String</code>
    * [.sCustomPath](#DzBridgeExporter+sCustomPath) : <code>String</code>
    * [.sPresetPath](#DzBridgeExporter+sPresetPath) : <code>String</code>
    * [.sConfigPath](#DzBridgeExporter+sConfigPath) : <code>String</code>
    * [.sMorphPath](#DzBridgeExporter+sMorphPath) : <code>String</code>
    * [.sFbxPath](#DzBridgeExporter+sFbxPath) : <code>String</code>
    * [.init(sDazBridgeName, sScriptPath, oBridgeScene)](#DzBridgeExporter+init)
    * [.prepareForExport(oBridgeScene)](#DzBridgeExporter+prepareForExport)

<a name="new_DzBridgeExporter_new"></a>

### new DzBridgeExporter(sDazBridgeName, sScriptPath, oBridgeScene)
Used to Export out Daz


| Param | Type |
| --- | --- |
| sDazBridgeName | <code>String</code> | 
| sScriptPath | <code>String</code> | 
| oBridgeScene | [<code>DzBridgeScene</code>](#DzBridgeScene) | 

<a name="DzBridgeExporter+sDazBridgeName"></a>

### dzBridgeExporter.sDazBridgeName : <code>String</code>
Name of Bridge

**Kind**: instance property of [<code>DzBridgeExporter</code>](#DzBridgeExporter)  
<a name="DzBridgeExporter+sRootPath"></a>

### dzBridgeExporter.sRootPath : <code>String</code>
Path to the the Export Directory

**Kind**: instance property of [<code>DzBridgeExporter</code>](#DzBridgeExporter)  
<a name="DzBridgeExporter+sCustomPath"></a>

### dzBridgeExporter.sCustomPath : <code>String</code>
Path to the Custom Export Directory

**Kind**: instance property of [<code>DzBridgeExporter</code>](#DzBridgeExporter)  
<a name="DzBridgeExporter+sPresetPath"></a>

### dzBridgeExporter.sPresetPath : <code>String</code>
Path to the Preset Folder

**Kind**: instance property of [<code>DzBridgeExporter</code>](#DzBridgeExporter)  
<a name="DzBridgeExporter+sConfigPath"></a>

### dzBridgeExporter.sConfigPath : <code>String</code>
Path to the Configs Folder

**Kind**: instance property of [<code>DzBridgeExporter</code>](#DzBridgeExporter)  
<a name="DzBridgeExporter+sMorphPath"></a>

### dzBridgeExporter.sMorphPath : <code>String</code>
LastUsed.csv from Morph Dialog

**Kind**: instance property of [<code>DzBridgeExporter</code>](#DzBridgeExporter)  
<a name="DzBridgeExporter+sFbxPath"></a>

### dzBridgeExporter.sFbxPath : <code>String</code>
Path to FBX File

**Kind**: instance property of [<code>DzBridgeExporter</code>](#DzBridgeExporter)  
<a name="DzBridgeExporter+init"></a>

### dzBridgeExporter.init(sDazBridgeName, sScriptPath, oBridgeScene)
Void : Initilizes Variables

**Kind**: instance method of [<code>DzBridgeExporter</code>](#DzBridgeExporter)  

| Param | Type |
| --- | --- |
| sDazBridgeName | <code>String</code> | 
| sScriptPath | <code>String</code> | 
| oBridgeScene | [<code>DzBridgeScene</code>](#DzBridgeScene) | 

<a name="DzBridgeExporter+prepareForExport"></a>

### dzBridgeExporter.prepareForExport(oBridgeScene)
Void : Delete previous export and recreate directories if neededISSUE : Currently the Both Enum is handled incorrectly new logic is neededTODO: Refactor logic

**Kind**: instance method of [<code>DzBridgeExporter</code>](#DzBridgeExporter)  

| Param | Type |
| --- | --- |
| oBridgeScene | [<code>DzBridgeScene</code>](#DzBridgeScene) | 

<a name="DzBridgeDialog"></a>

## DzBridgeDialog
**Kind**: global class  
<a name="new_DzBridgeDialog_new"></a>

### new DzBridgeDialog(oBridgeExporter)
Contains the Dialogs for the User to Control


| Param | Type |
| --- | --- |
| oBridgeExporter | [<code>DzBridgeExporter</code>](#DzBridgeExporter) | 

<a name="DzBridgeEnvironment"></a>

## DzBridgeEnvironment
**Kind**: global class  
<a name="new_DzBridgeEnvironment_new"></a>

### new DzBridgeEnvironment()
Edits needed to export out Environements and Props.TODO: Change logic to match Unreal Export

<a name="DzBridgeFigure"></a>

## DzBridgeFigure
**Kind**: global class  
<a name="new_DzBridgeFigure_new"></a>

### new DzBridgeFigure(oFigure)
Constructs any data needed for Figures and Helper Functions for Export


| Param | Type |
| --- | --- |
| oFigure | <code>DzNode</code> | 

<a name="DzBridgeHelpers"></a>

## DzBridgeHelpers
**Kind**: global class  

* [DzBridgeHelpers](#DzBridgeHelpers)
    * [new DzBridgeHelpers(sDazBridgeName, sScriptPath, sRootPath, sFbxPath)](#new_DzBridgeHelpers_new)
    * [.sDazBridgeName](#DzBridgeHelpers+sDazBridgeName) : <code>String</code>
    * [.sRootPath](#DzBridgeHelpers+sRootPath) : <code>String</code>
    * [.sScriptPath](#DzBridgeHelpers+sScriptPath) : <code>String</code>
    * [.sFbxPath](#DzBridgeHelpers+sFbxPath) : <code>String</code>
    * [.sFig](#DzBridgeHelpers+sFig) : <code>String</code>
    * [.sEnv](#DzBridgeHelpers+sEnv) : <code>String</code>
    * [.sMorphRules](#DzBridgeHelpers+sMorphRules) : <code>String</code>
    * [.bIncludeAnim](#DzBridgeHelpers+bIncludeAnim) : <code>Boolean</code>
    * [.oMeshTypes](#DzBridgeHelpers+oMeshTypes)
    * [.oExportTypes](#DzBridgeHelpers+oExportTypes)
    * [.init(sDazBridgeName, sScriptPath, sRootPath, sFbxPath)](#DzBridgeHelpers+init)
    * [.executeSubScript(sScript, aArgs)](#DzBridgeHelpers+executeSubScript) ⇒ <code>Object</code>
    * [.getGroupProperties(oGroup, bTraverse, bRecurse)](#DzBridgeHelpers+getGroupProperties) ⇒ <code>Array.&lt;DzProperty&gt;</code>
    * [.getElementProperties(oGroup, bTraverse, bRecurse)](#DzBridgeHelpers+getElementProperties) ⇒ <code>Array.&lt;DzProperty&gt;</code>
    * [.exportFBX(oNode, sName, nIdx, sSuffix, bAscii)](#DzBridgeHelpers+exportFBX)
    * [.exportOBJ(oNode, sName, nIdx, bSelected)](#DzBridgeHelpers+exportOBJ)
    * [.importOBJ(sName, nIdx)](#DzBridgeHelpers+importOBJ)
    * [.getPropertyName(oProperty)](#DzBridgeHelpers+getPropertyName) ⇒ <code>String</code>
    * [.addTempDirectory()](#DzBridgeHelpers+addTempDirectory)
    * [.cleanUpTempFiles(sPath)](#DzBridgeHelpers+cleanUpTempFiles)
    * [.deSelectAll()](#DzBridgeHelpers+deSelectAll)
    * [.changeLock(oProperty, bLock)](#DzBridgeHelpers+changeLock)
    * [.setLock(oBaseNode, bLock, bIsFigure)](#DzBridgeHelpers+setLock)
    * [.getObjectType(oNode)](#DzBridgeHelpers+getObjectType) ⇒ <code>String</code>
    * [.getParentingData(oParentNode, oBaseNode)](#DzBridgeHelpers+getParentingData) ⇒ <code>Array.&lt;String&gt;</code>
    * [.getMeshType(oNode)](#DzBridgeHelpers+getMeshType) ⇒ <code>Number</code>

<a name="new_DzBridgeHelpers_new"></a>

### new DzBridgeHelpers(sDazBridgeName, sScriptPath, sRootPath, sFbxPath)

| Param | Type |
| --- | --- |
| sDazBridgeName | <code>String</code> | 
| sScriptPath | <code>String</code> | 
| sRootPath | <code>String</code> | 
| sFbxPath | <code>String</code> | 

<a name="DzBridgeHelpers+sDazBridgeName"></a>

### dzBridgeHelpers.sDazBridgeName : <code>String</code>
Name of Bridge

**Kind**: instance property of [<code>DzBridgeHelpers</code>](#DzBridgeHelpers)  
<a name="DzBridgeHelpers+sRootPath"></a>

### dzBridgeHelpers.sRootPath : <code>String</code>
Path to the Export Directory

**Kind**: instance property of [<code>DzBridgeHelpers</code>](#DzBridgeHelpers)  
<a name="DzBridgeHelpers+sScriptPath"></a>

### dzBridgeHelpers.sScriptPath : <code>String</code>
Path to where the executed script is located.

**Kind**: instance property of [<code>DzBridgeHelpers</code>](#DzBridgeHelpers)  
<a name="DzBridgeHelpers+sFbxPath"></a>

### dzBridgeHelpers.sFbxPath : <code>String</code>
Path to FBX File

**Kind**: instance property of [<code>DzBridgeHelpers</code>](#DzBridgeHelpers)  
<a name="DzBridgeHelpers+sFig"></a>

### dzBridgeHelpers.sFig : <code>String</code>
Keyword for Figure Exports

**Kind**: instance property of [<code>DzBridgeHelpers</code>](#DzBridgeHelpers)  
<a name="DzBridgeHelpers+sEnv"></a>

### dzBridgeHelpers.sEnv : <code>String</code>
Keyword for Env/Prop Exports

**Kind**: instance property of [<code>DzBridgeHelpers</code>](#DzBridgeHelpers)  
<a name="DzBridgeHelpers+sMorphRules"></a>

### dzBridgeHelpers.sMorphRules : <code>String</code>
Used for the FBX Exporter to export user's Morphs

**Kind**: instance property of [<code>DzBridgeHelpers</code>](#DzBridgeHelpers)  
<a name="DzBridgeHelpers+bIncludeAnim"></a>

### dzBridgeHelpers.bIncludeAnim : <code>Boolean</code>
Enable or Disable Animation Export

**Kind**: instance property of [<code>DzBridgeHelpers</code>](#DzBridgeHelpers)  
<a name="DzBridgeHelpers+oMeshTypes"></a>

### dzBridgeHelpers.oMeshTypes
Types of Meshes

**Kind**: instance property of [<code>DzBridgeHelpers</code>](#DzBridgeHelpers)  
**Properties**

| Name | Type |
| --- | --- |
| Figure | <code>Number</code> | 
| Mesh | <code>Number</code> | 
| Other | <code>Number</code> | 
| Bone | <code>Number</code> | 
| NoFacets | <code>Number</code> | 
| Empty | <code>Number</code> | 

<a name="DzBridgeHelpers+oExportTypes"></a>

### dzBridgeHelpers.oExportTypes
Types of Exports

**Kind**: instance property of [<code>DzBridgeHelpers</code>](#DzBridgeHelpers)  
**Properties**

| Name | Type |
| --- | --- |
| Both | <code>Number</code> | 
| Figure | <code>Number</code> | 
| EnvProp | <code>Number</code> | 
| None | <code>Number</code> | 

<a name="DzBridgeHelpers+init"></a>

### dzBridgeHelpers.init(sDazBridgeName, sScriptPath, sRootPath, sFbxPath)
Void : Initilizes Variables

**Kind**: instance method of [<code>DzBridgeHelpers</code>](#DzBridgeHelpers)  

| Param | Type |
| --- | --- |
| sDazBridgeName | <code>String</code> | 
| sScriptPath | <code>String</code> | 
| sRootPath | <code>String</code> | 
| sFbxPath | <code>String</code> | 

<a name="DzBridgeHelpers+executeSubScript"></a>

### dzBridgeHelpers.executeSubScript(sScript, aArgs) ⇒ <code>Object</code>
Object : Executes a Script with a given script name

**Kind**: instance method of [<code>DzBridgeHelpers</code>](#DzBridgeHelpers)  

| Param | Type |
| --- | --- |
| sScript | <code>String</code> | 
| aArgs | <code>Array</code> | 

<a name="DzBridgeHelpers+getGroupProperties"></a>

### dzBridgeHelpers.getGroupProperties(oGroup, bTraverse, bRecurse) ⇒ <code>Array.&lt;DzProperty&gt;</code>
Array<DzProperty> : A function for getting a list of the properties in a group

**Kind**: instance method of [<code>DzBridgeHelpers</code>](#DzBridgeHelpers)  

| Param | Type |
| --- | --- |
| oGroup | <code>DzNode</code> | 
| bTraverse | <code>Boolean</code> | 
| bRecurse | <code>Boolean</code> | 

<a name="DzBridgeHelpers+getElementProperties"></a>

### dzBridgeHelpers.getElementProperties(oGroup, bTraverse, bRecurse) ⇒ <code>Array.&lt;DzProperty&gt;</code>
Array<DzProperty> : A function for getting the list properties for an element

**Kind**: instance method of [<code>DzBridgeHelpers</code>](#DzBridgeHelpers)  

| Param | Type |
| --- | --- |
| oGroup | <code>DzNode</code> | 
| bTraverse | <code>Boolean</code> | 
| bRecurse | <code>Boolean</code> | 

<a name="DzBridgeHelpers+exportFBX"></a>

### dzBridgeHelpers.exportFBX(oNode, sName, nIdx, sSuffix, bAscii)
Void : Silently exports FBX

**Kind**: instance method of [<code>DzBridgeHelpers</code>](#DzBridgeHelpers)  

| Param | Type |
| --- | --- |
| oNode | <code>DzNode</code> | 
| sName | <code>String</code> | 
| nIdx | <code>Number</code> | 
| sSuffix | <code>String</code> | 
| bAscii | <code>Boolean</code> | 

<a name="DzBridgeHelpers+exportOBJ"></a>

### dzBridgeHelpers.exportOBJ(oNode, sName, nIdx, bSelected)
Void : Silently exports OBJ

**Kind**: instance method of [<code>DzBridgeHelpers</code>](#DzBridgeHelpers)  

| Param | Type |
| --- | --- |
| oNode | <code>DzNode</code> | 
| sName | <code>String</code> | 
| nIdx | <code>Number</code> | 
| bSelected | <code>Boolean</code> | 

<a name="DzBridgeHelpers+importOBJ"></a>

### dzBridgeHelpers.importOBJ(sName, nIdx)
Void : Silently imports OBJ

**Kind**: instance method of [<code>DzBridgeHelpers</code>](#DzBridgeHelpers)  

| Param | Type |
| --- | --- |
| sName | <code>String</code> | 
| nIdx | <code>Number</code> | 

<a name="DzBridgeHelpers+getPropertyName"></a>

### dzBridgeHelpers.getPropertyName(oProperty) ⇒ <code>String</code>
String : Get the name of the Property

**Kind**: instance method of [<code>DzBridgeHelpers</code>](#DzBridgeHelpers)  
**Returns**: <code>String</code> - - Returns the name of the property  

| Param | Type |
| --- | --- |
| oProperty | <code>DzProperty</code> | 

<a name="DzBridgeHelpers+addTempDirectory"></a>

### dzBridgeHelpers.addTempDirectory()
Void : Helper function to create the temp directory if it doesn't exist

**Kind**: instance method of [<code>DzBridgeHelpers</code>](#DzBridgeHelpers)  
<a name="DzBridgeHelpers+cleanUpTempFiles"></a>

### dzBridgeHelpers.cleanUpTempFiles(sPath)
Void : Helper function to remove temporary files form a path

**Kind**: instance method of [<code>DzBridgeHelpers</code>](#DzBridgeHelpers)  

| Param | Type | Description |
| --- | --- | --- |
| sPath | <code>string</code> | Path of the temp folder used to export/import the obj |

<a name="DzBridgeHelpers+deSelectAll"></a>

### dzBridgeHelpers.deSelectAll()
Void : Helper function to deselect everything in the scene.

**Kind**: instance method of [<code>DzBridgeHelpers</code>](#DzBridgeHelpers)  
<a name="DzBridgeHelpers+changeLock"></a>

### dzBridgeHelpers.changeLock(oProperty, bLock)
Void : Change lock based on given Boolean

**Kind**: instance method of [<code>DzBridgeHelpers</code>](#DzBridgeHelpers)  

| Param | Type |
| --- | --- |
| oProperty | <code>DzProperty</code> | 
| bLock | <code>Boolean</code> | 

<a name="DzBridgeHelpers+setLock"></a>

### dzBridgeHelpers.setLock(oBaseNode, bLock, bIsFigure)
Void : Set lock for a node and all it's childen

**Kind**: instance method of [<code>DzBridgeHelpers</code>](#DzBridgeHelpers)  

| Param | Type |
| --- | --- |
| oBaseNode | <code>DzNode</code> | 
| bLock | <code>Boolean</code> | 
| bIsFigure | <code>Boolean</code> | 

<a name="DzBridgeHelpers+getObjectType"></a>

### dzBridgeHelpers.getObjectType(oNode) ⇒ <code>String</code>
String : Find out what type of Object we have

**Kind**: instance method of [<code>DzBridgeHelpers</code>](#DzBridgeHelpers)  
**Returns**: <code>String</code> - Object Type  

| Param | Type |
| --- | --- |
| oNode | <code>DzNode</code> | 

<a name="DzBridgeHelpers+getParentingData"></a>

### dzBridgeHelpers.getParentingData(oParentNode, oBaseNode) ⇒ <code>Array.&lt;String&gt;</code>
Array<String> : ...

**Kind**: instance method of [<code>DzBridgeHelpers</code>](#DzBridgeHelpers)  
**Returns**: <code>Array.&lt;String&gt;</code> - Parented nodes names  

| Param | Type |
| --- | --- |
| oParentNode | <code>DzNode</code> | 
| oBaseNode | <code>DzNode</code> | 

<a name="DzBridgeHelpers+getMeshType"></a>

### dzBridgeHelpers.getMeshType(oNode) ⇒ <code>Number</code>
Number  : ...

**Kind**: instance method of [<code>DzBridgeHelpers</code>](#DzBridgeHelpers)  
**Returns**: <code>Number</code> - Mesh Type  

| Param | Type |
| --- | --- |
| oNode | <code>DzNode</code> | 

<a name="DzBridgeMorphs"></a>

## DzBridgeMorphs
**Kind**: global class  

* [DzBridgeMorphs](#DzBridgeMorphs)
    * [new DzBridgeMorphs(sDazBridgeName, sScriptPath, sRootPath, sFbxPath)](#new_DzBridgeMorphs_new)
    * [.getMorphString(aExportableProperties)](#DzBridgeMorphs+getMorphString) ⇒ <code>String</code>
    * [.getErcKeyed(oErc, nIdx)](#DzBridgeMorphs+getErcKeyed) ⇒ <code>Object</code>
    * [.checkForMorphOnChild(oNode, aControlledMeshes, sMorphName)](#DzBridgeMorphs+checkForMorphOnChild) ⇒ <code>Array.&lt;String&gt;</code>
    * [.checkForBoneInChild(oNode, sBoneName, aControlledMeshes)](#DzBridgeMorphs+checkForBoneInChild) ⇒ <code>Array.&lt;String&gt;</code>
    * [.checkForBoneInAlias(oNode, oMorphProperty, aControlledMeshes)](#DzBridgeMorphs+checkForBoneInAlias) ⇒ <code>Array.&lt;String&gt;</code>
    * [.checkMorphControlsChildren(oNode, oMorphProperty)](#DzBridgeMorphs+checkMorphControlsChildren) ⇒ <code>Array.&lt;String&gt;</code>
    * [.loadMorphLinks(aExportableProperties, oNode)](#DzBridgeMorphs+loadMorphLinks)
    * [.disconnectMorphs(aExportableProperties)](#DzBridgeMorphs+disconnectMorphs)
    * [.reconnectMorphs(aExportableProperties)](#DzBridgeMorphs+reconnectMorphs)
    * [.disconnectSkeleton(oNode)](#DzBridgeMorphs+disconnectSkeleton)
    * [.reconnectSkeleton(oNode)](#DzBridgeMorphs+reconnectSkeleton)

<a name="new_DzBridgeMorphs_new"></a>

### new DzBridgeMorphs(sDazBridgeName, sScriptPath, sRootPath, sFbxPath)
Constructs the data of Morphs to be exported out of Daz.


| Param | Type |
| --- | --- |
| sDazBridgeName | <code>String</code> | 
| sScriptPath | <code>String</code> | 
| sRootPath | <code>String</code> | 
| sFbxPath | <code>String</code> | 

<a name="DzBridgeMorphs+getMorphString"></a>

### dzBridgeMorphs.getMorphString(aExportableProperties) ⇒ <code>String</code>
String : Converts the user's chosen morphs to a string for the fbx exporter

**Kind**: instance method of [<code>DzBridgeMorphs</code>](#DzBridgeMorphs)  
**Returns**: <code>String</code> - Contains all the active morphs on the node given with its property and value  

| Param | Type | Description |
| --- | --- | --- |
| aExportableProperties | <code>Array.&lt;DzMorphInfo&gt;</code> | contains the info needed to export the morphs out of Daz |

<a name="DzBridgeMorphs+getErcKeyed"></a>

### dzBridgeMorphs.getErcKeyed(oErc, nIdx) ⇒ <code>Object</code>
Object : Used to get the necessary data from the erclink for keyed data

**Kind**: instance method of [<code>DzBridgeMorphs</code>](#DzBridgeMorphs)  
**Returns**: <code>Object</code> - Contains the Keyed Data Rotation and Value  

| Param | Type | Description |
| --- | --- | --- |
| oErc | <code>DzERCLink</code> | ERCLink to the Morph Property |
| nIdx | <code>Number</code> | index for key value of the ERCLink |

<a name="DzBridgeMorphs+checkForMorphOnChild"></a>

### dzBridgeMorphs.checkForMorphOnChild(oNode, aControlledMeshes, sMorphName) ⇒ <code>Array.&lt;String&gt;</code>
Array : Find if Morph Exists on Children, Useful for FACS as they have their own versions.

**Kind**: instance method of [<code>DzBridgeMorphs</code>](#DzBridgeMorphs)  
**Returns**: <code>Array.&lt;String&gt;</code> - the Recieved Array with any objects found to contain the morph  

| Param | Type | Description |
| --- | --- | --- |
| oNode | <code>DzNode</code> | the Root Node/ Character that owns the morph |
| aControlledMeshes | <code>Array.&lt;String&gt;</code> | an Array for the morph that contains the current Objects that should have the morph. |
| sMorphName | <code>String</code> | Name of the Morph we are checking for |

<a name="DzBridgeMorphs+checkForBoneInChild"></a>

### dzBridgeMorphs.checkForBoneInChild(oNode, sBoneName, aControlledMeshes) ⇒ <code>Array.&lt;String&gt;</code>
Array : Find if Bone exists on Children and if it is weighted to see if we should export the morph on it

**Kind**: instance method of [<code>DzBridgeMorphs</code>](#DzBridgeMorphs)  
**Returns**: <code>Array.&lt;String&gt;</code> - the Recieved Array with any objects found to contain the morph  

| Param | Type | Description |
| --- | --- | --- |
| oNode | <code>DzNode</code> | the Root Node/ Character that owns the morph |
| sBoneName | <code>String</code> | the bone from the skeleton of the Root Node |
| aControlledMeshes | <code>Array.&lt;String&gt;</code> | an Array for the morph that contains the current Objects that should have the morph. |

<a name="DzBridgeMorphs+checkForBoneInAlias"></a>

### dzBridgeMorphs.checkForBoneInAlias(oNode, oMorphProperty, aControlledMeshes) ⇒ <code>Array.&lt;String&gt;</code>
Array : Check if the bone is an alias on the morph property

**Kind**: instance method of [<code>DzBridgeMorphs</code>](#DzBridgeMorphs)  
**Returns**: <code>Array.&lt;String&gt;</code> - the Recieved Array with any objects found to contain the morph  

| Param | Type | Description |
| --- | --- | --- |
| oNode | <code>DzNode</code> | the Root Node/ Character that owns the morph |
| oMorphProperty | <code>DzProperty</code> | - |
| aControlledMeshes | <code>Array.&lt;String&gt;</code> | an Array for the morph that contains the current Objects that should have the morph. |

<a name="DzBridgeMorphs+checkMorphControlsChildren"></a>

### dzBridgeMorphs.checkMorphControlsChildren(oNode, oMorphProperty) ⇒ <code>Array.&lt;String&gt;</code>
Array : Used as the main driver to find if we should include the morph on the child mesh.

**Kind**: instance method of [<code>DzBridgeMorphs</code>](#DzBridgeMorphs)  
**Returns**: <code>Array.&lt;String&gt;</code> - the Array with any objects found to contain the morph  

| Param | Type | Description |
| --- | --- | --- |
| oNode | <code>DzNode</code> | the Root Node/ Character that owns the morph |
| oMorphProperty | <code>DzProperty</code> | - |

<a name="DzBridgeMorphs+loadMorphLinks"></a>

### dzBridgeMorphs.loadMorphLinks(aExportableProperties, oNode)
Void : Load morph links to be exported out of the DTU

**Kind**: instance method of [<code>DzBridgeMorphs</code>](#DzBridgeMorphs)  

| Param | Type | Description |
| --- | --- | --- |
| aExportableProperties | <code>Array.&lt;DzMorphInfo&gt;</code> | contains the info needed to export the morphs out of Daz |
| oNode | <code>DzNode</code> | the Root Node/Character that owns the morph |

<a name="DzBridgeMorphs+disconnectMorphs"></a>

### dzBridgeMorphs.disconnectMorphs(aExportableProperties)
Void : disconnect the controllers from driving other morphs

**Kind**: instance method of [<code>DzBridgeMorphs</code>](#DzBridgeMorphs)  

| Param | Type | Description |
| --- | --- | --- |
| aExportableProperties | <code>Array.&lt;DzMorphInfo&gt;</code> | contains the info needed to export the morphs out of Daz |

<a name="DzBridgeMorphs+reconnectMorphs"></a>

### dzBridgeMorphs.reconnectMorphs(aExportableProperties)
Void : reconnect the controllers from driving other morphs

**Kind**: instance method of [<code>DzBridgeMorphs</code>](#DzBridgeMorphs)  

| Param | Type | Description |
| --- | --- | --- |
| aExportableProperties | <code>Array.&lt;DzMorphInfo&gt;</code> | contains the info needed to export the morphs out of Daz |

<a name="DzBridgeMorphs+disconnectSkeleton"></a>

### dzBridgeMorphs.disconnectSkeleton(oNode)
Void : Disconnect the skeleton so their arent driven by morphs

**Kind**: instance method of [<code>DzBridgeMorphs</code>](#DzBridgeMorphs)  

| Param | Type | Description |
| --- | --- | --- |
| oNode | <code>DzNode</code> | the Root Node/Character |

<a name="DzBridgeMorphs+reconnectSkeleton"></a>

### dzBridgeMorphs.reconnectSkeleton(oNode)
Void : Reconnect the skeleton so their arent driven by morphs

**Kind**: instance method of [<code>DzBridgeMorphs</code>](#DzBridgeMorphs)  

| Param | Type | Description |
| --- | --- | --- |
| oNode | <code>DzNode</code> | the Root Node/Character |

<a name="DzBridgePose"></a>

## DzBridgePose
**Kind**: global class  
<a name="new_DzBridgePose_new"></a>

### new DzBridgePose()
Constructs the data of the Pose to be Exported out of Daz.

<a name="DzBridgeScene"></a>

## DzBridgeScene
**Kind**: global class  

* [DzBridgeScene](#DzBridgeScene)
    * [new DzBridgeScene()](#new_DzBridgeScene_new)
    * [.checkChildType(oChildNode)](#DzBridgeScene+checkChildType) ⇒ <code>String</code>
    * [.overrideExportType(nExportType)](#DzBridgeScene+overrideExportType)

<a name="new_DzBridgeScene_new"></a>

### new DzBridgeScene()
Used to Create the type of Exports that exist in the scene

<a name="DzBridgeScene+checkChildType"></a>

### dzBridgeScene.checkChildType(oChildNode) ⇒ <code>String</code>
Used to Create the type of Exports that exist in the scene

**Kind**: instance method of [<code>DzBridgeScene</code>](#DzBridgeScene)  
**Returns**: <code>String</code> - Daz Content Type of given Node.  

| Param | Type | Description |
| --- | --- | --- |
| oChildNode | <code>DzNode</code> | the Child node of the RootNodes Found |

<a name="DzBridgeScene+overrideExportType"></a>

### dzBridgeScene.overrideExportType(nExportType)
Based on user's input we will remove the type of export they do not want.

**Kind**: instance method of [<code>DzBridgeScene</code>](#DzBridgeScene)  

| Param | Type | Description |
| --- | --- | --- |
| nExportType | <code>Number</code> | The type recieve from DzBridgeDialog.promptExportType |

<a name="DzBridgeSubdivision"></a>

## DzBridgeSubdivision
**Kind**: global class  

* [DzBridgeSubdivision](#DzBridgeSubdivision)
    * [new DzBridgeSubdivision(sScriptPath, oBridgeDialog)](#new_DzBridgeSubdivision_new)
    * [.lockSubdivisionProperties(bSubdivEnabled)](#DzBridgeSubdivision+lockSubdivisionProperties)
    * [.processFBX(sDtufilename)](#DzBridgeSubdivision+processFBX)
    * [.isSubdivPrereq()](#DzBridgeSubdivision+isSubdivPrereq)

<a name="new_DzBridgeSubdivision_new"></a>

### new DzBridgeSubdivision(sScriptPath, oBridgeDialog)
Handles the changes of Subdivision for Daz and the new Export Method.


| Param | Type |
| --- | --- |
| sScriptPath | <code>String</code> | 
| oBridgeDialog | [<code>DzBridgeDialog</code>](#DzBridgeDialog) | 

<a name="DzBridgeSubdivision+lockSubdivisionProperties"></a>

### dzBridgeSubdivision.lockSubdivisionProperties(bSubdivEnabled)
Void: Used to export out the subdivisions chosen by user.

**Kind**: instance method of [<code>DzBridgeSubdivision</code>](#DzBridgeSubdivision)  

| Param | Type | Description |
| --- | --- | --- |
| bSubdivEnabled | <code>Boolean</code> | Based on user's input to export out Subdivisions. |

<a name="DzBridgeSubdivision+processFBX"></a>

### dzBridgeSubdivision.processFBX(sDtufilename)
Void: Used to run the DzFBXBridges and allow the skin weights to be transferred

**Kind**: instance method of [<code>DzBridgeSubdivision</code>](#DzBridgeSubdivision)  

| Param | Type | Description |
| --- | --- | --- |
| sDtufilename | <code>String</code> | Path for the DTU File |

<a name="DzBridgeSubdivision+isSubdivPrereq"></a>

### dzBridgeSubdivision.isSubdivPrereq()
Void: Used to check if the fbx sdk 2020 exists in the path needed

**Kind**: instance method of [<code>DzBridgeSubdivision</code>](#DzBridgeSubdivision)  
<a name="DzBridgeWriter"></a>

## DzBridgeWriter
**Kind**: global class  

* [DzBridgeWriter](#DzBridgeWriter)
    * [new DzBridgeWriter(oBridgeExporter, oBridgeFigure, oBridgePose, oBridgeDialog)](#new_DzBridgeWriter_new)
    * [.writeSubdivisions()](#DzBridgeWriter+writeSubdivisions) ⇒ <code>Array.&lt;Object&gt;</code>

<a name="new_DzBridgeWriter_new"></a>

### new DzBridgeWriter(oBridgeExporter, oBridgeFigure, oBridgePose, oBridgeDialog)
Handles the changes of Subdivision for Daz and the new Export Method.


| Param | Type |
| --- | --- |
| oBridgeExporter | [<code>DzBridgeExporter</code>](#DzBridgeExporter) | 
| oBridgeFigure | [<code>DzBridgeFigure</code>](#DzBridgeFigure) | 
| oBridgePose | [<code>DzBridgePose</code>](#DzBridgePose) | 
| oBridgeDialog | [<code>DzBridgeDialog</code>](#DzBridgeDialog) | 

<a name="DzBridgeWriter+writeSubdivisions"></a>

### dzBridgeWriter.writeSubdivisions() ⇒ <code>Array.&lt;Object&gt;</code>
Void: Writes out the subdivision levels that were chosen by the user to the DTU

**Kind**: instance method of [<code>DzBridgeWriter</code>](#DzBridgeWriter)  
**Returns**: <code>Array.&lt;Object&gt;</code> - Contains the data that will be added to the DTU  
