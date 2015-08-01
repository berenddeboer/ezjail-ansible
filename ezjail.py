#!/usr/bin/python
DOCUMENTATION = '''
---
module: ezjail
author: Tom Lazar
short_description: Manage FreeBSD jails
requirements: [ zfs ]
description:
    - Manage FreeBSD jails
'''

class Ezjail(object):

    platform = 'FreeBSD'

    def __init__(self, module):
        self.module = module
        self.changed = False
        self.state = self.module.params.pop('state')
        self.name = self.module.params.pop('name')
        self.cmd = self.module.get_bin_path('ezjail-admin', required=True)

    def ezjail_admin(self, command, *params):
        return self.module.run_command(' '.join([self.cmd, command] + list(params)))

    def exists(self):
        (rc, out, err) = self.ezjail_admin('config', '-r', 'test', self.name)
        return rc==0

    def create(self):
        result = dict()
        if self.module.check_mode:
            self.changed = True
            return result
        (rc, out, err) = self.ezjail_admin('create', '-c',
            self.module.params['disktype'], self.name, self.module.params['ip_addr'])
        if rc == 0:
            self.changed = True
            if self.state == 'running':
                (rc, out, err) = self.ezjail_admin('start', self.name)
                if rc != 0:
                    result['failed'] = True
                    result['msg'] = "Could not start jail. %s%s" % (out, err)
        else:
            self.changed = False
            result['failed'] = True
            result['msg'] = "Could not create jail. %s%s" % (out, err)
        return result

    def destroy(self):
        raise NotImplemented

    def start(self):
        result = dict()
        if self.module.check_mode:
            self.changed = True
            return result
        (rc, out, err) = self.ezjail_admin('start', self.name)
        if rc != 0:
            result['failed'] = True
            result['msg'] = "Could not start jail. %s%s" % (out, err)
        else:
            self.changed = True
        return result

    def stop(self):
        result = dict()
        if self.module.check_mode:
            self.changed = True
            return result
        (rc, out, err) = self.ezjail_admin('stop', self.name)
        if rc != 0:
            result['failed'] = True
            result['msg'] = "Could not stop jail. %s%s" % (out, err)
        else:
            self.changed = True
        return result

    def __call__(self):

        result = dict(name=self.name, state=self.state)

        if self.state in ['present', 'running']:
            if not self.exists():
                result.update(self.create())
            else:
                self.start()
        elif self.state == 'absent':
            if self.exists():
                self.destroy()
        elif self.state == 'stopped':
            if self.exists():
                self.stop()

        result['changed'] = self.changed
        return result


MODULE_SPECS = dict(
    argument_spec=dict(
        name=dict(required=True, type='str'),
        state=dict(default='present', choices=['present', 'absent', 'running', 'stopped'], type='str'),
        disktype=dict(default='simple', choices=['simple', 'bde', 'eli', 'zfs'], type='str'),
        ip_addr=dict(required=False, type='str'),
        ),
    supports_check_mode=True
)


def main():
    module = AnsibleModule(**MODULE_SPECS)
    result = Ezjail(module)()
    if 'failed' in result:
        module.fail_json(**result)
    else:
        module.exit_json(**result)

# include magic from lib/ansible/module_common.py
#<<INCLUDE_ANSIBLE_MODULE_COMMON>>
if __name__ == "__main__":
    main()
