#!/usr/bin/env python3

from __future__ import print_function

usage = """Usage:
python3 example-service.py &
python3 example-client.py
python3 example-client.py --exit-service
"""

# Copyright (C) 2004-2006 Red Hat Inc. <http://www.redhat.com/>
# Copyright (C) 2005-2007 Collabora Ltd. <http://www.collabora.co.uk/>
#
# SPDX-License-Identifier: MIT
#
# Permission is hereby granted, free of charge, to any person
# obtaining a copy of this software and associated documentation
# files (the "Software"), to deal in the Software without
# restriction, including without limitation the rights to use, copy,
# modify, merge, publish, distribute, sublicense, and/or sell copies
# of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be
# included in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
# NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT
# HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY,
# WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
# DEALINGS IN THE SOFTWARE.

import sys
from traceback import print_exc

import dbus

def main():
    bus = dbus.SessionBus()

    try:
        remote_object = bus.get_object("com.example.SampleService",
                                       "/SomeObject")

        # you can either specify the dbus_interface in each call...
        hello_reply_list = remote_object.HelloWorld("Hello from example-client.py!",
            dbus_interface = "com.example.SampleInterface")
    except dbus.DBusException:
        print_exc()
        print(usage)
        sys.exit(1)

    print("client:", hello_reply_list)

    # ... or create an Interface wrapper for the remote object
    iface = dbus.Interface(remote_object, "com.example.SampleInterface")

    hello_reply_tuple = iface.GetTuple()

    print("client:", hello_reply_tuple)

    hello_reply_dict = iface.GetDict()

    print("client:", hello_reply_dict)

    # D-Bus exceptions are mapped to Python exceptions
    try:
        iface.RaiseException()
    except dbus.DBusException as e:
        print("client:", str(e))

    # introspection is automatically supported
    print("client:", remote_object.Introspect(dbus_interface="org.freedesktop.DBus.Introspectable"))

    if sys.argv[1:] == ['--exit-service']:
        iface.Exit()

if __name__ == '__main__':
    main()
