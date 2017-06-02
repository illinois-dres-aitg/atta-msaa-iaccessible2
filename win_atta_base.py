#!/usr/bin/env python27
#
# win_atta_base
# Optional base class for python27 Accessible Technology Test Adapters
#
# Developed by Jon Gunderson, Bei Zhang and Naijing Zhang 
# Copyright (c) 2017 University of Illinois
# Based on the ATTAs developed by Joanmarie Diggs (@joanmarie)
#
# For license information, see:
# https://www.w3.org/Consortium/Legal/2008/04-testsuite-copyright.html

import faulthandler
import signal
import sys
import threading
import traceback


from BaseHTTPServer import HTTPServer
from win_atta_assertion import AttaAssertion
from win_atta_request_handler import AttaRequestHandler

import pyia2


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
    LOG_NONE = 100

    LOG_LEVELS = {
        LOG_DEBUG: "DEBUG",
        LOG_INFO: "INFO",
        LOG_WARNING: "WARNING",
        LOG_ERROR: "ERROR",
    }

    FORMAT_NONE = "%(label)s%(msg)s"
    FORMAT_NORMAL = "\x1b[1m%(label)s\x1b[22m%(msg)s\x1b[0m"
    FORMAT_GOOD = "\x1b[32;1m%(label)s\x1b[22m%(msg)s\x1b[0m"
    FORMAT_WARNING = "\x1b[33;1m%(label)s\x1b[22m%(msg)s\x1b[0m"
    FORMAT_BAD = "\x1b[31;1m%(label)s\x1b[22m%(msg)s\x1b[0m"

    def __init__(self, host, port, name, version, api, log_level=None):
        """Initializes this ATTA."""

        self._log_level = log_level or self.LOG_DEBUG
        self._host = host
        self._port = int(port)
        self._server = None
        self._server_thread = None
        self._atta_name = name
        self._atta_version = version
        self._api_name = api
        self._api_version = ""
        self._enabled = False
        self._ready = False
        self._next_test = None, ""
        self._current_document_event = None
        self._current_document = None
        self._current_uri = ""
        self._monitored_event_types = []
        self._event_history = []
        self._listeners = {}

        if not sys.version_info[0] == 2:
            self._print(self.LOG_ERROR, "This ATTA requires Python 2.7.")
            return

# TODO: Is this information needed?
#        self._api_version = self._get_system_api_version()

