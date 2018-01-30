#!/usr/bin/env python27
#
# win_atta_base
# Optional base class for python27 Accessible Technology Test Adapters
#
# Developed by Jon Gunderson and Mihir Kumar
# Copyright (c) 2017 University of Illinois
# Based on the ATTAs developed by Joanmarie Diggs (@joanmarie)
#
# For license information, see:
# https://www.w3.org/Consortium/Legal/2008/04-testsuite-copyright.html

import argparse
import signal
import sys
import threading
import traceback

from urlparse import urlparse

from BaseHTTPServer import HTTPServer
from win_atta_assertion import AttaAssertion
from win_atta_request_handler import AttaRequestHandler

# import pyia2
# Mihir Kumar 1/10/18
import os
import sys
import time
from uiautomation import *
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class Atta(object):
    """Optional base class for python27 Accessible Technology Test Adapters."""

    STATUS_ERROR = "ERROR"
    STATUS_OK = "OK"

    FAILURE_ATTA_NOT_ENABLED = "ATTA not enabled"
    FAILURE_ATTA_NOT_READY = "ATTA not ready"
    FAILURE_ELEMENT_NOT_FOUND = "Element not found"

    LOG_DEBUG = 0
    LOG_INFO = 1
    LOG_WARNING = 2
    LOG_ERROR = 3
    LOG_TEST_NAME = 4
    LOG_TEST_URI = 5
    LOG_RESULT_PASS = 6
    LOG_RESULT_FAIL = 7
    LOG_NONE = 100

    LOG_LEVELS = {
        LOG_DEBUG: "DEBUG",
        LOG_INFO: "INFO",
        LOG_WARNING: "WARNING",
        LOG_ERROR: "ERROR",
        LOG_TEST_NAME: "TEST TITLE",
        LOG_TEST_URI: "TEST URI",
        LOG_RESULT_PASS: "PASS",
        LOG_RESULT_FAIL: "FAIL",
    }

    FORMAT_NONE = "%(label)s%(msg)s"
    FORMAT_NORMAL = "\x1b[1m%(label)s\x1b[22m%(msg)s\x1b[0m"
    FORMAT_GOOD = "\x1b[32;1m%(label)s\x1b[22m%(msg)s\x1b[0m"
    FORMAT_WARNING = "\x1b[33;1m%(label)s\x1b[22m%(msg)s\x1b[0m"
    FORMAT_BAD = "\x1b[31;1m%(label)s\x1b[22m%(msg)s\x1b[0m"

    def __init__(self, host, port, name, version, api, log_level=None):
        """Initializes this ATTA."""

        self._elem_details = {}

        try:
            #Atspi.get_desktop(0)
            # TODO: IA2 get_desktop?
            print 'need to get desktop?'
        except:
            self._print(self.LOG_ERROR, "Could not get desktop from UIA.")
            self._enabled = False
            return

        #self._interfaces = list(filter(lambda x: gir.find_by_name("Atk", x), ifaces))
        # TODO: self._interfaces neede?

