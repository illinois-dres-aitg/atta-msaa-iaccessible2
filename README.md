# Assistive Technology Test Adapters (ATTA) for IAccessible (MSAA) and IAccessible2
[Assistive Technology Test Adapter](https://spec-ops.github.io/atta-api/index.html) (ATTA) for use in testing ARIA implementation using the [web platform test suite](http://w3c-test.org/tools/runner/index.html).  

This project contains ATTAs for IAccessible (MSAA) and IAccessible2 accessibility APIs for the Microsoft Windows operating system and are designed to support automated testing of W3C [Acessible Rich Internet Application 1.1](https://www.w3.org/TR/wai-aria-1.1/) and W3C [CORE Accessibility API Mapping](https://www.w3.org/TR/core-aam-1.1/) (CORE-AAM) implementation in browsers implementing MSAA+IAccessible2.   

## Suporting Rsources
* [Assistive Technology Test Adapter](https://spec-ops.github.io/atta-api/index.html)
* [web platform test suite](http://w3c-test.org/tools/runner/index.html)
* [Python Comtypes Library](https://pypi.org/project/comtypes/)



## Python Requirements

* Install Python version 2.7.x
* Set environment variable to include python path information, typically adding the path `c:\python27\scripts\`
* Setup a [virtual environment](http://docs.python-guide.org/en/latest/dev/virtualenvs/) for python
* Activate the virtual environment using the `Scripts\activate.bat` in the directory where you created the virtual environment
* Clone this repository
* Change direcotry to the ATTA repository and install the required packages using `pip install - requirements.txt` 
* Requirements file for virtual environment:

```
  appdirs==1.4.3
  comtypes==1.1.3.post2
  faulthandler==2.6
  packaging==16.8
  pyparsing==2.2.0
  requests==2.13.0
  six==1.10.0
```

## Registering IAccessible2Proxy.dll

There is a file in the "IAccessible2Proxy.dll" is in the "pyia2" directory that needs to be registered with the Windows operating system.
From the Windows Command prompt type the following command:

```
regsvr32 c:\[path to diectory]\atta-msaa-iaccessible2\pyia2\IAccessible2Proxy.dll
```

NOTE: You need to run the command prompt as an administrator to register DLLs.

## Enabling Accessibility APIs on Chrome

* Use the [chrome://accessibility](chrome://accessibility) settings URL and check all the boxes related to using the accessibility API.
* No need to restart Chrome it will support IAccessible and IAccessible2 interfaces once you enable in the accessibiity settings.

## Enabling Accessibility APIs on Firefox

* I was not able to get Firefox to expose accessibility API information unless I had a screen reader running.
* Installed [NVDA](https://www.nvaccess.org/download/) and ran it before starting Firefox before testing, but [JAWS](https://www.freedomscientific.com/Downloads/JAWS) can also be used in its demo mode.  
* Once the accessibility API is enabled, you can exit the screen reader.

NOTE: If you down load NVDA, please donate to support the continued development of the open source scren reader.

## Running WPT with ATTA to get ARIA 1.1 and CORE AAM test results

1. Start Chrome or Firefox (e.g. typically canary or firefox nightly) to start a test run
1. Go to the [W3C WPT Test Runner](http://w3c-test.org/tools/runner/index.html )
1. To run the [ARIA 1.1 test cases](https://www.w3.org/wiki/ARIA_1.1_Testable_Statements), enter  ```/wai-ara/``` to the textbox label ```Run tests under path```.
1. Start the ATTA for IAccesible2 or MSAA (see options following)
1. Press the ```Start``` button in the WPT Test Runner

For IAccessible2 testing:

```
python att_ia2.py
```

For MSAA (or IAccessible) testing:

```
python att_msaa.py
```
1. To run the [CORE AAM test cases](https://www.w3.org/wiki/Core_AAM_1.1_Testable_Statements) use the same proceedure as for ARIA 1.1, but for the textbox labelled ```Run tests under path``` use ```/core-aam/```.


## Updating a local copy of the test cases for ARIA 1.1

Install and configure a local copy of [W3C Web Platform Tests](https://github.com/w3c/web-platform-tests).

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



