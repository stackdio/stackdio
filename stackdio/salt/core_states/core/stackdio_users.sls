{% set users=salt['pillar.get']('__stackdio__:users') %}

{% for user in users %}

{% set uid = 4000 + user.id %}
{% set username = user.username %}
{% set publickey = user.public_key %}

# Create the group
{{ username }}_group:
  group.present:
    - name: {{ username }}
    - gid: {{ uid }}

# Create the user
{{ username }}_user:
  user.present:
    - name: {{ username }}
    - shell: /bin/bash
    - uid: {{ uid }}
    - gid: {{ uid }}
    - createhome: true
    - require:
      - group: {{ username }}_group

# Add the public key to authorized_keys file
{{ username }}_authorized_keys:
  ssh_auth.present:
    - user: {{ username }}
    - name: {{ publickey }}
    - require:
      - user: {{ username }}_user

# Add a sudoers entry
{{ username }}_sudoers:
  file.managed:
    - name: /etc/sudoers.d/{{ username | replace('.', '_') }}
    - contents: "{{ username }} ALL=(ALL) NOPASSWD:ALL"
    - mode: 400
    - user: root
    - group: root
    - require:
      - ssh_auth: {{ username }}_authorized_keys

{% endfor %}
