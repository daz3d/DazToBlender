
#include "DzBlenderActionExtras.h"

#include <QtGui/qcheckbox.h>
#include <QtGui/QMessageBox>
#include <QtNetwork/qudpsocket.h>
#include <QtNetwork/qabstractsocket.h>
#include <QCryptographicHash>
#include <QtCore/qdir.h>
#include <qfiledialog.h>

#include <dzapp.h>
#include <dzscene.h>
#include <dzmainwindow.h>
#include <dzshape.h>
#include <dzproperty.h>
#include <dzobject.h>
#include <dzpresentation.h>
#include <dznumericproperty.h>
#include <dzimageproperty.h>
#include <dzcolorproperty.h>
#include <dpcimages.h>

#include "QtCore/qmetaobject.h"
#include "dzmodifier.h"
#include "dzgeometry.h"
#include "dzweightmap.h"
#include "dzfacetshape.h"
#include "dzfacetmesh.h"
#include "dzfacegroup.h"
#include "dzprogress.h"
#include "dzscript.h"
#include "dzfigure.h"

#include "DzBlenderAction.h"
#include "DzBlenderDialog.h"
#include "DzBridgeMorphSelectionDialog.h"
#include "DzBridgeSubdivisionDialog.h"
#include "DzBlenderUtils.h"

#ifdef WIN32
#include <shellapi.h>
#endif

bool ShowExplorerWindow(QString sFilePath)
{
	QString sFolderPath = QFileInfo(sFilePath).path();

#ifdef WIN32
	std::wstring wcsFileOutputPath(reinterpret_cast<const wchar_t*>(sFolderPath.utf16()));
	ShellExecuteW(NULL, L"open", wcsFileOutputPath.c_str(), NULL, NULL, SW_SHOWDEFAULT);
#elif defined(__APPLE__)
	QStringList args;
	args << "-e";
	args << "tell application \"Finder\"";
	args << "-e";
	args << "activate";
	args << "-e";
	if (QFileInfo(sFinalFilePath).exists()) {
		args << "select POSIX file \"" + sFilePath + "\"";
	}
	else {
		args << "select POSIX file \"" + sFolderPath + "/." + "\"";
	}
	args << "-e";
	args << "end tell";
	QProcess::startDetached("osascript", args);
#endif

	return true;
}

DzBlenderActionExtras_01::DzBlenderActionExtras_01()
{
	this->setText("BROKEN!");
	this->setDescription("An Extra Blender Action");

	this->setUseLegacyPaths(false);
}

