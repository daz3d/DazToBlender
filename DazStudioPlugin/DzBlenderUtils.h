#include <DzBridgeAction.h>
#include "DzBlenderDialog.h"

#include <dzexporter.h>


class QProcess;

class DzBlenderUtils
{
public:
	static int ExecuteBlenderScripts(QString sBlenderExecutablePath, QString sCommandlineArguments, QString sWorkingPath, QProcess* thisProcess, DzApp* dzApp, float fTimeoutInSeconds=120);
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
