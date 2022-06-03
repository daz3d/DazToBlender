# QA Manual Test Cases: Unreal script support #

## TC1. Load and Export Genesis 8 Basic Female to Unreal 
1. Start Daz Studio.
2. Confirm correct version number of pre-release Daz Studio bridge plugin.
3. Start Unreal Engine.
4. Confirm correct version number of pre-release UnrealEngine bridge plugin.
5. Load Genesis 8 Basic Female.
6. Select File->Send To->Daz To Unreal.
7. Confirm Asset Name is "Genesis8Female" in the Daz To Unreal dialog window.
8. Click "Accept".
9. Confirm Unreal Engine has successfully generated a new "Genesis8Female" asset in the Content Browser Pane.
10. Confirm that a "Genesis8Female" subfolder was generated in the Intermediate Folder, with "Genesis8Female.dtu" and "Genesis8Female.fbx" files.
11. Confirm that "ExportTextures" subfolder is present in the "Genesis8Female" folder, with 6 normal map files for: arms, eyes, face, legs, mouth, torso.
12. Confirm normal maps are valid images by opening each one in an image viewer.
13. In Daz Studio, go to the Surfaces pane and click the "Editor" tab.
14. Select "Genesis 8 Female", type "normal" in the search/filter bar text box which is found next to the magnifying glass icon.
15. Confirm that pane shows "(16): Normal Map" property with "Choose Map" text displayed.

## TC2. Load and Export Additional Genesis 8.1 Basic Female to Unreal
1. Continue from previous Daz Studio and Unreal Engine session (test case 1).
2. Deselect "Genesis 8 Female" from Scene.
3. Load Genesis 8.1 Basic Female.
4. Confirm new Scene node is created named "Genesis 8.1 Female".
5. Select File->Send To->Daz To Unreal.
6. Confirm Asset Name is "Genesis81Female" in the Daz To Unreal dialog window.
7. Click "Accept".
8. Confirm UnrealEngine has successfully generated a new "Genesis81Female" asset in the Content Browser Pane.
9. Confirm that a "Genesis81Female" subfolder was generated in the Intermediate Folder, with "Genesis81Female.dtu" and "Genesis81Female.fbx" files.
10. Confirm that "ExportTextures" subfolder is present in the "Genesis8Female" folder, with 5 normal map files for: body, face, head, arms, legs.
11. Confirm normal maps are valid images by opening each one in an image viewer.
12. In Daz Studio, go to the Surfaces pane and click the "Editor" tab.
13. Open the "Genesis 8.1 Female" tree and select "Skin-Lips-Nails", type "normal" in the search/filter bar text box which is found next to the magnifying glass icon.
14. Confirm that pane shows "(10): Normal Map" property with "Choose Map" text displayed.

## TC3. Load and Export Genesis 8.1 Basic Female with Custom Scene Node Label.
1. Start Daz Studio.
2. Confirm correct version number of pre-release Daz Studio bridge plugin.
3. Start Unreal Engine.
4. Confirm correct version number of pre-release UnrealEngine bridge plugin.
5. Load Genesis 8.1 Basic Female.
6. Select the Genesis 8.1 Basic Female from the Scene Pane.
7. Rename the node to "CustomSceneLabel".
8. Select File->Send To->Daz To Unreal.
9. Confirm Asset Name is "CustomSceneLabel" in the Daz To Unreal dialog window.
10. Click "Accept".
11. Confirm Unreal Engine has successfully generated a new "CustomSceneLabel" asset in the Content Browser Pane.
12. Confirm that a "CustomSceneLabel" subfolder was generated in the Intermediate Folder, with "CustomSceneLabel.dtu" and "CustomSceneLabel.fbx" files.

## TC4. Load and Export Genesis 8.1 Basic Female with Custom Asset Name to Unreal
1. Start Daz Studio.
2. Confirm correct version number of pre-release Daz Studio bridge plugin.
3. Start Unreal Engine.
4. Confirm correct version number of pre-release UnrealEngine bridge plugin.
5. Load Genesis 8.1 Basic Female.
6. Select File->Send To->Daz To Unreal.
7. Confirm Asset Name is "Genesis81Female" in the Daz To Unreal dialog window.
8. Change Asset Name to "CustomAssetName".
9. Click "Accept".
10. Confirm Unreal Engine has successfully generated a new "CustomAssetName" asset in the Content Browser Pane.
11. Confirm that a "CustomAssetName" subfolder was generated in the Intermediate Folder, with "CustomAssetName.dtu" and "CustomAssetName.fbx" files.

## TC5. Load and Export Genesis 8.1 Basic Female with Custom Intermediate Folder to Unreal
1. Start Daz Studio.
2. Confirm correct version number of pre-release Daz Studio bridge plugin.
3. Start Unreal Engine.
4. Confirm correct version number of pre-release UnrealEngine bridge plugin.
5. Load Genesis 8.1 Basic Female.
6. Select File->Send To->Daz To Unreal.
7. Confirm Intermediate Folder is "C:\Users\<username>\Documents\DazToUnreal" in the Daz To Unreal dialog window.
8. Change Intermediate Folder to "C:\CustomRoot".
9. Click "Accept".
10. Confirm Unreal Engine has successfully generated a new "Genesis81Female" asset in the Content Browser Pane.
11. Confirm there is a "C:\CustomRoot" folder with "Genesis81Female" subfolder containing "Genesis81Female.dtu" and "Genesis81Female.fbx".

