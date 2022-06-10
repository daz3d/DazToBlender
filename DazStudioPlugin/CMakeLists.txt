set(CMAKE_AUTOMOC ON)
set(CMAKE_AUTORCC ON)
set(CMAKE_INCLUDE_CURRENT_DIR ON)

set(DZ_PLUGIN_TGT_NAME dzblenderbridge)
set(DZ_PLUGIN_PROJECT_NAME "DzBlenderBridge")

include_directories(${COMMON_LIB_INCLUDE_DIR})

# if building a plugin and you want the compiled result placed in the Daz Studio ./plugins directory
if(DAZ_STUDIO_EXE_DIR)
	set(CMAKE_RUNTIME_OUTPUT_DIRECTORY ${DAZ_STUDIO_EXE_DIR}/plugins)
	set(CMAKE_LIBRARY_OUTPUT_DIRECTORY ${DAZ_STUDIO_EXE_DIR}/plugins)
endif()

if(WIN32)
	set(OS_SOURCES
		DzBlenderBridge.rc
	)
elseif(APPLE)
	set(OS_SOURCES "")
endif()

set(DPC_IMAGES_CPP "${CMAKE_CURRENT_BINARY_DIR}/DzBlenderIcon.cpp" )
set(DPC_SRC_IMAGES
	"Resources/Images/Daz to Blender.png"
)

add_custom_command(OUTPUT ${DPC_IMAGES_CPP}
	COMMAND ${DAZ_SDK_DPC_EXE} -mode image -o ${DPC_IMAGES_CPP} ${DPC_SRC_IMAGES}
	DEPENDS ${DPC_SRC_IMAGES}
	WORKING_DIRECTORY ${CMAKE_CURRENT_LIST_DIR}
)
set_property(SOURCE ${DPC_IMAGES_CPP} PROPERTY SKIP_AUTOMOC ON)

add_library( ${DZ_PLUGIN_TGT_NAME} SHARED
	DzBlenderAction.cpp
	DzBlenderAction.h
	DzBlenderDialog.cpp
	DzBlenderDialog.h
	pluginmain.cpp
	version.h
	Resources/resources.qrc
	${DPC_IMAGES_CPP}
	${OS_SOURCES}
	${QA_SRCS}
)

target_include_directories(${DZ_PLUGIN_TGT_NAME}
	PUBLIC
)

target_link_libraries(${DZ_PLUGIN_TGT_NAME}
	PRIVATE
	dzcore
	dzbridge-static
	${DZSDK_QT_CORE_TARGET}
	${DZSDK_QT_GUI_TARGET}
	${DZSDK_QT_SCRIPT_TARGET}
	${DZSDK_QT_NETWORK_TARGET}
	${FBX_IMPORT_LIBS}
	${OPENSUBDIV_LIB}
)

set_target_properties (${DZ_PLUGIN_TGT_NAME}
	PROPERTIES
	FOLDER ""
	PROJECT_LABEL ${DZ_PLUGIN_PROJECT_NAME}
)

target_compile_definitions(${DZ_PLUGIN_TGT_NAME}
	PUBLIC
	$<$<CONFIG:DEBUG>:UNITTEST_DZBRIDGE>
	${DZBRIDGE_LIB_FLAGS}
	__LEGACY_PATHS__
)
