#!py

import logging
import pprint
import os
import time
import json
import requests
import binascii
import M2Crypto
import salt.utils.smtp as smtp
import salt.config as config

logger = logging.getLogger(__name__)

def run():
    '''
    Run the reactor
    '''
    sns = data['post']

    if 'SubscribeURL' in sns:
        # This is just a subscription notification
        logger.info('EC2 Autoscale Subscription (via Salt Reactor)')
        logger.info('{0}\n'.format(pprint.pformat(sns)))
        r = requests.get(sns['SubscribeURL'])
        logger.info('Confirmation Response:')
        logger.info(r.text)
        return {}

    url_check = sns['SigningCertURL'].replace('https://', '')
    url_comps = url_check.split('/')
    if not url_comps[0].endswith('.amazonaws.com'):
        # The expected URL does not seem to come from Amazon, do not try to
        # process it
        logger.error('EC2 Autoscale SigningCertURL Error (via Salt Reactor)')
        logger.error('There was an error with the EC2 SigningCertURL.\n{1}\n{2}\nContent received was:\n\n{0}\n'.format(pprint.pformat(sns), url_check, url_comps[0]))
        return {}

    if not 'Subject' in sns:
        sns['Subject'] = ''

    pem_request = requests.request('GET', sns['SigningCertURL'])
    pem = pem_request.text

    str_to_sign = (
        'Message\n{Message}\n'
        'MessageId\n{MessageId}\n'
        'Subject\n{Subject}\n'
        'Timestamp\n{Timestamp}\n'
        'TopicArn\n{TopicArn}\n'
        'Type\n{Type}\n'
    ).format(**sns)

    cert = M2Crypto.X509.load_cert_string(str(pem))
    pubkey = cert.get_pubkey()
    pubkey.reset_context(md='sha1')
    pubkey.verify_init()
    pubkey.verify_update(str_to_sign.encode())

    decoded = binascii.a2b_base64(sns['Signature'])
    result = pubkey.verify_final(decoded)

    if result != 1:
        logger.error('There was an error with the EC2 Signature.')
        logger.error('Content received was:\n\n{0}\n'.format(pprint.pformat(sns)))
        return {}

    message = json.loads(sns['Message'])


    ret = {}

    if 'termination' in sns['Subject']:
        instance_id = str(message['EC2InstanceId'])
        ret = {
            'ec2_autoscale_termination': {
                'wheel.key.delete': [
                    {'match': 'terraform-test-' + instance_id},
                ]
            }
        }

    return ret
