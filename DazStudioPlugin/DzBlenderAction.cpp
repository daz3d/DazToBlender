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

#include "ImageTools.h"

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
					int snoozeTime = fTimeoutInSeconds * 1000 / fMilliSecondsPerTick;
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
		batchFileOut.write(sBatchString.toUtf8().constData());
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


#define LOAD_BOOL_FROM_OPTION(var,str,opt) if (opt.contains(str)) { if (opt[str].toInt() > 0) { var = true; } else { var = false; } }
#define LOAD_INT_FROM_OPTION(var,str,opt) if (opt.contains(str)) { var = opt[str].toInt(); }
#define LOAD_STRING_FROM_OPTION(var,str,opt) if (opt.contains(str)) { var = opt[str]; }

DzError	DzBlenderExporter::write(const QString& filename, const DzFileIOSettings* options)
{
	bool bDefaultToEnvironment = false;
	auto eAssetType = DZ_BRIDGE_NAMESPACE::DzBridgeAction::SelectBestRootNodeForTransfer(false);
	if (eAssetType == DZ_BRIDGE_NAMESPACE::EAssetType::Other || eAssetType == DZ_BRIDGE_NAMESPACE::EAssetType::Scene) {
		bDefaultToEnvironment = true;
	}

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

	// Blender specific options
	bool bRunSilent = false;
	QString sAssetType = "";
	QString sRigConversion = "";
	bool bGenerateGlb = false;
	bool bGenerateUsd = false;
	bool bGenerateFbx = false;
	bool bEmbedTextures = false;
	LOAD_BOOL_FROM_OPTION(bRunSilent, "RunSilent", optionsMap);
	LOAD_BOOL_FROM_OPTION(bGenerateGlb, "GenerateGlb", optionsMap);
	LOAD_BOOL_FROM_OPTION(bGenerateUsd, "GenerateUsd", optionsMap);
	LOAD_BOOL_FROM_OPTION(bGenerateFbx, "GenerateFbx", optionsMap);
	LOAD_BOOL_FROM_OPTION(bEmbedTextures, "EmbedTextures", optionsMap);
	LOAD_STRING_FROM_OPTION(sAssetType, "AssetType", optionsMap);
	LOAD_STRING_FROM_OPTION(sRigConversion, "RigConversion", optionsMap);
	// General Bridge options
	bool bConvertToPng = false;
	bool bConvertToJpg = false;
	bool bExportAllTextures = false;
	bool bCombineDiffuseAndAlphaMaps = false;
	bool bResizeTextures = false;
	QSize qTargetTextureSize = QSize(4096, 4096);
	bool bMultiplyTextureValues = false;
	bool bRecompressIfFileSizeTooBig = false;
	int nFileSizeThresholdToInitiateRecompression = 1024 * 1024 * 10; // size in bytes
	bool bForceReEncoding = false;
	bool bBakeMakeupOverlay = false;
	bool bBakeTranslucency = false;
	bool bBakeSpecularToMetallic = false;
	bool bBakeRefractionWeight = false;
	LOAD_BOOL_FROM_OPTION(bConvertToPng, "ConverToPng", optionsMap);
	LOAD_BOOL_FROM_OPTION(bConvertToJpg, "ConvertToJpg", optionsMap);
	LOAD_BOOL_FROM_OPTION(bExportAllTextures, "ExportAllTextures", optionsMap);
	LOAD_BOOL_FROM_OPTION(bCombineDiffuseAndAlphaMaps, "CombineDiffuseAndAlphaMaps", optionsMap);
	LOAD_BOOL_FROM_OPTION(bResizeTextures, "ResizeTextures", optionsMap);
	// qTargetTextureSize
	if (optionsMap.contains("TargetTextureSize")) {
		QString sTargetTextureSize = optionsMap["TargetTextureSize"];
		if (sTargetTextureSize.contains(",")) {
			auto values = sTargetTextureSize.split(",");
			QString sWidth = values[0];
			QString sHeight = values[1];
			qTargetTextureSize.setWidth(sWidth.toInt());
			qTargetTextureSize.setHeight(sHeight.toInt());
		}
	}
	LOAD_BOOL_FROM_OPTION(bMultiplyTextureValues, "MultiplyTextureValues", optionsMap);
	LOAD_BOOL_FROM_OPTION(bRecompressIfFileSizeTooBig, "RecompressIfFileSizeTooBig", optionsMap);
	LOAD_INT_FROM_OPTION(nFileSizeThresholdToInitiateRecompression, "FileSizeThresholdToInitiateRecompression", optionsMap);
	LOAD_BOOL_FROM_OPTION(bForceReEncoding, "ForceReEncoding", optionsMap);
	LOAD_BOOL_FROM_OPTION(bBakeMakeupOverlay, "BakeMakeupOverlay", optionsMap);
	LOAD_BOOL_FROM_OPTION(bBakeTranslucency, "BakeTranslucency", optionsMap);
	LOAD_BOOL_FROM_OPTION(bBakeSpecularToMetallic, "BakeSpecularToMetallic", optionsMap);
	LOAD_BOOL_FROM_OPTION(bBakeRefractionWeight, "BakeRefractionWeight", optionsMap);

	if (dzScene->getPrimarySelection() == NULL)
	{
		if (!bRunSilent) QMessageBox::critical(0, tr("No asset to export"), tr("There is no asset to export."), QMessageBox::Abort);
		return DZ_OPERATION_FAILED_ERROR;
	}

	DzProgress exportProgress(tr("Blender Exporter starting..."), 100, false, true );
	exportProgress.setInfo(QString("Exporting to:\n    \"%1\"\n").arg(filename));

	exportProgress.setInfo("Generating intermediate file");
	exportProgress.step(25);

	DzBlenderAction* pBlenderAction = new DzBlenderAction();
	pBlenderAction->m_pSelectedNode = dzScene->getPrimarySelection();
	pBlenderAction->m_sOutputBlendFilepath = QString(filename).replace("\\", "/");
	if (bRunSilent) {
		pBlenderAction->setNonInteractiveMode(DZ_BRIDGE_NAMESPACE::eNonInteractiveMode::DzExporterModeRunSilent);
		if (sAssetType != "") {
			pBlenderAction->setAssetType(sAssetType);
		}
		else {
			pBlenderAction->setAssetType(eAssetType);
		}
		if (sRigConversion != "") {
			pBlenderAction->m_sExportRigMode = sRigConversion;
		}
		//// BlenderExporter specific options which are blocked from regular bridge object scripting
		pBlenderAction->m_bGenerateFinalGlb = bGenerateGlb;
		pBlenderAction->m_bGenerateFinalFbx = bGenerateFbx;
		pBlenderAction->m_bGenerateFinalUsd = bGenerateUsd;
		pBlenderAction->m_bEmbedTexturesInOutputFile = bEmbedTextures;
		//// General Bridge Options
		pBlenderAction->setConvertToPng(bConvertToPng);
		pBlenderAction->setConvertToJpg(bConvertToJpg);
		pBlenderAction->setExportAllTextures(bExportAllTextures);
		pBlenderAction->setExportAllTextures(bExportAllTextures);
		pBlenderAction->setCombineDiffuseAndAlphaMaps(bCombineDiffuseAndAlphaMaps);
		pBlenderAction->setResizeTextures(bResizeTextures);
		// qTargetTextureSize
		pBlenderAction->setTargetTexturesSize(qTargetTextureSize);
		pBlenderAction->setMultiplyTextureValues(bMultiplyTextureValues);
		pBlenderAction->setRecompressIfFileSizeTooBig(bRecompressIfFileSizeTooBig);
		pBlenderAction->setFileSizeThresholdToInitiateRecompression(nFileSizeThresholdToInitiateRecompression);
		pBlenderAction->setForceReEncoding(bForceReEncoding);
		pBlenderAction->setBakeMakeupOverlay(bBakeMakeupOverlay);
		pBlenderAction->setBakeTranslucency(bBakeTranslucency);
		pBlenderAction->setBakeSpecularToMetallic(bBakeSpecularToMetallic);
		pBlenderAction->setBakeRefractionWeight(bBakeRefractionWeight);
	}
	else {
		pBlenderAction->setNonInteractiveMode(DZ_BRIDGE_NAMESPACE::eNonInteractiveMode::DzExporterMode);
	}
	pBlenderAction->createUI();
	DzBlenderDialog* pDialog = qobject_cast<DzBlenderDialog*>(pBlenderAction->getBridgeDialog());

	// Move Blender Executable Widgets to Top of Dialog
	pDialog->requireBlenderExecutableWidget(true);
	pDialog->showBlenderToolsOptions(true);
	pDialog->setOutputBlendFilepath(filename);
	if (bDefaultToEnvironment) {
		int nEnvIndex = pDialog->getAssetTypeCombo()->findText("Environment");
		pDialog->getAssetTypeCombo()->setCurrentIndex(nEnvIndex);
	}
	pBlenderAction->executeAction();
	DzError nExecuteActionResult = pBlenderAction->getExecutActionResult();

//	bool bUseBlenderTools = pDialog->getUseLegacyAddonCheckbox();
	pDialog->showBlenderToolsOptions(false);
	pDialog->requireBlenderExecutableWidget(false);

	if (
		(!bRunSilent && pDialog->result() == QDialog::Rejected)
		|| (nExecuteActionResult != DZ_NO_ERROR)
		) {
		exportProgress.cancel();
		return DZ_USER_CANCELLED_OPERATION;
	}

	// if Blender Executable is not set, fail gracefully
	if (pBlenderAction->m_sBlenderExecutablePath == "") {
		if (!bRunSilent) QMessageBox::critical(0, tr("No Blender Executable Found"), tr("You must set the path to your Blender Executable. Aborting."), QMessageBox::Abort );
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
    QProcess *thisProcess = new QProcess(this);
	pBlenderAction->m_nBlenderExitCode = DzBlenderUtils::ExecuteBlenderScripts(pBlenderAction->m_sBlenderExecutablePath, sCommandArgs, sIntermediatePath, thisProcess, 240);
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
    thisProcess->deleteLater();

	exportProgress.step(25);

	if (result)
	{
		exportProgress.update(100);
		if (!bRunSilent) QMessageBox::information(0, "Blender Exporter",
			tr("Export from Daz Studio complete."), QMessageBox::Ok);

#ifdef WIN32
//		ShellExecuteA(NULL, "open", sBlenderOutputPath.toUtf8().data(), NULL, NULL, SW_SHOWDEFAULT);
		std::wstring wcsBlenderOutputPath(reinterpret_cast<const wchar_t*>(sBlenderOutputPath.utf16()));
		ShellExecuteW(NULL, L"open", wcsBlenderOutputPath.c_str(), NULL, NULL, SW_SHOWDEFAULT);
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
			if (!bRunSilent) QMessageBox::critical(0, "Blender Exporter", tr(sErrorString.toUtf8()), QMessageBox::Ok);
		}
		else {
			QString sErrorString;
			sErrorString += QString("An error occured during the export process (ExitCode=%1).\n").arg(pBlenderAction->m_nBlenderExitCode);
			sErrorString += QString("Please check log files at : %1\n").arg(pBlenderAction->m_sDestinationPath);
			if (!bRunSilent) QMessageBox::critical(0, "Blender Exporter", tr(sErrorString.toUtf8()), QMessageBox::Ok);
		}
#ifdef WIN32
//		ShellExecuteA(NULL, "open", pBlenderAction->m_sDestinationPath.toUtf8().data(), NULL, NULL, SW_SHOWDEFAULT);
		std::wstring wcsDestinationPath(reinterpret_cast<const wchar_t*>(pBlenderAction->m_sDestinationPath.utf16()));
		ShellExecuteW(NULL, L"open", wcsDestinationPath.c_str(), NULL, NULL, SW_SHOWDEFAULT);
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

		exportProgress.cancel();
		return DZ_OPERATION_FAILED_ERROR;
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
	DzProgress* blenderProgress = new DzProgress(tr("PreProcessing Scene"), 100, false, true);

	if (parentNode && m_sExportRigMode != "" && m_sExportRigMode != "--")
	{
		QString sGeneration = parentNode->getName();
		bool bIsG9 = (sGeneration == "Genesis9");

		QString sBoneConverter = "bone_converter_aArgs.dsa";
		QString sUnrealMannyRigFile = "g9_to_unreal_manny.json";
		QString sG8UnrealRigFile = "g8_to_unreal.json";
		QString sMetahumanRigFile = "g9_to_metahuman.json";
		QString sG8MetahumanRigFile = "g8_to_metahuman.json";
		QString sUnityRigFile = "g9_to_unity.json";
		QString sG8UnityRigFile = "g8_to_unity.json";
		QString sMixamoRigFile = "g9_to_mixamo.json";
		QString sG8MixamoRigFile = "g8_to_mixamo.json";

		blenderProgress->setInfo(tr("Preparing Rig Converter files..."));
		QStringList aScriptFilelist = (QStringList() <<
			sBoneConverter <<
			sUnrealMannyRigFile << sG8UnrealRigFile <<
			sMetahumanRigFile << sG8MetahumanRigFile <<
			sUnityRigFile <<
			sMixamoRigFile << sG8MixamoRigFile
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
			if (bIsG9) {
				aArgs.append(QVariant(dzApp->getTempPath() + "/" + sMetahumanRigFile));
			} else {
				aArgs.append(QVariant(dzApp->getTempPath() + "/" + sG8MetahumanRigFile));
			}
		}
		else if (m_sExportRigMode == "unreal") {
			if (bIsG9) {
				aArgs.append(QVariant(dzApp->getTempPath() + "/" + sUnrealMannyRigFile));
			}
			else {
				aArgs.append(QVariant(dzApp->getTempPath() + "/" + sG8UnrealRigFile));
			}
		}
		else if (m_sExportRigMode == "unity") {
			if (bIsG9) {
				aArgs.append(QVariant(dzApp->getTempPath() + "/" + sUnityRigFile));
			}
			else {
				aArgs.append(QVariant(dzApp->getTempPath() + "/" + sG8UnityRigFile));
			}
		}
		else if (m_sExportRigMode == "mixamo") {
			if (bIsG9) {
				aArgs.append(QVariant(dzApp->getTempPath() + "/" + sMixamoRigFile));
			}
			else {
				aArgs.append(QVariant(dzApp->getTempPath() + "/" + sG8MixamoRigFile));
			}
		}
		else {
			// UNHANDLED ABORT
			aArgs.clear();
		}

		if (aArgs.length() > 0) {
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
			dzScene->selectAllNodes(false);
			//	dzScene->setPrimarySelection(parentNode);

		}
	}

	DzBridgeAction::preProcessScene(parentNode);

	blenderProgress->finish();

	return true;
}

DzBlenderAction::DzBlenderAction() :
	DzBridgeAction(tr("Send to &Blender..."), tr("Send the selected node to Blender."))
{
	this->setObjectName("DzBridge_DazToBlender_Action");

	m_nNonInteractiveMode = 0;
	m_sAssetType = QString("SkeletalMesh");
	//Setup Icon
	QString iconName = "Daz to Blender";
	QPixmap basePixmap = QPixmap::fromImage(getEmbeddedImage(iconName.toLatin1()));
	QIcon icon;
	icon.addPixmap(basePixmap, QIcon::Normal, QIcon::Off);
	QAction::setIcon(icon);

	m_sEmbeddedFolderPath = ":/DazBridgeBlender";

	// Enable Optional Daz Bridge Behaviors
	m_bDeferProcessingImageToolsJobs = true;
	m_aKnownIntermediateFileExtensionsList += "blend";
	m_aKnownIntermediateFileExtensionsList += "blend1";

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
	m_nExecuteActionResult = DZ_OPERATION_FAILED_ERROR;

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
	bool bDefaultToEnvironment = false;
	if (m_nNonInteractiveMode != DZ_BRIDGE_NAMESPACE::eNonInteractiveMode::DzExporterMode &&
		m_nNonInteractiveMode != DZ_BRIDGE_NAMESPACE::eNonInteractiveMode::DzExporterModeRunSilent)
	{
		auto result = SelectBestRootNodeForTransfer(true);
		if (result == DZ_BRIDGE_NAMESPACE::EAssetType::Other || result == DZ_BRIDGE_NAMESPACE::EAssetType::Scene) {
			bDefaultToEnvironment = true;
		}
		m_pSelectedNode = dzScene->getPrimarySelection();
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

	if (bDefaultToEnvironment) {
		int nEnvIndex = m_bridgeDialog->getAssetTypeCombo()->findText("Environment");
		m_bridgeDialog->getAssetTypeCombo()->setCurrentIndex(nEnvIndex);
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
			m_nExecuteActionResult = DZ_OPERATION_FAILED_ERROR;
			return;
		}

		// DB 2021-10-11: Progress Bar
		DzProgress* exportProgress = new DzProgress("Sending to Blender...", 10, false, true);

		DzError result = doPromptableObjectBaking();
		if (result != DZ_NO_ERROR) {
			exportProgress->finish();
			exportProgress->cancel();
			m_nExecuteActionResult = result;
			return;
		}
		exportProgress->step();

		//Create Daz3D folder if it doesn't exist
		QDir dir;
		dir.mkpath(m_sRootFolder);
		exportProgress->step();

		// if InteractiveMode, clean intermediate folder
		if (m_nNonInteractiveMode != DZ_BRIDGE_NAMESPACE::eNonInteractiveMode::ScriptMode) {
			cleanIntermediateSubFolder(m_sExportSubfolder);
		}

		if (m_sAssetType == "Environment") {
			// Sanity Check if zero nodes
			if (dzScene->getNumNodes() == 0) {
				dzApp->log("DazToBlender: CRITICAL ERROR: executeAction() Environment Export with zero nodes. Aborting.");
				exportProgress->finish();
				exportProgress->cancel();
				m_nExecuteActionResult = DZ_OPERATION_FAILED_ERROR;
				return;
			}

			QDir().mkdir(m_sDestinationPath);
			m_bUseLegacyAddon = false;

			exportProgress->step();
			DzNodeList rootNodeList = BuildRootNodeList();
			m_pSelectedNode = rootNodeList[0];
			preProcessScene(NULL);

			DzExportMgr* ExportManager = dzApp->getExportMgr();
			DzExporter* Exporter = ExportManager->findExporterByClassName("DzFbxExporter");
			DzFileIOSettings ExportOptions;
			ExportOptions.setBoolValue("IncludeSelectedOnly", false);
			ExportOptions.setBoolValue("IncludeVisibleOnly", true);
			ExportOptions.setBoolValue("IncludeFigures", true);
			ExportOptions.setBoolValue("IncludeProps", true);
			ExportOptions.setBoolValue("IncludeLights", false);
			ExportOptions.setBoolValue("IncludeCameras", false);
			ExportOptions.setBoolValue("IncludeAnimations", true);
			ExportOptions.setIntValue("RunSilent", !m_bShowFbxOptions);
			setExportOptions(ExportOptions);
			// NOTE: be careful to use m_sExportFbx and NOT m_sExportFilename since FBX and DTU base name may differ
			QString sEnvironmentFbx = m_sDestinationPath + m_sExportFbx + ".fbx";
			DzError result = Exporter->writeFile(sEnvironmentFbx, &ExportOptions);
			if (result != DZ_NO_ERROR) {
				undoPreProcessScene();
				m_nExecuteActionResult = result;
				exportProgress->finish();
				exportProgress->cancel();
				return;
			}
			exportProgress->step();

			writeConfiguration();
			exportProgress->step();

			undoPreProcessScene();
			exportProgress->step();
		}
		else {
			DzNode* pParentNode = NULL;
			if (m_pSelectedNode->isRootNode() == false) {
				dzApp->log("INFO: Selected Node for Export is not a Root Node, unparenting now....");
				pParentNode = m_pSelectedNode->getNodeParent();
				pParentNode->removeNodeChild(m_pSelectedNode, true);
				dzApp->log("INFO: Parent stored: " + pParentNode->getLabel() + ", New Root Node: " + m_pSelectedNode->getLabel());
			}
			exportProgress->step();
			exportHD(exportProgress);
			exportProgress->step();
			if (pParentNode) {
				dzApp->log("INFO: Restoring Parent relationship: " + pParentNode->getLabel() + ", child node: " + m_pSelectedNode->getLabel());
				pParentNode->addNodeChild(m_pSelectedNode, true);
			}
		}

		exportProgress->update(10);
		// DB 2021-09-02: messagebox "Export Complete"
		if (m_nNonInteractiveMode == 0)
		{
			QMessageBox::information(0, "Daz To Blender Bridge",
				tr("Export phase from Daz Studio complete. Please switch to Blender to begin Import phase."), QMessageBox::Ok);
		}

		// DB 2021-10-11: Progress Bar
		exportProgress->finish();

	}

	m_nExecuteActionResult = DZ_NO_ERROR;
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
	DzProgress* pDtuProgress = new DzProgress("Writing DTU file", 10, false, true);

	QString DTUfilename = m_sDestinationPath + m_sExportFilename + ".dtu";
	QFile DTUfile(DTUfilename);
	if (!DTUfile.open(QIODevice::WriteOnly)) {
		QString sErrorMessage = tr("ERROR: DzBridge: writeConfigureation(): unable to open file for writing: ") + DTUfilename;
		dzApp->log(sErrorMessage);
		return;
	}
	DzJsonWriter writer(&DTUfile);
	writer.startObject(true);

	writeDTUHeader(writer);
	pDtuProgress->step();

	// Plugin-specific items
	writer.addMember("Use Legacy Addon", m_bUseLegacyAddon);
	writer.addMember("Output Blend Filepath", m_sOutputBlendFilepath);
	writer.addMember("Texture Atlas Mode", m_sTextureAtlasMode);
	writer.addMember("Texture Atlas Size", m_nTextureAtlasSize);
	writer.addMember("Export Rig Mode", m_sExportRigMode);
	writer.addMember("Enable Gpu Baking", m_bEnableGpuBaking);
	writer.addMember("Embed Textures", m_bEmbedTexturesInOutputFile);
	writer.addMember("Generate Final Fbx", m_bGenerateFinalFbx);
	writer.addMember("Generate Final Glb", m_bGenerateFinalGlb);
	writer.addMember("Generate Final Usd", m_bGenerateFinalUsd);
	writer.addMember("Use MaterialX", m_bUseMaterialX);
	pDtuProgress->step();

	if (m_pSelectedNode->inherits("DzFigure")) {
		DzVec3 vObjectOffset(0, 0, 0);
		bool result = DZ_BRIDGE_NAMESPACE::DzBridgeTools::CalculateRawOffset(m_pSelectedNode, vObjectOffset);
		writer.startMemberArray("Object Correction Offset", true);
		writer.addItem(-vObjectOffset.m_x);
		writer.addItem(-vObjectOffset.m_y);
		writer.addItem(-vObjectOffset.m_z);
		writer.finishArray();
	}

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
		pDtuProgress->update(6);
		if (m_sAssetType == "Environment") {
			writeSceneMaterials(writer, pCVSStream);
			pDtuProgress->step();
			writeSceneDefinition(writer);
		}
		else {
			writeAllMaterials(m_pSelectedNode, writer, pCVSStream);
			pDtuProgress->step();
		}

		writeAllMorphs(writer);
		writeMorphLinks(writer);
		writeMorphNames(writer);
		pDtuProgress->step();

		DzBoneList aBoneList = getAllBones(m_pSelectedNode);

		writeSkeletonData(m_pSelectedNode, writer);
		writeHeadTailData(m_pSelectedNode, writer);
		writeJointOrientation(aBoneList, writer);
		writeLimitData(aBoneList, writer);
		writePoseData(m_pSelectedNode, writer, true);
		pDtuProgress->step();

		writeAllSubdivisions(writer);
		pDtuProgress->step();
		writeAllDforceInfo(m_pSelectedNode, writer);
		pDtuProgress->step();
	}

	m_ImageToolsJobsManager->processJobs();
	m_ImageToolsJobsManager->clearJobs();

	writer.finishObject();
	DTUfile.close();

	pDtuProgress->finish();
}

