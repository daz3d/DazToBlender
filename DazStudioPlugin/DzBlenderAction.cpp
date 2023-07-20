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

#include "DzBlenderAction.h"
#include "DzBlenderDialog.h"
#include "DzBridgeMorphSelectionDialog.h"
#include "DzBridgeSubdivisionDialog.h"

#ifdef WIN32
#include <shellapi.h>
#endif

#include "dzbridge.h"

DzBlenderAction::DzBlenderAction() :
	DzBridgeAction(tr("Daz To &Blender"), tr("Send the selected node to Blender."))
{
	m_nNonInteractiveMode = 0;
	m_sAssetType = QString("SkeletalMesh");
	//Setup Icon
	QString iconName = "Daz to Blender";
	QPixmap basePixmap = QPixmap::fromImage(getEmbeddedImage(iconName.toLatin1()));
	QIcon icon;
	icon.addPixmap(basePixmap, QIcon::Normal, QIcon::Off);
	QAction::setIcon(icon);

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

	// m_subdivisionDialog creation REQUIRES valid Character or Prop selected
	if (dzScene->getNumSelectedNodes() != 1)
	{
		if (m_nNonInteractiveMode == 0) QMessageBox::warning(0, tr("Error"),
			tr("Please select one Character or Prop to send."), QMessageBox::Ok);

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

	if (!m_subdivisionDialog) m_subdivisionDialog = DZ_BRIDGE_NAMESPACE::DzBridgeSubdivisionDialog::Get(m_bridgeDialog);
	if (!m_morphSelectionDialog) m_morphSelectionDialog = DZ_BRIDGE_NAMESPACE::DzBridgeMorphSelectionDialog::Get(m_bridgeDialog);

	return true;
}

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
		DzNodeList rootNodes = buildRootNodeList();
		if (rootNodes.length() == 1)
		{
			dzScene->setPrimarySelection(rootNodes[0]);
		}
		else if (rootNodes.length() > 1)
		{
			if (m_nNonInteractiveMode == 0)
			{
				QMessageBox::warning(0, tr("Error"),
					tr("Please select one Character or Prop to send."), QMessageBox::Ok);
			}
		}
	}

	// Create the dialog
	if (m_bridgeDialog == nullptr)
	{
		m_bridgeDialog = new DzBlenderDialog(mw);
	}
	else
	{
		if (m_nNonInteractiveMode == 0)
		{
			m_bridgeDialog->resetToDefaults();
			m_bridgeDialog->loadSavedSettings();
		}
	}

	// Prepare member variables when not using GUI
	if (m_nNonInteractiveMode == 1)
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
			m_mMorphNameToLabel.clear();
			foreach(QString morphName, m_aMorphListOverride)
			{
				QString label = m_morphSelectionDialog->GetMorphLabelFromName(morphName);
				m_mMorphNameToLabel.insert(morphName, label);
			}
		}
		else
		{
			m_bEnableMorphs = false;
			m_sMorphSelectionRule = "";
			m_mMorphNameToLabel.clear();
		}

	}

	// If the Accept button was pressed, start the export
	int dlgResult = -1;
	if (m_nNonInteractiveMode == 0)
	{
		dlgResult = m_bridgeDialog->exec();
	}
	if (m_nNonInteractiveMode == 1 || dlgResult == QDialog::Accepted)
	{
		// Read Common GUI values
		if (readGui(m_bridgeDialog) == false)
		{
			return;
		}

		// DB 2021-10-11: Progress Bar
		DzProgress* exportProgress = new DzProgress("Sending to Blender...", 10);

		// Read Custom GUI values
//		DzBlenderDialog* blenderDialog = qobject_cast<DzBlenderDialog*>(m_bridgeDialog);

#if __LEGACY_PATHS__
		if (m_sAssetType == "SkeletalMesh" || m_sAssetType == "Animation")
		{
			m_sRootFolder = QDesktopServices::storageLocation(QDesktopServices::DocumentsLocation) + "/DAZ 3D/Bridges/Daz To Blender/Exports/FIG";
			m_sRootFolder = m_sRootFolder.replace("\\", "/");
			m_sExportSubfolder = "FIG0";
			m_sExportFbx = "B_FIG";
			m_sExportFilename = "FIG";
		}
		else
		{
			m_sRootFolder = QDesktopServices::storageLocation(QDesktopServices::DocumentsLocation) + "/DAZ 3D/Bridges/Daz To Blender/Exports/ENV";
			m_sRootFolder = m_sRootFolder.replace("\\", "/");
			m_sExportSubfolder = "ENV0";
			m_sExportFbx = "B_ENV";
			m_sExportFilename = "ENV";
		}
		m_sDestinationPath = m_sRootFolder + "/" + m_sExportSubfolder + "/";
		m_sDestinationFBX = m_sDestinationPath + m_sExportFbx + ".fbx";
#endif

		//Create Daz3D folder if it doesn't exist
		QDir dir;
		dir.mkpath(m_sRootFolder);
		exportProgress->step();

		exportHD(exportProgress);

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

	QString srcPath = ":/DazBridgeBlender/BlenderPlugin.zip";
	QFile srcFile(srcPath);
//	QString destPath = destinationFolder + "/BlenderPlugin.zip";
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

	if (m_sAssetType.toLower().contains("mesh") || m_sAssetType == "Animation")
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
		writeAllMaterials(m_pSelectedNode, writer, pCVSStream);
		writeAllMorphs(writer);

		writeMorphLinks(writer);
		//writer.startMemberObject("MorphLinks");
		//writer.finishObject();
		writeMorphNames(writer);
		//writer.startMemberArray("MorphNames");
		//writer.finishArray();

		DzBoneList aBoneList = getAllBones(m_pSelectedNode);

		writeSkeletonData(m_pSelectedNode, writer);
		writeHeadTailData(m_pSelectedNode, writer);

		writeJointOrientation(aBoneList, writer);
		writeLimitData(aBoneList, writer);
		writePoseData(m_pSelectedNode, writer, true);
		writeAllSubdivisions(writer);
		writeAllDforceInfo(m_pSelectedNode, writer);
	}

	if (m_sAssetType == "Pose")
	{
	   writeAllPoses(writer);
	}

	if (m_sAssetType == "Environment")
	{
		writeEnvironment(writer);
	}

	writer.finishObject();
	DTUfile.close();

}

