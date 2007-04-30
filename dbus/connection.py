# Copyright (C) 2007 Collabora Ltd. <http://www.collabora.co.uk/>
#
# Licensed under the Academic Free License version 2.1
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published
# by the Free Software Foundation; either version 2.1 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA

__all__ = ('Connection',)
__docformat__ = 'reStructuredText'

import logging

from _dbus_bindings import Connection as _Connection, ErrorMessage, \
                           MethodCallMessage, MethodReturnMessage, \
                           DBusException, LOCAL_PATH, LOCAL_IFACE
from dbus.proxies import ProxyObject


_logger = logging.getLogger('dbus.methods')


def _noop(*args, **kwargs):
    pass


class Connection(_Connection):
    """A connection to another application. In this base class there is
    assumed to be no bus daemon.
    """

    ProxyObjectClass = ProxyObject

    def get_object(self, named_service, object_path, introspect=True):
        """Return a local proxy for the given remote object.

        Method calls on the proxy are translated into method calls on the
        remote object.

        :Parameters:
            `named_service` : str
                A bus name (either the unique name or a well-known name)
                of the application owning the object
            `object_path` : str
                The object path of the desired object
            `introspect` : bool
                If true (default), attempt to introspect the remote
                object to find out supported methods and their signatures

        :Returns: a `dbus.proxies.ProxyObject`
        """
        return self.ProxyObjectClass(self, named_service, object_path,
                                     introspect=introspect)

    def activate_name_owner(self, bus_name):
        """Return the unique name for the given bus name, activating it
        if necessary and possible.

        If the name is already unique or this connection is not to a
        bus daemon, just return it.

        :Returns: a bus name. If the given `bus_name` exists, the returned
            name identifies its current owner; otherwise the returned name
            does not exist.
        :Raises DBusException: if the implementation has failed
            to activate the given bus name.
        """
        return bus_name

    def call_async(self, bus_name, object_path, dbus_interface, method,
                   signature, args, reply_handler, error_handler,
                   timeout=-1.0, utf8_strings=False, byte_arrays=False,
                   require_main_loop=True):
        """Call the given method, asynchronously.

        If the reply_handler is None, successful replies will be ignored.
        If the error_handler is None, failures will be ignored. If both
        are None, the implementation may request that no reply is sent.

        :Returns: The dbus.lowlevel.PendingCall.
        """
        if object_path == LOCAL_PATH:
            raise DBusException('Methods may not be called on the reserved '
                                'path %s' % LOCAL_PATH)
        if dbus_interface == LOCAL_IFACE:
            raise DBusException('Methods may not be called on the reserved '
                                'interface %s' % LOCAL_IFACE)
        # no need to validate other args - MethodCallMessage ctor will do

        get_args_opts = {'utf8_strings': utf8_strings,
                         'byte_arrays': byte_arrays}

        message = MethodCallMessage(destination=bus_name,
                                    path=object_path,
                                    interface=dbus_interface,
                                    method=method)
        # Add the arguments to the function
        try:
            message.append(signature=signature, *args)
        except Exception, e:
            _logger.error('Unable to set arguments %r according to '
                          'signature %r: %s: %s',
                          args, signature, e.__class__, e)
            raise

        if reply_handler is None and error_handler is None:
            # we don't care what happens, so just send it
            self.send_message(message)
            return

        if reply_handler is None:
            reply_handler = _noop
        if error_handler is None:
            error_handler = _noop

        def msg_reply_handler(message):
            if isinstance(message, MethodReturnMessage):
                reply_handler(*message.get_args_list(**get_args_opts))
            elif isinstance(message, ErrorMessage):
                args = message.get_args_list()
                # FIXME: should we do something with the rest?
                if len(args) > 0:
                    error_handler(DBusException(args[0]))
                else:
                    error_handler(DBusException())
            else:
                error_handler(TypeError('Unexpected type for reply '
                                        'message: %r' % message))
        return self.send_message_with_reply(message, msg_reply_handler,
                                        timeout/1000.0,
                                        require_main_loop=require_main_loop)

    def call_blocking(self, bus_name, object_path, dbus_interface, method,
                      signature, args, timeout=-1.0, utf8_strings=False,
                      byte_arrays=False):
        """Call the given method, synchronously.
        """
        if object_path == LOCAL_PATH:
            raise DBusException('Methods may not be called on the reserved '
                                'path %s' % LOCAL_PATH)
        if dbus_interface == LOCAL_IFACE:
            raise DBusException('Methods may not be called on the reserved '
                                'interface %s' % LOCAL_IFACE)
        # no need to validate other args - MethodCallMessage ctor will do

        get_args_opts = {'utf8_strings': utf8_strings,
                         'byte_arrays': byte_arrays}

        message = MethodCallMessage(destination=bus_name,
                                    path=object_path,
                                    interface=dbus_interface,
                                    method=method)
        # Add the arguments to the function
        try:
            message.append(signature=signature, *args)
        except Exception, e:
            _logger.error('Unable to set arguments %r according to '
                          'signature %r: %s: %s',
                          args, signature, e.__class__, e)
            raise

        # make a blocking call
        reply_message = self.send_message_with_reply_and_block(
            message, timeout)
        args_list = reply_message.get_args_list(**get_args_opts)
        if len(args_list) == 0:
            return None
        elif len(args_list) == 1:
            return args_list[0]
        else:
            return tuple(args_list)