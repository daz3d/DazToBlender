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
#include "DzBlenderUtils.h"

#include <Alembic/Abc/All.h>
#include <Alembic/AbcGeom/All.h>
#include <Alembic/AbcCoreOgawa/All.h>
#include "Alembic/AbcGeom/OCurves.h"
#include "Alembic/AbcGeom/Basis.h"
#include "Alembic/AbcGeom/CurveType.h"

bool DzBlenderAction::writeAbcMesh(DzNode* pNode, Alembic::Abc::OArchive &AbcArchive, Alembic::Abc::TimeSamplingPtr &TimeSampling)
{
	// mesh pathway
	Alembic::AbcGeom::OPolyMesh MeshObj(AbcArchive.getTop(), pNode->getLabel().toLocal8Bit().constData(), TimeSampling);
	Alembic::AbcGeom::OPolyMeshSchema& MeshSchema = MeshObj.getSchema();			

	// Update the character and current figure mesh for the frame
	pNode->update();
	pNode->finalize();
	DzObject* pObject = pNode->getObject();

	// Get the Geometry
	DzVertexMesh* pVertexMesh = pObject->getCachedGeom();
	// Next get the vertex indexes and count for each face
	DzFacetMesh* pFacetMesh = dynamic_cast<DzFacetMesh*>(pVertexMesh);

	std::map<int, int> oOldVertexIndexToNewVertexIndex;
	std::vector<int> aUniqueVertexIndices;
	// First pass to get vertex numbers and create a remapping
	{

		for (int nFacetIndex = 0; nFacetIndex < pFacetMesh->getNumFacets(); nFacetIndex++)
		{
			// Add the vertex count for this face
			DzFacet pFacet = pFacetMesh->getFacet(nFacetIndex);
			int nFacetVertexCount = 3;
			if (pFacet.isQuad())
			{
				nFacetVertexCount = 4;
			}

			// Add the vertex indices for this face
			for (int FacetVertexIndex = 0; FacetVertexIndex < nFacetVertexCount; FacetVertexIndex++)
			{
				if (std::find(aUniqueVertexIndices.begin(), aUniqueVertexIndices.end(), pFacet.m_vertIdx[FacetVertexIndex]) == aUniqueVertexIndices.end()) {
					aUniqueVertexIndices.push_back(pFacet.m_vertIdx[FacetVertexIndex]);
				}
			}
		}
	}
	int newIndex = 0;
	std::sort(aUniqueVertexIndices.begin(), aUniqueVertexIndices.end());
	for (auto iterator : aUniqueVertexIndices)
	{
		int oldIndex = iterator;
		oOldVertexIndexToNewVertexIndex.insert(std::pair<int, int>(oldIndex, newIndex));
		newIndex++;
	}

	// Get the vertex positions
	std::vector<Imath::V3f> aAlembicVertices;
	float scaleFactor = 1.0f;
	// At this point uniqueVertexIndices is a sorted list of just the used vertices.  So using this will update the indexes as they are exported
	for (auto vertexID: aUniqueVertexIndices)
	{
		aAlembicVertices.push_back(Imath::V3f(pVertexMesh->getVertex(vertexID)[0] * scaleFactor, pVertexMesh->getVertex(vertexID)[1] * scaleFactor, pVertexMesh->getVertex(vertexID)[2] * scaleFactor));
	}

	// Add the vertex positions for the frame
	Alembic::AbcGeom::OPolyMeshSchema::Sample oFrameSample;
	oFrameSample.setPositions(Alembic::Abc::V3fArraySample(aAlembicVertices));

	std::vector<int> aFaceVertexIndices;
	std::vector<int> aFaceVertexCounts;
	for (int nFacetIndex = 0; nFacetIndex < pFacetMesh->getNumFacets(); nFacetIndex++)
	{
		// Add the vertex count for this face
		DzFacet oFacet = pFacetMesh->getFacet(nFacetIndex);
		int nFacetVertexCount = 3;
		if (oFacet.isQuad())
		{
			nFacetVertexCount = 4;
		}
		aFaceVertexCounts.push_back(nFacetVertexCount);

		// Add the vertex indices for this face
		for (int nFacetVertexIndex = 0; nFacetVertexIndex < nFacetVertexCount; nFacetVertexIndex++)
		{
			int nVertexIndexInFace = oFacet.m_vertIdx[nFacetVertexIndex];
			int nConvertedIndex = oOldVertexIndexToNewVertexIndex[nVertexIndexInFace];
			aFaceVertexIndices.push_back(nConvertedIndex);
		}
	}

	// Add the face data for the frame
	oFrameSample.setFaceIndices(Alembic::Abc::Int32ArraySample(aFaceVertexIndices));
	oFrameSample.setFaceCounts(Alembic::Abc::Int32ArraySample(aFaceVertexCounts));

	// Add the frame to the Mesh
	MeshSchema.set(oFrameSample);
	
	return true;
}

