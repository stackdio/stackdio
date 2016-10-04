# Mount the device to the given mount point, but first
# make sure the device exists. AWS requires the device
# to be defined like sdb, but in modern kernels the
# device will be remapped to xvdf.

# look up the device name using our nifty find_ebs_device method
# in our extended mount module

{% for vol in grains.get('volumes', []) %}

{% set device_name = salt['mount.find_ebs_device'](vol['device']) %}

{% if device_name %}

{% if vol['create_fs'] %}

# First create the FS if it's an empty volume
{{ vol['mount_point'] }}_create_fs:
  cmd.run:
    - name: 'mkfs -t {{ vol['filesystem_type'] }} {{ device_name }}'
    - user: root
    - require_in:
      - mount: {{ vol['mount_point'] }}
{% endif %}

# Mount the volume
{{ vol['mount_point'] }}:
  mount.mounted:
    - device: {{ device_name }}
    - fstype: {{ vol['filesystem_type'] }}
    - mount: true
    - mkmnt: true
    - persist: false
{% endif %}

{% endfor %}