## TC6. Load and Export Genesis 8.1 Basic Female with Enable Morphs to Unreal
1. Start Daz Studio.
2. Confirm correct version number of pre-release Daz Studio bridge plugin.
3. Start Unreal Engine.
4. Confirm correct version number of pre-release UnrealEngine bridge plugin.
5. Load Genesis 8.1 Basic Female.
6. Select File->Send To->Daz To Unreal.
7. Check "Enable Morphs", then Click "Choose Morphs".
8. Select a Morph such as "Genesis 8.1 Female -> Actor -> Bodybuilder" from the left and middle panes. Then click "Add For Export" so that it appears in the right pane.
9. Click "Accept" for the Morph Selection dialog.
10. Click "Accept" for the Daz To Unreal dialog.
11. Confirm Unreal Engine has successfully generated a new "Genesis81Female" asset in the Content Browser Pane.
12. Double-click the "Genesis81Female" asset to show the asset viewer window.
13. Confirm that the exported morph appears in the "Morph Target Preview" pane on the right side of the asset viewer window.
14. Confirm that moving the slider to 1.0 fully applies the morph.
15. Confirm that moving the slider to 0.0 fully removes the morph.

## TC7. Load and Export Genesis 8.1 Basic Female with Enable Subdivisions to Unreal
1. Start Daz Studio.
2. Confirm correct version number of pre-release Daz Studio bridge plugin.
3. Start Unreal Engine.
4. Confirm correct version number of pre-release UnrealEngine bridge plugin.
5. Load Genesis 8.1 Basic Female.
6. Select File->Send To->Daz To Unreal.
7. Check "Enable Subdivision", then Click "Choose Subdivisions".
8. Select the drop-down for Genesis 8.1 Female, and change to Subdivision Level 2.
9. Click "Accept" for the Subdivision Levels dialog.
10. Click "Accept" for the Daz To Unreal dialog.
11. Confirm Unreal Engine has successfully generated a new "Genesis81Female" asset in the Content Browser Pane.
12. Double-click the "Genesis81Female" asset to show the asset viewer window.
13. Confirm that the Vertices info printed in the top left corner of the preview window shows 271,418 instead of 19,775.
14. Confirm that a "Genesis81Female" subfolder was generated in the Intermediate Folder, with "Genesis81Female.dtu", "Genesis81Female.fbx", "Genesis81Female_base.fbx" and "Genesis81Female_HD.fbx" files.

## TC8. Load and Export Custom Scene File to Unreal
1. Start Daz Studio.
2. Confirm correct version number of pre-release Daz Studio bridge plugin.
3. Start Unreal Engine.
4. Confirm correct version number of pre-release UnrealEngine bridge plugin.
5. Select File->Open... and load "QA-Test-Scene-01.duf".
6. Select File->Send To->Daz To Unreal.
7. Confirm the Asset Name is "QATestScene01".
8. Click "Accept".
9. Confirm Unreal Engine has successfully generated a new "QATestScene01" asset in the Content Browser Pane.
10. Confirm that a "QATestScene01" subfolder was generated in the Intermediate Folder, with "QATestScene01.dtu" and "QATestScene01.fbx" files.

## TC9. Load and Export Victoria 8.1 to Unreal
1. Start Daz Studio.
2. Confirm correct version number of pre-release Daz Studio bridge plugin.
3. Start Unreal Engine.
4. Confirm correct version number of pre-release UnrealEngine bridge plugin.
5. Load Victoria 8.1.
6. Select File->Send To->Daz To Unreal.
7. Confirm the Asset Name is "Victoria81".
8. Click "Accept".
9. Confirm Unreal Engine has successfully generated a new "Victoria81" asset in the Content Browser Pane.
10. Confirm that a "Victoria81" subfolder was generated in the Intermediate Folder, with "Victoria81.dtu" and "Victoria81.fbx" files.
11. Confirm that "ExportTextures" subfolder is NOT present in the "Victoria81" folder.

## TC10. Load and Export Victoria 8.1 with "Victoria 8.1 Tattoo All - Add" to Unreal
1. Start Daz Studio.
2. Confirm correct version number of pre-release Daz Studio bridge plugin.
3. Start Unreal Engine.
4. Confirm correct version number of pre-release UnrealEngine bridge plugin.
5. Load Victoria 8.1.
6. Open the Materials section and load "Victoria 8.1 Tattoo All - Add" onto Victoria 8.1.
7. Wait for the L.I.E. textures to be baked and updated in the Viewport.  This can take a few minutes.
8. Select File->Send To->Daz To Unreal.
9. Confirm the Asset Name is "Victoria81".
10. Click "Accept".
11. Confirm Unreal Engine has successfully generated a new "Victoria81" asset in the Content Browser Pane.
12. Double-click the "Victoria81" asset to show the asset viewer window.
13. Confirm that the asset has full body tattoos visible in the asset viewer.
14. Confirm that a "Victoria81" subfolder was generated in the Intermediate Folder, with "Victoria81.dtu" and "Victoria81.fbx" files, and additional "ExportTextures" folder with 8 PNG texture files (d10.png to d17.png).
