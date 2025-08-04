#define PYTHON_EXCEPTION_CODE 11

#include "DzBlenderUtils.h"

#include <qmessagebox.h>
#include <QProcess>
#include <qfileinfo.h>
#include <qdir.h>

#include <dzscene.h>
#include <dzprogress.h>

#include "DzBlenderAction.h"

#ifdef WIN32
#include <Windows.h>
#include <shellapi.h>
#endif

int DzBlenderUtils::ExecuteBlenderScripts(QString sBlenderExecutablePath, QString sCommandlineArguments, QString sWorkingPath, QProcess* thisProcess, DzApp* dzApp, float fTimeoutInSeconds)
{
	// fork or spawn child process
	QStringList args = sCommandlineArguments.split(";");
	
	float fMilliSecondsPerTick = 200;
	int numTotalTicks = fTimeoutInSeconds * 1000 / fMilliSecondsPerTick;
	DzProgress* progress = new DzProgress("Running Blender Script", numTotalTicks, false, true);
	progress->enable(true);
	QProcess* pToolProcess = thisProcess;
	dzApp->log("DEBUG: Blender Exporter: setting working dir for blender script: " + sWorkingPath);
	pToolProcess->setWorkingDirectory(sWorkingPath);
	pToolProcess->setProcessChannelMode(QProcess::MergedChannels);
	pToolProcess->setReadChannel(QProcess::StandardOutput);
	dzApp->log("DEBUG: Blender Exporter: starting blender script: [" + sBlenderExecutablePath + "] with args: " + args.join(";"));
	pToolProcess->start(sBlenderExecutablePath, args);
	int currentTick = 0;
	int timeoutTicks = numTotalTicks;
	bool bUserInitiatedTermination = false;
#ifdef __APPLE__
	while (pToolProcess->state() != QProcess::NotRunning)
#else
	while (pToolProcess->waitForFinished(fMilliSecondsPerTick) == false)
#endif
	{
#ifdef __APPLE__
		int iMilliSecondsPerTick = (int) fMilliSecondsPerTick;
		if (iMilliSecondsPerTick < 0) iMilliSecondsPerTick = 200;
		struct timespec ts = { iMilliSecondsPerTick / 1000, (iMilliSecondsPerTick % 1000) * 1000 * 1000 };
		nanosleep(&ts, NULL);
#endif
		QApplication::processEvents();
		while (pToolProcess->canReadLine()) {
			QByteArray qa = pToolProcess->readLine();
			QString sProcessOutput = qa.data();
			sProcessOutput = sProcessOutput.replace("\n","").replace("\r","");
			//dzApp->log("BLENDER: " + sProcessOutput);
			progress->setCurrentInfo("BLENDER: " + sProcessOutput);
		}
		// if timeout reached, then terminate process
		if (currentTick++ > timeoutTicks) {
			if (!bUserInitiatedTermination)
			{
				QString sTimeoutText = QObject::tr("The current Blender operation is taking a long time.\nDo you want to Ignore this time-out and wait a little longer, or \nDo you want to Abort the operation now?");
				int result = QMessageBox::critical(0, QObject::tr("Blender Exporter: Blender Process Timout Error"), sTimeoutText, QMessageBox::Ignore, QMessageBox::Abort);
				if (result == QMessageBox::Ignore) {
					int snoozeTime = 60 * 1000 / fMilliSecondsPerTick;
					timeoutTicks += snoozeTime;
				}
				else {
					dzApp->log("DEBUG: executeBlenderScripts(): User initiated termination...");
					bUserInitiatedTermination = true;
				}
			}
			else
			{
				if (currentTick - timeoutTicks < 5) {
					QString mesg = QString("DEBUG: currentTick = %1, timeoutTicks = %2, terminating...").arg(currentTick).arg(timeoutTicks);
					dzApp->log( mesg );
					pToolProcess->terminate();
				}
				else {
					dzApp->log("DEBUG: Sending Kill Signal to Blender Process...");
					pToolProcess->kill();
				}
			}
		}
		if (pToolProcess->state() == QProcess::Running) {
			progress->step();
		}
		else if (pToolProcess->state() == QProcess::NotRunning) {
			dzApp->log("DEBUG: QProcess State is now NotRunning, stopping monitor....");
			break;
		}
		else {
			QString mesg = "DEBUG: QProcess State Changed to: " + QString(pToolProcess->state());
			dzApp->log( mesg );
			progress->setCurrentInfo( mesg );
		}
	}
	// dzApp->log("DEBUG: flushing Blender output buffer...");
	while (pToolProcess->canReadLine()) {
		QByteArray qa = pToolProcess->readLine();
		QString sProcessOutput = qa.data();
		sProcessOutput = sProcessOutput.replace("\n","").replace("\r","");
		// dzApp->log("BLENDER: " + sProcessOutput);
		progress->setCurrentInfo("BLENDER: " + sProcessOutput);
	}
	int nBlenderExitCode = pToolProcess->exitCode();
	QProcess::ExitStatus qExitStatus = pToolProcess->exitStatus();
	if (qExitStatus == QProcess::CrashExit) {
		if (nBlenderExitCode == 0) {
			dzApp->warning("Blender Exporter: ERROR: Blender process Crashed but exit code is 0, manually setting to -1...");
			nBlenderExitCode = -1;
		}
	}
	
	QString mesg;
#ifdef __APPLE__
	if (nBlenderExitCode != 0 && nBlenderExitCode != 120)
#else
	if (nBlenderExitCode != 0)
#endif
	{
		if (nBlenderExitCode == PYTHON_EXCEPTION_CODE) {
			mesg = QString("Blender Exporter: ERROR: Python error:.... %1").arg(nBlenderExitCode);
		} else {
			mesg = QString("Blender Exporter: ERROR: exit code = %1").arg(nBlenderExitCode);
		}
		dzApp->warning(mesg);
		progress->setCloseOnFinish(false);
	} else {
		mesg = QString("Blender Exporter: DEBUG: blender script successful, exit code = %1").arg(nBlenderExitCode);
		dzApp->log(mesg);
	}
	progress->setCurrentInfo(mesg);
	progress->finish();
	//	delete progress;
	
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

	int nBlenderExitCode = DzBlenderUtils::ExecuteBlenderScripts(sBlenderExecutablePath, sCommandArgs, sIntermediatePath, thisProcess, dzApp, 240);
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

	bool result = false;

#if 1
	QProcess *thisProcess = new QProcess(this);
	pBlenderAction->m_nBlenderExitCode = DzBlenderUtils::ExecuteBlenderScripts(pBlenderAction->m_sBlenderExecutablePath, sCommandArgs, sIntermediatePath, thisProcess, dzApp, 240);
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
#else
	result = pBlenderAction->executeBlenderScripts(pBlenderAction->m_sBlenderExecutablePath, sCommandArgs);
#endif

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

#include "moc_DzBlenderUtils.cpp"
