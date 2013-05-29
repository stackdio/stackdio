import json
from django.utils.text import slugify

INSTANCE_SIZES = {
    "aws": {
        "Large Instance": {
            "name": "Large Instance",
            "price": 0.26,
            "ram": 7680,
            "disk": 850,
            "id": "m1.large",
            "uuid": "5f5b2fbcebe50538bf9582b19d13cb0c91c81266"
        },
        "Double Extra Large Instance": {
            "name": "Double Extra Large Instance",
            "price": 1.0,
            "ram": 30720,
            "disk": 850,
            "id": "m3.2xlarge",
            "uuid": "372b07c9446bc9454fd7db287e849f4d4bbee4d1"
        },
        "High-Memory Quadruple Extra Large Instance": {
            "name": "High-Memory Quadruple Extra Large Instance",
            "price": 2.0,
            "ram": 70042,
            "disk": 1690,
            "id": "m2.4xlarge",
            "uuid": "4292ef44ee3d3374d2866127e706ac9d155e0c98"
        },
        "High-Memory Double Extra Large Instance": {
            "name": "High-Memory Double Extra Large Instance",
            "price": 1.0,
            "ram": 35021,
            "disk": 850,
            "id": "m2.2xlarge",
            "uuid": "fb31cdf8bfe50299659a3909bb3b9b15a429d8eb"
        },
        "High-CPU Medium Instance": {
            "name": "High-CPU Medium Instance",
            "price": 0.17,
            "ram": 1740,
            "disk": 350,
            "id": "c1.medium",
            "uuid": "052ae5005adb1f02356f2b4f30b88db3bab6f31c"
        },
        "High-Memory Extra Large Instance": {
            "name": "High-Memory Extra Large Instance",
            "price": 0.5,
            "ram": 17510,
            "disk": 420,
            "id": "m2.xlarge",
            "uuid": "0d8b93749d62c0baf8400818062e04501f715d85"
        },
        "Medium Instance": {
            "name": "Medium Instance",
            "price": 0.13,
            "ram": 3700,
            "disk": 410,
            "id": "m1.medium",
            "uuid": "2d74f708968eca8f9e566105e623731a1dfa4059"
        },
        "Cluster Compute Quadruple Extra Large Instance": {
            "name": "Cluster Compute Quadruple Extra Large Instance",
            "price": 1.3,
            "ram": 23552,
            "disk": 1690,
            "id": "cc1.4xlarge",
            "uuid": "0cb1e7faf62029b3b5694788d30ecb9acfd0c8ee"
        },
        "High Storage Eight Extra Large Instance": {
            "name": "High Storage Eight Extra Large Instance",
            "price": 4.6,
            "ram": 119808,
            "disk": 48000,
            "id": "hs1.8xlarge",
            "uuid": "b398aac7f30240c4a9449f17c03a5c7de850a429"
        },
        "Small Instance": {
            "name": "Small Instance",
            "price": 0.065,
            "ram": 1740,
            "disk": 160,
            "id": "m1.small",
            "uuid": "d44e305011eb14d60c4dbce85efae2c327fddf52"
        },
        "High Memory Cluster Eight Extra Large": {
            "name": "High Memory Cluster Eight Extra Large",
            "price": 3.5,
            "ram": 244000,
            "disk": 240,
            "id": "cr1.8xlarge",
            "uuid": "5902bcc378858da09d0d87e31a3e9579099f1afc"
        },
        "Extra Large Instance": {
            "name": "Extra Large Instance",
            "price": 0.5,
            "ram": 15360,
            "id": "m3.xlarge",
            "uuid": "dc320bc220943570c819a5cb5bd89e922709a4ab"
        },
        "Micro Instance": {
            "name": "Micro Instance",
            "price": 0.02,
            "ram": 613,
            "disk": 15,
            "id": "t1.micro",
            "uuid": "e7fc1f058c75d93f04c3522ea8294a909a95c612"
        },
        "Cluster Compute Eight Extra Large Instance": {
            "name": "Cluster Compute Eight Extra Large Instance",
            "price": 2.4,
            "ram": 63488,
            "disk": 3370,
            "id": "cc2.8xlarge",
            "uuid": "deabcd60e063410adb94f4bda725e54bbf0fe2af"
        },
        "High-CPU Extra Large Instance": {
            "name": "High-CPU Extra Large Instance",
            "price": 0.68,
            "ram": 7680,
            "disk": 1690,
            "id": "c1.xlarge",
            "uuid": "0ffb1c9fbbeac021bce98e25f6cbac4597a0d816"
        },
        "Cluster GPU Quadruple Extra Large Instance": {
            "name": "Cluster GPU Quadruple Extra Large Instance",
            "price": 2.1,
            "ram": 22528,
            "disk": 1690,
            "id": "cg1.4xlarge",
            "uuid": "831fc8f24b7b20a352ee1cf581e1a3ad26f60ec8"
        }
    }
}

PROVIDER_TYPE_ID_MAP = {
    'aws': 1,
}

if __name__ == '__main__':

    i, fixtures = 1, []

    for provider_type in INSTANCE_SIZES:
        instances = INSTANCE_SIZES[provider_type]
        provider_type_id = PROVIDER_TYPE_ID_MAP[provider_type]

        for k, v in instances.iteritems():
            try:
                fixtures.append({
                    'pk': i,
                    'model': 'cloud.cloudinstancesize',
                    'fields': {
                        'title':            k,
                        'slug':             slugify(unicode(k)),
                        'description':      k,
                        'provider_type':    provider_type_id,
                        'instance_id':      v['id'],
                    }
                })
                i += 1
            except KeyError, e:
                print v
                raise
             
    print json.dumps(fixtures, indent=4)
