# Export Out Higher Subdivsion.

1. Make sure you have downloaded the newest version of the FBX SDK. 
    1. Go to https://www.autodesk.com/developer-network/platform-technologies/fbx-sdk-2020-2
    2. Download any option for your operating system just make sure to remember which **VS20XX** you chose.

    ![](img/fbxSdkOptions.png ':size=400')

    1. Go to your install path, *\Autodesk\FBX\FBX SDK\2020.2\lib\vs20XX\x64\release*
    2. Grab the libfbxsdk.dll and copy it to *\DAZ 3D\DAZStudio4\scripts\support\DAZ\dzBridgeUtils*
2. Now go to export out of Daz and follow these steps:  
      
    ![](img/dazUISubdivExplain.png ':size=200')

   1. Choose Level of Detail you wish to export.    
   2. Select the checkbox for Advanced Settings.
   3. Check Better Subdivision Export 
*For more information on how it works check out the original repository from cocktailboy and their explanation!*

- [How it works?][ExplanationURL]
- [Author's Git Repo][CocktailRepo]

[CocktailRepo]: https://github.com/cocktailboy/daz-to-ue4-subd-skin/blob/master/Daz_to_UE4_Subd_Skin_Weight.pdf
[ExplanationURL]: https://github.com/cocktailboy/daz-to-ue4-subd-skin/blob/master/Daz_to_UE4_Subd_Skin_Weight.pdf