// Setup custom FBX export options
void DzBlenderAction::setExportOptions(DzFileIOSettings& ExportOptions)
{
//	ExportOptions.setBoolValue("IncludeFaceGroupsAsPolygonSets", false);
//	ExportOptions.setBoolValue("IncludeFaceGroupsAsPolygonGroups", false);

	ExportOptions.setBoolValue("IncludeFPS", true);
	ExportOptions.setBoolValue("IncludeRotationLocks", false);
	ExportOptions.setBoolValue("IncludeRotationLimits", false);

	ExportOptions.setBoolValue("BasePoseOnly", false);
	ExportOptions.setBoolValue("GenerateMayaHelperScript", false);
	ExportOptions.setBoolValue("MentalRayMaterials", false);

	// Unable to use this option, since generated files are referenced only in FBX and unknown to DTU
	ExportOptions.setBoolValue("MergeDiffuseOpacity", false);
	// disable these options since we use Blender to generate a new FBX with embedded files
	ExportOptions.setBoolValue("EmbedTextures", false);
	ExportOptions.setBoolValue("CollectTextures", false);

	// Custom Properties
	ExportOptions.setBoolValue("IncludeNodeNamesLabels", true);
	ExportOptions.setBoolValue("IncludeNodePresentation", true);
	ExportOptions.setBoolValue("IncludeNodeSelectionMap", true);
	ExportOptions.setBoolValue("IncludeSceneIDs", true);
	ExportOptions.setBoolValue("IncludeFollowTargets", true);

}

