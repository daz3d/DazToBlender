#pragma once
#include "dzbasicdialog.h"
#include <QtGui/qcombobox.h>
#include <QtCore/qsettings.h>
#include <DzBridgeDialog.h>

class QPushButton;
class QLineEdit;
class QCheckBox;
class QComboBox;
class QGroupBox;
class QLabel;
class QWidget;
class DzBlenderAction;

class UnitTest_DzBlenderDialog;

#include "dzbridge.h"

class DzBlenderDialog : public DZ_BRIDGE_NAMESPACE::DzBridgeDialog{
	friend DzBlenderAction;
	Q_OBJECT
	Q_PROPERTY(QWidget* intermediateFolderEdit READ getIntermediateFolderEdit)
public:
	Q_INVOKABLE QLineEdit* getIntermediateFolderEdit() { return intermediateFolderEdit; }

	/** Constructor **/
	 DzBlenderDialog(QWidget *parent=nullptr);

	/** Destructor **/
	virtual ~DzBlenderDialog() {}

	Q_INVOKABLE void resetToDefaults() override;
	Q_INVOKABLE bool loadSavedSettings() override;
	Q_INVOKABLE void saveSettings() override;
	void accept() override;

protected slots:
	void HandleSelectIntermediateFolderButton();
	void HandleAssetTypeComboChange(int state);
	void HandleTargetPluginInstallerButton();
	virtual void HandleDisabledChooseSubdivisionsButton();
	virtual void HandleOpenIntermediateFolderButton(QString sFolderPath="");
	void HandlePdfButton() override;
	void HandleYoutubeButton() override;
	void HandleSupportButton() override;

protected:
	QLineEdit* intermediateFolderEdit;
	QPushButton* intermediateFolderButton;

	virtual void refreshAsset();

#ifdef UNITTEST_DZBRIDGE
	friend class UnitTest_DzBlenderDialog;
#endif
};
