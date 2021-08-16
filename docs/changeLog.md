# Change Log

## 2.4.0

*2021-08-09*

Bugs Fixed:
- Poses not working on Root Bone
- Poses now being applied correctly when multiple characters are being exported
- Male facial rig broken when using Rigify
- Dropdown added in Morph List allowing the control of morphs for multiple characters in one scene
- Option to Refresh the Dropdown in the morph list to allow the reopening of blender scenes with the morphs still being available

New Features / Additions:
- Support for importing multiple figures with morph list work
- Dropdown to choose between different figure's morphs
- Option to customize Export Path for Blender, allowing you to move where blender exists
   1. Go to Import Settings
   2. Check use Custom Path
   3. Choose the folder that you wish to use
- Allow Collect Textures to work relative to user's export (sharing of export files between computers)
- Can now disable remove incompatible nodes during export
- Can now disable morph optimization

Updates to Support Figure Compatibility:
- Changed the Figure export logic allowing more then just Genesis Characters to export in that method
- This will allow export of any Asset as a figure if the type is Actor/Character
- Basic Support for DzLegacyFigures


## 2.3.9

*2021-06-21*

Morph Updates
 - Created a controller that allows morphs that are being manipulated to also still be independently controlled 
   - (only for visible, non-hidden morphs)
- By default, the morph prefix is removed, but an option exist if you would like to disable it 

Morph Optimizations
- Deleted morphs that shouldn't have been included on the children objects (i.e. morphs that use a logic of checking if the figure has the 
   bone, an alias, or the morph itself on the children object)
- Deleted morphs that don't exist in Daz but still export

General Updates
- Multiply the 2nd Stage Drivers by zero (if first stage does not exist)
- Solved an issue where some versions of 2.83 and 2.92 fail
- Consolidated the settings under General Settings and renamed to Import Settings
- Allow users to disable the viewport changes for the display settings
- Optimizations made to check if bone is weighted before adding it as included mesh


## 2.3.9-beta

*2021-06-07*

- Solve issue where some versions of 2.83 and 2.92 will fail. 
- Combined the the Settings all under general settings and renamed to Import Settings.
- Allow the user to disable the viewport changes for the display settings.
- By Default the morph prefix is removed but, an option exist if you would like to disable it.
- Optimization made to check if bone is weighted before adding it as included mesh.


## 2.3.8-beta

*2021-06-04*

- Create a Controllers that allows morphs that are being controlled to still be controlled themselves only for non-hidden morphs
-  Multiply the 2nd Stage Drivers by zero if first stage does not exist.
- Optimize Morphs
   - Delete the morphs that shouldn't be on the children objects. Uses a logic of checking if the figure has the bone, an alias, or the morph itself on the children object.
   - Delete morphs that don't exist in Daz but export.

## 2.3.7

*2021-06-04*

- New Export Logic 
    - Will Check if Node found is a Character if not it will export as Environment/Prop.
    - Will also unparent and reparent Characters that are in Groups.
- Able to Export Genesis and Genesis 2 Figures as Characters …
    - Does not support Genesis 1 and 2 Skinning Method will automatically convert weights
- Fixed Offset 
    - Some morphs will translate skeletons now it will take that account in fixing skeletons
- Added Figure Data to DTU.
- Code Refactor Updates
- Added some morph presets to simplify export process
- Added Refresh Button on Dropdown to reload the dropdown menu if Character is missing.
- Morph Updates
    - Fix the ErcMultiply execution in blender to have it apply correctly.
    - Added an option to disable Morph links during export.
        - Fixes multiple morphs on one controller.
            - For example Surprised Morph for Genesis 8.1 is made of multiple morphs now it will export them separately as the default option.
    - Updates to Drivers Additions to match better to Daz setup
- Add new function to bulk remove the morph prefix 
    - Choose your Asset in the dropdown and run 
- Rigify Updates
     - Moved Rigging to its own panel.
     - Fixed face not following when morphs are on the import
- Bug Fixes
     - Fixed Python Error Runtime Error Change Size during Iteration 
     - Allow Bridge to Skip over FBX error in some cases the script will fix errors in the FBX importer.
- Add Option to Collect Textures
- Add support for 2.93

## 2.3.6-beta

*2021-05-28*

- Add an option to collect textures
    - This will include paths of all the external textures in the dtu.
- Bugfix
    - Fixed “TypeError” issue when importing a character with hand and leg JCMs to the Blender.

## 2.3.5-beta

*2021-05-25*

- New Export Logic 
    - Will Check if Node found is a Character if not it will export as Environment/Prop.
    - Will also unparent and reparent Characters that are in Groups.
