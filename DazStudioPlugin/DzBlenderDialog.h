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
	 DzBlenderDialog(QWidget *parent=nullptr);

	/** Destructor **/
	virtual ~DzBlenderDialog() {}

	Q_INVOKABLE void resetToDefaults() override;
	Q_INVOKABLE bool loadSavedSettings() override;
	Q_INVOKABLE void saveSettings() override;
	void accept() override;

	DzFileValidator m_dzValidatorFileExists;
	Q_INVOKABLE bool isBlenderTextBoxValid(const QString& text = "");
	Q_INVOKABLE bool disableAcceptUntilAllRequirementsValid();

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

protected:
	QLineEdit* m_wIntermediateFolderEdit;
	QPushButton* m_wIntermediateFolderButton;

	QLineEdit* m_wBlenderExecutablePathEdit;
	QPushButton* m_wBlenderExecutablePathButton;
	QWidget* m_wBlenderExecutablePathRowLabelWdiget;

	virtual void refreshAsset();

#ifdef UNITTEST_DZBRIDGE
	friend class UnitTest_DzBlenderDialog;
#endif
};