QString DzBlenderAction::readGuiRootFolder()
{
	QString rootFolder = QDesktopServices::storageLocation(QDesktopServices::DocumentsLocation) + QDir::separator() + "DazToBlender";
#if __LEGACY_PATHS__
	if (m_bUseLegacyPaths) 
	{
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
	}
	else
	{
		if (m_bridgeDialog)
		{
			QLineEdit* intermediateFolderEdit = nullptr;
			DzBlenderDialog* blenderDialog = qobject_cast<DzBlenderDialog*>(m_bridgeDialog);

			if (blenderDialog)
				intermediateFolderEdit = blenderDialog->getIntermediateFolderEdit();

			if (intermediateFolderEdit)
				rootFolder = intermediateFolderEdit->text().replace("\\", "/") + "/Daz3D";
		}
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
	if (m_bUseLegacyPaths) 
	{
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
	}
#endif

	// Read Custom GUI values
	DzBlenderDialog* pBlenderDialog = qobject_cast<DzBlenderDialog*>(m_bridgeDialog);

	if (pBlenderDialog)
	{
		if (m_sBlenderExecutablePath == "" || isInteractiveMode() ) m_sBlenderExecutablePath = pBlenderDialog->m_wBlenderExecutablePathEdit->text().replace("\\", "/");
		
		// if dzexporter mode, then read blender tools options
		if (m_nNonInteractiveMode == DZ_BRIDGE_NAMESPACE::eNonInteractiveMode::DzExporterMode)
		{
			m_bUseLegacyAddon = pBlenderDialog->getUseLegacyAddonCheckbox();
			m_sTextureAtlasMode = pBlenderDialog->getTextureAtlasMode();
			m_sExportRigMode = pBlenderDialog->getExportRigMode();
			m_nTextureAtlasSize = pBlenderDialog->getTextureAtlasSize();
			m_bEnableGpuBaking = pBlenderDialog->getUseGpuBaking();
			m_bEmbedTexturesInOutputFile = pBlenderDialog->getEnableEmbedTexturesInOutputFile();
			m_bGenerateFinalFbx = pBlenderDialog->getGenerateFbx();
			m_bGenerateFinalGlb = pBlenderDialog->getGenerateGlb();
			m_bGenerateFinalUsd = pBlenderDialog->getGenerateUsd();
			m_bUseMaterialX = pBlenderDialog->getUseMaterialX();
		}
		else if (m_nNonInteractiveMode != DZ_BRIDGE_NAMESPACE::eNonInteractiveMode::DzExporterModeRunSilent)
		{
			m_bUseLegacyAddon = false;
			m_sOutputBlendFilepath = "";
			m_sTextureAtlasMode = "";
			m_sExportRigMode = "";
			m_nTextureAtlasSize = 0;
			m_bEnableGpuBaking = false;
			m_bEmbedTexturesInOutputFile = false;
			m_bGenerateFinalFbx = false;
			m_bGenerateFinalGlb = false;
			m_bGenerateFinalUsd = false;
			m_bUseMaterialX = false;
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
	if (!result) return false;

	if (m_bPostProcessFbx == false)
		return false;

	OpenFBXInterface* openFBX = OpenFBXInterface::GetInterface();
	FbxScene* pScene = openFBX->CreateScene("Base Mesh Scene");
	if (openFBX->LoadScene(pScene, fbxFilePath) == false)
	{
		QString sFbxErrorMessage = tr("ERROR: DzBlenderBridge: openFBX->LoadScene():\n\n")
			+ QString("File: \"%1\"\n\n").arg(fbxFilePath)
			+ QString("FbxStatusCode: %1\n").arg(openFBX->GetErrorCode())
			+ QString("Error Message: %1\n\n").arg(openFBX->GetErrorString());
		dzApp->log(sFbxErrorMessage);
		if (m_nNonInteractiveMode == 0) QMessageBox::warning(0, tr("Error"),
			tr("An error occurred while processing the Fbx file:\n\n") + sFbxErrorMessage, QMessageBox::Ok);
		return false;
	}

	m_bExperimental_FbxPostProcessing = false;
	if (m_nNonInteractiveMode == DZ_BRIDGE_NAMESPACE::eNonInteractiveMode::DzExporterMode ||
		m_nNonInteractiveMode == DZ_BRIDGE_NAMESPACE::eNonInteractiveMode::DzExporterModeRunSilent)
	{
		m_bExperimental_FbxPostProcessing = true;
	}
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
				//else if (m_sExportRigMode == "mixamo") {
				//	RootBone->SetName("Armature");
				//	Attr->SetName("Armature");
				//}
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

				FbxTools::DetachGeometry(pScene);
			}
		}
	}

	if (openFBX->SaveScene(pScene, fbxFilePath) == false)
	{
		QString sFbxErrorMessage = tr("ERROR: DzBlenderBridge: openFBX->SaveScene():\n\n")
			+ QString("File: \"%1\"\n\n").arg(fbxFilePath)
			+ QString("FbxStatusCode: %1\n").arg(openFBX->GetErrorCode())
			+ QString("Error Message: %1\n\n").arg(openFBX->GetErrorString());
		dzApp->log(sFbxErrorMessage);
		if (m_nNonInteractiveMode == 0) QMessageBox::warning(0, tr("Error"),
			tr("An error occurred while processing the Fbx file:\n\n") + sFbxErrorMessage, QMessageBox::Ok);
		return false;
	}

	return true;
}


#include "moc_DzBlenderAction.cpp"