bool DzBlenderAction::writeAbcCurve(DzNode* pNode, Alembic::Abc::OArchive &AbcArchive, Alembic::Abc::TimeSamplingPtr &TimeSampling)
{
	printf("DEBUG: writeAbcCurve() pNode=%s\n", pNode->getLabel().toLocal8Bit().data());
	Alembic::AbcGeom::OCurves oCurve(AbcArchive.getTop(), pNode->getLabel().toLocal8Bit().constData(), TimeSampling);
	Alembic::AbcGeom::OCurvesSchema &oCurveSchema = oCurve.getSchema();
	
	int nNumLines=-1;
	int nNumLineSegments=-1;
	int nNumLineVertIndexes=-1;
	int nNumVerts=-1;

	DzFacetMesh* pFacetMesh = qobject_cast<DzFacetMesh*>(pNode->getObject()->getCachedGeom());
	if (pFacetMesh) {
		nNumLines = getNumPolylines(pFacetMesh);
		nNumLineSegments = getNumPolylineSegments(pFacetMesh);
		nNumLineVertIndexes = getNumPolylineVertexDataIndices(pFacetMesh);
		nNumVerts = pFacetMesh->getNumVertices();		
	}

	printf("DEBUG: %s: numPolyLines: %i, segments: %i, vert_indexes: %i, numVerts: %i\n", pNode->getLabel().toLocal8Bit().constData(), nNumLines, nNumLineSegments, nNumLineVertIndexes, nNumVerts);

	std::vector<Imath::V3f> aAlembicVertices;
	std::vector<int32_t> aPolylineVertexIndices;
	float scaleFactor = 1.0f;

	for (int nPolylineIndex=0; nPolylineIndex < nNumLines; nPolylineIndex++)
	{
		QVariantList* pVertexIndices = new QVariantList();
		if (getPolylineVertexIndices(pFacetMesh, nPolylineIndex, *pVertexIndices) == false) {
			QString mesg = QString("ERROR: writeAbcCurve(): failed trying to call getPolylineVertexIndices on nPolyLineIndex #%1").arg(nPolylineIndex);
			dzApp->warning(mesg);
			printf("%s\n", mesg.toLocal8Bit().data());
			return false;
		}
		for (int i=0; i < pVertexIndices->count(); i++)
		{
			int nVertexIndex = pVertexIndices->at(i).toInt();
			if (nVertexIndex > nNumVerts) {
				QString mesg = QString("ERROR: writeAbcCurve(): nVertexCounter larger than num verts: %i").arg(nVertexIndex);
				dzApp->warning( mesg );
				printf("%s\n", mesg.toLocal8Bit().data() );
				return false;
			}
			Imath::V3f vDataPoint(
				pFacetMesh->getVertex(nVertexIndex)[0] * scaleFactor,
				pFacetMesh->getVertex(nVertexIndex)[1] * scaleFactor,
				pFacetMesh->getVertex(nVertexIndex)[2] * scaleFactor
			);
			aAlembicVertices.push_back(vDataPoint);			
		}
		aPolylineVertexIndices.push_back(pVertexIndices->count());
#if __APPLE__
//		delete(pVertexIndices);
#endif
	}

	
	Alembic::AbcGeom::OCurvesSchema::Sample oFrameSample( Alembic::Abc::P3fArraySample(aAlembicVertices), aPolylineVertexIndices);
	oFrameSample.setBasis(Alembic::AbcGeom::kNoBasis);
	oFrameSample.setType(Alembic::AbcGeom::kLinear);
	oFrameSample.setWrap(Alembic::AbcGeom::kNonPeriodic);
//	Alembic::AbcGeom::Box3d box;
//	oFrameSample.setSelfBounds(box);
	oCurveSchema.set(oFrameSample);

	return true;
}

