#ifdef UNITTEST_DZBRIDGE

#include "UnitTest_DzBlenderAction.h"
#include "DzBlenderAction.h"


UnitTest_DzBlenderAction::UnitTest_DzBlenderAction()
{
	m_testObject = (QObject*) new DzBlenderAction();
}

bool UnitTest_DzBlenderAction::runUnitTests()
{
	RUNTEST(_DzBridgeBlenderAction);
	RUNTEST(executeAction);
	RUNTEST(createUI);
	RUNTEST(writeConfiguration);
	RUNTEST(setExportOptions);
	RUNTEST(readGuiRootFolder);

	return true;
}

bool UnitTest_DzBlenderAction::_DzBridgeBlenderAction(UnitTest::TestResult* testResult)
{
	bool bResult = true;
	TRY_METHODCALL(new DzBlenderAction());
	return bResult;
}

bool UnitTest_DzBlenderAction::executeAction(UnitTest::TestResult* testResult)
{
	bool bResult = true;
	TRY_METHODCALL(qobject_cast<DzBlenderAction*>(m_testObject)->executeAction());
	return bResult;
}

bool UnitTest_DzBlenderAction::createUI(UnitTest::TestResult* testResult)
{
	bool bResult = true;
	TRY_METHODCALL(qobject_cast<DzBlenderAction*>(m_testObject)->createUI());
	return bResult;
}

bool UnitTest_DzBlenderAction::writeConfiguration(UnitTest::TestResult* testResult)
{
	bool bResult = true;
	TRY_METHODCALL(qobject_cast<DzBlenderAction*>(m_testObject)->writeConfiguration());
	return bResult;
}

bool UnitTest_DzBlenderAction::setExportOptions(UnitTest::TestResult* testResult)
{
	bool bResult = true;
	DzFileIOSettings arg;
	TRY_METHODCALL(qobject_cast<DzBlenderAction*>(m_testObject)->setExportOptions(arg));
	return bResult;
}

bool UnitTest_DzBlenderAction::readGuiRootFolder(UnitTest::TestResult* testResult)
{
	bool bResult = true;
	TRY_METHODCALL(qobject_cast<DzBlenderAction*>(m_testObject)->readGuiRootFolder());
	return bResult;
}


#include "moc_UnitTest_DzBlenderAction.cpp"

#endif
