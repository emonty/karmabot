# Copyright the Karmabot authors and contributors.
# All rights reserved.  See AUTHORS.
#
# This file is part of 'karmabot' and is distributed under the BSD license.
# See LICENSE for more details.
import re


# TODO: regular expressions in this module should be
# replaced with something more robust and more efficient.

# TODO: stripping listen commands such as --/++
class Command(object):

    def __init__(self, parent, format, handler,
                 help=None, visible=True, exclusive=False):
        self.parent = parent
        self.format = format
        self.handler = handler
        self.help = help
        self.visible = visible
        self.exclusive = exclusive

    def to_regex(self):

        def sub_parameter(match):
            name = match.group(1)
            if name == "thing":
                parameter_regex = r"(?:\([^()]+\))|[#!\w]+"
            else:
                # This regex may come back to haunt me.
                parameter_regex = r".+"

            return r"(?P<{name}>{regex})".format(name=name,
                                                 regex=parameter_regex)

        regex = self.format
        regex = regex.replace("+", r"\+")
        regex = re.sub(r"{(\w+)}", sub_parameter, regex)
        return regex


class CommandParser(object):

    def __init__(self, command_infos):
        self._command_infos = command_infos

    def handle_command(self, text, context, handled=False):
        for command_info in self._command_infos:
            match = command_info["re"].search(text)
            if match:
                instance = None
                foo = match.groupdict()
                thing = foo.get('thing', None)
                command = command_info['command']
                foo.update({'context': context})

                if thing:
                    foo.update({'thing': context.bot.things.get_thing(thing,
                                                                     context)})
                    handler_cls = command.handler.__module__.split('.').pop()
                    instance = foo['thing']._facets.get(handler_cls)

                substitution = self.dispatch_command(command, instance, foo)
                handled = True
                if substitution:
                    # Start over with the new string
                    newtext = ''.join([text[:match.start()], substitution,
                                      text[match.end():]])
                    return self.handle_command(newtext, context, True)

                if command_info["exclusive"]:
                    break

        return (handled, text)

    def dispatch_command(self, command, instance, kw):
        if instance:
            return command.handler(instance, **kw)
        else:
            return command.handler(command, **kw)
