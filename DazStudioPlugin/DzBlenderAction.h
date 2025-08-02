#pragma once
#include <dzaction.h>
#include <dznode.h>
#include <dzjsonwriter.h>
#include <QtCore/qfile.h>
#include <QtCore/qtextstream.h>

#include <DzBridgeAction.h>
#include "DzBlenderDialog.h"

#include <Alembic/Abc/All.h>

class UnitTest_DzBlenderAction;

#include "dzbridge.h"

class DzBlenderAction : public DZ_BRIDGE_NAMESPACE::DzBridgeAction {
	 Q_OBJECT
public:
	DzBlenderAction();
	DzError getExecutActionResult() { return m_nExecuteActionResult; }

	Q_INVOKABLE virtual void setUseLegacyPaths(bool arg) { m_bUseLegacyPaths = arg; }
	Q_INVOKABLE virtual bool getUseLegacyPaths() { return m_bUseLegacyPaths; }

	Q_INVOKABLE void writeConfiguration() override;
	Q_INVOKABLE void setExportOptions(DzFileIOSettings& ExportOptions) override;

	Q_INVOKABLE virtual bool readGui(DZ_BRIDGE_NAMESPACE::DzBridgeDialog*) override;

	Q_INVOKABLE QString createBlenderFiles(bool replace = true);

	Q_INVOKABLE bool createUI();

	// DB 2024-09-01: Refactored convenience function accessible from Daz Script, C++ users should use DzBlenderUtils::ExecuteBlenderScripts() directly
	Q_INVOKABLE bool executeBlenderScripts(QString sFilePath, QString sCommandlineArguments);

	bool writeHair(QString sFilePath, QList<DzNode*> aHairNodesList);
	bool writeAbcMesh(DzNode* pNode, Alembic::Abc::OArchive& AbcArchive, Alembic::Abc::TimeSamplingPtr& TimeSampling);
	bool writeAbcCurve(DzNode* pNode, Alembic::Abc::OArchive& AbcArchive, Alembic::Abc::TimeSamplingPtr& TimeSampling, int groom_id);

	void executeAction() override;

protected:
	bool m_bUseLegacyPaths = true;

	 virtual QString readGuiRootFolder() override;

	 virtual bool preProcessScene(DzNode* parentNode) override;
	 virtual bool postProcessFbx(QString fbxFilePath) override;

	 int m_nPythonExceptionExitCode = 11;  // arbitrary exit code to check for blener python exceptions
	 int m_nBlenderExitCode = 0;
	 QString m_sBlenderExecutablePath = "";

	 bool m_bUseLegacyAddon = false;
	 QString m_sOutputBlendFilepath = "";
	 QString m_sTextureAtlasMode = "";

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