#        if not self._get_accessibility_enabled() \
#           and not self._set_accessibility_enabled(True):
#            return

        self._enabled = True

    @staticmethod
    def _on_exception():
        """Handles exceptions, returning a string with the error."""

        return "EXCEPTION: %s" % traceback.format_exc(limit=1, chain=False)

    def _print(self, level, string, **kwargs):
        """Prints the string, typically to stdout."""

        if level >= self._log_level:
            print("%s: %s" % (self.LOG_LEVELS.get(level), string))

    def log_message(self, string, level):
        self._print(level, string)

    def start(self, **kwargs):
        """Starts this ATTA (i.e. before running a series of tests)."""

        self._print(self.LOG_INFO,"[WIN_ATTA_BASE][start]")

        if not self._enabled:
            self._print(self.LOG_ERROR, "Start failed because ATTA is not enabled.")
            return

        faulthandler.enable(all_threads=False)
        signal.signal(signal.SIGINT, self.shutdown)
        signal.signal(signal.SIGTERM, self.shutdown)


        self._print(self.LOG_INFO, "Starting server on http://%s:%s/" % (self._host, self._port))
        self._server = HTTPServer((self._host, self._port), AttaRequestHandler)
        
        AttaRequestHandler.set_atta(self)


        if self._server_thread is None:
            self._server_thread = threading.Thread(target=self._server.serve_forever)
            self._server_thread.start()

        self._print(self.LOG_INFO, "[WIN_ATTA_BASE][start]: " + str(self._server_thread))

    def get_info(self, **kwargs):
        """Returns a dict of details about this ATTA needed by the harness."""

        return {"ATTAname": self._atta_name,
                "ATTAversion": self._atta_version,
                "API": self._api_name,
                "APIversion": self._api_version}

    def is_enabled(self, **kwargs):
        """Returns True if this ATTA is enabled."""

        return self._enabled

    def is_ready(self, document=None, **kwargs):
        """Returns True if this ATTA is able to proceed with a test run."""

        print('[BASE][is_ready][A][_ready]: ' + str(self._ready))    

        try:
            pyia2.com_coinitialize()
        except:
            print('[_is_ready]: error cointializing')

        print('[BASE][is_ready][B][_ready]: ' + str(self._ready))    

        if self._ready:
            return True

        test_name, test_uri = self._next_test
        print('[BASE][is_ready][C][test_name]: ' + str(test_name))    
        print('[BASE][is_ready][C][test_uri]:  ' + str(test_uri))    

        if test_name is None:
            return False

        # need to get the current IAccessible for document here because of theading issues
        if self._current_document_event:
            self._current_document = pyia2.accessibleObjectFromEvent(self._current_document_event)

        document = document or self._current_document
        if document is None:
            return False

        print('[BASE][is_ready][D][document]: ' + str(document))    
        print('[BASE][is_ready][D][children]: ' + str(pyia2.get_children(document)))    

        uri = pyia2.get_value(document)
        print('[BASE][is_ready][D][uri]: ' + str(uri))    

        self._ready = uri and uri == test_uri

        if self._ready:
            self._current_document = document
            self._print(self.LOG_INFO, "Test is '%s' (%s)" % (test_name, test_uri))

        print('[BASE][is_ready][E][_ready]: ' + str(self._ready))    

        return self._ready

    def start_test_run(self, name, url, **kwargs):
        """Sets the test details the ATTA should be looking for. The ATTA should
        update its "ready" status upon finding that file."""

        self._print(self.LOG_INFO, "%s (%s)" % (name, url) + "\n[BASE][start_test_run] ")

        self._next_test = name, url
        self._ready = False

    def start_listen(self, event_types, **kwargs):
        """Causes the ATTA to start listening for the specified events."""

        self._monitored_event_types = []
        self._event_history = []

        for event_type in event_types:
            self._register_listener(event_type, self._on_test_event, **kwargs)
            self._monitored_event_types.append(event_type)

    def run_tests(self, obj_id, assertions):
        """Runs the assertions on the object with the specified id, returning
        a dict with the results, the status of the run, and any messages."""

        print("[BASE][run_tests][A]")

        if not self.is_enabled():
            return {"status": self.STATUS_ERROR,
                    "message": self.FAILURE_ATTA_NOT_ENABLED,
                    "results": []}

        if not self.is_ready():
            return {"status": self.STATUS_ERROR,
                    "message": self.FAILURE_ATTA_NOT_READY,
                    "results": []}

        print("[BASE][run_tests][B]")

        to_run = self._create_platform_assertions(assertions)
        print("[BASE][run_tests][C][to_run]: " + str(to_run))

        obj = self._get_element_with_id(self._current_document, obj_id)

        print("[BASE][run_tests][D][obj]: " + str(obj))

        if not obj:
            return {"status": self.STATUS_ERROR,
                    "message": self.FAILURE_ELEMENT_NOT_FOUND,
                    "results": []}

        results = [self._run_test(obj, a) for a in to_run]

        print("[BASE][run_tests][E][results]: " + str(results))

        return {"status": self.STATUS_OK,
                "results": results}

    def stop_listen(self, **kwargs):
        """Causes the ATTA to stop listening for the specified events."""

        for event_type in self._monitored_event_types:
            self._deregister_listener(event_type, self._on_test_event, **kwargs)

        self._monitored_event_types = []
        self._event_history = []

    def end_test_run(self, **kwargs):
        """Cleans up cached information at the end of a test run."""

        self._current_document = None
        self._next_test = None, ""
        self._ready = False

    def shutdown(self, signum=None, frame=None, **kwargs):
        """Shuts down this ATTA (i.e. after all tests have been run)."""

        if not self._enabled:
            return

        self._ready = False

        try:
            signal_string = "on signal %s" % signal.Signals(signum).name
        except AttributeError:
            signal_string = "on signal %s" % str(signum)
        except:
            signal_string = ""
        self._print(self.LOG_INFO, "Shutting down server %s" % signal_string)

        if self._server is not None:
            thread = threading.Thread(target=self._server.shutdown)
            thread.start()

    def _get_element_with_id(self, root, element_id, **kwargs):
        """Returns the accessible descendant of root with the specified id."""

        print("[BASE][_get_element_with_id][root]: " + str(root))
        print("[BASE][_get_element_with_id][root][role]: " + pyia2.get_role(root))
        print("[BASE][_get_element_with_id][root][childCount]: " + str(pyia2.get_child_count(root)))
        print("[BASE][_get_element_with_id][element_id]: " + str(element_id))

        if not element_id:
            return None

        pred = lambda x: self._get_id(x) == element_id

        elem =  self._find_descendant(root, pred, **kwargs)

        print("[BASE][_get_element_with_id][elem]: " + str(elem))

        return elem

    def _in_current_document(self, obj, **kwargs):
        """Returns True if obj is an element in the current test's document."""

        if not self._current_document:
            return False

        pred = lambda x: x == self._current_document
        return self._find_ancestor(obj, pred, **kwargs) is not None

    def _find_ancestor(self, obj, pred, **kwargs):
        """Returns the ancestor of obj for which pred returns True."""

        if obj is None:
            return None

        parent = self._get_parent(obj)
        while parent:
            if pred(parent):
                return parent
            parent = self._get_parent(parent)

        return None

    def _find_descendant(self, root, pred, **kwargs):
        """Returns the descendant of root for which pred returns True."""

        if pred(root) or root is None:
            return root

        children = self._get_children(root, **kwargs)