// Setup custom FBX export options
void DzBlenderAction::setExportOptions(DzFileIOSettings& ExportOptions)
{
	//ExportOptions.setBoolValue("doEmbed", false);
	//ExportOptions.setBoolValue("doDiffuseOpacity", false);
	//ExportOptions.setBoolValue("doCopyTextures", false);
	ExportOptions.setBoolValue("doFps", true);
	ExportOptions.setBoolValue("doLocks", false);
	ExportOptions.setBoolValue("doLimits", false);
	ExportOptions.setBoolValue("doBaseFigurePoseOnly", false);
	ExportOptions.setBoolValue("doHelperScriptScripts", false);
	ExportOptions.setBoolValue("doMentalRayMaterials", false);
}

QString DzBlenderAction::readGuiRootFolder()
{
	QString rootFolder = QDesktopServices::storageLocation(QDesktopServices::DocumentsLocation) + QDir::separator() + "DazToBlender";
#if __LEGACY_PATHS__
	if (m_sAssetType == "SkeletalMesh")
	{
		rootFolder = QDesktopServices::storageLocation(QDesktopServices::DocumentsLocation) + "/DAZ 3D/Bridges/Daz To Blender/Exports/FIG/FIG0";
		rootFolder = rootFolder.replace("\\", "/");
	}
	else
	{
		rootFolder = QDesktopServices::storageLocation(QDesktopServices::DocumentsLocation) + "/DAZ 3D/Bridges/Daz To Blender/Exports/ENV/ENV0";
		rootFolder = rootFolder.replace("\\", "/");
	}
#else
	if (m_bridgeDialog)
	{
		QLineEdit* intermediateFolderEdit = nullptr;
		DzBlenderDialog* blenderDialog = qobject_cast<DzBlenderDialog*>(m_bridgeDialog);

		if (blenderDialog)
			intermediateFolderEdit = blenderDialog->getAssetsFolderEdit();

		if (intermediateFolderEdit)
			rootFolder = intermediateFolderEdit->text().replace("\\", "/") + "/Daz3D";
	}
#endif

	return rootFolder;
}

#include "moc_DzBlenderAction.cpp"