#         self._supported_properties = {
#             "accessible": lambda x: x is not None,
#             "childCount": pyia2.get_child_count,
#             "description": pyia2.get_description,
#             "name": pyia2.get_name,
# #            "interfaces": pyia2.get_interfaces,
#             "objectAttributes": pyia2.get_ia2_attribute_set,
#             "parent": pyia2.get_parent,
#             "relations": pyia2.get_ia2_relation_set,
#             "role": pyia2.get_ia2_role,
#             "type": pyia2.get_type_set,
#             "interfaces": pyia2.get_interface_set,
#             "states": pyia2.get_ia2_state_set,
#         }

        self._log_level = log_level or self.LOG_DEBUG
        self._host = host
        self._port = int(port)
        self._ansi_formatting = True

        self._server = None
        self._server_thread = None
        self._atta_name = name
        self._atta_version = version
        self._api_name = api
        self._api_version = ""
        self._enabled = True
        self._ready = False
        self._next_test = None, ""

        self._results = {}
        self._monitored_event_types = []
        self._event_history = []
        self._listeners = {}
        self._accessible_element = []

        # Information from IAccessible
        # self._accessible_document = None
        # self._current_uri = ""

        # if not sys.version_info[0] == 2:
        #     self._print(self.LOG_ERROR, "This ATTA requires Python 2.7.")
        #     return

    @staticmethod
    def _on_exception():
        """Handles exceptions, returning a string with the error."""
        return "_on_exception called"
        # return "EXCEPTION: %s" % traceback.format_exc(limit=1, chain=False)

    def _print(self, level, string, **kwargs):
        """Prints the string, typically to stdout."""
        # if level >= self._log_level:
        #     print("%s: %s" % (self.LOG_LEVELS.get(level), string))

    def log_message(self, string, level):
        self._print(level, string)

    def start(self, atta, **kwargs):
        """Starts this ATTA (i.e. before running a series of tests)."""

        if not self._enabled:
            return


        #
        # self._register_listener(pyia2.EVENT_OBJECT_FOCUS, atta._on_load_complete)
        # self._register_listener(pyia2.EVENT_OBJECT_STATECHANGE, atta._on_load_complete)
        # self._register_listener(pyia2.EVENT_OBJECT_SELECTION, atta._on_load_complete)
        # self._register_listener(pyia2.EVENT_OBJECT_SELECTIONREMOVE, atta._on_load_complete)
        # self._register_listener(pyia2.EVENT_OBJECT_NAMECHANGE, atta._on_load_complete)
        # self._register_listener(pyia2.EVENT_OBJECT_DESCRIPTIONCHANGE, atta._on_load_complete)

        # self._register_listener(pyia2.IA2_EVENT_DOCUMENT_LOAD_COMPLETE, atta._on_load_complete)
        # self._register_listener(pyia2.IA2_EVENT_ACTIVE_DESCENDANT_CHANGED, atta._on_load_complete)
        # self._register_listener(pyia2.IA2_EVENT_OBJECT_ATTRIBUTE_CHANGED, atta._on_load_complete)

        self._print(self.LOG_INFO,"[WIN_UIA_BASE][start]")

        if not self._enabled:
            self._print(self.LOG_ERROR, "Start failed because ATTA is not enabled.")
            return

        # faulthandler.enable(all_threads=False)
        # signal.signal(signal.SIGINT, self.shutdown)
        # signal.signal(signal.SIGTERM, self.shutdown)


        self._print(self.LOG_INFO, "Starting server on http://%s:%s/" % (self._host, self._port))
        self._server = HTTPServer((self._host, self._port), AttaRequestHandler)

        AttaRequestHandler.set_atta(self)


        if self._server_thread is None:
            self._server_thread = threading.Thread(target=self._server.serve_forever)
            self._server_thread.start()

        self._print(self.LOG_INFO, "[WIN_ATTA_BASE][start]: " + str(self._server_thread))
        # self.run_tests()
        print 'start was called'

    def get_info(self, **kwargs):
        """Returns a dict of details about this ATTA needed by the harness."""

        return {"ATTAname": self._atta_name,
                 "ATTAversion": self._atta_version,
                 "API": self._api_name,
                 "APIversion": self._api_version}
        print 'get_info was called'

    def is_enabled(self, **kwargs):
        """Returns True if this ATTA is enabled."""

        return self._enabled
        print 'is_enabled called'

    def is_ready(self, document=None, **kwargs):
        """Returns True if this ATTA is able to proceed with a test run."""

        # if self._ready:
        #     return True

        # test_name, test_uri = self._next_test
        # if test_name is None:
        #     return False

        # if self._accessible_document is None:
        #     return False

        # uri = self._accessible_document.uri

        # self._ready = uri and uri == test_uri

        # if self._ready:
        #     self._print(self.LOG_TEST_NAME, "%s" % test_name)
        #     self._print(self.LOG_TEST_URI,  "%s" % test_uri)

        # return self._ready
        return True
        print 'is_ready called'

    def start_test_run(self, name, url, **kwargs):
        """Sets the test details the ATTA should be looking for. The ATTA should
        update its "ready" status upon finding that file."""

