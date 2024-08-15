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


class DzBlenderUtils
{
public:
	static bool generateBlenderBatchFile(QString batchFilePath, QString sBlenderExecutablePath, QString sCommandArgs);
};

class DzBlenderExporter : public DzExporter {
	Q_OBJECT
public:
	DzBlenderExporter() : DzExporter(QString("blend")) {};

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

protected:

	 void executeAction();
	 Q_INVOKABLE bool createUI();
	 Q_INVOKABLE void writeConfiguration();
	 Q_INVOKABLE void setExportOptions(DzFileIOSettings& ExportOptions);
	 Q_INVOKABLE QString createBlenderFiles(bool replace = true);
	 virtual QString readGuiRootFolder() override;
	 Q_INVOKABLE virtual bool readGui(DZ_BRIDGE_NAMESPACE::DzBridgeDialog*) override;

	 Q_INVOKABLE bool executeBlenderScripts(QString sFilePath, QString sCommandlineArguments);

	 int m_nPythonExceptionExitCode = 11;  // arbitrary exit code to check for blener python exceptions
	 int m_nBlenderExitCode = 0;
	 QString m_sBlenderExecutablePath = "";

	 friend class DzBlenderExporter;
#ifdef UNITTEST_DZBRIDGE
	friend class UnitTest_DzBlenderAction;
#endif

};
