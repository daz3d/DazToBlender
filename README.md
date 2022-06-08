# Daz To Blender Bridge
A Daz Studio Plugin based on Daz Bridge Library, allowing transfer of Daz Studio characters and props to Blender.

* Owner: [Daz 3D][OwnerURL] – [@Daz3d][TwitterURL]
* License: [Apache License, Version 2.0][LicenseURL] - see ``LICENSE`` and ``NOTICE`` for more information.
* Offical Release: [Daz to Blender Bridge][ProductURL]
* Official Project: [github.com/daz3d/DazToBlender][RepositoryURL]


## Table of Contents
1. About the Bridge
2. Prerequisites
3. How to Install
4. How to Use
5. How to Build
6. How to QA Test
7. How to Develop
8. Directory Structure


## 1. About the Bridge
This is a refactored version of the original DazToBlender Bridge using the Daz Bridge Library as a foundation. Using the Bridge Library allows it to share source code and features with other bridges such as the refactored DazToUnity and DazToBlender bridges. This will improve development time and quality of all bridges.

The Daz To Blender Bridge consists of two parts: a Daz Studio plugin which exports assets to Blender and a Blender Plugin which contains scripts and other resources to help recreate the look of the original Daz Studio asset in Blender.


## 2. Prerequisites
- A compatible version of the [Daz Studio][DazStudioURL] application
  - Minimum: 4.10
- A compatible version of the [Blender][BlenderURL] application
  - Minimum: 2.83 LTS
- Operating System:
  - Windows 7 or newer
  - macOS 10.13 (High Sierra) or newer


## 3. How to Install
### Daz Studio ###
- You can install the Daz To Blender Bridge automatically through the Daz Install Manager or Daz Central.  This will automatically add a new menu option under File -> Send To -> Daz To Blender.
- Alternatively, you can manually install by downloading the latest build from Github Release Page and following the instructions there to install into Daz Studio.

### Blender ###
1. The Daz Studio Plugin now comes embedded with an installer for Blender.  From the Daz To Blender Bridge Dialog, there is now section in the Advanced Settings section for Installing the Blender Plugin.
2. Select your Blender Version from the drop down menu.  If your Blender version is not directly supported by this drop-down or you have a custom plugins folder, then select "Custom Addon Path".
3. Then click the "Install Plugin" button.  If you selected a supported version of Blender, you should see a popup dialog box confirming if the Blender plugin was successfully installed for your version of Blender.  Be sure to restart Blender after installing the Blender Plugin.
4. From Blender, open the Blender Preferences window by selecting Edit -> Preferences from the Blender main menu. 
5. In the Blender Preferences window, click on the Addons button found along the left side of the window.
6. Scroll down the list of add-ons, and look for "Import-Export: DazToBlender".  Check the box next to "Import-Export: DazToBlender" to enable the plugin.  A DazToBlender tab should now appear on the Blender "Tool-shelf" which are a set of vertical tabs along the right edge of the Blender viewport window.

The following steps are for people who wish to use the "Custom Addon Path" installation option.

1. If you chose "Custom Addon Path", you will see a window popup to choose a custom Scripts or Addons folder.  The starting folder path will be the location where Blender stores preferences and files for each version of Blender.  
2. If you are using an unsupported version of Blender, you should see a subfolder corresponding to your version from the starting folder path.  Open that folder and select the scripts folder.  Then click "Select Folder".
3. If you have configured a custom Scripts path from the Blender Preferences window, then you may navigate to that folder and click "Select Folder".  You will then see a confirmation dialog stating if the plugin installation was successful.


## 4. How to Use
1. Open your character in Daz Studio.
2. Make sure any clothing or hair is parented to the main body.
3. From the main menu, select File -> Send To -> Daz To Blender.
4. A dialog will pop up: choose what type of conversion you wish to do, "Static Mesh" (no skeleton), "Skeletal Mesh" (Character or with joints), or "Animation".
5. To enable Morphs or Subdivision levels, click the CheckBox to Enable that option, then click the "Choose Morphs" or "Bake  Subdivisions" button to configure your selections.
6. Click Accept, then wait for a dialog popup to notify you when to switch to Blender.
7. From Blender, click the "DazToBlender" tab from the Blender toolshelf, located along the right-edge of the Blender viewport.
8. For Daz Characters or other assets transferred with the "Skeletal Mesh" option, select `Import New Genesis Figure`.  For props or other assets transferred using the "Static Mesh" option, select `Import New Env/Prop`.

