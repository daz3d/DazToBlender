import bpy

from bpy.props import (
    StringProperty,
)

from bpy.types import (
    PropertyGroup,
)


class ImportFilesCollection(PropertyGroup):
    name: StringProperty(
        name="File Path",
        description="Filepath used for importing the file",
        maxlen=1024,
        subtype="FILE_PATH",
    )


class CustomPathProperties(PropertyGroup):
    # test
    path: StringProperty(
        name="",
        description="Choose Path for Auto-Import",
        default="",
        maxlen=1024,
        subtype="DIR_PATH",
    )
