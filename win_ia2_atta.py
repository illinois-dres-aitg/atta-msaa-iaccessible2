#!/usr/bin/env python27
#
# ia2_atta
#
# Accessible Technology Test Adapter for MSAA+IAccessible2
# Tests MSAA+IAccessible2 (server-side) implementations via MSAA+IAccessible2 (client-side)
#
# Developed by Jon Gunderson, Bei Zhang and Naijing Zhang 
# Copyright (c) 2017 University of Illinois
# Based on the ATTAs developed by Joanmarie Diggs (@joanmarie)
#
# For license information, see:
# https://www.w3.org/Consortium/Legal/2008/04-testsuite-copyright.html

import argparse
import re
import sys
import threading

from win_atta_base import Atta

import pyia2
from pyia2.utils import IA2Lib


class IA2Atta(Atta):
    """Accessible Technology Test Adapter to test IAccessible2 support."""

    def __init__(self, host, port, ansi_formatting, name="ATTA for IA2", version="0.5", api="IAccessible2"):
        """Initializes this ATTA."""

        self._listener_thread = None
        self._proxy = None
        self._interfaces = []
        self._last_id = ""

        try:
            #Atspi.get_desktop(0)
            # TODO: IA2 get_desktop?
            print("need get desktop?")
        except:
            self._print(self.LOG_ERROR, "Could not get desktop from IA2.")
            self._enabled = False
            return

        #self._interfaces = list(filter(lambda x: gir.find_by_name("Atk", x), ifaces))
        # TODO: self._interfaces neede?

        self._supported_properties = {
            "accessible": lambda x: x is not None,
            "childCount": pyia2.get_child_count,
            "description": pyia2.get_description,
            "name": pyia2.get_name,
#            "interfaces": pyia2.get_interfaces,
            "objectAttributes": pyia2.get_ia2_attributes_as_array,
            "parent": pyia2.get_parent,
            "relations": pyia2.get_relation_set,
            "role": pyia2.get_ia2_role,
            "states": pyia2.get_ia2_state_set,
        }

        super(IA2Atta, self).__init__(host, port, name, version, api, Atta.LOG_INFO)

    def start(self, atta, **kwargs):
        """Starts this ATTA (i.e. before running a series of tests)."""

        if not self._enabled:
            return

        self._register_listener(pyia2.IA2_EVENT_DOCUMENT_LOAD_COMPLETE, atta._on_load_complete)

        super(IA2Atta, self).start(**kwargs)
        return

    def _run_test(self, obj, assertion, **kwargs):
        """Runs a single assertion on obj, returning a results dict."""

        return super(IA2Atta, self)._run_test(obj, assertion, **kwargs)

    def shutdown(self, signum=None, frame=None, **kwargs):
        """Shuts down this ATTA (i.e. after all tests have been run)."""

        if not self._enabled:
            return

        super(IA2Atta, self).shutdown(signum, frame, **kwargs)

    def _get_rendering_engine(self, **kwargs):
        """Returns a string with details of the user agent's rendering engine."""

        if not self._current_document:
            return ""

        return "Rendering engine unknown"

    def _get_system_api_version(self, **kwargs):
        """Returns a string with the installed version of the accessibility API."""

        return "Version Unknown"


    def _get_accessibility_enabled(self, **kwargs):
        """Returns True if accessibility support is enabled on this platform."""

        # For Microsoft Windows assume accessibility is always enabled
        enabled = True
        return enabled

    def _set_accessibility_enabled(self, enable, **kwargs):
        """Returns True if accessibility support was successfully set."""

        # For Microsoft Windows assume accessibility is always enabled
        success = True
        return success

    def _register_listener(self, event_type, callback, **kwargs):
        """Registers an accessible-event listener on the platform."""

        print("registered: A")
        pyia2.Registry.registerEventListener(callback, event_type)
        print("registered: B")


    def _deregister_listener(self, event_type, callback, **kwargs):
        """De-registers an accessible-event listener on the platform."""

        pyia2.Registry.deregisterEventListener(callback, event_type)

    def _get_id(self, obj, **kwargs):
        """Returns the element id associated with obj or an empty string upon failure."""

        if obj is None:
            return ""

        value = pyia2.get_id(obj)    
        if len(value) and self._last_id != value:
            print('[_get_id]: ' + value)
            self._last_id = value

        return value   


    def _get_uri(self, document, **kwargs):
        """Returns the URI associated with document or an empty string upon failure."""

        if document is None:
            return ""

        if pyia2.get_name(document):
            return  pyia2.get_value(document)

        return ""

    def _get_children(self, obj, **kwargs):
        """Returns the children of obj or [] upon failure or absence of children."""


        try:
            count = pyia2.get_child_count(obj)
        except:
            self._print(self.LOG_ERROR, "[IA2][_get_children]" + self._on_exception())
            return []