#        self._print(self.LOG_INFO, "%s (%s)\n" % (name, url))

        self._next_test = name, url
        self._ready = False
        print 'start_test_run called'

    def end_test_run(self, **kwargs):
        """Cleans up cached information at the end of a test run."""

        self._accessible_document = None
        self._next_test = None, ""
        self._ready = False
        print 'end_test_run'


    def run_tests(self, obj_id, assertions):
        """Runs the assertions on the object with the specified id, returning
        a dict with the results, the status of the run, and any messages."""

        if not self.is_enabled():
            return {"status": self.STATUS_ERROR,
                    "message": self.FAILURE_ATTA_NOT_ENABLED,
                    "results": []}

        if not self.is_ready():
            return {"status": self.STATUS_ERROR,
                    "message": self.FAILURE_ATTA_NOT_READY,
                    "results": []}

        to_run = self._create_platform_assertions(assertions)

        # acc_elem = self._get_accessible_element_with_id(self._accessible_document, obj_id)
        self.mihirTest(assertions)
        print assertions
        acc_elem = self._accessible_element

        if not acc_elem:
            return {"status": self.STATUS_ERROR,
                    "message": self.FAILURE_ELEMENT_NOT_FOUND,
                    "results": []}

        results = [self._run_test(acc_elem, a) for a in to_run]

        return {"status": self.STATUS_OK,
                "results": results}
        print 'run_tests called'

    def start_listen(self, event_types, **kwargs):
        """Causes the ATTA to start listening for the specified events."""

        # self._monitored_event_types = []
        # self._event_history = []

        # for event_type in event_types:
        #     self._register_listener(event_type, self._on_test_event, **kwargs)
        #     self._monitored_event_types.append(event_type)
        print 'start listen called'

    def stop_listen(self, **kwargs):
        """Causes the ATTA to stop listening for the specified events."""

        # for event_type in self._monitored_event_types:
        #     self._deregister_listener(event_type, self._on_test_event, **kwargs)

        # self._monitored_event_types = []
        # self._event_history = []
        print 'stop_listen'

    def shutdown(self, atta, signum=None, frame=None, **kwargs):
        """Shuts down this ATTA (i.e. after all tests have been run)."""
        # self._deregister_listener(pyia2.EVENT_OBJECT_FOCUS, atta._on_load_complete)
        # self._deregister_listener(pyia2.EVENT_OBJECT_STATECHANGE, atta._on_load_complete)
        # self._deregister_listener(pyia2.EVENT_OBJECT_SELECTION, atta._on_load_complete)
        # self._deregister_listener(pyia2.EVENT_OBJECT_SELECTIONREMOVE, atta._on_load_complete)
        # self._deregister_listener(pyia2.EVENT_OBJECT_NAMECHANGE, atta._on_load_complete)
        # self._deregister_listener(pyia2.EVENT_OBJECT_DESCRIPTIONCHANGE, atta._on_load_complete)
        # self._deregister_listener(pyia2.IA2_EVENT_DOCUMENT_LOAD_COMPLETE, atta._on_load_complete)
        # self._deregister_listener(pyia2.IA2_EVENT_ACTIVE_DESCENDANT_CHANGED, atta._on_load_complete)
        # self._deregister_listener(pyia2.IA2_EVENT_OBJECT_ATTRIBUTE_CHANGED, atta._on_load_complete)

        # if not self._enabled:
        #     return

        # self._ready = False

        # try:
        #     signal_string = "on signal %s" % signal.Signals(signum).name
        # except AttributeError:
        #     signal_string = "on signal %s" % str(signum)
        # except:
        #     signal_string = ""
        # self._print(self.LOG_INFO, "Shutting down server %s" % signal_string)

        # if self._server is not None:
        #     thread = threading.Thread(target=self._server.shutdown)
        #     thread.start()
        print 'shutdown called'

    def get_relation_targets(self, obj, relation_type, **kwargs):
        """Returns the elements of pointed to by relation_type for obj."""

        # if not obj:
        #     raise AttributeError("Object not found")

        # self._print(self.LOG_DEBUG, "get_relation_targets() not implemented")
        print 'get_relation_targets called'

    def _get_rendering_engine(self, **kwargs):
        """Returns a string with details of the user agent's rendering engine."""

        print "_get_rendering_engine called"

    def _get_accessible_element_with_id(self, accessible_document, element_id, **kwargs):
        """Returns the accessible descendant of root with the specified id."""

        # if not element_id:
        #     return None

        # for elem in accessible_document.test_elements:
        #     if elem.test_id == element_id:
        #         return elem

        # return None
        print '_get_accessible_element_with_id called'

    def _get_id(self, obj, **kwargs):
        """Returns the element id associated with obj or an empty string upon failure."""

        # if obj is None:
        #     return ""

        # value = pyia2.get_id(obj)
        # if len(value) and self._last_id != value:
        #     self._last_id = value

        # return value
        print '_get_id called'

    def _get_children(self, obj, **kwargs):
        """Returns the children of obj or [] upon failure or absence of children."""

        # try:
        #     count = pyia2.get_child_count(obj)
        # except:
        #     self._print(self.LOG_ERROR, "[BASE][_get_children]" + self._on_exception())
        #     return []

