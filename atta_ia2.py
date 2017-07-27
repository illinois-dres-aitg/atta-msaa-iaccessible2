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
from pyia2.utils import AccessibleDocument



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
            "objectAttributes": pyia2.get_ia2_attribute_set,
            "parent": pyia2.get_parent,
            "relations": pyia2.get_ia2_relation_set,
            "role": pyia2.get_ia2_role,
            "type": pyia2.get_type_set,
            "interfaces": pyia2.get_interface_set,
            "states": pyia2.get_ia2_state_set,
        }

        super(IA2Atta, self).__init__(host, port, name, version, api, Atta.LOG_INFO)

    def start(self, atta, **kwargs):
        """Starts this ATTA (i.e. before running a series of tests)."""

        if not self._enabled:
            return

        self._register_listener(pyia2.EVENT_OBJECT_FOCUS, atta._on_load_complete)
        self._register_listener(pyia2.EVENT_OBJECT_STATECHANGE, atta._on_load_complete)
        self._register_listener(pyia2.EVENT_OBJECT_SELECTION, atta._on_load_complete)
        self._register_listener(pyia2.EVENT_OBJECT_SELECTIONREMOVE, atta._on_load_complete)
        self._register_listener(pyia2.EVENT_OBJECT_NAMECHANGE, atta._on_load_complete)
        self._register_listener(pyia2.EVENT_OBJECT_DESCRIPTIONCHANGE, atta._on_load_complete)

        self._register_listener(pyia2.IA2_EVENT_DOCUMENT_LOAD_COMPLETE, atta._on_load_complete)
        self._register_listener(pyia2.IA2_EVENT_ACTIVE_DESCENDANT_CHANGED, atta._on_load_complete)
        self._register_listener(pyia2.IA2_EVENT_OBJECT_ATTRIBUTE_CHANGED, atta._on_load_complete)




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

        pyia2.Registry.registerEventListener(callback, event_type)


    def _deregister_listener(self, event_type, callback, **kwargs):
        """De-registers an accessible-event listener on the platform."""

        pyia2.Registry.deregisterEventListener(callback, event_type)

    def _get_id(self, obj, **kwargs):
        """Returns the element id associated with obj or an empty string upon failure."""

        if obj is None:
            return ""

        value = pyia2.get_id(obj)    
        if len(value) and self._last_id != value:
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

    def get_property_value(self, acc_elem, property_name, **kwargs):
        """Returns the value of property_name for obj."""

#        print("[IA2][get_property_value][acc_elem]: " + str(acc_elem))
#        print("[IA2][get_property_value][property_name]: " + property_name)

        if not acc_elem and property_name != "accessible":
            raise AttributeError("Object not found")

        try:
            if property_name == 'role':
                if self._api_name == 'IAccessible2':
                    value =  acc_elem.ia2_role
                else:
                    value =  acc_elem.role
            if property_name == 'name':
                value =  acc_elem.name
            if property_name == 'value':
                value =  acc_elem.value
            if property_name == 'description':
                value =  acc_elem.description
            if property_name == 'objectAttributes':
                value =  acc_elem.objectAttributes
            if property_name == 'states':
                value =  acc_elem.states
            if property_name == 'relations':
                value =  acc_elem.relations
            if property_name == 'interfaces':
                value =  acc_elem.interfaces
            if property_name == 'minimumValue':
                value =  acc_elem.ia2_value_min
            if property_name == 'currentValue':
                value =  acc_elem.ia2_value_current
            if property_name == 'maximumValue':
                value =  acc_elem.ia2_value_max
        except:
            self._print(self.LOG_ERROR, "[IA2][get_property_value][except]" + self._on_exception())
            value = []    

        return value

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

        if event.type == pyia2.IA2_EVENT_DOCUMENT_LOAD_COMPLETE:
            ao = pyia2.accessibleObjectFromEvent(event)
            self._accessible_document = pyia2.AccessibleDocument(ao)
        else:
            if self._accessible_document:
                self._accessible_document.addEvent(event.type)
                self._accessible_document.updateTestElements()

    def _on_test_event(self, data, **kwargs):
        """Callback for platform accessibility events the ATTA is testing."""

#        try:
#            pyia2.com_coinitialize()
#        except:
#            print('[IA2][_on_test_event]: error cointializing')

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
    print("Starting ATTA for IAccessible2")
    ia2_atta = IA2Atta("localhost", 4119, False)
    if not ia2_atta.is_enabled():
        print("not enabled")
        sys.exit(1)
    ia2_atta.start(ia2_atta)
    pyia2.Registry.start()

