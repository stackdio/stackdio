#!py

import os

def run():
    trusted_keys_dir = os.path.join(__opts__['pki_dir'], 'trusted_minion_keys')

    ret = {}

    for trusted_key in os.listdir(trusted_keys_dir):
        with open(os.path.join(trusted_keys_dir, trusted_key), 'r') as f:
            if f.read() == data['pub']:
                ret['accept-minion-key'] = {
                    'wheel.key.accept': [
                        {'match': data['id']},
                    ]
                }
                break

    return ret
