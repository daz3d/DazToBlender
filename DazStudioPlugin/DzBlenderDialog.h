#pragma once
#include "dzbasicdialog.h"
#include <QtGui/qcombobox.h>
#include <QtGui/qcheckbox.h>
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
class QHBoxLayout;

class UnitTest_DzBlenderDialog;

#include "dzbridge.h"

class DzFileValidator : public QValidator {
public:
	State validate(QString& input, int& pos) const;
};

class DzBlenderDialog : public DZ_BRIDGE_NAMESPACE::DzBridgeDialog{
	friend DzBlenderAction;
	Q_OBJECT
	Q_PROPERTY(QWidget* m_wIntermediateFolderEdit READ getIntermediateFolderEdit)
public:
	Q_INVOKABLE QLineEdit* getIntermediateFolderEdit() { return m_wIntermediateFolderEdit; }

	/** Constructor **/
	 DzBlenderDialog(QWidget *parent=nullptr, const QString& windowTitle = "");

	/** Destructor **/
	virtual ~DzBlenderDialog() {}

	Q_INVOKABLE void resetToDefaults() override;
	Q_INVOKABLE bool loadSavedSettings() override;
	Q_INVOKABLE void saveSettings() override;
	void accept() override;

	DzFileValidator m_dzValidatorFileExists;
	Q_INVOKABLE bool isBlenderTextBoxValid(const QString& text = "");
	Q_INVOKABLE bool disableAcceptUntilAllRequirementsValid();

	// Move Blender Executable Widgets to Top of Dialog
	Q_INVOKABLE void requireBlenderExecutableWidget(bool bRequired);

	Q_INVOKABLE bool showBlenderToolsOptions(const bool visible);
	Q_INVOKABLE bool setOutputBlendFilepath(const QString& filename);
	Q_INVOKABLE bool getUseBlenderToolsCheckbox() { return m_wUseBlendToolsCheckBox->isChecked(); }
	Q_INVOKABLE int setUseBlenderToolsCheckbox(const bool state);
	Q_INVOKABLE QString getTextureAtlasMode() { return m_wBakeTextureAtlasCombobox->itemData(m_wBakeTextureAtlasCombobox->currentIndex()).toString(); }
	Q_INVOKABLE QString getExportRigMode() { return m_wExportRigCombobox->itemData(m_wExportRigCombobox->currentIndex()).toString(); }
	Q_INVOKABLE int getTextureAtlasSize() { return m_wAtlasSizeCombobox->itemData(m_wAtlasSizeCombobox->currentIndex()).toInt(); }

protected:
	virtual void showEvent(QShowEvent* event) override { disableAcceptUntilAllRequirementsValid(); DzBridgeDialog::showEvent(event); }

protected slots:
	void HandleSelectIntermediateFolderButton();
	void HandleAssetTypeComboChange(int state);
	void HandleTargetPluginInstallerButton();
	virtual void HandleDisabledChooseSubdivisionsButton();
	virtual void HandleOpenIntermediateFolderButton(QString sFolderPath="");
	void HandlePdfButton() override;
	void HandleYoutubeButton() override;
	void HandleSupportButton() override;

	void HandleSelectBlenderExecutablePathButton();
	void HandleTextChanged(const QString &text);
	bool HandleAcceptButtonValidationFeedback();
	void updateBlenderExecutablePathEdit(bool isValid);

protected:
	QLineEdit* m_wIntermediateFolderEdit;
	QPushButton* m_wIntermediateFolderButton;

	QLineEdit* m_wBlenderExecutablePathEdit;
	QPushButton* m_wBlenderExecutablePathButton;
	QLabel* m_wBlenderExecutableRowLabel;
	QHBoxLayout* m_wBlenderExecutablePathLayout;
	QGroupBox* m_wRequiredInputFrame;
	QFormLayout* m_wRequiredInputFrameLayout;

	QGroupBox* m_wBlenderToolsGroupbox;
	QLineEdit* m_wBlenderOutputFilename;
	QCheckBox* m_wUseBlendToolsCheckBox;
	QComboBox* m_wBakeTextureAtlasCombobox;
	QComboBox* m_wAtlasSizeCombobox;
	QComboBox* m_wExportRigCombobox;

	virtual void refreshAsset();

	bool m_bBlenderRequired = false;

#ifdef UNITTEST_DZBRIDGE
	friend class UnitTest_DzBlenderDialog;
#endif
};
