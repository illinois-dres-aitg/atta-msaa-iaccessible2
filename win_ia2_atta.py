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
from pyia2.constants import CHILDID_SELF, \
    UNLOCALIZED_ROLE_NAMES, \
    UNLOCALIZED_STATE_NAMES
# from pyia2.utils import IA2Lib
# from comtypes.gen.Accessibility import IAccessible

class IA2Atta(Atta):
    """Accessible Technology Test Adapter to test IAccessible2 support."""

    def __init__(self, host, port, ansi_formatting, name="ATTA for IA2", version="", api="IA2"):
        """Initializes this ATTA."""

        self._listener_thread = None
        self._proxy = None
        self._interfaces = []

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
            "interfaces": pyia2.get_interfaces,
            "objectAttributes": pyia2.get_attributes_as_array,
            "parent": pyia2.get_parent,
            "relations": pyia2.get_relation_set,
            "role": pyia2.get_role,
            "states": pyia2.get_state_set,
        }

        super(IA2Atta, self).__init__(host, port, name, version, api, Atta.LOG_INFO, ansi_formatting)

    def start(self, **kwargs):
        """Starts this ATTA (i.e. before running a series of tests)."""

        if not self._enabled:
            return

        self._register_listener("document:load-complete", self._on_load_complete)
        if self._listener_thread is None:
            self._listener_thread = threading.Thread(target=Atspi.event_main)
            self._listener_thread.setDaemon(True)
            self._listener_thread.setName("IA2 Client")
            self._listener_thread.start()

        super().start(**kwargs)

    def _run_test(self, obj, assertion, **kwargs):
        """Runs a single assertion on obj, returning a results dict."""