void DzBlenderActionExtras_01::executeAction()
{
	this->m_pSelectedNode = dzScene->getPrimarySelection();
	if (m_pSelectedNode == nullptr && dzScene->getNumNodes() == 1) {
		m_pSelectedNode = dzScene->getNode(0);
	}
	
	if ( m_pSelectedNode == nullptr || (m_pSelectedNode->getObject() == nullptr) )
	{
		QMessageBox::critical(0, tr("No selection"), tr("You must select a figure to output."), QMessageBox::Abort );
		m_nExecuteActionResult = DZ_OPERATION_FAILED_ERROR;
		return;
	}

	this->createUI();
	
	QString sOriginalFilename = QFileDialog::getSaveFileName(0, "Package into an easy export folder...");

	if (sOriginalFilename.isEmpty() || sOriginalFilename == "") {
		m_nExecuteActionResult = DZ_DOES_NOT_EXIST_ERROR;
		return;
	}

	QFileInfo oFileInfo(sOriginalFilename);
	m_sExportFilename = oFileInfo.fileName();
	m_sExportSubfolder = m_sExportFilename;
	m_sRootFolder = oFileInfo.path();
	
	QString sFinalFilePath = m_sRootFolder + "/" + m_sExportSubfolder + "/" + m_sExportFilename + ".dtu";
	
//	this->setNonInteractiveMode(DZ_BRIDGE_NAMESPACE::eNonInteractiveMode::DzExporterModeRunSilent);
	this->setNonInteractiveMode(1);
	this->m_sExportRigMode = "--";
//	this->m_bGenerateFinalFbx = true;
//	this->m_bGenerateFinalGlb = true;

//	this->m_nTextureAtlasSize = 1024;
//	this->m_sTextureAtlasMode = "single_atlas";
	
	this->setEmbedTexturesInOutputFile(true);
	this->setExportAllTextures(true);
	this->setConvertToJpg(true);
	this->setConvertToPng(true);
	this->setBakeMakeupOverlay(true);
	
	DzBlenderAction::executeAction();
	if (m_nExecuteActionResult != DZ_NO_ERROR || m_pSelectedNode == nullptr ||
		m_pSelectedNode->getObject() == nullptr ) 
	{
		return;
	}

//	// if Blender Executable is not set, fail gracefully
//	if (this->m_sBlenderExecutablePath == "") {
//		QMessageBox::critical(0, tr("No Blender Executable Found"), tr("You must set the path to your Blender Executable. Aborting."), QMessageBox::Abort );
//		m_nExecuteActionResult = DZ_OPERATION_FAILED_ERROR;
//		return;
//	}
//
//	QString sIntermediatePath = QFileInfo(this->m_sDestinationFBX).dir().path().replace("\\", "/");
//	QString sIntermediateScriptsPath = sIntermediatePath + "/Scripts";
//	QDir().mkdir(sIntermediateScriptsPath);
//
//	QStringList aScriptFilelist = (QStringList() << 
//		"create_blend.py" <<
//		"blender_tools.py" <<
//		"NodeArrange.py" <<
//		"game_readiness_tools.py"
//		);
//	// copy 
//	foreach(auto sScriptFilename, aScriptFilelist)
//	{
//		bool replace = true;
//		QString sEmbeddedFolderPath = ":/DazBridgeBlender";
//		QString sEmbeddedFilepath = sEmbeddedFolderPath + "/" + sScriptFilename;
//		QFile srcFile(sEmbeddedFilepath);
//		QString tempFilepath = sIntermediateScriptsPath + "/" + sScriptFilename;
//		DZ_BRIDGE_NAMESPACE::DzBridgeAction::copyFile(&srcFile, &tempFilepath, replace);
//		srcFile.close();
//	}
//
//	QString sBlenderLogPath = sIntermediatePath + "/" + "create_blend.log";
//	QString sScriptPath = sIntermediateScriptsPath + "/" + "create_blend.py";
//	QString sCommandArgs = QString("--background;--log-file;%1;--python-exit-code;%2;--python;%3;%4").arg(sBlenderLogPath).arg(this->m_nPythonExceptionExitCode).arg(sScriptPath).arg(this->m_sDestinationFBX);
//#if WIN32
//	QString batchFilePath = sIntermediatePath + "/" + "create_blend.bat";
//#else
//	QString batchFilePath = sIntermediatePath + "/" + "create_blend.sh";
//#endif
//	DzBlenderUtils::GenerateBlenderBatchFile(batchFilePath, this->m_sBlenderExecutablePath, sCommandArgs);
//
//	bool result = false;
//	result = this->executeBlenderScripts(this->m_sBlenderExecutablePath, sCommandArgs);

	QString sBlenderOutputPath = QFileInfo(sFinalFilePath).dir().path().replace("\\", "/");

	if (m_nExecuteActionResult == DZ_NO_ERROR)
	{
		QMessageBox::information(0, "Blender Exporter",
			tr("Export from Daz Studio complete."), QMessageBox::Ok);

#ifdef WIN32
		std::wstring wcsBlenderOutputPath(reinterpret_cast<const wchar_t*>(sBlenderOutputPath.utf16()));
		ShellExecuteW(NULL, L"open", wcsBlenderOutputPath.c_str(), NULL, NULL, SW_SHOWDEFAULT);
#elif defined(__APPLE__)
		QStringList args;
		args << "-e";
		args << "tell application \"Finder\"";
		args << "-e";
		args << "activate";
		args << "-e";
		if (QFileInfo(sFinalFilePath).exists()) {
			args << "select POSIX file \"" + sFinalFilePath + "\"";
		}
		else {
			args << "select POSIX file \"" + sBlenderOutputPath + "/." + "\"";
		}
		args << "-e";
		args << "end tell";
		QProcess::startDetached("osascript", args);
#endif
	}
	else
	{
		// custom message for code 11 (Python Error)
//		if (this->m_nBlenderExitCode == this->m_nPythonExceptionExitCode) {
//			QString sErrorString;
//			sErrorString += QString("An error occured while running the Blender Python script (ExitCode=%1).\n").arg(this->m_nBlenderExitCode);
//			sErrorString += QString("\nPlease check log files at : %1\n").arg(this->m_sDestinationPath);
//			sErrorString += QString("\nYou can rerun the Blender command-line script manually using: %1").arg(batchFilePath);
//			QMessageBox::critical(0, "Blender Exporter", tr(sErrorString.toUtf8()), QMessageBox::Ok);
//		}
//		else {
			QString sErrorString;
			sErrorString += QString("An error occured during the export process (ExitCode=%1).\n").arg(this->m_nBlenderExitCode);
			sErrorString += QString("Please check log files at : %1\n").arg(this->m_sDestinationPath);
			QMessageBox::critical(0, "Blender Exporter", tr(sErrorString.toUtf8()), QMessageBox::Ok);
//		}
#ifdef WIN32
		std::wstring wcsDestinationPath(reinterpret_cast<const wchar_t*>(this->m_sDestinationPath.utf16()));
		ShellExecuteW(NULL, L"open", wcsDestinationPath.c_str(), NULL, NULL, SW_SHOWDEFAULT);
#elif defined(__APPLE__)
		QStringList args;
		args << "-e";
		args << "tell application \"Finder\"";
		args << "-e";
		args << "activate";
		args << "-e";
		args << "select POSIX file \"" + sBlenderOutputPath + "\"";
		args << "-e";
		args << "end tell";
		QProcess::startDetached("osascript", args);
#endif
		m_nExecuteActionResult = DZ_OPERATION_FAILED_ERROR;
		return;
	}
	
	m_nExecuteActionResult = DZ_NO_ERROR;
	return;
}