bool DzBlenderAction::writeHair(QString sFilePath, QMap<DzNode*, DzNode*> &oUndoTable)
{
	if (oUndoTable.count() < 1) {
		return false;
	}

	printf("DEBUG: writeHair(%s)\n", sFilePath.toLocal8Bit().data());
	// Create the Abc file and set the time to match Daz output
	Alembic::AbcCoreOgawa::WriteArchive AbcWriteArchive;
	Alembic::Abc::OArchive AbcArchive = Alembic::Abc::OArchive(AbcWriteArchive, sFilePath.toLocal8Bit().data());
	Alembic::Abc::TimeSamplingPtr TimeSampling = Alembic::Abc::TimeSamplingPtr(new Alembic::Abc::TimeSampling((double)dzScene->getTimeStep() / 4800, 0.0));

	foreach(DzNode* pNode, oUndoTable.keys())
	{
		if (isStrandBasedHair(pNode) == false) {
//			writeAbcMesh(pNode, AbcArchive, TimeSampling);
			continue;
		}

		writeAbcCurve(pNode, AbcArchive, TimeSampling);

	}
	
	return true;
}


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
	dzApp->log("DEBUG: Blender Exporter: setting working dir for blender script: " + sWorkingPath);
	pToolProcess->setWorkingDirectory(sWorkingPath);
	pToolProcess->setProcessChannelMode(QProcess::MergedChannels);
	pToolProcess->setReadChannel(QProcess::StandardOutput);
	dzApp->log("DEBUG: Blender Exporter: starting blender script: [" + sFilePath + "] with args: " + args.join(";"));
	pToolProcess->start(sFilePath, args);
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
			if (!bUserInitiatedTermination) {
				QString sTimeoutText = tr("\
The current Blender operation is taking a long time.\n\
Do you want to Ignore this time-out and wait a little longer, or \n\
Do you want to Abort the operation now?");
				int result = QMessageBox::critical(0,
					tr("Blender Exporter: Blender Process Timout Error"),
					sTimeoutText,
					QMessageBox::Ignore,
					QMessageBox::Abort);
				if (result == QMessageBox::Ignore) {
					int snoozeTime = 60 * 1000 / fMilliSecondsPerTick;
					timeoutTicks += snoozeTime;
				} else {
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
				} else {
					dzApp->log("DEBUG: Sending Kill Signal to Blender Process...");
					pToolProcess->kill();
				}
			}
		}
		if (pToolProcess->state() == QProcess::Running) {
			progress->step();
		} else if (pToolProcess->state() == QProcess::NotRunning) {
			dzApp->log("DEBUG: QProcess State is now NotRunning, stopping monitor....");
			break;
		} else {
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
	m_nBlenderExitCode = pToolProcess->exitCode();
	QProcess::ExitStatus qExitStatus = pToolProcess->exitStatus();
	if (qExitStatus == QProcess::CrashExit) {
		if (m_nBlenderExitCode == 0) {
			dzApp->log("Blender Exporter: ERROR: Blender process Crashed but exit code is 0, manually setting to -1...");
			m_nBlenderExitCode = -1;
		}
	}

	QString mesg;
#ifdef __APPLE__
	if (m_nBlenderExitCode != 0 && m_nBlenderExitCode != 120)
#else
	if (m_nBlenderExitCode != 0)
#endif
	{
		if (m_nBlenderExitCode == m_nPythonExceptionExitCode) {
			mesg = QString("Blender Exporter: ERROR: Python error:.... %1").arg(m_nBlenderExitCode);
		} else {
			mesg = QString("Blender Exporter: ERROR: exit code = %1").arg(m_nBlenderExitCode);
		}
		dzApp->warning(mesg);
	} else {
		mesg = QString("Blender Exporter: DEBUG: blender script successful, exit code = %1").arg(m_nBlenderExitCode);
		dzApp->log(mesg);
	}
	progress->setCurrentInfo(mesg);
	progress->finish();
	delete progress;

	bool bResult = (m_nBlenderExitCode == 0);
	return bResult;
}

