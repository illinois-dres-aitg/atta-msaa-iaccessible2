# atta-msaa-iaccessible2
Assistive Technology Test Adapter (ATTA) for use in testing ARIA implementation using the web platform test suite

This project contains ATTAs for IAccessible2 and MSAA accessibility APIs for the Windows operating system and are designed to support automated testing of ARIA implementations in browsers implementing MSAA+IAccessible2.   

## Python Requirements

## Setting up a virtual environment

## Running the ATTA

For IAccessible2 testing:

```
python att_ia2.py
```

For MSAA (or IAccessible) testing:

```
python att_msaa.py
```

## Updating a local copy of the test cases for ARIA 1.1

1. Generate all tests and put them in a temporary directory.

```
mkdir temp; perl wai-aria/tools/make_tests.pl -d temp -s aria11
```   

1. Remove certain test files that have been updated by hand

```
rm temp/*activedescendant*
```

Note: Assuming you have no changes to make to the active descendant tests.
   This is needed because I've had to hand-edit the those tests to add
   the step to change focus. You'll overwrite that if you replace the
   hand-edited tests with the generated tests. This is a known issue
   which we'll hopefully fix soon.

1. COpy updated test files to ```wai-aria``` directory 

```
cp temp/* wai-aria
```
1. Having done the above, you'll have a local copy of the regenerated tests. To get them added to the official repo, you'll need to do a pull request for the upstream (w3c's official) web-platform-tests repo.

HTH.


