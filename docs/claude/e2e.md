# E2E Testing — Phase Instructions

- This file is generated. Add project-specific instructions to `e2e.local.md` in this directory.
- Write the actual E2E test plan and results in `docs/e2e/`.

- E2E tests should cover all features, including all interactions that start from any buttons. You must test that error handling works properly for
  the UI element being tested.

- Your job is to fix any errors and keep E2E tests in good shape. Do not skip tests because you assume the issues are unrelated or transient.
- E2E means end-to-end. Test the actual flow. Verify from database that the operation worked as expected. For example, if creating an entity,
  before running the test, check that the entity does not exist in the database, and after running the test, check that the entity was created 
  in the database.
  
- E2E test must create the test data it needs and clean it up after the test.
- E2E test must not hide errors if an expected element is missing.
- Don't be lazy. Do testing properly. If you are prevented from E2E test, figure it out, instead of skipping or disabling the test.
- Do not report that all tests pass if you disable or skip tests.
- Track all new major features and bug fixes between released versions in CHANGES.md. Do not include bug fixes that affect only the current, non-released version. The file is ordered in reverse order. Current version is in version.txt and tagged with git. Add new features under the next minor release number.