DzBlenderActionExtras_02::DzBlenderActionExtras_02() :
	DzAction(tr("Package into an easy export folder..."), tr("An Extra Blender Action"))
{	
}

void DzBlenderActionExtras_02::executeAction()
{
	DzNode* m_pSelectedNode = dzScene->getPrimarySelection();
	if (m_pSelectedNode == nullptr && dzScene->getNumNodes() == 1) {
		dzScene->setPrimarySelection(dzScene->getNode(0));
		m_pSelectedNode = dzScene->getPrimarySelection();
	}
	
	if ( m_pSelectedNode == nullptr || (m_pSelectedNode->getObject() == nullptr) )
	{
		QMessageBox::critical(0, tr("No selection"), tr("You must select a figure to output."), QMessageBox::Abort );
		return;
	}
	
	QString sOriginalFilename = QFileDialog::getSaveFileName(0, "Package into an easy export folder...", QDesktopServices::storageLocation(QDesktopServices::DocumentsLocation));

	if (sOriginalFilename.isEmpty() || sOriginalFilename == "") {
		return;
	}

	QFileInfo oFileInfo(sOriginalFilename);
	QString sExportFilename = oFileInfo.fileName();
	QString sExportFolder = sExportFilename;
	QString sRootFolder = oFileInfo.path();
	
	QString sFinalFilePath = sRootFolder + "/" + sExportFolder + "/" + sExportFilename + ".dtu";

	QString sFinalFolderPath = sRootFolder + "/" + sExportFolder;
	sFinalFolderPath.replace("\\", "/");
	QDir dir;
	dir.mkpath(sFinalFolderPath);


	DzBlenderAction oBridge;
	oBridge.setCombineStrandHairPartsEnabled(true);
	oBridge.setNonInteractiveMode(1); // set script mode to disable GUI prompts
	
	oBridge.setUseLegacyPaths(false); // do not use legacy add-on intermediate folder system (blender, maya, cd4d)

	oBridge.setRootFolder(sRootFolder); // set base folder for exports
	oBridge.setExportFolder(sExportFolder); // set relative output folder for asset
	oBridge.setExportFilename(sExportFilename); // set basefilename (no extension)

//	oBridge.aMorphList = aMorphNames; // set morph names to export
	oBridge.setAllowMorphDoubleDipping(true); // must be enabled so that blendshape vertex deltas are fully evaluated to correct final vertex positions
	oBridge.setEmbedTexturesInOutputFile(false); // embed textures in fbx
	oBridge.setExportAllTextures(true); // collect all textures in ExportTextures folder
	oBridge.setBakeMakeupOverlay(true); // bake HD makeup overlays to diffuse texture

	oBridge.executeAction();

	DzError oExecuteActionResult = oBridge.getExecutActionResult();
	if (oExecuteActionResult == DZ_NO_ERROR)
	{
		QMessageBox::information(0, "Blender Exporter",
			tr("Export from Daz Studio complete."), QMessageBox::Ok);
		ShowExplorerWindow(sFinalFilePath);
	}
	else
	{
		QString sErrorString;
		sErrorString += QString("An error occured during the export operation (ErrorCode=%1).\n").arg(oExecuteActionResult);
		sErrorString += QString("Please check log files at : %1\n").arg(oBridge.getDestinationPath());
		QMessageBox::critical(0, "Blender Exporter", tr(sErrorString.toUtf8()), QMessageBox::Ok);

		ShowExplorerWindow(oBridge.getDestinationPath());
	}

}

