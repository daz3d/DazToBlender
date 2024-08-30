#include <QtGui/qcheckbox.h>
#include <QtGui/QMessageBox>
#include <QtNetwork/qudpsocket.h>
#include <QtNetwork/qabstractsocket.h>
#include <QCryptographicHash>
#include <QtCore/qdir.h>

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

#ifdef WIN32
#include <shellapi.h>
#endif

#include "dzbridge.h"

int DzBlenderUtils::ExecuteBlenderScripts(QString sBlenderExecutablePath, QString sCommandlineArguments, QString sWorkingPath, QProcess* thisProcess, float fTimeoutInSeconds)
{
	// fork or spawn child process
	QStringList args = sCommandlineArguments.split(";");

//	float fTimeoutInSeconds = 2 * 60;
	float fMilliSecondsPerTick = 200;
	int numTotalTicks = fTimeoutInSeconds * 1000 / fMilliSecondsPerTick;
	DzProgress* progress = new DzProgress("Running Blender Script", numTotalTicks, false, true);
	progress->enable(true);
	QProcess* pToolProcess = new QProcess(thisProcess);
	pToolProcess->setWorkingDirectory(sWorkingPath);
	pToolProcess->start(sBlenderExecutablePath, args);
	int currentTick = 0;
	int timeoutTicks = numTotalTicks;
	bool bUserInitiatedTermination = false;
	while (pToolProcess->waitForFinished(fMilliSecondsPerTick) == false) {
		// if timeout reached, then terminate process
		if (currentTick++ > timeoutTicks) {
			if (!bUserInitiatedTermination)
			{
				QString sTimeoutText = QObject::tr("\
The current Blender operation is taking a long time.\n\
Do you want to Ignore this time-out and wait a little longer, or \n\
Do you want to Abort the operation now?");
				int result = QMessageBox::critical(0,
					QObject::tr("Daz To Blender: Blender Timout Error"),
					sTimeoutText,
					QMessageBox::Ignore,
					QMessageBox::Abort);
				if (result == QMessageBox::Ignore) {
					int snoozeTime = 60 * 1000 / fMilliSecondsPerTick;
					timeoutTicks += snoozeTime;
				}
				else {
					bUserInitiatedTermination = true;
				}
			}
			else
			{
				if (currentTick - timeoutTicks < 5) {
					pToolProcess->terminate();
				}
				else {
					pToolProcess->kill();
				}
			}
		}
		if (pToolProcess->state() == QProcess::Running) {
			progress->step();
		}
		else {
			break;
		}
	}
	progress->setCurrentInfo("Blender Script Completed.");
	progress->finish();
	delete progress;
	int nBlenderExitCode = pToolProcess->exitCode();

	return nBlenderExitCode;
}

bool DzBlenderUtils::GenerateBlenderBatchFile(QString batchFilePath, QString sBlenderExecutablePath, QString sCommandArgs)
{
	QString sBatchFileFolder = QFileInfo(batchFilePath).dir().path().replace("\\", "/");
	QDir().mkdir(sBatchFileFolder);

	// 4. Generate manual batch file to launch blender scripts
	QString sBatchString = QString("\"%1\"").arg(sBlenderExecutablePath);
	foreach(QString arg, sCommandArgs.split(";"))
	{
		if (arg.contains(" "))
		{
			sBatchString += QString(" \"%1\"").arg(arg);
		}
		else
		{
			sBatchString += " " + arg;
		}
	}
	// write batch
	QFile batchFileOut(batchFilePath);
	bool bResult = batchFileOut.open(QIODevice::WriteOnly | QIODevice::OpenModeFlag::Truncate);
	if (bResult) {
		batchFileOut.write(sBatchString.toAscii().constData());
		batchFileOut.close();
	}
	else {
		dzApp->log("ERROR: GenerateBlenderBatchFile(): Unable to open batch file for writing: " + batchFilePath);
	}

	return true;
}

bool DzBlenderUtils::PrepareAndRunBlenderProcessing(QString sDestinationFbx, QString sBlenderExecutablePath, QProcess* thisProcess, int nPythonExceptionExitCode)
{
	QString sIntermediatePath = QFileInfo(sDestinationFbx).dir().path().replace("\\", "/");
	QString sIntermediateScriptsPath = sIntermediatePath + "/Scripts";
	QDir().mkdir(sIntermediateScriptsPath);

	QStringList aScriptFilelist = (QStringList() << 
		"create_blend.py" <<
		"blender_tools.py" <<
		"NodeArrange.py" <<
		"game_readiness_tools.py"
		);
	// copy 
	foreach(auto sScriptFilename, aScriptFilelist)
	{
		bool replace = true;
		QString sEmbeddedFolderPath = ":/DazBridgeBlender";
		QString sEmbeddedFilepath = sEmbeddedFolderPath + "/" + sScriptFilename;
		QFile srcFile(sEmbeddedFilepath);
		QString tempFilepath = sIntermediateScriptsPath + "/" + sScriptFilename;
		DZ_BRIDGE_NAMESPACE::DzBridgeAction::copyFile(&srcFile, &tempFilepath, replace);
		srcFile.close();
	}

	QString sBlenderLogPath = sIntermediatePath + "/" + "create_blend.log";
	QString sScriptPath = sIntermediateScriptsPath + "/" + "create_blend.py";
	QString sCommandArgs = QString("--background;--log-file;%1;--python-exit-code;%2;--python;%3;%4").arg(sBlenderLogPath).arg(nPythonExceptionExitCode).arg(sScriptPath).arg(sDestinationFbx);
#if WIN32
	QString batchFilePath = sIntermediatePath + "/" + "create_blend.bat";
#else
	QString batchFilePath = sIntermediatePath + "/" + "create_blend.sh";
#endif
	DzBlenderUtils::GenerateBlenderBatchFile(batchFilePath, sBlenderExecutablePath, sCommandArgs);

	int nBlenderExitCode = DzBlenderUtils::ExecuteBlenderScripts(sBlenderExecutablePath, sCommandArgs, sIntermediatePath, thisProcess, 240);
#ifdef __APPLE__
	if (nBlenderExitCode != 0 && nBlenderExitCode != 120)
#else
	if (nBlenderExitCode != 0)
#endif
	{
		if (nBlenderExitCode == nPythonExceptionExitCode) {
			dzApp->log(QString("Daz To Blender: ERROR: Python error:.... %1").arg(nBlenderExitCode));
		}
		else {
			dzApp->log(QString("Daz To Blender: ERROR: exit code = %1").arg(nBlenderExitCode));
		}
		return false;
	}

	return true;
}