#        print("[IA2][_get_children][obj][count]: " + str(count))

        try:
            children = pyia2.get_children(obj)
        except:
            self._print(self.LOG_ERROR, "[IA2][_get_children]" + self._on_exception())
            return []

#        print("[IA2][_get_children][obj][children]: " + str(children))

        return children

    def _get_parent(self, obj, **kwargs):
        """Returns the parent of obj or None upon failure."""

        try:
            parent = pyia2.get_parent(obj)
        except:
            self._print(self.LOG_ERROR, "[IA2][_get_parent]" + self._on_exception())
            return None

        return parent

    def get_property_value(self, obj, property_name, **kwargs):
        """Returns the value of property_name for obj."""

        if not obj and property_name != "accessible":
            raise AttributeError("Object not found")

        getter = self._supported_properties.get(property_name)
        if getter is None:
            raise ValueError("Unsupported property: %s" % property_name)

        return getter(obj)

    def get_relation_targets(self, obj, relation_type, **kwargs):
        """Returns the elements of pointed to by relation_type for obj."""

        if not obj:
            raise AttributeError("Object not found")

        self._print(self.LOG_DEBUG, "get_relation_targets() not implemented")




    def get_bug(self, assertion_string, expected_result, actual_result, **kwargs):
        """Returns a string containing bug information for an assertion."""

        test_name = self._next_test[0]
        if not test_name:
            return ""

        engine = self._get_rendering_engine()
        if engine != "Gecko":
            return ""

        return ""

    def _on_load_complete(self, event):
        """Callback for the platform's signal that a document has loaded."""

#        self._print(self.LOG_DEBUG, self._get_uri(data.source), "LOADED: ")
#        if self.is_ready(data.source):
#            application = Atspi.Accessible.get_application(data.source)
#            Atspi.Accessible.set_cache_mask(application, Atspi.Cache.DEFAULT)

#        try:
#            pyia2.com_coinitialize()
#        except:
#            print('[_on_load_complete]: error cointializing')

        print("[_on_load_complete]: Start")
        self._current_document_event   = event
        self._current_document = pyia2.accessibleObjectFromEvent(event)
        print("[_on_load_complete] _current_document_event:      " + str(self._current_document_event))
        print("[_on_load_complete] current_document_iaccesible: " + str(self._current_document))

        if  self._current_document:
            self._current_role        = pyia2.get_role(self._current_document)
            self._current_uri         = pyia2.get_value(self._current_document)
            self._current_name        = pyia2.get_name(self._current_document)
            self._current_child_count = pyia2.get_child_count(self._current_document)
            self._current_children    = pyia2.get_children(self._current_document)
            print("[_on_load_complete][_current_role]:        " + self._current_role)
            print("[_on_load_complete][_current_uri]:         " + self._current_uri)
            print("[_on_load_complete][_current_name]:        " + self._current_name)
            print("[_on_load_complete][_current_child_count]: " + str(self._current_child_count))
            print("[_on_load_complete][_current_children]:    " + str(self._current_children))

    def _on_test_event(self, data, **kwargs):
        """Callback for platform accessibility events the ATTA is testing."""

        try:
            pyia2.com_coinitialize()
        except:
            print('[_on_test_event]: error cointializing')

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


def get_cmdline_options():
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", action="store")
    parser.add_argument("--port", action="store")
    parser.add_argument("--ansi-formatting", action="store_true")
    return vars(parser.parse_args())

if __name__ == "__main__":
    print("Starting ATTA for MSAA+IAccessible2")
    ia2_atta = IA2Atta("localhost", 4119, False)
    if not ia2_atta.is_enabled():
        print("not enabled")
        sys.exit(1)
    ia2_atta.start(ia2_atta)
    pyia2.Registry.start()