#        print("[BASE][_get_children][obj][count]: " + str(count))

#         try:
#             children = pyia2.get_children(obj)
#         except:
#             self._print(self.LOG_ERROR, "[BASE][_get_children]" + self._on_exception())
#             return []

# #        print("[BASE][_get_children][obj][children]: " + str(children))

#         return children
        print 'get_children called'

    def get_property_value(self, acc_elem, property_name, **kwargs):
        """Returns the value of property_name for obj."""

        # if not acc_elem and property_name != "accessible":
        #     raise AttributeError("Object not found")

        # remember to remove self._elem_details data structure and all its assignments!
        value = str()
        print 'property_name: ' + property_name

        try:
            if property_name == 'ControlType':
                value = acc_elem.ControlTypeName[:-7]

            elif property_name == acc_elem.ControlTypeName[:-7] + '.ColumnCount':
                value = str(acc_elem.CurrentColumnCount())

            elif property_name == acc_elem.ControlTypeName[:-7] + '.RowCount':
                value = str(acc_elem.CurrentRowCount())

            elif property_name == acc_elem.ControlTypeName[:-7] + '.Row':
                value = str(acc_elem.CurrentRow())

            elif property_name == acc_elem.ControlTypeName[:-7] + '.Column':
                value = str(acc_elem.CurrentColumn())

            elif property_name == acc_elem.ControlTypeName[:-7] + '.ColumnSpan':
                value = str(acc_elem.CurrentColumnSpan())

            elif property_name == acc_elem.ControlTypeName[:-7] + '.RowSpan':
                value = str(acc_elem.CurrentRowSpan())

            elif property_name == 'IUIAutomationElement.Orientation':
                print 'IUIAutomationElement.Orientation: '
                print type(acc_elem.GetCurrentSelection())
                value = str(acc_elem.GetCurrentSelection())

            elif property_name == 'Value.IsReadOnly':
                try:
                    value = str(acc_elem.CurrentIsReadOnly())
                except:
                    # value = acc_elem.CurrentIsReadOnly()
                    print "Can't get acc_elem.CurrentIsReadOnly()"

            # if property_name == 'role':
            #     if self._api_name == 'IAccessible2':
            #         value =  acc_elem.ia2_role
            #     else:
            #         value =  acc_elem.role
            # if property_name == 'accName':
            #     value =  acc_elem.accName
            # if property_name == 'accValue':
            #     value =  acc_elem.accValue
            # if property_name == 'accDescription':
            #     value =  acc_elem.accDescription
            # if property_name == 'objectAttributes':
            #     value =  acc_elem.objectAttributes
            # if property_name == 'textAttributes':
            #     value =  acc_elem.textAttributes
            # if property_name == 'states':
            #     value =  acc_elem.states
            # if property_name == 'relations':
            #     value =  acc_elem.relations
            # if property_name == 'interfaces':
            #     value =  acc_elem.interfaces
            # if property_name == 'minimumValue':
            #     value =  acc_elem.ia2_value_min
            # if property_name == 'currentValue':
            #     value =  acc_elem.ia2_value_current
            # if property_name == 'maximumValue':
            #     value =  acc_elem.ia2_value_max
            # if property_name == 'groupPosition':
            #     value =  acc_elem.groupPosition
            # if property_name == 'localizedExtendedRole':
            #     value =  acc_elem.localizedExtendedRole
            # if property_name == 'accKeyboardShortcut':
            #     value =  acc_elem.accKeyboardShortcut
            # if property_name == 'columnExtent':
            #     value =  acc_elem.columnExtent
            # if property_name == 'rowExtent':
            #     value =  acc_elem.rowExtent

        except:
            print 'entered except line 457'
            self._print(self.LOG_ERROR, "[BASE][get_property_value][except]" + self._on_exception())
            value = []

        #self._print(self.LOG_INFO, "[BASE][get_property_value][" + property_name + "]: " + str(value))
        print 'Value: ' + value
        return value

    def get_bug(self, assertion_string, expected_result, actual_result, **kwargs):
        """Returns a string containing bug information for an assertion."""

        # test_name = self._next_test[0]
        # if not test_name:
        #     return ""

        # engine = self._get_rendering_engine()
        # if engine != "Gecko":
        #     return ""

        # return ""
        print "get_bug called"

    def _on_test_event(self, data, **kwargs):
        """Callback for platform accessibility events the ATTA is testing."""

