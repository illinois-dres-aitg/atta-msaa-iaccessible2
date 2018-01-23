#!/usr/bin/env python3
#
# atta_assertion
# Shareable Assertion support for Accessible Technology Test Adapters
#
# Developed by Jon Gunderson, Mihir Kumar and Bei Zhang
# Copyright (c) 2017 University of Illinois
# Based on the ATTAs developed by Joanmarie Diggs (@joanmarie)
#
# For license information, see:
# https://www.w3.org/Consortium/Legal/2008/04-testsuite-copyright.html

import json
import re
import traceback

from textwrap import TextWrapper


class AttaAssertion(object):

    STATUS_PASS = "PASS"
    STATUS_FAIL = "FAIL"
    STATUS_NOT_RUN = "NOT RUN"

    EXPECTATION_EXISTS = "exists"
    EXPECTATION_IS = "is"
    EXPECTATION_IS_NOT = "isNot"
    EXPECTATION_CONTAINS = "contains"
    EXPECTATION_DOES_NOT_CONTAIN = "doesNotContain"
    EXPECTATION_IS_LESS_THAN = "isLT"
    EXPECTATION_IS_LESS_THAN_OR_EQUAL = "isLTE"
    EXPECTATION_IS_GREATER_THAN = "isGT"
    EXPECTATION_IS_GREATER_THAN_OR_EQUAL = "isGTE"
    EXPECTATION_IS_TYPE = "isType"
    EXPECTATION_IS_ANY = "isAny"

    CLASS_EVENT = "event"
    CLASS_PROPERTY = "property"
    CLASS_RELATION = "relation"
    CLASS_RESULT = "result"
    CLASS_TBD = "TBD"

    _text_wrapper = TextWrapper(width=80, break_on_hyphens=False, break_long_words=False)
    _labels = ["ASSERTION:", "STATUS:", "ACTUAL VALUE:", "MESSAGES:"]

    def __init__(self, acc_elem, assertion, atta):
        self._atta = atta
        self._acc_elem = acc_elem
        self._as_string = " ".join(map(str, assertion))
        self._test_class = assertion[0]
        self._test_string = assertion[1]
        self._expectation = assertion[2]
        self._expected_value = assertion[3]
        self._actual_value = None
        self._messages = []
        self._status = self.STATUS_NOT_RUN
        self._bug = ""

        # in some cases for MSAA there is more than one acceptable role value so convert to array
        if self._expected_value.find("[") == 0 and self._expected_value.find("]"):
            self._expected_value  = self._expected_value[1:]
            self._expected_value  = self._expected_value[:-1]
            self._expected_value = self._expected_value.split(",")


    @classmethod
    def get_test_class(cls, assertion):
        if cls.CLASS_TBD in assertion:
            return AttaDumpInfoAssertion

        test_class = assertion[0]
        if test_class == cls.CLASS_PROPERTY:
            return AttaPropertyAssertion
        if test_class == cls.CLASS_EVENT:
            return AttaEventAssertion
        if test_class == cls.CLASS_RELATION:
            return AttaRelationAssertion
        if test_class == cls.CLASS_RESULT:
            return AttaResultAssertion

        return None

    def is_known_issue(self):
        return bool(self._bug)

    def __str__(self):
        label_width = max(list(map(len, self._labels))) + 2
        self._text_wrapper.subsequent_indent = " " * (label_width+1)

        def _wrap(towrap):
            if isinstance(towrap, list):
                towrap = ",\n".join(map(str, towrap))
            return "\n".join(self._text_wrapper.wrap(str(towrap)))

        return "\n\n{self._labels[0]:>{width}} {self._as_string}" \
               "\n{self._labels[1]:>{width}} {self._status}" \
               "\n{self._labels[2]:>{width}} {actual_value}" \
               "\n{self._labels[3]:>{width}} {messages}\n".format(
                   width=label_width,
                   self=self,
                   actual_value=_wrap(self._actual_value),
                   messages=_wrap(self._messages))

    def _on_exception(self):
        error = traceback.format_exc(limit=1, chain=False)
        self._messages.append(re.sub("\s+", " ", error))

    def _compare(self, a, b):
        if a == b:
            return 0

        try:
            float_a = float(a)
            float_b = float(b)
        except:
            return None

        return min(max(float_a - float_b, -1), 1)

    def _get_result(self):
        value = self._get_value()

        if self._expectation == self.EXPECTATION_IS_TYPE:
            self._actual_value = self._atta.type_to_string(value)
        else:
            self._actual_value = value

        if self._expectation == self.EXPECTATION_IS:
            result = self._compare(self._actual_value, self._expected_value) == 0
        elif self._expectation == self.EXPECTATION_IS_NOT:
            result = self._compare(self._actual_value, self._expected_value) != 0
        elif self._expectation == self.EXPECTATION_IS_LESS_THAN:
            result = self._compare(self._actual_value, self._expected_value) == -1
        elif self._expectation == self.EXPECTATION_IS_GREATER_THAN:
            result = self._compare(self._actual_value, self._expected_value) == 1
        elif self._expectation == self.EXPECTATION_IS_LESS_THAN_OR_EQUAL:
            result = self._compare(self._actual_value, self._expected_value) in [0, -1]
        elif self._expectation == self.EXPECTATION_IS_GREATER_THAN_OR_EQUAL:
            result = self._compare(self._actual_value, self._expected_value) in [0, 1]
        elif self._expectation == self.EXPECTATION_CONTAINS:
            result = self._actual_value and self._expected_value in self._actual_value
        elif self._expectation == self.EXPECTATION_DOES_NOT_CONTAIN:
            result = isinstance(self._actual_value, list) \
                     and self._expected_value not in self._actual_value
        elif self._expectation == self.EXPECTATION_IS_ANY:
            result = self._actual_value in self._expected_value
        elif self._expectation == self.EXPECTATION_IS_TYPE:
            result = self._actual_value == self._expected_value
        elif self._expectation == self.EXPECTATION_EXISTS:
            result = self._expected_value == self._actual_value
        else:
            result = False

        if result:
            self._status = self.STATUS_PASS
        else:
            self._status = self.STATUS_FAIL
            self._bug = self._atta.get_bug(self._as_string, self._expected_value, self._actual_value)
            if self._bug:
                self._messages.append(self._bug)

