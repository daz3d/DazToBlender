
#include "DzBlenderAction.h"

class DzBlenderActionExtras_01 : public DzBlenderAction {
	Q_OBJECT
public:
	DzBlenderActionExtras_01();
	virtual QString getDefaultMenuPath() const override { return tr("&File/Send To/Bridge Tools"); }
	
	void executeAction() override;

};

class DzBlenderActionExtras_02 : public DzAction {
	Q_OBJECT
public:
	DzBlenderActionExtras_02();
	virtual QString getDefaultMenuPath() const override { return tr("&File/Send To/Bridge Tools"); }
	
	void executeAction() override;

};

class DzBlenderActionExtras_03 : public DzAction {
	Q_OBJECT
public:
	DzBlenderActionExtras_03();
	virtual QString getDefaultMenuPath() const override { return tr("&File/Send To/Bridge Tools"); }

	void executeAction() override;

};

class DzBlenderActionExtras_04 : public DzAction {
	Q_OBJECT
public:
	DzBlenderActionExtras_04();
	virtual QString getDefaultMenuPath() const override { return tr("&File/Send To/Bridge Tools"); }

	void executeAction() override;

};

class DzFbxPoseBinder : public DzAction {
	Q_OBJECT
public:
	DzFbxPoseBinder();
	virtual QString getDefaultMenuPath() const override { return tr("&File/Send To/Bridge Tools"); }
	
	void executeAction() override;
	bool bakeT0BindPose(QString sFbxFilePath, bool bEmbedTexturesInOutputFile);
	
};

class DzBlenderActionExtras_XXX : public DzAction {
	Q_OBJECT
public:
	DzBlenderActionExtras_XXX();
	virtual QString getDefaultMenuPath() const override { return tr("&File/Send To/Bridge Tools"); }

	void executeAction() override;

};
