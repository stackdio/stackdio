# -*- coding: utf-8 -*-

# Copyright 2014,  Digital Reasoning
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#


from core.validation import ValidationErrors, BaseValidator
from blueprints.models import BlueprintHostDefinition


class StackAddRemoveHostsValidator(BaseValidator):
    ACTIONS = ('add', 'remove')

    def validate(self):
        self._validate_action()
        self._validate_args()
        return self._errors

    def _validate_action(self):
        action = self.data.get('action', '')
        if not action:
            self.set_error('action', ValidationErrors.REQUIRED_FIELD)
            return False
        elif action not in self.ACTIONS:
            self.set_error('action', 'Must be one of {0}'.format(self.ACTIONS))
            return False
        return True

    def _validate_args(self):
        args = self.data.get('args', [])
        if not isinstance(args, list):
            self.set_error('args', ValidationErrors.LIST_REQUIRED)
            return False
        elif not args:
            self.set_error('args', 'At least one action argument is required.')
            return False

        for arg in args:
            if not isinstance(arg, dict):
                self._errors.setdefault('args', []).append(
                    ValidationErrors.OBJECT_REQUIRED
                )
                continue

            arg_errors = {}
            arg_errors.update(self._validate_count(arg))
            arg_errors.update(self._validate_arg_hostdef(arg))

            if self.data['action'] == self.ACTIONS[0]:
                arg_errors.update(self._validate_arg_backfill(arg))

            self._errors.setdefault('args', []).append(arg_errors)

        if not any(self._errors['args']):
            del self._errors['args']

    def _validate_arg_hostdef(self, arg):
        e, k = {}, 'host_definition'
        if k not in arg:
            e[k] = ValidationErrors.REQUIRED_FIELD
        elif not isinstance(arg[k], int):
            e[k] = ValidationErrors.INT_REQUIRED
        # check for the instance
        else:
            try:
                BlueprintHostDefinition.objects.get(
                    pk=arg[k],
                    blueprint__owner=self.request.user
                )
            except BlueprintHostDefinition.DoesNotExist:
                e[k] = ValidationErrors.DOES_NOT_EXIST
        return e

    def _validate_arg_backfill(self, arg):
        e, backfill = {}, arg.get('backfill')
        if backfill is None:
            return e
        if not isinstance(backfill, bool):
            e['backfill'] = ValidationErrors.BOOLEAN_REQUIRED
        return e
