
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

