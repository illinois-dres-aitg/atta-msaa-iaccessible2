#!/usr/bin/env python27
#
# win_atta_request_handler
# Optional Request Handler for Accessible Technology Test Adapters
#
# Developed by Jon Gunderson, Mihir Kumar and Bei Zhang
# Copyright (c) 2017 University of Illinois
# Based on the ATTAs developed by Joanmarie Diggs (@joanmarie)
#
# For license information, see:
# https://www.w3.org/Consortium/Legal/2008/04-testsuite-copyright.html

import json
import threading
import time
import traceback

from BaseHTTPServer import BaseHTTPRequestHandler

class AttaRequestHandler(BaseHTTPRequestHandler):
    """Optional request handler for python27 Accessible Technology Test Adapters."""

    _atta = None
    _timeout = 5
    _running_tests = False

    @classmethod
    def set_atta(cls, atta):
        cls._atta = atta

    @classmethod
    def is_running_tests(cls):
        return cls._running_tests

    def do_GET(self):
        self.dispatch()

    def do_POST(self):
        self.dispatch()

    def dispatch(self):
        if len(self.path):

            if self.path.endswith("start"):
                self.start_test_run()
            elif self.path.endswith("startlisten"):
                self.start_listen()
            elif self.path.endswith("test"):
                self.run_tests()
            elif self.path.endswith("stoplisten"):
                self.stop_listen()
            elif self.path.endswith("end"):
                self.end_test_run()
        else:
            self.send_error(400, "UNHANDLED PATH: %s" % self.path)

    def send_error(self, code, message=None):

        if message is None:
            message = "Error: bad request"

        self.send_response(code, message)
        self.send_header("Content-Type", "text/plain")
        self.add_headers()
        # JRG
        # self.wfile.write(bytes("%s\n" % message, "utf-8"))
        self.wfile.write(bytes("%s\n" % message))

    @staticmethod
    def dump_json(obj):

        return json.dumps(obj, indent=4, sort_keys=True)

    def add_aria_headers(self):

        self.send_header("Content-Type", "application/json")
        self.add_headers()

    def add_headers(self):

        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Access-Control-Allow-Methods", "POST")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Expose-Headers", "Allow, Content-Type")
        self.send_header("Allow", "POST")
        self.end_headers()

    def get_params(self, *params):

        submission = {}
        response = {}
        errors = []

        try:
            length = self.headers.__getitem__("content-length")
            content = self.rfile.read(int(length))
            submission = json.loads(content.decode("utf-8"))
        except:
            error = traceback.format_exc(limit=1, chain=False)
            errors.append(error)

        for param in params:
            value = submission.get(param)
            if value is None:
                errors.append("Parameter %s not found" % param)
            else:
                response[param] = value

        response["error"] = "; ".join(errors)
        return response

    def log_error(self, format, *args):
        self._atta.log_message(format % args, self._atta.LOG_ERROR)

    def log_message(self, format, *args):
        self._atta.log_message(format % args, self._atta.LOG_DEBUG)

    def _send_response(self, response, status_code=200):

        if response.get("statusText") is None:
            response["statusText"] = ""

        message = response.get("statusText")
        self.send_response(status_code, message)
        self.add_aria_headers()
        dump = self.dump_json(response)
        try:
#            self.wfile.write(bytes(dump, "utf-8"))
            self.wfile.write(dump)
        except Exception as error:
            self._atta.log_message('[RH][_send_response]' + error, self._atta.LOG_ERROR)

    def _wait(self, start_time, method, response={}):

        # the method seems to always be is_ready from ATTA object
        if method.__call__():
            return False

        if time.time() - start_time > self._timeout:
            msg = "Timeout waiting for %s() to return True" % method.__name__
            response.update({"status": "ERROR", "statusText": msg})
            self._send_response(response, 500)
            return False

        return True

    def _wait_for_run_request(self):
        win_atta_request_handler = self

        class Timer(threading.Thread):
            def __init__(self, timeout):
                super(self.__class__, self).__init__()
                self.timeout = time.time() + timeout

            def run(self):
                while not AttaRequestHandler.is_running_tests():
                    if time.time() > self.timeout:
                        msg = "'test' request not received from WPT."
                        win_atta_request_handler._atta.log_message(msg, win_atta_request_handler._atta.LOG_ERROR)
                        return

        thread = Timer(self._timeout)
        thread.start()

    def start_test_run(self):

        AttaRequestHandler._running_tests = False
        response = {}
        params = self.get_params("test", "url")
        error = params.get("error")
        if error:
            response["status"] = "ERROR"
            response["statusText"] = error
            self._send_response(response)
            return

        if not (self._atta and self._atta.is_enabled()):
            response["status"] = "ERROR"
            response["statusText"] = "ENABLED ATTA NOT FOUND. TEST MUST BE RUN MANUALLY."
            self._send_response(response)
            return

        start_time = time.time()
        response.update(self._atta.get_info())
        self._atta.start_test_run(name=params.get("test"), url=params.get("url"))
        while self._wait(start_time, self._atta.is_ready, response):
            time.sleep(0.5)

        response["status"] = "READY"
        self._send_response(response)
        self._wait_for_run_request()

    def start_listen(self):
        self._atta.log_message('[RH][start_listen]', self._atta.LOG_DEBUG)

        params = self.get_params("events")
        error = params.get("error")
        response = {}
        if error:
            response["status"] = "ERROR"
            response["statusText"] = error
            self._send_response(response)
            return

        if self._atta is not None:
            self._atta.start_listen(params.get("events"))

        response["status"] = "READY"
        self._send_response(response)

    def run_tests(self):

        AttaRequestHandler._running_tests = True
        params = self.get_params("title", "id", "data")
        response = {}
        if self._atta is not None:

            result = self._atta.run_tests(params.get("id"), params.get("data", {}))
            response.update(result)

        if not response.get("results"):
            response["statusText"] = params.get("error")

        self._send_response(response)

    def stop_listen(self):
        self._atta.log_message('[RH][stop_listen]', self._atta.LOG_DEBUG)

        if self._atta is not None:
            self._atta.stop_listen()

        response = {"status": "READY"}
        self._send_response(response)

    def end_test_run(self):
        self._atta.log_message('[RH][end_test_run]', self._atta.LOG_DEBUG)

        self._atta.end_test_run()
        response = {"status": "DONE"}
        self._send_response(response)
        AttaRequestHandler._running_tests = False
