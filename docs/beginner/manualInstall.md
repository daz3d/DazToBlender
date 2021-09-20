## Manual Installation
---
* Find the Newest Release [Here][ReleasesURL]
 ### How to download a new release from GitHub
 ---
 1. Go to the link listed above to find the newest release on GitHub.
 2. Under Assets you will find the newest build. It will be named DazToBlender_VersionNumber
 3. Download the zip and Inside you will find the Contents needed to use the bridge. Follow the steps below on how to install the bridge

 ## How To Manually Install This Bridge Version For Blender
 ---
  1. Navigate within the unzipped DazToBlender-#.#.# folder to: 
   1. DazToBlender-#.#.#\Blender\appdata_common\Blender Foundation\Blender\BLENDER_VERSION\scripts\addons --> and copy the DTB folder located here
     
  2. . Navigate to where the Blender application folder is installed within your system files
    1. (by default, this should be similar to: "C:\Program Files\Blender Foundation\#.##") and navigate to --> scripts --> addons
     1. Choose the version you wish to Install to For example, 2.92
     2. Go to ...\Blender\#.##\scripts\addons\ and Copy the DTB folder to this location
1. Drag & drop, or paste the DTB folder (copied earlier, from step 1) in the addons folder here

  ### How To Manually Install This Bridge Version For Daz Studio
  ---
   There are three available methods to install the Daz Side of the bridge manually. Please note, only one of these three DS methods will need to be followed in order for this section of the bridge installation process to be completed.

   1. The frst method available to install the bridge to Daz Studio is by 'Installing the bridge via the RunOnce Script'. To do this:
      
      **Note this is not necessary if you have installed by Daz Central/Daz Install Manager**

      1. Navigate within the unzipped DazToBlender-#.#.# folder to: DazToBlender-#.#.#\Daz Studio\appdir_common\scripts\support --> and copy the "DAZ" folder located here
      2.  Open a separate File Explorer window and type "%appdata%" in the top of your File Explorer and then within this Roaming folder navigate to:
      3. Daz 3D --> Studio4 --> RunOnce Drag & drop, or paste the DAZ folder (copied earlier, from step 1) in the plugins folder here (see attached)


   2. The second method available to install the bridge to Daz Studio is 'Replacing the version from DIM or Daz Central'. To do this:

      1. Navigate to the install path location of Daz Studio on your system. (by default this should be simmilar to:)
          *(WIN) C:\Program Files\DAZ 3D\DAZStudio4*
          *(Mac) -IP-
      2. Find the location of the original bridge installation (should be located under a path similar to): \scripts\support\DAZ\
      3. Within the 'Build Downloaded' folder, you will find the necessary files under \Daz Studio\
      4. Now, replace the previous install files with the new contents found here


   3.  The third method available to install the bridge to Daz Studio is 'Manually adding a script to your Daz Studio'.
      

      Once you have placed these files to their corresponding locations, the Daz to Blender #.#.# bridge should now be installed and available within Daz Studio under Scripts --> Bridges --> Daz to Blender.

      *Inprogress*

[OwnerURL]: https://www.daz3d.com
[TwitterURL]: https://twitter.com/Daz3d
[LicenseURL]: http://www.apache.org/licenses/LICENSE-2.0
[ProductURL]: https://www.daz3d.com/daz-to-blender-bridge
[RepositoryURL]: https://github.com/daz3d/DazToBlender/
[DazStudioURL]: https://www.daz3d.com/get_studio
[ReleasesURL]: https://github.com/daz3d/DazToBlender/releases
[BlenderURL]: https://www.blender.org/download
[BlenderDocsURL]: https://docs.blender.org/manual/en/latest/advanced/