# JRG
#        if obj:
#            Atspi.Accessible.clear_cache(obj)

        return super()._run_test(obj, assertion, **kwargs)

    def shutdown(self, signum=None, frame=None, **kwargs):
        """Shuts down this ATTA (i.e. after all tests have been run)."""

        if not self._enabled:
            return

        self._deregister_listener("document:load-complete", self._on_load_complete)
        if self._listener_thread is not None:
            Atspi.event_quit()
            self._listener_thread.join()
            self._listener_thread = None

        super().shutdown(signum, frame, **kwargs)

    def _get_rendering_engine(self, **kwargs):
        """Returns a string with details of the user agent's rendering engine."""

        if not self._current_document:
            return ""

        try:
            attrs = Atspi.Accessible.get_attributes(self._current_document) or {}
        except:
            return ""

        return attrs.get("toolkit") or self._current_document.get_toolkit_name()

    def _get_system_api_version(self, **kwargs):
        """Returns a string with the installed version of the accessibility API."""

        try:
            version = Atk.get_version()
        except:
            self._print(self.LOG_ERROR, "Could not get ATK version.")
            return ""

        actual_version = list(map(int, version.split(".")))
        minimum_version = list(map(int, self._api_min_version.split(".")))
        if actual_version < minimum_version:
            msg = "ATK %s < %s." % (version, self._api_min_version)
            self._print(self.LOG_WARNING, msg)

        return version

    def _get_accessibility_enabled(self, **kwargs):
        """Returns True if accessibility support is enabled on this platform."""

        try:
            self._proxy = Gio.DBusProxy.new_for_bus_sync(
                Gio.BusType.SESSION,
                Gio.DBusProxyFlags.NONE,
                None,
                "org.a11y.Bus",
                "/org/a11y/bus",
                "org.freedesktop.DBus.Properties",
                None)
        except:
            self._print(self.LOG_ERROR, self._on_exception())
            return False

        enabled = self._proxy.Get("(ss)", "org.a11y.Status", "IsEnabled")
        return enabled

    def _set_accessibility_enabled(self, enable, **kwargs):
        """Returns True if accessibility support was successfully set."""

        if not self._proxy:
            return False

        should_enable = GLib.Variant("b", enable)
        self._proxy.Set("(ssv)", "org.a11y.Status", "IsEnabled", should_enable)
        success = self._get_accessibility_enabled() == enable

        if success and enable:
            msg = "Accessibility support was just enabled. Browser restart may be needed."
            self._print(self.LOG_WARNING, msg)

        return success

    def _register_listener(self, event_type, callback, **kwargs):
        """Registers an accessible-event listener on the platform."""

        listener = self._listeners.get(callback, Atspi.EventListener.new(callback))
        Atspi.EventListener.register(listener, event_type)
        self._listeners[callback] = listener

    def _deregister_listener(self, event_type, callback, **kwargs):
        """De-registers an accessible-event listener on the platform."""

        listener = self._listeners.get(callback)
        if listener:
            Atspi.EventListener.deregister(listener, event_type)

    def _get_id(self, obj, **kwargs):
        """Returns the element id associated with obj or an empty string upon failure."""

        if obj is None:
            return ""

        try:
            attrs = Atspi.Accessible.get_attributes(obj) or {}
        except:
            return ""

        # Gecko and WebKitGtk respectively
        return attrs.get("id") or attrs.get("html-id") or ""

    def _get_uri(self, document, **kwargs):
        """Returns the URI associated with document or an empty string upon failure."""

        if document is None:
            return ""

        try:
            Atspi.Accessible.clear_cache(document)
        except:
            self._print(self.LOG_ERROR, self._on_exception())
            return ""

        # Gecko and WebKitGtk respectively
        for name in ("DocURL", "URI"):
            try:
                uri = Atspi.Document.get_document_attribute_value(document, name)
            except:
                return ""
            if uri:
                return uri

        return ""

    def _get_children(self, obj, **kwargs):
        """Returns the children of obj or [] upon failure or absence of children."""

        try:
            count = Atspi.Accessible.get_child_count(obj)
        except:
            self._print(self.LOG_ERROR, self._on_exception())
            return []

        try:
            children = [Atspi.Accessible.get_child_at_index(obj, i) for i in range(count)]
        except:
            self._print(self.LOG_ERROR, self._on_exception())
            return []

        return children

    def _get_parent(self, obj, **kwargs):
        """Returns the parent of obj or None upon failure."""

        try:
            parent = Atspi.Accessible.get_parent(obj)
        except:
            self._print(self.LOG_ERROR, self._on_exception())
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

        is_type = lambda x: Atspi.Relation.get_relation_type(x) == relation_type
        relations = list(filter(is_type, Atspi.Accessible.get_relation_set(obj)))
        if not len(relations) == 1:
            return []

        count = Atspi.Relation.get_n_targets(relations[0])
        return [Atspi.Relation.get_target(relations[0], i) for i in range(count)]

    def get_supported_methods(self, obj=None, **kwargs):
        """Returns a name:callable dict of supported platform methods."""

        if obj is None:
            obj_interfaces = self._interfaces
        else:
            obj_interfaces = self.get_property_value(obj, "interfaces")

        def _include(method):
            return method.get_container().get_name() in obj_interfaces

        if self._supported_methods:
            return {k: v for k, v in self._supported_methods.items() if _include(v)}
            return self._supported_methods

        gir = gi.Repository.get_default()
        for iface in self._interfaces:
            atk_info = gir.find_by_name("Atk", iface)
            for method in atk_info.get_methods():
                if self.get_client_side_method(method):
                    self._supported_methods[method.get_symbol()] = method

        return {k: v for k, v in self._supported_methods.items() if _include(v)}

    def get_client_side_method(self, server_side_method, **kwargs):
        """Returns the client-side API method for server_side_method."""

        interface = server_side_method.get_container().get_name()

        gir = gi.Repository.get_default()
        info = gir.find_by_name("Atspi", interface)
        if not info:
            return None

        server_side_symbol = server_side_method.get_symbol()
        client_side_methods = {m.get_symbol(): m for m in info.get_methods()}
        client_side_symbols = list(client_side_methods.keys())

        # Things which are unique or hard to reliably map via heuristic.
        mappings = {
            "atk_selection_add_selection": "atspi_selection_select_child",
            "atk_selection_ref_selection": "atspi_selection_get_selected_child",
            "atk_selection_remove_selection": "atspi_selection_deselect_selected_child",
            "atk_selection_select_all_selection": "atspi_selection_select_all",
            "atk_value_set_value": "atspi_value_set_current_value",
            "atk_value_get_increment": "atspi_value_get_minimum_increment",
        }

        mapped = mappings.get(server_side_symbol)
        if mapped in client_side_symbols:
            return client_side_methods.get(mapped)

        # Ideally, the symbols are the same, not counting the API name.
        candidate_symbol = server_side_symbol.replace("atk", "atspi")
        if candidate_symbol in client_side_symbols:
            return client_side_methods.get(candidate_symbol)

        # AT-SPI2 tends to use "get" when ATK uses "ref"
        replaced = candidate_symbol.replace("_ref_", "_get_")
        if replaced in client_side_symbols:
            return client_side_methods.get(replaced)

        # AT-SPI2 tends to use "get_accessible_at" when ATK uses "ref_at"
        replaced = candidate_symbol.replace("_ref_at", "_get_accessible_at")
        if replaced in client_side_symbols:
            return client_side_methods.get(replaced)

        # They sometimes split words differently ("key_binding", "keybinding").
        collapsed = candidate_symbol.replace("_", "")
        matches = list(map(lambda x: x.replace("_", ""), client_side_symbols))
        if collapsed in matches:
            index = matches.index(collapsed)
            return client_side_methods.get(client_side_symbols[index])

        # AT-SPI2 tends to use "get n" when ATK uses "get ... count".
        if "_get_" in server_side_symbol and "_count" in server_side_symbol:
            matches = list(filter(lambda x: "get_n_" in x, client_side_symbols))
            if len(matches) == 1:
                return client_side_methods.get(matches[0])

        return None

    def get_bug(self, assertion_string, expected_result, actual_result, **kwargs):
        """Returns a string containing bug information for an assertion."""

        test_name = self._next_test[0]
        if not test_name:
            return ""

        engine = self._get_rendering_engine()
        if engine != "Gecko":
            return ""

        # TODO: Give this smarts. At the present time it is a quick-and-dirty way to be
        # sure all of the bugs we need to file related to ARIA 1.1 have been filed.

        if "property interfaces" in assertion_string:
            if "Value" in assertion_string and "separator" in test_name:
                return "https://bugzil.la/1355954"

        if "property objectAttributes" in assertion_string:
            if "contains" in assertion_string:
                if expected_result.startswith("placeholder-text"):
                    return "https://bugzil.la/1303429"
                if expected_result.startswith("level") and "heading" in test_name:
                    return "https://bugzil.la/1357100"
                if expected_result.startswith("valuetext") and "separator" in test_name:
                    return "https://bugzil.la/1355954"
                if expected_result.startswith("haspopup"):
                    return "https://bugzil.la/1355449"
            if "doesNotContain" in assertion_string:
                if expected_result.startswith("rowspan"):
                    return "https://bugzil.la/1357153"
                if expected_result.startswith("colspan"):
                    return "https://bugzil.la/1357153"

        if "property role" in assertion_string:
            if expected_result.endswith("TREE_ITEM") and actual_result.endswith("LIST_ITEM"):
                return "https://bugzil.la/1355423"
            if expected_result.endswith("ARTICLE") and actual_result.endswith("DOCUMENT_FRAME"):
                return "https://bugzil.la/1305446"
            if expected_result.endswith("PANEL") and "figure" in test_name:
                return "https://bugzil.la/1356049"
            if expected_result.endswith("LANDMARK") and "region" in test_name:
                return "https://bugzil.la/1210630"

        if "property states" in assertion_string:
            if expected_result.endswith("VERTICAL") or expected_result.endswith("HORIZONTAL"):
                return "https://bugzil.la/1357042"
            if expected_result not in actual_result:
                if expected_result.endswith("ACTIVE") and "aria-current" in test_name:
                    return "https://bugzil.la/1355921"
                if expected_result.endswith("HAS_POPUP"):
                    return "https://bugzil.la/1355447"
                if expected_result.endswith("READ_ONLY"):
                    return "https://bugzil.la/1356018"

        if "result atk_table_cell_get" in assertion_string:
            if "row_span=" in expected_result or "column_span=" in expected_result:
                return "https://bugzil.la/1357013"
            if "row=" in expected_result or "column=" in expected_result:
                return "https://bugzil.la/1357188"

        if "result atk_table_get_n_rows" in assertion_string \
           or "atk_table_get_n_columns" in assertion_string:
            return "https://bugzil.la/1356997"

        if "result atk_value_get" in assertion_string:
            if "separator" in test_name and "focusable" in test_name:
                return "https://bugzil.la/1355954"
            if "slider" in test_name or "scrollbar" in test_name:
                return "https://bugzil.la/1357071"
            if "spinbutton" in test_name:
                return "https://bugzil.la/1357097"

        return ""

    def string_to_method_and_arguments(self, callable_as_string, **kwargs):
        """Converts callable_as_string into the appropriate callable platform method
        and list of arguments with the appropriate types."""

        try:
            method_string, args_string = re.split("\(", callable_as_string, maxsplit=1)
            args_string = args_string[:-1]
        except ValueError:
            method_string = callable_as_string
            args_list = []
        else:
            args_list = list(filter(lambda x: x != "", args_string.split(",")))

        supported_methods = self.get_supported_methods()
        method = supported_methods.get(method_string)
        if not method:
            raise NameError("%s is not supported" % method_string)

        in_args = filter(lambda x: x.get_direction() == Direction.IN, method.get_arguments())
        arg_types = list(map(lambda x: x.get_type().get_tag(), in_args))
        if len(arg_types) != len(args_list):
            string = self._atta.value_to_string(method)
            raise TypeError("Incorrect argument count for %s" % string)

        py_types = list(map(self.platform_type_to_python_type, arg_types))
        args = [py_types[i](arg) for i, arg in enumerate(args_list)]
        return method, args

    def get_result(self, method, arguments, **kwargs):
        """Returns the result of calling method with the specified arguments."""

        if method.get_namespace() == "Atk":
            method = self.get_client_side_method(method)

        if method and method.get_symbol() == "atspi_table_cell_get_position":
            msg = "You must have AT-SPI2 version 2.24.1 or later: https://bugzil.la/1348340."
            self._print(self.LOG_WARNING, msg)

        arguments.insert(0, kwargs.get("obj"))
        return method.invoke(*arguments)

    def get_supported_actions(self, obj, **kwargs):
        """Returns a list of names of supported actions for obj."""

        try:
            count = Atspi.Action.get_n_actions(obj)
        except:
            return []

        return [Atspi.Action.get_action_name(obj, i) for i in range(count)]

    def get_supported_properties(self, obj, **kwargs):
        """Returns a list of supported platform properties for obj."""

        return self._supported_properties.keys()

    def get_supported_relation_types(self, obj=None, **kwargs):
        """Returns a list of supported platform relation types."""

        if obj:
            relation_set = Atspi.Accessible.get_relation_set(obj)
            return list(map(Atspi.Relation.get_relation_type, relation_set))

        if self._supported_relation_types:
            return self._supported_relation_types

        types = map(Atspi.RelationType, range(Atspi.RelationType.LAST_DEFINED))
        self._supported_relation_types = list(types)
        return self._supported_relation_types

    def string_to_value(self, string, **kwargs):
        """Returns the value (e.g. a platform constant) represented by string."""

        values_maps = {
            "RELATION": map(Atspi.RelationType, range(Atspi.RelationType.LAST_DEFINED)),
            "ROLE": map(Atspi.Role, range(Atspi.Role.LAST_DEFINED)),
            "STATE": map(Atspi.StateType, range(Atspi.StateType.LAST_DEFINED)),
        }

        values_map = values_maps.get(string.split("_")[0], [])
        for value in values_map:
            if self.value_to_string(value) == string:
                return value

        return None

    def platform_type_to_python_type(self, platform_type, **kwargs):
        """Returns the python type associated with the specified platform type."""

        types_map =  {
            TypeTag.BOOLEAN: bool,
            TypeTag.INT8: int,
            TypeTag.UINT8: int,
            TypeTag.INT16: int,
            TypeTag.UINT16: int,
            TypeTag.INT32: int,
            TypeTag.UINT32: int,
            TypeTag.INT64: int,
            TypeTag.UINT64: int,
            TypeTag.FLOAT: float,
            TypeTag.DOUBLE: float,
            TypeTag.GLIST: list,
            TypeTag.GSLIST: list,
            TypeTag.ARRAY: list,
            TypeTag.GHASH: dict,
            TypeTag.UTF8: str,
            TypeTag.FILENAME: str,
            TypeTag.UNICHAR: str,
        }

        return types_map.get(platform_type, str)

    def type_to_string(self, value, **kwargs):
        """Returns the type of value as a harness-compliant string."""

        value_type = type(value)
        if value_type in (Atspi.Accessible, Atspi.Relation):
            return "Object"

        if value_type == Atspi.StateSet:
            return "List"

        if value_type in (Atspi.Role, Atspi.RelationType, Atspi.StateType):
            return "Constant"

        return super().type_to_string(value, **kwargs)

    def value_to_string(self, value, **kwargs):
        """Returns the string representation of value (e.g. a platform constant)."""

        value_type = type(value)
        if value_type == Atspi.Accessible:
            return self._get_id(value, **kwargs) or Atspi.Accessible.get_role_name(value)

        if value_type == Atspi.Relation:
            return self.value_to_string(Atspi.Relation.get_relation_type(value))

        if value_type == Atspi.StateSet:
            all_states = [Atspi.StateType(i) for i in range(Atspi.StateType.LAST_DEFINED)]
            states = [s for s in all_states if value.contains(s)]
            return list(map(self.value_to_string, states))

        if value_type in (Atspi.Role, Atspi.RelationType, Atspi.StateType):
            value_name = value.value_name.replace("ATSPI_", "")
            if value_type == Atspi.Role:
                # ATK (which we're testing) has ROLE_STATUSBAR; AT-SPI (which we're using)
                # has ROLE_STATUS_BAR. ATKify the latter so we can verify the former.
                value_name = value_name.replace("ROLE_STATUS_BAR", "ROLE_STATUSBAR")
            return value_name

        if value_type == FunctionInfo:
            method_args = []
            for arg in value.get_arguments():
                method_args.append("%s %s" % (arg.get_type().get_tag_as_string(), arg.get_name()))

            string = "%s(%s)" % (value.get_symbol(), ", ".join(method_args))
            if value.is_deprecated():
                string = "DEPRECATED: %s" % string
            return string

        return super().value_to_string(value, **kwargs)

    def _on_load_complete(self, data, **kwargs):
        """Callback for the platform's signal that a document has loaded."""

        self._print(self.LOG_DEBUG, self._get_uri(data.source), "LOADED: ")
        if self.is_ready(data.source):
            application = Atspi.Accessible.get_application(data.source)
            Atspi.Accessible.set_cache_mask(application, Atspi.Cache.DEFAULT)

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


def get_cmdline_options():
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", action="store")
    parser.add_argument("--port", action="store")
    parser.add_argument("--ansi-formatting", action="store_true")
    return vars(parser.parse_args())

if __name__ == "__main__":
    print("init")
    ia2_atta = IA2Atta("localhost", 8000,False)
    if not ia2_atta.is_enabled():
        print("not enabled")
        sys.exit(1)
    ia2_atta.start()