### Morphs ###
- If you enabled the Export Morphs option, you will see sliders for each Morph in the "Morphs List" section of the DazToBlender toolshelf.

### Animation ###
- To use the "Animation" asset type option, your Figure must use animations on the Daz Studio "Timeline" system.  
- If you are using "aniMate" or "aniBlocks" based animations, you need to right-click in the "aniMate" panel and select "Bake To Studio Keyframes".  
- Once your animation is on the "Timeline" system, you can start the transfer using File -> Send To -> Daz To Blender.  
- The transferred animation should now be usable through the Blender Animation interface.

### Subdivision Support ###
- Daz Studio uses Catmull-Clark Subdivision Surface technology which is a mathematical way to describe an infinitely smooth surface in a very efficient manner. Similar to how an infinitely smooth circle can be described with just the radius, the base resolution mesh of a Daz Figure is actually the mathematical data in an equation to describe an infinitely smooth surface. For Software which supports Catmull-Clark Subdivision and subdivision surface-based morphs (also known as HD Morphs), there is no loss in quality or detail by exporting the base resolution mesh (subdivision level 0).
- For Software which does not fully support Catmull-Clark Subdivision or HD Morphs, we can "Bake" additional subdivision detail levels into the mesh to more closely approximate the detail of the original surface. However, baking each additional subdivision level requires exponentially more CPU time, memory, and storage space.
- Since version 2.8, Blender has built-in Catmull-Clark Subdivision Surface support like Daz Studio. This is much faster and should be used instead of baking out subdivision levels during the Bridge Export process.
- Blender Subdivision is fully supported by modern Daz Figures which will transfer to Blender as a fully compatible level 0 subdivision surface, ready for subdivision operations through Blender.  
- You can find out more about Blender's built-in Subdivision Support here: https://docs.blender.org/manual/en/3.1/modeling/modifiers/generate/subdivision_surface.html


## 5. How to Build
Requirements: Daz Studio 4.5+ SDK, Qt 4.8.1, Autodesk Fbx SDK, Pixar OpenSubdiv Library, CMake, C++ development environment

Download or clone the DazToBlender github repository to your local machine. The Daz Bridge Library is linked as a git submodule to the DazBridge repository. Depending on your git client, you may have to use `git submodule init` and `git submodule update` to properly clone the Daz Bridge Library.

Use CMake to configure the project files. Daz Bridge Library will be automatically configured to static-link with DazToBlender. If using the CMake gui, you will be prompted for folder paths to dependencies: Daz SDK, Qt 4.8.1, Fbx SDK and OpenSubdiv during the Configure process.