#        try:
#            pyia2.com_coinitialize()
#        except:
#            print('[IA2][_on_test_event]: error cointializing')

        # if not self._in_current_document(data.source):
        #     return

        # event_as_dict = {
        #     "obj": data.source,
        #     "type": data.type,
        #     "detail1": data.detail1,
        #     "detail2": data.detail2,
        #     "any_data": data.any_data
        # }

        # self._event_history.append(event_as_dict)
        print '_on_test_event called'

    def _in_current_document(self, obj, **kwargs):
        """Returns True if obj is an element in the current test's document."""

        # if not self._current_document:
        #     return False

        # pred = lambda x: x == self._current_document
        # return self._find_ancestor(obj, pred, **kwargs) is not None
        print '_in_current_document called'

    def _find_ancestor(self, obj, pred, **kwargs):
        """Returns the ancestor of obj for which pred returns True."""

        # if obj is None:
        #     return None

        # parent = self._get_parent(obj)
        # while parent:
        #     if pred(parent):
        #         return parent
        #     parent = self._get_parent(parent)

        # return None
        print '_find_ancestor called'

    def _find_descendant(self, root, pred, **kwargs):
        """Returns the descendant of root for which pred returns True."""

        # if pred(root) or root is None:
        #     return root

        # children = self._get_children(root, **kwargs)
        # for child in children:
        #     element = self._find_descendant(child, pred, **kwargs)
        #     if element:
        #         return element

        # return None
        print '_find_descendant called'

    def _get_system_api_version(self, **kwargs):
        """Returns a string with the installed version of the accessibility API."""
        print '_get_system_api_version called'
        return "Version Unknown"

    def _get_accessibility_enabled(self, **kwargs):
        """Returns True if accessibility support is enabled on this platform."""

        # For Microsoft Windows assume accessibility is always enabled
        # enabled = True
        # return enabled
        print '_get_accessibility_enabled called'

    def _set_accessibility_enabled(self, enable, **kwargs):
        """Returns True if accessibility support was successfully set."""

        # For Microsoft Windows assume accessibility is always enabled
        # success = True
        # return success
        print '_set_accessibility_enabled called'

    # def _register_listener(self, event_type, callback, **kwargs):
    #     """Registers an accessible-event listener on the platform."""

    #     pyia2.Registry.registerEventListener(callback, event_type)

    # def _deregister_listener(self, event_type, callback, **kwargs):
    #     """De-registers an accessible-event listener on the platform."""

    #     pyia2.Registry.deregisterEventListener(callback, event_type)

    def _get_assertion_test_class(self, assertion, **kwargs):
        """Returns the appropriate Assertion class for assertion."""
        print '_get_assertion_test_class called'
        return AttaAssertion.get_test_class(assertion)


    def _create_platform_assertions(self, assertions, **kwargs):
        """Performs platform-specific changes needed to harness assertions."""

        is_event = lambda x: x and x[0] == "event"
        event_assertions = list(filter(is_event, assertions))
        # We don't need these event assertions so always return assertions
        return assertions

        if not event_assertions:
            return assertions

        platform_assertions = list(filter(lambda x: x not in event_assertions, assertions))

        # The properties associated with accessible events are currently given to
        # us as individual subtests. Unlike other assertions, event properties are
        # not independent of one another. Because these should be tested as an all-
        # or-nothing assertion, we'll combine the subtest values into a dictionary
        # passed along with each subtest.
        properties = {}
        for test, name, verb, value in event_assertions:
            properties[name] = value

        combined_event_assertions = ["event", "event", "contains", properties]
        platform_assertions.append(combined_event_assertions)
        print 'printing platform_assertions: '
        print platform_assertions
        return platform_assertions

    def _run_test(self, acc_elem, assertion, **kwargs):
        """Runs a single assertion on accessible element object, returning a results dict."""

        bug = ""
        test_class = self._get_assertion_test_class(assertion)

        if test_class is None:
            result = AttaAssertion.STATUS_FAIL
            message = "ERROR: %s is not a valid assertion" % assertion
            log = message
        else:
            test = test_class(acc_elem, assertion, self)
            result, message, log = test.run()
            if result == AttaAssertion.STATUS_FAIL:
                bug = test.get_bug()

        test_file = urlparse(self._next_test[1]).path

        status_results = self._results.get(bug or result, {})

        file_results = status_results.get(test_file, [])

        file_results.append(" ".join(map(str, assertion)))

        status_results[test_file] = file_results

        self._results[bug or result] = status_results

        if not self._ansi_formatting:
            formatting = self.FORMAT_NONE
        elif result == AttaAssertion.STATUS_PASS:
            formatting = self.FORMAT_GOOD
        elif not test_class:
            formatting = self.FORMAT_BAD
        elif result == AttaAssertion.STATUS_FAIL:
            if bug:
                formatting = self.FORMAT_WARNING
            else:
                formatting = self.FORMAT_BAD
        else:
            formatting = self.FORMAT_WARNING

        string = " ".join(map(str, assertion))
        if message:
            string = "%s %s" % (string, message)

        if result == AttaAssertion.STATUS_PASS:
            self._print(self.LOG_RESULT_PASS, "%s" % string)
        else:
            self._print(self.LOG_RESULT_FAIL, "%s" % string)

        return {"result": result, "message": message, "log": log}



