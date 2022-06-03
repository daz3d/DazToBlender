#ifdef UNITTEST_DZBRIDGE

#include "UnitTest_DzBlenderDialog.h"
#include "DzBlenderDialog.h"


UnitTest_DzBlenderDialog::UnitTest_DzBlenderDialog()
{
	m_testObject = (QObject*) new DzBlenderDialog();
}

bool UnitTest_DzBlenderDialog::runUnitTests()
{
	RUNTEST(_DzBridgeBlenderDialog);
	RUNTEST(getIntermediateFolderEdit);
	RUNTEST(resetToDefaults);
	RUNTEST(loadSavedSettings);
	RUNTEST(HandleSelectIntermediateFolderButton);
	RUNTEST(HandleAssetTypeComboChange);

	return true;
}

bool UnitTest_DzBlenderDialog::_DzBridgeBlenderDialog(UnitTest::TestResult* testResult)
{
	bool bResult = true;
	TRY_METHODCALL(new DzBlenderDialog());
	return bResult;
}

bool UnitTest_DzBlenderDialog::getIntermediateFolderEdit(UnitTest::TestResult* testResult)
{
	bool bResult = true;
	TRY_METHODCALL(qobject_cast<DzBlenderDialog*>(m_testObject)->getIntermediateFolderEdit());
	return bResult;
}

bool UnitTest_DzBlenderDialog::resetToDefaults(UnitTest::TestResult* testResult)
{
	bool bResult = true;
	TRY_METHODCALL(qobject_cast<DzBlenderDialog*>(m_testObject)->resetToDefaults());
	return bResult;
}

bool UnitTest_DzBlenderDialog::loadSavedSettings(UnitTest::TestResult* testResult)
{
	bool bResult = true;
	TRY_METHODCALL(qobject_cast<DzBlenderDialog*>(m_testObject)->loadSavedSettings());
	return bResult;
}

bool UnitTest_DzBlenderDialog::HandleSelectIntermediateFolderButton(UnitTest::TestResult* testResult)
{
	bool bResult = true;
	TRY_METHODCALL(qobject_cast<DzBlenderDialog*>(m_testObject)->HandleSelectIntermediateFolderButton());
	return bResult;
}

bool UnitTest_DzBlenderDialog::HandleAssetTypeComboChange(UnitTest::TestResult* testResult)
{
	bool bResult = true;
	TRY_METHODCALL(qobject_cast<DzBlenderDialog*>(m_testObject)->HandleAssetTypeComboChange(0));
	return bResult;
}


#include "moc_UnitTest_DzBlenderDialog.cpp"
#endif
