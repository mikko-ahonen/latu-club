# Implementation — Phase Instructions

- This file is generated. Add project-specific instructions to `implementation.local.md` in this directory.
- Write the actual implementation notes in `docs/implementation/`.
- Implementation always needs a proper unit test
- Implementation is not ready until all issues found in unit testing has been fixed
- Before starting to fix a bug, create a proper failing regression test case. Document the issue and important findings in the comments of the regression test
- Don't be lazy. Proper regression test case must not take shortcuts. Do not skip it if test data does not exist, you encounter a tooling issue, 'it 
  cannot be tested' etc.
- Always commit your changes to git after you have properly verified that a fix for a bug works, by running the test case
- Before you start, make sure you understand the security model in `docs/implementation/security.md`.
- Do not make any unsubstantiated claims. Only claim you to you have fixed an issue if you have first made a test case that realistically the tests proves the issue exists, and the test case is failing, and then your fixes makes the test case to pass.
- Always commit your changes to git after an issue has been fixed, or you have created substantial change.

- Use constants for all hard-coded values such as pixel widths and heights

- Track all new major features and bug fixes between released versions in CHANGES.md. Do not include bug fixes that affect only the current, non-released version. The file is ordered in reverse order. Current version is in version.txt and tagged with git. Add new features under the next minor release number.

- For taking screenshots for documentation, see [docs/screenshot-guide.md](docs/screenshot-guide.md)





## Key Commands


## Structure

Do not create extra directory structure. Store directories at the repository root.

```
latu-club/
├── doc/               # Documentation

└── tests/              # Test suites
```


## File Locations

- All documentation: `doc/` directory    # For all concise, clear, documentation
- Temporary files: `tmp/` directory      # For example test reports, plans, bug fix reports