## 6. How to QA Test
To Do:
1. Write `QA Manaul Test Cases.md` for DazToBlender using [Example QA Manual Test Cases.md](https://github.com/daz3d/DazToC4D/blob/master/Test/Example%20QA%20Manual%20Test%20Cases.md).
2. Implement the manual tests cases as automated test scripts in `Test/TestCases`.
3. Update `Test/UnitTests` with latest changes to DazToBlender class methods.

The `QA Manaul Test Cases.md` document should contain instructions for performing manual tests.  The Test folder also contains subfolders for UnitTests, TestCases and Results. To run automated Test Cases, run Daz Studio and load the `Test/testcases/test_runner.dsa` script, configure the sIncludePath on line 4, then execute the script. Results will be written to report files stored in the `Test/Reports` subfolder.

To run UnitTests, you must first build special Debug versions of the DazToBlender and DzBridge Static sub-projects with Visual Studio configured for C++ Code Generation: Enable C++ Exceptions: Yes with SEH Exceptions (/EHa). This enables the memory exception handling features which are used during null pointer argument tests of the UnitTests. Once the special Debug version of DazToBlender dll is built and installed, run Daz Studio and load the `Test/UnitTests/RunUnitTests.dsa` script. Configure the sIncludePath and sOutputPath on lines 4 and 5, then execute the script. Several UI dialog prompts will appear on screen as part of the UnitTests of their related functions. Just click OK or Cancel to advance through them. Results will be written to report files stored in the `Test/Reports` subfolder.

For more information on running QA test scripts and writing your own test scripts, please refer to `How To Use QA Test Scripts.md` and `QA Script Documentation and Examples.dsa` which are located in the Daz Bridge Library repository: https://github.com/daz3d/DazBridgeUtils.

Special Note: The QA Report Files generated by the UnitTest and TestCase scripts have been designed and formatted so that the QA Reports will only change when there is a change in a test result.  This allows Github to conveniently track the history of test results with source-code changes, and allows developers and QA testers to notified by Github or their git client when there are any changes and the exact test that changed its result.


## 7. How to Modify and Develop
The Daz Studio Plugin source code is contained in the `DazStudioPlugin` folder. The Blender Plugin source code and resources are available in the `/Blender/appdata_common/Blender Foundation/Blender/BLENDER_VERSION/scripts/addons/DTB` folder.

The DazToBlender Bridge uses a branch of the Daz Bridge Library which is modified to use the `DzBlenderNS` namespace. This ensures that there are no C++ Namespace collisions when other plugins based on the Daz Bridge Library are also loaded in Daz Studio. In order to link and share C++ classes between this plugin and the Daz Bridge Library, a custom `CPP_PLUGIN_DEFINITION()` macro is used instead of the standard DZ_PLUGIN_DEFINITION macro and usual .DEF file. NOTE: Use of the DZ_PLUGIN_DEFINITION macro and DEF file use will disable C++ class export in the Visual Studio compiler.


## 8. Directory Structure
Within the Blender directory are hierarchies of subdirectories that correspond to locations on the target machine. Portions of the hierarchy are consistent between the supported platforms and should be replicated exactly while others serve as placeholders for locations that vary depending on the platform of the target machine.

Placeholder directory names used in this repository are:

Name  | Windows  | macOS
------------- | ------------- | -------------
appdata_common  | Equivalent to the expanded form of the `%AppData%` environment variable.  Sub-hierarchy is common between 32-bit and 64-bit architectures. | Equivalent to the `~/Library/Application Support` directory.  Sub-hierarchy is common between 32-bit and 64-bit architectures.
appdir_common  | The directory containing the primary executable (.exe) for the target application.  Sub-hierarchy is common between 32-bit and 64-bit architectures.  | The directory containing the primary application bundle (.app) for the target application.  Sub-hierarchy is common between 32-bit and 64-bit architectures.
BLENDER_VERSION  | The directory named according to the version of the Blender application - see [Blender Documentation][BlenderDocsURL] - e.g., "2.80", "2.83", etc.  | Same on both platforms.

The directory structure is as follows:

- `Blender`:                  Files that pertain to the _Blender_ side of the bridge
  - `appdata_common`:         See table above
    - `Blender Foundation`:   Application data specific to the organization
**^ Note:** _this level of the hierarchy is not present on macOS_ **^**
      - `Blender`:            Application data specific to the application
        - `BLENDER_VERSION`:  See table above
          - `...`:            Remaining sub-hierarchy
- `DazStudioPlugin`:          Files that pertain to the _Daz Studio_ side of the DazToBlender bridge
- `dzbridge-common`:          Files from the Daz Bridge Library used by DazStudioPlugin
- `Test`:                     Scripts and generated output (reports) used for Quality Assurance Testing.

[OwnerURL]: https://www.daz3d.com
[TwitterURL]: https://twitter.com/Daz3d
[LicenseURL]: http://www.apache.org/licenses/LICENSE-2.0
[ProductURL]: https://www.daz3d.com/daz-to-blender-bridge
[RepositoryURL]: https://github.com/daz3d/DazToBlender/
[DazStudioURL]: https://www.daz3d.com/get_studio
[ReleasesURL]: https://github.com/daz3d/DazToBlender/releases
[BlenderURL]: https://www.blender.org/download
[BlenderDocsURL]: https://docs.blender.org/manual/en/latest/advanced/blender_directory_layout.html#platform-dependent-paths