DzBlenderActionExtras_03::DzBlenderActionExtras_03() :
	DzAction(tr("Export Strand-based Hair (Combined)..."), tr("An Extra Blender Action"))
{
}

void DzBlenderActionExtras_03::executeAction()
{
	bool m_bCombineStrandHairParts = true;
	DzNode* m_pSelectedNode = dzScene->getPrimarySelection();
	if (m_pSelectedNode == nullptr) {
		QMessageBox::information(0, tr("ERROR"), tr("Please Select Figure Node"), QMessageBox::Ok);
		return;
	}

	m_pSelectedNode = m_pSelectedNode->getSkeleton();

	if (m_pSelectedNode == nullptr || (m_pSelectedNode->getObject() == nullptr))
	{
		QMessageBox::critical(0, tr("No selection"), tr("You must select a figure to output."), QMessageBox::Abort);
		return;
	}

	QString sOriginalFilename = QFileDialog::getSaveFileName(0, "Package into an easy export folder...", QDesktopServices::storageLocation(QDesktopServices::DocumentsLocation));

	if (sOriginalFilename.isEmpty() || sOriginalFilename == "") {
		return;
	}

	QFileInfo oFileInfo(sOriginalFilename);
	QString sExportFilename = oFileInfo.fileName();
	QString sExportFolder = sExportFilename;
	QString sRootFolder = oFileInfo.path();

	QString sFinalFilePath = sRootFolder + "/" + sExportFolder + "/" + sExportFilename + ".dtu";

	QString sFinalFolderPath = sRootFolder + "/" + sExportFolder;
	sFinalFolderPath.replace("\\", "/");
	QDir dir;
	dir.mkpath(sFinalFolderPath);

	DzBlenderAction oBridge;
	oBridge.setCombineStrandHairPartsEnabled(true);
	oBridge.setNonInteractiveMode(1); // set script mode to disable GUI prompts

	oBridge.setUseLegacyPaths(false); // do not use legacy add-on intermediate folder system (blender, maya, cd4d)

	oBridge.setRootFolder(sRootFolder); // set base folder for exports
	oBridge.setExportFolder(sExportFolder); // set relative output folder for asset
	oBridge.setExportFilename(sExportFilename); // set basefilename (no extension)

	//	oBridge.aMorphList = aMorphNames; // set morph names to export
	oBridge.setAllowMorphDoubleDipping(true); // must be enabled so that blendshape vertex deltas are fully evaluated to correct final vertex positions
	oBridge.setEmbedTexturesInOutputFile(false); // embed textures in fbx
	oBridge.setExportAllTextures(true); // collect all textures in ExportTextures folder
	oBridge.setBakeMakeupOverlay(true); // bake HD makeup overlays to diffuse texture

	DzNode* parentNode = m_pSelectedNode;
	QMap<DzNode*, DzNode*> oUndoTable;
	oBridge.hideAllStrandBasedHair(parentNode, oUndoTable);
	// hide scalp
	foreach(DzNode *pHairNode, oUndoTable.keys())
	{
		if (pHairNode->getSkeleton() && pHairNode->getSkeleton()->getFollowTarget()) {
			DzNode* pFollowTarget = pHairNode->getSkeleton()->getFollowTarget();
			// if not directly following figure (parentNode), assume is scalp
			if (pFollowTarget != parentNode) {
				pFollowTarget->setVisible(false);
				if (oUndoTable.contains(pFollowTarget) == false)
				{
					DzNode* pParentNode = pFollowTarget->getNodeParent();
					if (pParentNode) {
						oUndoTable.insert(pFollowTarget, pParentNode);
						pParentNode->removeNodeChild(pFollowTarget);
					}
				}
			}
		}
	}

	dzApp->setBusyCursor();
	if (oUndoTable.count() > 0) {
		QList<DzNode*> aHairNodesList = oUndoTable.keys();
		if (m_bCombineStrandHairParts)
		{
			QString sHairPostfix = QString("_%1.abc").arg("hair");
			QString sAbcFilename = QString(sFinalFilePath).replace(".dtu", sHairPostfix, Qt::CaseInsensitive);
			oBridge.writeHair(sAbcFilename, aHairNodesList);
		}
		else
		{
			foreach(DzNode * pHairNode, aHairNodesList) {
				if (oBridge.isStrandBasedHair(pHairNode) == false) continue;
				QString sHairPostfix = QString("_%1.abc").arg(oBridge.cleanString(pHairNode->getLabel()));
				QString sAbcFilename = QString(sFinalFilePath).replace(".dtu", sHairPostfix, Qt::CaseInsensitive);
				oBridge.writeHair(sAbcFilename, QList<DzNode*>() << pHairNode);
			}
		}
	}
	dzApp->clearBusyCursor();

	// UNDO
	foreach(DzNode* pHairNode, oUndoTable.keys())
	{
		DzNode* pParentNode = oUndoTable[pHairNode];
		if (pParentNode) {
			pParentNode->addNodeChild(pHairNode);
		}
		pHairNode->setVisible(true);
	}

	ShowExplorerWindow(sFinalFilePath);
}

