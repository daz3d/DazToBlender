#include "dzplugin.h"
#include "dzapp.h"

#include "version.h"
#include "DzBlenderAction.h"
#include "DzBlenderDialog.h"

#include "dzbridge.h"

CPP_PLUGIN_DEFINITION("Daz To Blender Bridge");

DZ_PLUGIN_AUTHOR("Daz 3D, Inc");

DZ_PLUGIN_VERSION(PLUGIN_MAJOR, PLUGIN_MINOR, PLUGIN_REV, PLUGIN_BUILD);

#ifdef _DEBUG
DZ_PLUGIN_DESCRIPTION(QString(
	"<b>Pre-Release DazToBlender Bridge %1.%2.%3.%4 </b><br>\
<a href = \"https://github.com/daz3d/DazToBlender\">Github</a><br><br>"
).arg(PLUGIN_MAJOR).arg(PLUGIN_MINOR).arg(PLUGIN_REV).arg(PLUGIN_BUILD));
#else
DZ_PLUGIN_DESCRIPTION(QString(
"This plugin provides the ability to send assets to Blender. \
Documentation and source code are available on <a href = \"https://github.com/daz3d/DazToBlender\">Github</a>.<br>"
));
#endif

DZ_PLUGIN_CLASS_GUID(DzBlenderAction, 8bbeb9ab-1108-4364-acd6-82569ccc4f13);
NEW_PLUGIN_CUSTOM_CLASS_GUID(DzBlenderDialog, 692e00cb-5650-4b69-ae08-0201b8f75390);

#if defined(UNITTEST_DZBRIDGE) && defined(WIN32)

#include "UnitTest_DzBlenderAction.h"
#include "UnitTest_DzBlenderDialog.h"

DZ_PLUGIN_CLASS_GUID(UnitTest_DzBlenderAction, 6a463c62-cf71-4162-840d-7e668d0af218);
DZ_PLUGIN_CLASS_GUID(UnitTest_DzBlenderDialog, 96225142-26d8-475f-b9b4-ef7662dbe52f);

#endif

DZ_PLUGIN_CLASS_GUID(DzBlenderExporter, f823002f-db9d-408f-9a28-694a536a726b);