bool DzBlenderAction::preProcessScene(DzNode* parentNode)
{
	DzProgress* blenderProgress = new DzProgress(tr("PreProcessing Scene"), 100, false, true);

	DzBridgeAction::preProcessScene(parentNode);

	QMap<DzNode*, DzNode*> oUndoTable;
	hideAllStrandBasedHair(parentNode, oUndoTable);
	// hide scalp
	foreach(DzNode* pHairNode, oUndoTable.keys())
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
	if (oUndoTable.count() > 0) {
		QString sAbcTest = QString(m_sDestinationFBX).replace(".fbx", ".abc");
		writeHair(sAbcTest, oUndoTable);
	}
	
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
//				QString label = MorphTools::GetMorphLabelFromName(morphName, m_pSelectedNode);
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
			if (rootNodeList.isEmpty()) {
				exportProgress->finish();
				exportProgress->cancel();
				m_nExecuteActionResult = DZ_OPERATION_FAILED_ERROR;
				return;
			}
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
	// 2025-07-21, DB: NOTE: m_bConvertFbxJointsEnabled defaults to true in DzBlender and is passed as true to DzBridgeAction
	//   so that the base class joint conversion operations are performed first.  DzBlender then adds additional behavior
	//   below to bake the standard Daz Rig joint orientations for compatibility with Blender Fbx Importer.
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

	if (m_bConvertFbxJointsEnabled)
	{
		if (m_sExportRigMode == "" || m_sExportRigMode == "--")
		{
			QList<FbxNode*> nodeList;
			FbxNode* pFbxRootNode = pScene->GetRootNode();
			FbxTools::GetAllMeshes(pFbxRootNode, nodeList);
			FbxNode* pFbxRootBone = nullptr;
			QString sFbxRootBoneName = "";
			for (int ChildIndex = 0; ChildIndex < pFbxRootNode->GetChildCount(); ++ChildIndex)
			{
				FbxNode* ChildNode = pFbxRootNode->GetChild(ChildIndex);
				FbxNodeAttribute* Attr = ChildNode->GetNodeAttribute();
				if (Attr && Attr->GetAttributeType() == FbxNodeAttribute::eSkeleton)
				{
					pFbxRootBone = ChildNode;
					sFbxRootBoneName = pFbxRootBone->GetName();
					break;
				}
			}

			FbxTools::FixClusterTranformLinks(pScene, pFbxRootBone, nullptr);
			// Bake New Bind Pose
			FbxPose* pNewBindPose = FbxTools::SaveBindMatrixToPose(pScene, "NewBindPose", nullptr, true);
			FbxTools::ApplyBindPose(pScene, pNewBindPose);
			foreach(FbxNode * pNode, nodeList) {
				QString debugName(pNode->GetName());
				FbxMesh* pMesh = pNode->GetMesh();
				FbxAMatrix matrix = pNode->EvaluateGlobalTransform();
				FbxVector4* pVertexBuffer = pMesh->GetControlPoints();
				if (pVertexBuffer == NULL) continue;
				FbxTools::BakePoseToVertexBuffer(pVertexBuffer, &matrix, pNewBindPose, pMesh);
				// Clear Pre/Post Rotations
				pNode->SetPreRotation(FbxNode::eSourcePivot, FbxVector4(0, 0, 0));
				pNode->SetPostRotation(FbxNode::eSourcePivot, FbxVector4(0, 0, 0));
				pNode->LclScaling.Set(FbxDouble3(1.0, 1.0, 1.0));
				pNode->LclRotation.Set(FbxDouble3(0, 0, 0));
				pNode->LclTranslation.Set(FbxDouble3(0, 0, 0));
			}
			pNewBindPose->Destroy();
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