#        print('[_find_descendant][childern]: ' + str(children))
        for child in children:
#            print('[_find_descendant][child]: ' + str(child))
#            print('[_find_descendant][child][role]: ' + pyia2.get_role(child))
#            print('[_find_descendant][child][name]: ' + pyia2.get_name(child))
            element = self._find_descendant(child, pred, **kwargs)
            if element:
                return element

        return None

    def _get_system_api_version(self, **kwargs):
        """Returns a string with the installed version of the accessibility API."""


        self._print(self.LOG_DEBUG, "_get_system_api_version() not implemented")
        return ""

    def _get_accessibility_enabled(self, **kwargs):
        """Returns True if accessibility support is enabled on this platform."""

        self._print(self.LOG_DEBUG, "_get_accessibility_enabled() not implemented")
        return False

    def _set_accessibility_enabled(self, enable, **kwargs):
        """Returns True if accessibility support was successfully set."""

        self._print(self.LOG_DEBUG, "_set_accessibility_enabled() not implemented")
        return False

    def _register_listener(self, event_type, callback, **kwargs):
        """Registers an accessible-event listener on the platform."""

        self._print(self.LOG_DEBUG, "_register_listener() not implemented")

    def _deregister_listener(self, event_type, callback, **kwargs):
        """De-registers an accessible-event listener on the platform."""

        self._print(self.LOG_DEBUG, "_deregister_listener() not implemented")

    def _create_platform_assertions(self, assertions, **kwargs):
        """Performs platform-specific changes needed to harness assertions."""

        is_event = lambda x: x and x[0] == "event"
        event_assertions = list(filter(is_event, assertions))
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
        return platform_assertions

    def _run_test(self, obj, assertion, **kwargs):
        """Runs a single assertion on obj, returning a results dict."""

        bug = ""
        test_class = self._get_assertion_test_class(assertion)
        if test_class is None:
            result = AttaAssertion.STATUS_FAIL
            message = "ERROR: %s is not a valid assertion" % assertion
            log = message
        else:
            test = test_class(obj, assertion, self)
            result, message, log = test.run()
            if result == AttaAssertion.STATUS_FAIL:
                bug = test.get_bug()

        test_file = parse.urlsplit(self._next_test[1]).path
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

        self._print(self.LOG_INFO, string, "%s: " % result, formatting)
        return {"result": result, "message": message, "log": log}



    def _get_uri(self, document, **kwargs):
        """Returns the URI associated with document or an empty string upon failure."""

        self._print(self.LOG_DEBUG, "_get_uri() not implemented")
        return ""


    def _get_parent(self, obj, **kwargs):
        """Returns the parent of obj or None upon failure."""

        self._print(self.LOG_DEBUG, "_get_parent() not implemented")
        return None

    def _on_load_complete(self, data, **kwargs):
        """Callback for the platform's signal that a document has loaded."""

        self._print(self.LOG_DEBUG, "_on_load_complete() not implemented")

    def _on_test_event(self, data, **kwargs):
        """Callback for platform accessibility events the ATTA is testing."""
        self._print(self.LOG_DEBUG, "_on_test_event() not implemented")