DzError	DzBlenderExporter::write(const QString& filename, const DzFileIOSettings* options)
{
	if (dzScene->getNumSelectedNodes() != 1)
	{
		DzNodeList rootNodes = DZ_BRIDGE_NAMESPACE::DzBridgeAction::BuildRootNodeList();
		if (rootNodes.length() == 1)
		{
			dzScene->setPrimarySelection(rootNodes[0]);
		}
		else if (rootNodes.length() > 1)
		{
			QMessageBox::critical(0, tr("Error: No Selection"),
					tr("Please select one Character or Prop in the scene to export."), QMessageBox::Abort);
			return DZ_OPERATION_FAILED_ERROR;
		}
	}

	//if (dzScene->getPrimarySelection() == NULL)
	//{
	//	QMessageBox::critical(0, tr("Blender Exporter: No Selection"), tr("Please select an object in the scene to export."), QMessageBox::Abort);
	//	return DZ_OPERATION_FAILED_ERROR;
	//}

	QString sBlenderOutputPath = QFileInfo(filename).dir().path().replace("\\", "/");

	// process options
	QMap<QString, QString> optionsMap;
	int numKeys = options->getNumValues();
	for (int i = 0; i < numKeys; i++) {
		auto key = options->getKey(i);
		auto val = options->getValue(i);
		optionsMap.insert(key, val);
		dzApp->log(QString("DEBUG: DzBlenderExporter: Options[%1]=[%2]").arg(key).arg(val) );
	}

	DzProgress exportProgress(tr("Blender Exporter starting..."), 100, false, true );
	exportProgress.setInfo(QString("Exporting to:\n    \"%1\"\n").arg(filename));

	exportProgress.setInfo("Generating intermediate file");
	exportProgress.step(25);

	DzBlenderAction* pBlenderAction = new DzBlenderAction();
	pBlenderAction->m_sOutputBlendFilepath = QString(filename).replace("\\", "/");
	pBlenderAction->setNonInteractiveMode(DZ_BRIDGE_NAMESPACE::eNonInteractiveMode::DzExporterMode);
	pBlenderAction->createUI();
	DzBlenderDialog* pDialog = qobject_cast<DzBlenderDialog*>(pBlenderAction->getBridgeDialog());

	// Move Blender Executable Widgets to Top of Dialog
	pDialog->requireBlenderExecutableWidget(true);
	pDialog->showBlenderToolsOptions(true);
	pDialog->setOutputBlendFilepath(filename);
	pBlenderAction->executeAction();
//	bool bUseBlenderTools = pDialog->getUseBlenderToolsCheckbox();
	pDialog->showBlenderToolsOptions(false);
	pDialog->requireBlenderExecutableWidget(false);

	if (pDialog->result() == QDialog::Rejected) {
		exportProgress.cancel();
		return DZ_USER_CANCELLED_OPERATION;
	}

	// if Blender Executable is not set, fail gracefully
	if (pBlenderAction->m_sBlenderExecutablePath == "") {
		QMessageBox::critical(0, tr("No Blender Executable Found"), tr("You must set the path to your Blender Executable. Aborting."), QMessageBox::Abort );
		return DZ_OPERATION_FAILED_ERROR;
	}

	QString sIntermediatePath = QFileInfo(pBlenderAction->m_sDestinationFBX).dir().path().replace("\\", "/");
	QString sIntermediateScriptsPath = sIntermediatePath + "/Scripts";
	QDir().mkdir(sIntermediateScriptsPath);

	QStringList aScriptFilelist = (QStringList() << 
		"create_blend.py" <<
		"blender_tools.py" <<
		"NodeArrange.py" <<
		"game_readiness_tools.py"
		);
	// copy 
	foreach(auto sScriptFilename, aScriptFilelist)
	{
		bool replace = true;
		QString sEmbeddedFolderPath = ":/DazBridgeBlender";
		QString sEmbeddedFilepath = sEmbeddedFolderPath + "/" + sScriptFilename;
		QFile srcFile(sEmbeddedFilepath);
		QString tempFilepath = sIntermediateScriptsPath + "/" + sScriptFilename;
		DZ_BRIDGE_NAMESPACE::DzBridgeAction::copyFile(&srcFile, &tempFilepath, replace);
		srcFile.close();
	}

	exportProgress.setInfo("Generating Blend File");
	exportProgress.step(25);

	QString sBlenderLogPath = sIntermediatePath + "/" + "create_blend.log";
	QString sScriptPath = sIntermediateScriptsPath + "/" + "create_blend.py";
	QString sCommandArgs = QString("--background;--log-file;%1;--python-exit-code;%2;--python;%3;%4").arg(sBlenderLogPath).arg(pBlenderAction->m_nPythonExceptionExitCode).arg(sScriptPath).arg(pBlenderAction->m_sDestinationFBX);
#if WIN32
	QString batchFilePath = sIntermediatePath + "/" + "create_blend.bat";
#else
	QString batchFilePath = sIntermediatePath + "/" + "create_blend.sh";
#endif
	DzBlenderUtils::GenerateBlenderBatchFile(batchFilePath, pBlenderAction->m_sBlenderExecutablePath, sCommandArgs);

	//bool result = pBlenderAction->executeBlenderScripts(pBlenderAction->m_sBlenderExecutablePath, sCommandArgs);
	bool result = false;
	pBlenderAction->m_nBlenderExitCode = DzBlenderUtils::ExecuteBlenderScripts(pBlenderAction->m_sBlenderExecutablePath, sCommandArgs, sIntermediatePath, &QProcess(this), 240);
#ifdef __APPLE__
	if (pBlenderAction->m_nBlenderExitCode != 0 && pBlenderAction->m_nBlenderExitCode != 120)
#else
	if (pBlenderAction->m_nBlenderExitCode != 0)
#endif
	{
		if (pBlenderAction->m_nBlenderExitCode == pBlenderAction->m_nPythonExceptionExitCode) {
			dzApp->log(QString("Daz To Blender: ERROR: Python error:.... %1").arg(pBlenderAction->m_nBlenderExitCode));
		}
		else {
			dzApp->log(QString("Daz To Blender: ERROR: exit code = %1").arg(pBlenderAction->m_nBlenderExitCode));
		}
		result = false;
	}
	else {
		result = true;
	}


	exportProgress.step(25);
	//if (result) 
	//{
	//	bool replace = true;
	//	QString sBlendIntermediateFile = QString(pBlenderAction->m_sDestinationFBX).replace(".fbx", ".blend", Qt::CaseInsensitive);
	//	QFile srcFile(sBlendIntermediateFile);
	//	bool copy_result = DZ_BRIDGE_NAMESPACE::DzBridgeAction::copyFile(&srcFile, &QString(filename), replace);
	//	srcFile.close();
	//	if (copy_result == false) {
	//		QMessageBox::critical(0, tr("Blender Exporter"), 
	//			tr("Unable to copy Blend file to destination."), QMessageBox::Abort);
	//	}
	//}

	if (result)
	{
		exportProgress.update(100);
		QMessageBox::information(0, "Blender Exporter",
			tr("Export from Daz Studio complete."), QMessageBox::Ok);

#ifdef WIN32
		ShellExecuteA(NULL, "open", sBlenderOutputPath.toLocal8Bit().data(), NULL, NULL, SW_SHOWDEFAULT);
		//// The above line does the equivalent as following lines, but has advantage of only opening 1 explorer window
		//// with multiple clicks.
		//
		//	QStringList args;
		//	args << "/select," << QDir::toNativeSeparators(sIntermediateFolderPath);
		//	QProcess::startDetached("explorer", args);
		//
#elif defined(__APPLE__)
		QStringList args;
		args << "-e";
		args << "tell application \"Finder\"";
		args << "-e";
		args << "activate";
		args << "-e";
		if (QFileInfo(filename).exists()) {
			args << "select POSIX file \"" + filename + "\"";
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
		if (pBlenderAction->m_nBlenderExitCode == pBlenderAction->m_nPythonExceptionExitCode) {
			QString sErrorString;
			sErrorString += QString("An error occured while running the Blender Python script (ExitCode=%1).\n").arg(pBlenderAction->m_nBlenderExitCode);
			sErrorString += QString("\nPlease check log files at : %1\n").arg(pBlenderAction->m_sDestinationPath);
			sErrorString += QString("\nYou can rerun the Blender command-line script manually using: %1").arg(batchFilePath);
			QMessageBox::critical(0, "Blender Exporter", tr(sErrorString.toLocal8Bit()), QMessageBox::Ok);
		}
		else {
			QString sErrorString;
			sErrorString += QString("An error occured during the export process (ExitCode=%1).\n").arg(pBlenderAction->m_nBlenderExitCode);
			sErrorString += QString("Please check log files at : %1\n").arg(pBlenderAction->m_sDestinationPath);
			QMessageBox::critical(0, "Blender Exporter", tr(sErrorString.toLocal8Bit()), QMessageBox::Ok);
		}
#ifdef WIN32
		ShellExecuteA(NULL, "open", pBlenderAction->m_sDestinationPath.toLocal8Bit().data(), NULL, NULL, SW_SHOWDEFAULT);
#elif defined(__APPLE__)
		QStringList args;
		args << "-e";
		args << "tell application \"Finder\"";
		args << "-e";
		args << "activate";
		args << "-e";
		args << "select POSIX file \"" + batchFilePath + "\"";
		args << "-e";
		args << "end tell";
		QProcess::startDetached("osascript", args);
#endif
	}

	exportProgress.finish();

	return DZ_NO_ERROR;
};

bool DzBlenderAction::executeBlenderScripts(QString sFilePath, QString sCommandlineArguments)
{
	// fork or spawn child process
	QString sWorkingPath = m_sDestinationPath;
	QStringList args = sCommandlineArguments.split(";");

	float fTimeoutInSeconds = 2 * 60;
	float fMilliSecondsPerTick = 200;
	int numTotalTicks = fTimeoutInSeconds * 1000 / fMilliSecondsPerTick;
	DzProgress* progress = new DzProgress("Running Blender Script", numTotalTicks, false, true);
	progress->enable(true);
	QProcess* pToolProcess = new QProcess(this);
	pToolProcess->setWorkingDirectory(sWorkingPath);
	pToolProcess->start(sFilePath, args);
	int currentTick = 0;
	int timeoutTicks = numTotalTicks;
	bool bUserInitiatedTermination = false;
	while (pToolProcess->waitForFinished(fMilliSecondsPerTick) == false) {
		// if timeout reached, then terminate process
		if (currentTick++ > timeoutTicks) {
			if (!bUserInitiatedTermination)
			{
				QString sTimeoutText = tr("\
The current Blender operation is taking a long time.\n\
Do you want to Ignore this time-out and wait a little longer, or \n\
Do you want to Abort the operation now?");
				int result = QMessageBox::critical(0,
					tr("Daz To Blender: Blender Timout Error"),
					sTimeoutText,
					QMessageBox::Ignore,
					QMessageBox::Abort);
				if (result == QMessageBox::Ignore) {
					int snoozeTime = 60 * 1000 / fMilliSecondsPerTick;
					timeoutTicks += snoozeTime;
				} else {
					bUserInitiatedTermination = true;
				}
			} 
			else 
			{
				if (currentTick - timeoutTicks < 5) {
					pToolProcess->terminate();
				} else {
					pToolProcess->kill();
				}
			}
		}
		if (pToolProcess->state() == QProcess::Running) {
			progress->step();
		} else {
			break;
		}
	}
	progress->setCurrentInfo("Blender Script Completed.");
	progress->finish();
	delete progress;
	m_nBlenderExitCode = pToolProcess->exitCode();
#ifdef __APPLE__
	if (m_nBlenderExitCode != 0 && m_nBlenderExitCode != 120)
#else
	if (m_nBlenderExitCode != 0)
#endif
	{
		if (m_nBlenderExitCode == m_nPythonExceptionExitCode) {
			dzApp->log(QString("Daz To Blender: ERROR: Python error:.... %1").arg(m_nBlenderExitCode));
		} else {
			dzApp->log(QString("Daz To Blender: ERROR: exit code = %1").arg(m_nBlenderExitCode));
		}
		return false;
	}

	return true;
}

bool DzBlenderAction::preProcessScene(DzNode* parentNode)
{
	DzBridgeAction::preProcessScene(parentNode);

	if (m_sExportRigMode == "" || m_sExportRigMode == "--")
		return true;

	DzProgress* blenderProgress = new DzProgress(tr("PreProcessing Scene"), 100, false, true);

	QString sBoneConverter = "bone_converter_aArgs.dsa";
	QString sUnrealMannyRigFile = "g9_to_unreal_manny.json";
	QString sMetahumanRigFile = "g9_to_metahuman.json";
	QString sUnityRigFile = "g9_to_unity.json";
	QString sMixamoRigFile = "g9_to_mixamo.json";

	blenderProgress->setInfo(tr("Preparing Rig Converter files..."));
	QStringList aScriptFilelist = (QStringList() <<
		sBoneConverter <<
		sUnrealMannyRigFile <<
		sMetahumanRigFile <<
		sUnityRigFile <<
		sMixamoRigFile
		);
	// copy 
	foreach(auto sScriptFilename, aScriptFilelist)
	{
		bool replace = true;
		QString sEmbeddedFolderPath = ":/DazBridgeBlender";
		QString sEmbeddedFilepath = sEmbeddedFolderPath + "/" + sScriptFilename;
		QFile srcFile(sEmbeddedFilepath);
		QString tempFilepath = dzApp->getTempPath() + "/" + sScriptFilename;
		DZ_BRIDGE_NAMESPACE::DzBridgeAction::copyFile(&srcFile, &tempFilepath, replace);
		srcFile.close();
	}

	/// BONE CONVERSION OPERATION
	blenderProgress->setInfo(tr("Converting Rig..."));
	blenderProgress->step();
	QString sScriptFilepath = dzApp->getTempPath() + "/" + sBoneConverter;

	// Compile arguments
	QVariantList aArgs;
	if (m_sExportRigMode == "metahuman") {
		aArgs.append(QVariant(dzApp->getTempPath() + "/" + sMetahumanRigFile));
	}
	else if (m_sExportRigMode == "unreal") {
		aArgs.append(QVariant(dzApp->getTempPath() + "/" + sUnrealMannyRigFile));
	}
	else if (m_sExportRigMode == "unity") {
		aArgs.append(QVariant(dzApp->getTempPath() + "/" + sUnityRigFile));
	}
	else if (m_sExportRigMode == "mixamo") {
		aArgs.append(QVariant(dzApp->getTempPath() + "/" + sMixamoRigFile));
	}

	QScopedPointer<DzScript> Script(new DzScript());
	// run bone conversion on main figure
	dzScene->selectAllNodes(false);
	dzScene->setPrimarySelection(parentNode);
	Script.reset(new DzScript());
	Script->loadFromFile(sScriptFilepath);
	Script->execute(aArgs);
	// iterate through node children list before making changes to it, otherwise it gets invalidated during processing
	QList<DzFigure*> figureList;
	foreach(QObject* listNode, parentNode->getNodeChildren())
	{
		if (listNode->inherits("DzFigure") == false) continue;
		DzFigure* figChild = qobject_cast<DzFigure*>(listNode);
		if (figChild) {
			figureList.append(figChild);
		}
	}
/*
	// run bone conversion each geograft and attached body part (aka, ALL FOLLOWERS)
	foreach(DzFigure* figChild, figureList) {
		if (figChild == NULL) continue;
		QString sChildName = figChild->getName();
		QString sChildLabel = figChild->getLabel();
		dzApp->debug(QString("DzBlenderAction: DEBUG: converting skeleton for: %1 [%2]").arg(sChildLabel).arg(sChildName));
		dzScene->selectAllNodes(false);
		dzScene->setPrimarySelection(figChild);
		Script.reset(new DzScript());
		Script->loadFromFile(sScriptFilepath);
		Script->execute(aArgs);
		DzSkeleton* pFollowTarget = figChild->getFollowTarget();
		figChild->setFollowTarget(NULL);
		figChild->setFollowTarget(pFollowTarget);
	}
*/
	dzScene->selectAllNodes(false);
//	dzScene->setPrimarySelection(parentNode);

	blenderProgress->finish();

	return true;
}

DzBlenderAction::DzBlenderAction() :
	DzBridgeAction(tr("Send to &Blender..."), tr("Send the selected node to Blender."))
{
	m_nNonInteractiveMode = 0;
	m_sAssetType = QString("SkeletalMesh");
	//Setup Icon
	QString iconName = "Daz to Blender";
	QPixmap basePixmap = QPixmap::fromImage(getEmbeddedImage(iconName.toLatin1()));
	QIcon icon;
	icon.addPixmap(basePixmap, QIcon::Normal, QIcon::Off);
	QAction::setIcon(icon);
	// Enable Optional Daz Bridge Behaviors

}

bool DzBlenderAction::createUI()
{
	// Check if the main window has been created yet.
	// If it hasn't, alert the user and exit early.
	DzMainWindow* mw = dzApp->getInterface();
	if (!mw)
	{
		if (m_nNonInteractiveMode == 0) QMessageBox::warning(0, tr("Error"),
			tr("The main window has not been created yet."), QMessageBox::Ok);

		return false;
	}

	// Create the dialog
	if (!m_bridgeDialog)
	{
		m_bridgeDialog = new DzBlenderDialog(mw);
	}
	else
	{
		DzBlenderDialog* blenderDialog = qobject_cast<DzBlenderDialog*>(m_bridgeDialog);
		if (blenderDialog)
		{
			blenderDialog->resetToDefaults();
			blenderDialog->loadSavedSettings();
		}
	}

	// m_subdivisionDialog creation REQUIRES valid Character or Prop selected
	if (dzScene->getNumSelectedNodes() != 1)
	{
		if (m_nNonInteractiveMode == 0) QMessageBox::warning(0, tr("Error"),
			tr("Please select one Character or Prop to send."), QMessageBox::Ok);

		return false;
	}

	if (!m_subdivisionDialog) m_subdivisionDialog = DZ_BRIDGE_NAMESPACE::DzBridgeSubdivisionDialog::Get(m_bridgeDialog);
	if (!m_morphSelectionDialog) m_morphSelectionDialog = DZ_BRIDGE_NAMESPACE::DzBridgeMorphSelectionDialog::Get(m_bridgeDialog);

	return true;
}

#include "dzexportmgr.h"
void DzBlenderAction::executeAction()
{
	// CreateUI() disabled for debugging -- 2022-Feb-25
	/*
		 // Create and show the dialog. If the user cancels, exit early,
		 // otherwise continue on and do the thing that required modal
		 // input from the user.
		 if (createUI() == false)
			 return;
	*/

	// Check if the main window has been created yet.
	// If it hasn't, alert the user and exit early.
	DzMainWindow* mw = dzApp->getInterface();
	if (!mw)
	{
		if (m_nNonInteractiveMode == 0)
		{
			QMessageBox::warning(0, tr("Error"),
				tr("The main window has not been created yet."), QMessageBox::Ok);
		}
		return;
	}

	// Create and show the dialog. If the user cancels, exit early,
	// otherwise continue on and do the thing that required modal
	// input from the user.
	if (dzScene->getNumSelectedNodes() != 1)
	{
		DzNodeList rootNodes = BuildRootNodeList();
		if (rootNodes.length() == 1)
		{
			dzScene->setPrimarySelection(rootNodes[0]);
		}
		//else if (rootNodes.length() > 1)
		//{
		//	if (m_nNonInteractiveMode == 0)
		//	{
		//		QMessageBox::warning(0, tr("Error"),
		//			tr("Please select one Character or Prop to send."), QMessageBox::Ok);
		//	}
		//}
	}

	// Create the dialog
	if (m_bridgeDialog == nullptr)
	{
		m_bridgeDialog = new DzBlenderDialog(mw);
	}
	else
	{
		if ( m_nNonInteractiveMode == DZ_BRIDGE_NAMESPACE::eNonInteractiveMode::FullInteractiveMode )
		{
			m_bridgeDialog->resetToDefaults();
			m_bridgeDialog->loadSavedSettings();
		}
	}

	// Prepare member variables when not using GUI
	if (isInteractiveMode() == false)
	{
//		if (m_sRootFolder != "") m_bridgeDialog->getIntermediateFolderEdit()->setText(m_sRootFolder);

		if (m_aMorphListOverride.isEmpty() == false)
		{
			m_bEnableMorphs = true;
			m_sMorphSelectionRule = m_aMorphListOverride.join("\n1\n");
			m_sMorphSelectionRule += "\n1\n.CTRLVS\n2\nAnything\n0";
			if (m_morphSelectionDialog == nullptr)
			{
				m_morphSelectionDialog = DZ_BRIDGE_NAMESPACE::DzBridgeMorphSelectionDialog::Get(m_bridgeDialog);
			}
			m_MorphNamesToExport.clear();
			foreach(QString morphName, m_aMorphListOverride)
			{
				QString label = m_morphSelectionDialog->GetMorphLabelFromName(morphName);
				m_MorphNamesToExport.append(morphName);
			}
		}
		else
		{
			m_bEnableMorphs = false;
			m_sMorphSelectionRule = "";
			m_MorphNamesToExport.clear();
		}

	}

	// If the Accept button was pressed, start the export
	int dlgResult = -1;
	if ( isInteractiveMode() )
	{
		dlgResult = m_bridgeDialog->exec();
	}
	if (isInteractiveMode() == false || dlgResult == QDialog::Accepted)
	{
		// Read Common GUI values
		if (readGui(m_bridgeDialog) == false)
		{
			return;
		}

		// DB 2021-10-11: Progress Bar
		DzProgress* exportProgress = new DzProgress("Sending to Blender...", 10);

		//Create Daz3D folder if it doesn't exist
		QDir dir;
		dir.mkpath(m_sRootFolder);
		exportProgress->step();

		if (m_sAssetType == "Environment") {
			QDir().mkdir(m_sDestinationPath);
			m_pSelectedNode = dzScene->getPrimarySelection();
			m_bUseBlenderTools = true;

			auto objectList = dzScene->getNodeList();
			foreach(auto el, objectList) {
				DzNode* pNode = qobject_cast<DzNode*>(el);
				preProcessScene(pNode);
			}
			DzExportMgr* ExportManager = dzApp->getExportMgr();
			DzExporter* Exporter = ExportManager->findExporterByClassName("DzFbxExporter");
			DzFileIOSettings ExportOptions;
			ExportOptions.setBoolValue("doSelected", false);
			ExportOptions.setBoolValue("doVisible", true);
			ExportOptions.setBoolValue("doFigures", true);
			ExportOptions.setBoolValue("doProps", true);
			ExportOptions.setBoolValue("doAnims", true);
			ExportOptions.setIntValue("RunSilent", true);
			ExportOptions.setBoolValue("doLights", false);
			ExportOptions.setBoolValue("doCameras", false);
			setExportOptions(ExportOptions);
			// NOTE: be careful to use m_sExportFbx and NOT m_sExportFilename since FBX and DTU base name may differ
			QString sEnvironmentFbx = m_sDestinationPath + m_sExportFbx + ".fbx";
			Exporter->writeFile(sEnvironmentFbx, &ExportOptions);

			writeConfiguration();

			// ?? potential crash because assumes single preprocessscene event
			undoPreProcessScene();

			// if not in DzExporterMode, then run the blender script manually
			if (m_nNonInteractiveMode != DZ_BRIDGE_NAMESPACE::eNonInteractiveMode::DzExporterMode) {
				DzBlenderUtils::PrepareAndRunBlenderProcessing(m_sDestinationFBX, m_sBlenderExecutablePath, &QProcess(this), m_nPythonExceptionExitCode);
			}
		}
		else {
			exportHD(exportProgress);
		}

		// DB 2021-10-11: Progress Bar
		exportProgress->finish();

		// DB 2021-09-02: messagebox "Export Complete"
		if (m_nNonInteractiveMode == 0)
		{
			QMessageBox::information(0, "Daz To Blender Bridge",
				tr("Export phase from Daz Studio complete. Please switch to Blender to begin Import phase."), QMessageBox::Ok);
		}

	}
}

QString DzBlenderAction::createBlenderFiles(bool replace)
{

	QString srcPath = ":/DazBridgeBlender/BlenderAddon.zip";
	QFile srcFile(srcPath);
//	QString destPath = destinationFolder + "/BlenderAddon.zip";
//	this->copyFile(&srcFile, &destPath, replace);
	srcFile.close();

	return "";
}

void DzBlenderAction::writeConfiguration()
{
	QString DTUfilename = m_sDestinationPath + m_sExportFilename + ".dtu";
	QFile DTUfile(DTUfilename);
	DTUfile.open(QIODevice::WriteOnly);
	DzJsonWriter writer(&DTUfile);
	writer.startObject(true);

	writeDTUHeader(writer);

	// Plugin-specific items
	writer.addMember("Use Blender Tools", m_bUseBlenderTools);
	writer.addMember("Output Blend Filepath", m_sOutputBlendFilepath);
	writer.addMember("Texture Atlas Mode", m_sTextureAtlasMode);
	writer.addMember("Texture Atlas Size", m_nTextureAtlasSize);
	writer.addMember("Export Rig Mode", m_sExportRigMode);
	writer.addMember("Enable Gpu Baking", m_bEnableGpuBaking);
	writer.addMember("Embed Textures", m_bEmbedTexturesInOutputFile);
	writer.addMember("Generate Final Fbx", m_bGenerateFinalFbx);
	writer.addMember("Generate Final Glb", m_bGenerateFinalGlb);

//	if (m_sAssetType.toLower().contains("mesh") || m_sAssetType == "Animation")
	if (true)
	{
		QTextStream *pCVSStream = nullptr;
		if (m_bExportMaterialPropertiesCSV)
		{
			QString filename = m_sDestinationPath + m_sExportFilename + "_Maps.csv";
			QFile file(filename);
			file.open(QIODevice::WriteOnly);
			pCVSStream = new QTextStream(&file);
			*pCVSStream << "Version, Object, Material, Type, Color, Opacity, File" << endl;
		}
		if (m_sAssetType == "Environment") {
			writeSceneMaterials(writer, pCVSStream);
		}
		else {
			writeAllMaterials(m_pSelectedNode, writer, pCVSStream);
		}
		writeAllMorphs(writer);

		writeMorphLinks(writer);
		writeMorphNames(writer);

		DzBoneList aBoneList = getAllBones(m_pSelectedNode);

		writeSkeletonData(m_pSelectedNode, writer);
		writeHeadTailData(m_pSelectedNode, writer);

		writeJointOrientation(aBoneList, writer);
		writeLimitData(aBoneList, writer);
		writePoseData(m_pSelectedNode, writer, true);
		writeAllSubdivisions(writer);
		writeAllDforceInfo(m_pSelectedNode, writer);
	}

	//if (m_sAssetType == "Pose")
	//{
	//   writeAllPoses(writer);
	//}

	//if (m_sAssetType == "Environment")
	//{
	//	writeEnvironment(writer);
	//}

	writer.finishObject();
	DTUfile.close();

}

// Setup custom FBX export options
void DzBlenderAction::setExportOptions(DzFileIOSettings& ExportOptions)
{
	ExportOptions.setBoolValue("doFps", true);
	ExportOptions.setBoolValue("doLocks", false);
	ExportOptions.setBoolValue("doLimits", false);
	ExportOptions.setBoolValue("doBaseFigurePoseOnly", false);
	ExportOptions.setBoolValue("doHelperScriptScripts", false);
	ExportOptions.setBoolValue("doMentalRayMaterials", false);

	// Unable to use this option, since generated files are referenced only in FBX and unknown to DTU
	ExportOptions.setBoolValue("doDiffuseOpacity", false);
	// disable these options since we use Blender to generate a new FBX with embedded files
	ExportOptions.setBoolValue("doEmbed", false);
	ExportOptions.setBoolValue("doCopyTextures", false);
}

QString DzBlenderAction::readGuiRootFolder()
{
	QString rootFolder = QDesktopServices::storageLocation(QDesktopServices::DocumentsLocation) + QDir::separator() + "DazToBlender";
#if __LEGACY_PATHS__
	if (m_sAssetType == "SkeletalMesh" || m_sAssetType == "Animation")
	{
		rootFolder = QDesktopServices::storageLocation(QDesktopServices::DocumentsLocation) + "/DAZ 3D/Bridges/Daz To Blender/Exports/FIG/FIG0";
		rootFolder = rootFolder.replace("\\", "/");
	}
	else
	{
		rootFolder = QDesktopServices::storageLocation(QDesktopServices::DocumentsLocation) + "/DAZ 3D/Bridges/Daz To Blender/Exports/ENV/ENV0";
		rootFolder = rootFolder.replace("\\", "/");
	}
	if (m_bridgeDialog)
	{
		QLineEdit* intermediateFolderEdit = nullptr;
		DzBlenderDialog* blenderDialog = qobject_cast<DzBlenderDialog*>(m_bridgeDialog);
		if (blenderDialog)
			intermediateFolderEdit = blenderDialog->getIntermediateFolderEdit();
		if (intermediateFolderEdit)
			rootFolder = intermediateFolderEdit->text().replace("\\", "/");
	}
#else
	if (m_bridgeDialog)
	{
		QLineEdit* intermediateFolderEdit = nullptr;
		DzBlenderDialog* blenderDialog = qobject_cast<DzBlenderDialog*>(m_bridgeDialog);

		if (blenderDialog)
			intermediateFolderEdit = blenderDialog->getIntermediateFolderEdit();

		if (intermediateFolderEdit)
			rootFolder = intermediateFolderEdit->text().replace("\\", "/") + "/Daz3D";
	}
#endif

	return rootFolder;
}

bool DzBlenderAction::readGui(DZ_BRIDGE_NAMESPACE::DzBridgeDialog* BridgeDialog)
{
	bool bResult = DzBridgeAction::readGui(BridgeDialog);
	if (!bResult)
	{
		return false;
	}

#if __LEGACY_PATHS__
	QString sDefaultRootFolder = QDesktopServices::storageLocation(QDesktopServices::DocumentsLocation) + "/DAZ 3D/Bridges/Daz To Blender/";
	if (m_sRootFolder == "")
		m_sRootFolder = sDefaultRootFolder;
	if (m_sAssetType == "SkeletalMesh" || m_sAssetType == "Animation")
	{
		m_sRootFolder = m_sRootFolder + "/Exports/FIG";
		m_sRootFolder = m_sRootFolder.replace("\\", "/");
		m_sExportSubfolder = "FIG0";
		m_sExportFbx = "B_FIG";
		m_sExportFilename = "FIG";
	}
	else
	{
		m_sRootFolder = m_sRootFolder + "/Exports/ENV";
		m_sRootFolder = m_sRootFolder.replace("\\", "/");
		m_sExportSubfolder = "ENV0";
		m_sExportFbx = "B_ENV";
		m_sExportFilename = "ENV";
	}
	m_sDestinationPath = m_sRootFolder + "/" + m_sExportSubfolder + "/";
	m_sDestinationFBX = m_sDestinationPath + m_sExportFbx + ".fbx";
#endif

	// Read Custom GUI values
	DzBlenderDialog* pBlenderDialog = qobject_cast<DzBlenderDialog*>(m_bridgeDialog);

	if (pBlenderDialog)
	{
		if (m_sBlenderExecutablePath == "" || isInteractiveMode() ) m_sBlenderExecutablePath = pBlenderDialog->m_wBlenderExecutablePathEdit->text().replace("\\", "/");
		
		// if dzexporter mode, then read blender tools options
		if (m_nNonInteractiveMode == DZ_BRIDGE_NAMESPACE::eNonInteractiveMode::DzExporterMode) 
		{
			m_bUseBlenderTools = pBlenderDialog->getUseBlenderToolsCheckbox();
			m_sTextureAtlasMode = pBlenderDialog->getTextureAtlasMode();
			m_sExportRigMode = pBlenderDialog->getExportRigMode();
			m_nTextureAtlasSize = pBlenderDialog->getTextureAtlasSize();
			m_bEnableGpuBaking = pBlenderDialog->getUseGpuBaking();
			m_bEmbedTexturesInOutputFile = pBlenderDialog->getEnableEmbedTexturesInOutputFile();
			m_bGenerateFinalFbx = pBlenderDialog->getGenerateFbx();
			m_bGenerateFinalGlb = pBlenderDialog->getGenerateGlb();
		}
		else
		{
			m_bUseBlenderTools = false;
			m_sOutputBlendFilepath = "";
			m_sTextureAtlasMode = "";
			m_sExportRigMode = "";
			m_nTextureAtlasSize = 0;
			m_bEnableGpuBaking = false;
			m_bEmbedTexturesInOutputFile = false;
			m_bGenerateFinalFbx = false;
			m_bGenerateFinalGlb = false;
		}
	}
	else
	{
		// TODO: issue error and fail gracefully
		dzApp->log("Daz To Blender: ERROR: Blender Dialog was not initialized.  Cancelling operation...");

		return false;
	}

	return true;
}

#include "FbxTools.h"
#include "OpenFBXInterface.h"

void FixPrePostRotations(FbxNode* pNode)
{
	QString sNodeName = pNode->GetName();
	for (int nChildIndex = 0; nChildIndex < pNode->GetChildCount(); nChildIndex++)
	{
		FbxNode* pChildBone = pNode->GetChild(nChildIndex);
		FixPrePostRotations(pChildBone);
	}
	if (sNodeName.contains("twist", Qt::CaseInsensitive) == false)
	{
		pNode->SetPreRotation(FbxNode::EPivotSet::eSourcePivot, FbxVector4(0, 0, 0));
		pNode->SetPostRotation(FbxNode::EPivotSet::eSourcePivot, FbxVector4(0, 0, 0));
	}
}

FbxNode* GetBone(FbxNode* pNode) {
	for (int i = 0; i < pNode->GetChildCount(); i++) {
		FbxNode* pChild = pNode->GetChild(i);
		auto attribute = pChild->GetNodeAttribute();
		if (attribute && attribute->GetAttributeType() == FbxNodeAttribute::eSkeleton) {
			FbxSkeleton* pSkeleton = (FbxSkeleton*) attribute;
			if (pSkeleton->GetSkeletonType() == FbxSkeleton::eLimbNode) {
				return pChild;
			}
		}
	}

	return NULL;
}

FbxNode* GetMeshRootBone(FbxMesh* meshNode) {
	if (meshNode == nullptr) {
		return nullptr;
	}

	// Iterate through the connected nodes
	int connectionCount = meshNode->GetSrcObjectCount(FbxCriteria::ObjectType(FbxNode::ClassId));
	for (int i = 0; i < connectionCount; ++i) {
		FbxNode* connectedNode = (FbxNode*)meshNode->GetSrcObject(FbxCriteria::ObjectType(FbxNode::ClassId), i);

		// Check if this node has a FbxSkeleton attribute
		if (connectedNode && connectedNode->GetNodeAttribute()) {
			FbxNodeAttribute* attribute = connectedNode->GetNodeAttribute();
			if (attribute->GetAttributeType() == FbxNodeAttribute::eSkeleton) {
//				FbxSkeleton* skeleton = (FbxSkeleton*)attribute;
				return GetBone(connectedNode);
			}
		}
	}

	return nullptr;  // No eLimbNode found
}

bool DzBlenderAction::postProcessFbx(QString fbxFilePath)
{
	bool result = DzBridgeAction::postProcessFbx(fbxFilePath);
	//	if (!result) return false;

	if (m_bPostProcessFbx == false)
		return false;

	OpenFBXInterface* openFBX = OpenFBXInterface::GetInterface();
	FbxScene* pScene = openFBX->CreateScene("Base Mesh Scene");
	if (openFBX->LoadScene(pScene, fbxFilePath.toLocal8Bit().data()) == false)
	{
		if (m_nNonInteractiveMode == 0) QMessageBox::warning(0, "Error",
			"An error occurred while processing the Fbx file...", QMessageBox::Ok);
		printf("\n\nAn error occurred while processing the Fbx file...");
		return false;
	}

	m_bExperimental_FbxPostProcessing = (m_nNonInteractiveMode == DZ_BRIDGE_NAMESPACE::eNonInteractiveMode::DzExporterMode);
	if (m_bExperimental_FbxPostProcessing)
	{
		// Find the root bone.  There should only be one bone off the scene root
		FbxNode* RootNode = pScene->GetRootNode();
		FbxNode* RootBone = nullptr;
		QString RootBoneName("");
		for (int ChildIndex = 0; ChildIndex < RootNode->GetChildCount(); ++ChildIndex)
		{
			FbxNode* ChildNode = RootNode->GetChild(ChildIndex);
			FbxNodeAttribute* Attr = ChildNode->GetNodeAttribute();
			if (Attr && Attr->GetAttributeType() == FbxNodeAttribute::eSkeleton)
			{
				RootBone = ChildNode;
				RootBoneName = RootBone->GetName();
				if (m_sExportRigMode == "unreal" || m_sExportRigMode == "metahuman") {
					RootBone->SetName("root");
					Attr->SetName("root");
				}
				else if (m_sExportRigMode == "mixamo") {
					RootBone->SetName("Armature");
					Attr->SetName("Armature");
				}
				break;
			}
		}

		//// Daz characters sometimes have additional skeletons inside the character for accesories
		//if (AssetType == DazAssetType::SkeletalMesh)
		//{
		//	FDazToUnrealFbx::ParentAdditionalSkeletalMeshes(Scene);
		//}
		// Daz Studio puts the base bone rotations in a different place than Unreal expects them.
		//if (CachedSettings->FixBoneRotationsOnImport && AssetType == DazAssetType::SkeletalMesh && RootBone)
		//{
		//	FDazToUnrealFbx::RemoveBindPoses(Scene);
		//	FDazToUnrealFbx::FixClusterTranformLinks(Scene, RootBone);
		//}		
		if (RootBone)
		{

			if (m_sExportRigMode == "unreal" || m_sExportRigMode == "metahuman") {
				FbxTools::RemoveBindPoses(pScene);
				FbxTools::FixClusterTranformLinks(pScene, RootBone);

				FbxTools::AddIkNodes(pScene, RootBone, "foot_l", "foot_r", "hand_l", "hand_r");

				FbxPose* pNewBindPose = FbxTools::SaveBindMatrixToPose(pScene, "NewBindPose", nullptr, true);
				FbxTools::ApplyBindPose(pScene, pNewBindPose);
//				FbxTools::DetachGeometry(pScene);

				QList<FbxNode*> nodeList;
				FbxTools::GetAllMeshes(RootNode, nodeList);
				foreach(FbxNode * pNode, nodeList) {
					QString debugName(pNode->GetName());
					FbxMesh* pMesh = pNode->GetMesh();
					FbxAMatrix matrix = pNode->EvaluateGlobalTransform();
					FbxVector4* pVertexBuffer = pMesh->GetControlPoints();
					if (pVertexBuffer == NULL) continue;
					FbxTools::BakePoseToVertexBuffer(pVertexBuffer, &matrix, pNewBindPose, pMesh);

					pNode->SetPreRotation(FbxNode::eSourcePivot, FbxVector4(0, 0, 0));
					pNode->SetPostRotation(FbxNode::eSourcePivot, FbxVector4(0, 0, 0));
					pNode->LclScaling.Set(FbxDouble3(1.0, 1.0, 1.0));
					pNode->LclRotation.Set(FbxDouble3(0, 0, 0));
					pNode->LclTranslation.Set(FbxDouble3(0, 0, 0));
				}

			}


		}

	}

	if (openFBX->SaveScene(pScene, fbxFilePath.toLocal8Bit().data()) == false)
	{
		if (m_nNonInteractiveMode == 0) QMessageBox::warning(0, "Error",
			"An error occurred while processing the Fbx file...", QMessageBox::Ok);

		printf("\n\nAn error occurred while processing the Fbx file...");
		return false;
	}

	return true;
}


#include "moc_DzBlenderAction.cpp"
