#!/bin/bash -e

# 
# Launch a micro instance for deploying stackd.io
#

script_dir="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
function log_msg {
    echo "[$(date)] $1"
}

function usage {
    echo "Usage: $0 KEYPAIR_NAME_NAME SECURITY_GROUP"
    echo "**NOTE:** Both the keypair and security group must exist"
    exit 1
}

if [[ ! `which aws` ]]; then
    log_msg "Must have the AWS CLI installed: http://aws.amazon.com/cli/"
    exit 1
fi

if [[ ! `which jq` ]]; then
    log_msg "Must have jq installed: http://stedolan.github.io/jq/"
    exit 1
fi

KEYPAIR_NAME=$1
SECURITY_GROUP=$2
if [ -z $KEYPAIR_NAME -o -z $SECURITY_GROUP ]; then usage; fi

KEYPAIR_FILE=${KEYPAIR_FILE-$HOME/.ssh/${KEYPAIR_NAME}.pem}

if [ ! -e $KEYPAIR_FILE ]; then
    log_msg "The specified KEYPAIR_FILE \"$KEYPAIR_FILE\" does not exist."
    exit 1
fi

INSTANCE_TYPE=${INSTANCE_TYPE-t1.micro}
AMI_ID=${AMI_ID-ami-eb6b0182}

log_msg "#####################################################################"
log_msg " Launching stackd.io instance"
log_msg " Instance type   : $INSTANCE_TYPE"
log_msg " Base AMI        : $AMI_ID"
log_msg " Key pair name   : $KEYPAIR_NAME"
log_msg " Key pair file   : $KEYPAIR_FILE"
log_msg " Security group  : $SECURITY_GROUP"
log_msg "#####################################################################"


log_msg "Launching the instance"
INSTANCE_ID=$(aws ec2 run-instances \
    --count 1 \
    --image-id $AMI_ID \
    --instance-type $INSTANCE_TYPE \
    --key-name $KEYPAIR_NAME \
    --security-groups $SECURITY_GROUP |\
    jq .Instances[].InstanceId | sed 's/"//g')

log_msg "Launched instance ID  : $INSTANCE_ID"

log_msg "Getting hostname"
HOSTNAME=$(aws ec2 describe-instances \
    --instance-ids $INSTANCE_ID |\
    jq .Reservations[].Instances[].PublicDnsName | sed 's/"//g')
while [ "$HOSTNAME" == 'null' ]; do
    echo -n "."
    HOSTNAME=$(aws ec2 describe-instances \
        --instance-ids $INSTANCE_ID |\
        jq .Reservations[].Instances[].PublicDnsName | sed 's/"//g')
    sleep 2
done
echo

log_msg "Hostname     : $HOSTNAME"

log_msg "Waiting for ssh to become available..."
while [[ ! $(ssh -i ~/.ssh/${KEYPAIR_NAME}.pem \
    -o "PasswordAuthentication=no" \
    -o "ConnectTimeout=3" root@${HOSTNAME} "uptime" 2>/dev/null) ]]; do
    echo -n "."
    sleep 2
done
echo

log_msg "Uploading deployment code"
scp -i $KEYPAIR_FILE -r ${script_dir} root@${HOSTNAME}:/tmp

log_msg "Logging into $HOSTNAME"
ssh -i $KEYPAIR_FILE root@${HOSTNAME}

log_msg "#####################################################################"
log_msg "Assuming things worked, you should be able to start using stackd.io:"
echo
echo "    http://${HOSTNAME}"
echo
log_msg "And in summary:"
log_msg " Instance type   : $INSTANCE_TYPE"
log_msg " Instance ID     : $INSTANCE_ID"
log_msg " Hostname        : $HOSTNAME"
log_msg " Base AMI        : $AMI_ID"
log_msg " Key pair name   : $KEYPAIR_NAME"
log_msg " Key pair file   : $KEYPAIR_FILE"
log_msg " Security group  : $SECURITY_GROUP"
log_msg "#####################################################################"

