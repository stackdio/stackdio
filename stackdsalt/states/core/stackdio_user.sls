{% if 'stackdio_username' in pillar and pillar.get('stackdio_publickey') %}

{% set username=pillar['stackdio_username'] %}
{% set publickey=pillar['stackdio_publickey'] %}

# Create the group
stackdio_group:
  group.present:
    - name: {{ username }}
    - gid: 4000

# Create the user
stackdio_user:
  user.present:
    - name: {{ username }}
    - shell: /bin/bash
    - uid: 4000
    - gid: 4000
    - createhome: true
    - require:
      - group: stackdio_group

# Add the public key to authorized_keys file
stackdio_authorized_keys:
  ssh_auth:
    - present
    - user: {{ username }}
    - name: {{ publickey }}
    - require:
      - user: stackdio_user

# Add a sudoers entry
stackdio_sudoers:
  file.managed:
    - name: /etc/sudoers.d/{{ username }}
    - contents: "{{ username }}  ALL=(ALL)  NOPASSWD:ALL"
    - require:
      - ssh_auth: stackdio_authorized_keys

{% endif %}
