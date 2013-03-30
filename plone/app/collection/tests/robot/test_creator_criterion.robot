*** Settings ***

Library  Selenium2Library  timeout=2  implicit_wait=0
Library  plone.app.collection.testing_keywords.Keywords

Variables  plone/app/testing/interfaces.py

Resource  collection_keywords.txt

Suite Setup  Suite Setup
Suite Teardown  Suite Teardown

*** Variables ***

${front-page}  http://localhost:55001/plone/
${test-folder}  http://localhost:55001/plone/acceptance-test-folder

${PORT} =  55001
${ZOPE_URL} =  http://localhost:${PORT}
${PLONE_URL} =  ${ZOPE_URL}/plone
${BROWSER} =  Firefox


*** Test Cases ***

Test Creator Criterion
    Log in as site owner
    Go to  ${test-folder}
    Add Page  Site owner document
    Logout
    Log in as test user
    Go to  ${test-folder}
    Add Page  Test user document
    Create Collection  Creator Criterion Collection

    Click Edit In Edit Bar
    Set Creator Criterion To  ${TEST_USER_ID}

    Page should not contain  Site owner document
    Page should contain  Test user document