#     def _get_uri(self, document, **kwargs):
#         """Returns the URI associated with document or an empty string upon failure."""

#         if document is None:
#             return ""

#         if pyia2.get_name(document):
#             return  pyia2.get_value(document)

#         return ""


#     def _get_parent(self, obj, **kwargs):
#         """Returns the parent of obj or None upon failure."""

#         try:
#             parent = pyia2.get_parent(obj)
#         except:
#             self._print(self.LOG_ERROR, "[BASE][_get_parent]" + self._on_exception())
#             return None

#         return parent

#     def _on_load_complete(self, event):
#         """Callback for the platform's signal that a document has loaded."""

# #        self._print(self.LOG_INFO, "[BASE][_on_load_complete][event.type]" + str(event.type))

#         if event.type == pyia2.IA2_EVENT_DOCUMENT_LOAD_COMPLETE:
#             ao = pyia2.accessibleObjectFromEvent(event)
#             self._accessible_document = pyia2.AccessibleDocument(ao)
#         else:
#             if self._accessible_document:
#                 if self._accessible_document.addEvent(event.type):
# #                    self._print(self.LOG_INFO, "[BASE][_on_load_complete][events]" + str(self._accessible_document.events))
#                     self._accessible_document.updateTestElements()

    def _on_test_event(self, data, **kwargs):
        """Callback for platform accessibility events the ATTA is testing."""
        if not self._in_current_document(data.source):
            return

        event_as_dict = {
            "obj": data.source,
            "type": data.type,
            "detail1": data.detail1,
            "detail2": data.detail2,
            "any_data": data.any_data
        }

        self._event_history.append(event_as_dict)
        print '_on_test_event called'

    # Mihir Kumar 1/10/18
    # Helper functions

    def mihirEnumAndLogControl(self, control, assertions, maxDepth = 0xFFFFFFFF, showAllName = True, showMore = False):
        """
        control: Control
        maxDepth: integer
        showAllName: bool
        showMore: bool
        """

        for c, d in self.mihirWalkControl(control, True, maxDepth):
            self.mihirLogControl(c, assertions, d, showAllName, showMore)

    def mihirWalkControl(self, control, includeTop = False, maxDepth = 0xFFFFFFFF):
        """
        control: Control
        maxDepth: integer
        yield 2 items tuple(Control, depth)
        """
        if includeTop:
            yield control, 0
        if maxDepth <= 0:
            return
        depth = 0
        child = control.GetFirstChildControl()
        controlList = [child]
        while depth >= 0:
            lastControl = controlList[-1]
            if lastControl:
                yield lastControl, depth + 1
                child = lastControl.GetNextSiblingControl()
                controlList[depth] = child
                if depth + 1 < maxDepth:
                    child = lastControl.GetFirstChildControl()
                    if child:
                        depth += 1
                        controlList.append(child)
            else:
                del controlList[depth]
                depth -= 1

    def mihirLogControl(self, control, assertions, depth = 0, showAllName = True, showMore = False):
        """
        control: Control
        depth: integer
        showAllName: bool
        showMore: bool
        """

        # print 'control.AutomationId: ' + control.AutomationId
        # print 'control.ControlTypeName: ' + control.ControlTypeName

        # AutomationIds can be: 'cell', 'test'

        if control.AutomationId != 'test' and control.AutomationId != 'cell':
            return

        def getKeyName(theDict, theValue):
            for key in theDict:
                if theValue == theDict[key]:
                    return key
        name = control.Name
        if not showAllName and name and len(name) > 30:
            name = name[:30] + '...'
        indent = ' ' * depth * 4

        self._accessible_element = control

        Logger.Write('{0}ControlType: '.format(indent))
        Logger.Write(control.ControlTypeName, ConsoleColor.DarkGreen)

        Logger.Write('    ClassName: ')
        Logger.Write(control.ClassName, ConsoleColor.DarkGreen)

        Logger.Write('    AutomationId: ')
        Logger.Write(control.AutomationId, ConsoleColor.DarkGreen)

        Logger.Write('    Rect: ')
        left, top, right, bottom = control.BoundingRectangle
        Logger.Write(str(control.BoundingRectangle), ConsoleColor.DarkGreen)

        Logger.Write('    Name: ')
        Logger.Write(name, ConsoleColor.DarkGreen)

        Logger.Write('    Handle: ')
        Logger.Write('0x{0:X}({0})'.format(control.Handle), ConsoleColor.DarkGreen)

        Logger.Write('    Depth: ')
        Logger.Write(str(depth), ConsoleColor.DarkGreen)

        if ((isinstance(control, ValuePattern) and control.IsValuePatternAvailable())):
            Logger.Write('    Value: ')
            Logger.Write(control.CurrentValue(), ConsoleColor.DarkGreen)

        if ((isinstance(control, RangeValuePattern) and control.IsRangeValuePatternAvailable())):
            Logger.Write('    RangeValue: ')
            Logger.Write(str(control.RangeValuePatternCurrentValue()), ConsoleColor.DarkGreen)

        if isinstance(control, TogglePattern) and control.IsTogglePatternAvailable():
            Logger.Write('    CurrentToggleState: ')
            Logger.Write('ToggleState.' + getKeyName(ToggleState.__dict__, control.CurrentToggleState()), ConsoleColor.DarkGreen)

        if isinstance(control, SelectionItemPattern) and control.IsSelectionItemPatternAvailable():
            Logger.Write('    CurrentIsSelected: ')
            Logger.Write(str(control.CurrentIsSelected()), ConsoleColor.DarkGreen)

        if isinstance(control, ExpandCollapsePattern) and control.IsExpandCollapsePatternAvailable():
            Logger.Write('    CurrentExpandCollapseState: ')
            Logger.Write('ExpandCollapseState.' + getKeyName(ExpandCollapseState.__dict__, control.CurrentExpandCollapseState()), ConsoleColor.DarkGreen)

        if isinstance(control, ScrollPattern) and control.IsScrollPatternAvailable():
            Logger.Write('    CurrentHorizontalViewSize: ')
            Logger.Write(str(control.CurrentHorizontalViewSize()), ConsoleColor.DarkGreen)

            Logger.Write('    CurrentVerticalViewSize: ')
            Logger.Write(str(control.CurrentVerticalViewSize()), ConsoleColor.DarkGreen)

            Logger.Write('    CurrentHorizontalScrollPercent: ')
            Logger.Write(str(control.CurrentHorizontalScrollPercent()), ConsoleColor.DarkGreen)

            Logger.Write('    CurrentVerticalScrollPercent: ')
            Logger.Write(str(control.CurrentVerticalScrollPercent()), ConsoleColor.DarkGreen)

        if isinstance(control, GridPattern) and control.IsGridPatternAvailable():
            Logger.Write('    RowCount: ')
            Logger.Write(str(control.CurrentRowCount()), ConsoleColor.DarkGreen)

            Logger.Write('    ColumnCount: ')
            Logger.Write(str(control.CurrentColumnCount()), ConsoleColor.DarkGreen)

        if isinstance(control, GridItemPattern) and control.IsGridItemPatternAvailable():
            Logger.Write('    Row: ')
            Logger.Write(str(control.CurrentRow()), ConsoleColor.DarkGreen)

            Logger.Write('    Column: ')
            Logger.Write(str(control.CurrentColumn()), ConsoleColor.DarkGreen)

        if showMore:
            Logger.Write('    SupportedPattern:')
            for key in PatternDict:
                pattern = _AutomationClient.instance().dll.GetElementPattern(control.Element, key)
                if pattern:
                    _AutomationClient.instance().dll.ReleasePattern(pattern)
                    Logger.Write(' ' + PatternDict[key], ConsoleColor.DarkGreen)

        Logger.Write(Logger.LineSep)

    def mihirTest(self, assertions):
        ancestor = False
        showAllName = False
        showMore = False
        depth = 0xFFFFFFFF
        wait_time_in_seconds = 5

        edgeWindow = WindowControl(searchDepth = 1, ClassName = 'ApplicationFrameWindow')

        control = edgeWindow

        if WaitForExist(edgeWindow, wait_time_in_seconds):
            Logger.WriteLine("There is an Edge window open :D", ConsoleColor.Green)
        else:
            Logger.WriteLine("There is no Edge window open :(", ConsoleColor.Red)

        control = edgeWindow
        controlList = []
        while control:
            controlList.insert(0, control)
            control = control.GetParentControl()
        if len(controlList) == 1:
            control = controlList[0]
        else:
            control = controlList[1]

        self.mihirEnumAndLogControl(control, assertions, depth, showAllName, showMore)

        Logger.Log('Ends\n')


def get_cmdline_options():
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", action="store")
    parser.add_argument("--port", action="store")
    parser.add_argument("--ansi-formatting", action="store_true")
    return vars(parser.parse_args())