DzBlenderActionExtras_04::DzBlenderActionExtras_04() :
	DzAction(tr("Export Strand-based Hair (Separate)..."), tr("An Extra Blender Action"))
{
}

void DzBlenderActionExtras_04::executeAction()
{
	bool m_bCombineStrandHairParts = false;
	DzNode* m_pSelectedNode = dzScene->getPrimarySelection();
	if (m_pSelectedNode == nullptr) {
		QMessageBox::information(0, tr("ERROR"), tr("Please Select Figure Node"), QMessageBox::Ok);
		return;
	}

	m_pSelectedNode = m_pSelectedNode->getSkeleton();

	if (m_pSelectedNode == nullptr || (m_pSelectedNode->getObject() == nullptr))
	{
		QMessageBox::critical(0, tr("No selection"), tr("You must select a figure to output."), QMessageBox::Abort);
		return;
	}

	QString sOriginalFilename = QFileDialog::getSaveFileName(0, "Package into an easy export folder...", QDesktopServices::storageLocation(QDesktopServices::DocumentsLocation));

	if (sOriginalFilename.isEmpty() || sOriginalFilename == "") {
		return;
	}

	QFileInfo oFileInfo(sOriginalFilename);
	QString sExportFilename = oFileInfo.fileName();
	QString sExportFolder = sExportFilename;
	QString sRootFolder = oFileInfo.path();

	QString sFinalFilePath = sRootFolder + "/" + sExportFolder + "/" + sExportFilename + ".dtu";

	QString sFinalFolderPath = sRootFolder + "/" + sExportFolder;
	sFinalFolderPath.replace("\\", "/");
	QDir dir;
	dir.mkpath(sFinalFolderPath);

	DzBlenderAction oBridge;
	oBridge.setCombineStrandHairPartsEnabled(true);
	oBridge.setNonInteractiveMode(1); // set script mode to disable GUI prompts

	oBridge.setUseLegacyPaths(false); // do not use legacy add-on intermediate folder system (blender, maya, cd4d)

	oBridge.setRootFolder(sRootFolder); // set base folder for exports
	oBridge.setExportFolder(sExportFolder); // set relative output folder for asset
	oBridge.setExportFilename(sExportFilename); // set basefilename (no extension)

	//	oBridge.aMorphList = aMorphNames; // set morph names to export
	oBridge.setAllowMorphDoubleDipping(true); // must be enabled so that blendshape vertex deltas are fully evaluated to correct final vertex positions
	oBridge.setEmbedTexturesInOutputFile(false); // embed textures in fbx
	oBridge.setExportAllTextures(true); // collect all textures in ExportTextures folder
	oBridge.setBakeMakeupOverlay(true); // bake HD makeup overlays to diffuse texture

	DzNode* parentNode = m_pSelectedNode;
	QMap<DzNode*, DzNode*> oUndoTable;
	oBridge.hideAllStrandBasedHair(parentNode, oUndoTable);
	// hide scalp
	foreach(DzNode * pHairNode, oUndoTable.keys())
	{
		if (pHairNode->getSkeleton() && pHairNode->getSkeleton()->getFollowTarget()) {
			DzNode* pFollowTarget = pHairNode->getSkeleton()->getFollowTarget();
			// if not directly following figure (parentNode), assume is scalp
			if (pFollowTarget != parentNode) {
				pFollowTarget->setVisible(false);
				if (oUndoTable.contains(pFollowTarget) == false)
				{
					DzNode* pParentNode = pFollowTarget->getNodeParent();
					if (pParentNode) {
						oUndoTable.insert(pFollowTarget, pParentNode);
						pParentNode->removeNodeChild(pFollowTarget);
					}
				}
			}
		}
	}
	dzApp->setBusyCursor();
	if (oUndoTable.count() > 0) {
		QList<DzNode*> aHairNodesList = oUndoTable.keys();
		if (m_bCombineStrandHairParts)
		{
			QString sHairPostfix = QString("_%1.abc").arg("hair");
			QString sAbcFilename = QString(sFinalFilePath).replace(".dtu", sHairPostfix, Qt::CaseInsensitive);
			oBridge.writeHair(sAbcFilename, aHairNodesList);
		}
		else
		{
			foreach(DzNode * pHairNode, aHairNodesList) {
				if (oBridge.isStrandBasedHair(pHairNode) == false) continue;
				QString sHairPostfix = QString("_%1.abc").arg(oBridge.cleanString(pHairNode->getLabel()));
				QString sAbcFilename = QString(sFinalFilePath).replace(".dtu", sHairPostfix, Qt::CaseInsensitive);
				oBridge.writeHair(sAbcFilename, QList<DzNode*>() << pHairNode);
			}
		}
	}
	dzApp->clearBusyCursor();

	// UNDO
	foreach(DzNode * pHairNode, oUndoTable.keys())
	{
		DzNode* pParentNode = oUndoTable[pHairNode];
		if (pParentNode) {
			pParentNode->addNodeChild(pHairNode);
		}
		pHairNode->setVisible(true);
	}

	ShowExplorerWindow(sFinalFilePath);
}

DzBlenderActionExtras_05::DzBlenderActionExtras_05() :
	DzAction(tr("Placeholder..."), tr("An Extra Blender Action"))
{
}

void DzBlenderActionExtras_05::executeAction() {

}



#include "moc_DzBlenderActionExtras.cpp"