- Able to Export Genesis and Genesis 2 Figures as Characters …
    - Does not support Genesis 1 and 2 Skinning Method will automatically convert weights
- Fixed Offset 
    - Some morphs will translate skeletons now it will take that account in fixing skeletons
- Added Figure Data to DTU.
- Code Refactor Updates
- Added some morph presets to simplify export process
- Added Refresh Button on Dropdown to reload the dropdown menu if Character is missing.
- Morph Updates
    - Fix the ErcMultiply execution in blender to have it apply correctly.
    - Added an option to disable Morph links during export.
        - Fixes multiple morphs on one controller.
            - For example Surprised Morph for Genesis 8.1 is made of multiple morphs now it will export them separately as the default option.
    - Updates to Drivers Additions to match better to Daz setup
- Add new function to bulk remove the morph prefix 
    - Choose your Asset in the dropdown and run 
- Rigify Updates
     - Moved Rigging to its own panel.
     - Fixed face not following when morphs are on the import
- Bug Fixes
     - Fixed Python Error Runtime Error Change Size during Iteration 
     - Allow Bridge to Skip over FBX error in some cases the script will fix errors in the FBX importer.
- Add Option to Collect Textures


## 2.3.1.1

*2021-04-12*

- When we change the scale of the mesh we are updating the Scene Units, Viewport, and Camera to work better with your larger mesh. 

- If you wish to not have this feature turned on now you can skip it completely but, still scale the object. 

- Also, if you do not have a camera in your scene it will not fail and just skip editing the camera. 

## 2.3.1

*2021-04-09*

New Features:
- New morph selection dialog during export. 
    - Auto-generate a list of every morph in your export, including clothing and hair morphs
    - Filter through your morphs to highlight and select which ones you would like to export.
    - Create morph presets to be reused with any figure of your liking. 
    - This script will automatically grab all associated morphs that are being controlled by your morph in this selection. 
- Added an option to disable morphs exporting out of Daz. 
- Changed location of exported files to: /Documents/DAZ 3D/Bridges/Daz To Blender/
- A new UI design for the Blender side of the bridge. New options are explained below;
   - Pose Tools
      - Choose from your figure imported in the dropdown and import them from Daz Studio in a pose.
      - Checkbox to add poses to Pose Library
   - Morph List
     - Get controllers (using the same name in Daz) that will let you control all of your imported morphs that aren’t being automatically driven, 
       even when you are in pose mode. 
     - Available controllers are separated into groups based on the corresponding mesh names.
   - Material Settings
     - Checkbox to combine duplicate materials at import
   - General Settings 
     - Dropdown for scaling options
     - Refresh all Daz figures 
         - Refresh dropdown of figures in your scene (useful for when your figure isn’t in the choices)
         - Note: only works with figures in the newest update (2.3.1) and forward.
         - Moved “Remove all Daz” to “General Settings”.
    - Commands List
         - This is WIP but, is a list of all the commands you can use and the command box.

- Automatically create a pose library with the imported pose
- Added a new option to import poses directly from (.duf) files and automatically save them directly to your pose library
- Automatically combine duplicate materials during import
- Added a new option to scale figure mesh with three different options:
   - Real Size (centimeters/Daz scale)
   - x10
   - x100 (meters)
- Setup auto-drivers for morphs imported into the scene. 
   - Currently, ERC Keyed Drivers are limited support. 
   - Currently, drivers for morphs that control bones are not supported. 
- Automatically setup settings correctly for materials when using Transmission (Eevee) - Screen Space Refraction 
- Automatically set Blending Mode for materials using Alpha/Opacity maps, (this is needed for Eevee Renders).
- Added basic support for materials using: Irayuber, AoA_Subsurface, omUberSurface, and DAZ Studio Default. 
- Added support to import in characters that have deleted faces on the figure. 


Bug Fixes:
- Improved compatibility for Mac OS. (for Blender) 
   - Will not fix compatibility issues with your version of MacOS. 
- Fixed folders; previously, not all were being deleted from your import. 
- Fixed skeletons importing a different size than the base figures in Daz from a Full body morph. 
- Fixed Skeletons importing incorrectly if you scale the bones in Daz Studio
- Fixed the skeletons of props being incorrect.
- Fixed locations of props and environments being incorrect after import.
- Fixed child objects morphs not being controlled by the Main Controller. 
    - i.e: eyelashes not moving when using the figure head morphs. 
- Fixed scale being incorrect when importing figures of different sizes. 
- Fixed Incorrect Rotation on Hip Bone Custom Shape