#        self._atta._print(self._atta.LOG_INFO, self._test_class + ' ' + self._test_string + ' ' + self._expectation + ' ' + str(self._expected_value) + ', ' + str(result))

        return result

    def _get_value(self):
        pass

    def get_bug(self):
        return self._bug

    def run(self):
        self._get_result()
        return self._status, " ".join(self._messages), str(self)



class AttaEventAssertion(AttaAssertion):

    def __init__(self, obj, assertion, atta):
        super(self.__class__, self).__init__(obj, assertion, atta)

    def _get_result(self):
#        result = self._expected_value in self._atta.get_event_history()

        self._atta._print(self._atta.LOG_INFO, "[ASSERTION][AttaEventAssertion][_get_result][_expected_value]: " + str(self._expected_value))
        self._atta._print(self._atta.LOG_INFO, "[ASSERTION][AttaEventAssertion][_get_result][events]:          " + str(self._atta._accessible_document.events))

        result = self._expected_value in self._atta._accessible_document.events

        self._atta._print(self._atta.LOG_INFO, "[ASSERTION][AttaEventAssertion][_get_result][result]:          " + str(result))

        if result:
            self._status = self.STATUS_PASS
            return True

        self._status = self.STATUS_FAIL
        return False


class AttaPropertyAssertion(AttaAssertion):

    def __init__(self, acc_elem, assertion, atta):

        super(self.__class__, self).__init__(acc_elem, assertion, atta)
        if self._expected_value == "<nil>":
            self._expected_value = "None"

    def _get_value(self):
        try:
            value = self._atta.get_property_value(self._acc_elem, self._test_string)
        except Exception as error:
            self._messages.append("[ASSERTION][AttaPropertyAssertion]ERROR: %s" % error)
            return None

        return value


class AttaRelationAssertion(AttaAssertion):

    def __init__(self, acc_elem, assertion, atta):
        super(self.__class__, self).__init__(acc_elem, assertion, atta)
        self._relation_type = atta.string_to_value(self._test_string)

    def _get_value(self):
        try:
            targets = self._atta.get_relation_targets(self._acc_elem, self._relation_type)
        except Exception as error:
            self._messages.append("[ASSERTION][AttaRelationAssertion]ERROR: %s" % error)
            return None

        return "[%s]" % " ".join(self._atta.value_to_string(targets))


class AttaResultAssertion(AttaAssertion):

    def __init__(self, acc_elem, assertion, atta):
        super(self.__class__, self).__init__(acc_elem, assertion, atta)
        self._method = None
        self._args = []

        try:
            result = self._atta.string_to_method_and_arguments(self._test_string)
        except Exception as error:
            self._messages.append("[ASSERTION][AttaResultAssertion][__init__]ERROR: %s" % error)
        else:
            self._method, self._args = result

    def _get_value(self):
        try:
            value = self._atta.get_result(self._method, self._args, acc_elem=self._acc_elem)
        except AttributeError:
            return None
        except Exception as error:
            self._messages.append("[ASSERTION][AttaResultAssertion][_get_value]ERROR: %s" % error)
            return None

        return value


class AttaDumpInfoAssertion(AttaAssertion):

    def __init__(self, acc_elem, assertion, atta):
        assertion = [""] * 4
        super(AttaDumpInfoAssertion, self).__init__(acc_elem, assertion, atta)

    def run(self):
        info = dict.fromkeys(["properties", "relation targets", "supported methods"])

        properties = self._atta.get_supported_properties(self._obj)
        getter = lambda x: self._atta.get_property_value(self._obj, x)
        info["properties"] = {prop: getter(prop) for prop in properties}

        info["actions"] = self._atta.get_supported_actions(self._obj)

        relation_types = self._atta.get_supported_relation_types(self._obj)
        getter = lambda x: self._atta.get_relation_targets(self._obj, x)
        info["relation targets"] = {rtype: getter(rtype) for rtype in relation_types}

        supported_methods = self._atta.get_supported_methods(self._obj)
        methods = list(map(self._atta.value_to_string, supported_methods.values()))
        info["supported methods"] = sorted(methods)

        info = self._atta.value_to_string(info)
        log = json.dumps(info, indent=4, sort_keys=True)
        self._status = self.STATUS_FAIL
        return self._status, " ".join(self._messages), log
