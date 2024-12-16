#pragma once
#include <dzaction.h>
#include <dznode.h>
#include <dzjsonwriter.h>
#include <QtCore/qfile.h>
#include <QtCore/qtextstream.h>
#include <dzexporter.h>

#include <DzBridgeAction.h>
#include "DzBlenderDialog.h"

class UnitTest_DzBlenderAction;

#include "dzbridge.h"

class QProcess;
class DzBlenderUtils
{
public:
	static int ExecuteBlenderScripts(QString sBlenderExecutablePath, QString sCommandlineArguments, QString sWorkingPath, QProcess* thisProcess, float fTimeoutInSeconds=120);
	static bool GenerateBlenderBatchFile(QString batchFilePath, QString sBlenderExecutablePath, QString sCommandArgs);
	static bool PrepareAndRunBlenderProcessing(QString sDestinationFbx, QString sBlenderExecutablePath, QProcess* thisProcess, int nPythonExceptionExitCode);
};

class DzBlenderExporter : public DzExporter {
	Q_OBJECT
public:
	DzBlenderExporter() : DzExporter(QString("blend")) { this->setObjectName("DzBridge_DazToBlender_Exporter"); };

public slots:
	virtual void getDefaultOptions(DzFileIOSettings* options) const {};
	virtual QString getDescription() const override { return QString("Blender File"); };
	virtual bool isFileExporter() const override { return true; };

protected:
	virtual DzError	write(const QString& filename, const DzFileIOSettings* options) override;
};

class DzBlenderAction : public DZ_BRIDGE_NAMESPACE::DzBridgeAction {
	 Q_OBJECT
public:
	DzBlenderAction();
	DzError getExecutActionResult() { return m_nExecuteActionResult; }

protected:
	Q_INVOKABLE virtual void setUseLegacyPaths(bool arg) { m_bUseLegacyPaths = arg; }
	Q_INVOKABLE virtual bool getUseLegacyPaths() { return m_bUseLegacyPaths; }
	bool m_bUseLegacyPaths = true;

	void executeAction() override;
	 Q_INVOKABLE void writeConfiguration() override;
	 Q_INVOKABLE void setExportOptions(DzFileIOSettings& ExportOptions) override;
	 virtual QString readGuiRootFolder() override;
	 Q_INVOKABLE virtual bool readGui(DZ_BRIDGE_NAMESPACE::DzBridgeDialog*) override;

	 Q_INVOKABLE QString createBlenderFiles(bool replace = true);

	 Q_INVOKABLE bool createUI();

	 // DB 2024-09-01: Refactored convenience function accessible from Daz Script, C++ users should use DzBlenderUtils::ExecuteBlenderScripts() directly
	 Q_INVOKABLE bool executeBlenderScripts(QString sFilePath, QString sCommandlineArguments);

	 virtual bool preProcessScene(DzNode* parentNode) override;
	 virtual bool postProcessFbx(QString fbxFilePath) override;

	 int m_nPythonExceptionExitCode = 11;  // arbitrary exit code to check for blener python exceptions
	 int m_nBlenderExitCode = 0;
	 QString m_sBlenderExecutablePath = "";

	 bool m_bUseLegacyAddon = false;
	 QString m_sOutputBlendFilepath = "";
	 QString m_sTextureAtlasMode = "";
	 QString m_sExportRigMode = "";

	 int m_nTextureAtlasSize = 0;
	 bool m_bEnableGpuBaking = false;
	 bool m_bEmbedTexturesInOutputFile = false;

	 bool m_bGenerateFinalFbx = false;
	 bool m_bGenerateFinalGlb = false;
	 bool m_bGenerateFinalUsd = false;
	 bool m_bUseMaterialX = false;


	 friend class DzBlenderExporter;
#ifdef UNITTEST_DZBRIDGE
	friend class UnitTest_DzBlenderAction;
#endif

};
