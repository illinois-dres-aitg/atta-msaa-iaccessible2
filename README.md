# atta-msaa-iaccessible2
Assistive Technology Test Adapter (ATTA) for use in testing ARIA implementation using the web platform test suite

This project contains ATTAs for IAccessible2 and MSAA accessibility APIs for the Windows operating system and are designed to support automated testing of ARIA implementations in browsers implementing MSAA+IAccessible2.   

## Python Requirements

## Setting up a virtual environment

## Running the ATTA

1. You need to have either Chrome or Firefox open to one of the following URLS:
    * http://w3c-test.org/tools/runner/index.html (for using the W3C version of WPT)
    * localhost:8000/tools/runner/index.html (for using a local version of WPT)
1. Add to the textbox label ```Run tests under path``` add ```/wai-ara/```
1. Start the ATTA for IAccesible2 or MSAA (see options following)
1. Press the ```Start``` button

For IAccessible2 testing:

```
python att_ia2.py
```

For MSAA (or IAccessible) testing:

```
python att_msaa.py
```

## Setting up a local copy of WPT



## Updating a local copy of the test cases for ARIA 1.1

The following instructions are assuming you are in the WPT root directory.

1. Generate all tests and put them in a temporary directory.

```
mkdir temp; perl wai-aria/tools/make_tests.pl -d temp -s aria11
```   

2. Remove certain test files that have been updated by hand

```
rm temp/*activedescendant*
```

Note: Assuming you have no changes to make to the active descendant tests.
   This is needed because I've had to hand-edit the those tests to add
   the step to change focus. You'll overwrite that if you replace the
   hand-edited tests with the generated tests. This is a known issue
   which we'll hopefully fix soon.

3. Copy updated test files to ```wai-aria``` directory 

```
cp temp/* wai-aria
```

4. Having done the above, you'll have a local copy of the regenerated tests. To get them added to the official repo, you'll need to do a pull request for the upstream (w3c's official) web-platform-tests repo.



