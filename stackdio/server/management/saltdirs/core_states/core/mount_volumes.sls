# Mount the device to the given mount point, but first
# make sure the device exists. AWS requires the device
# to be defined like sdb, but in modern kernels the
# device will be remapped to xvdf.

# look up the device name using our nifty find_ebs_device method
# in our extended mount module

{% for vol in grains.get('volumes', []) %}

{% set device_name = salt['mount.find_ebs_device'](vol['device']) %}

{% if device_name %}

{% if vol['create_fs'] and not salt['extfs.fs_exists'](device_name) %}

# First create the FS if it's an empty volume and there's not already a filesystem on it
{{ vol['mount_point'] }}_create_fs:
  module.run:
    - name: extfs.mkfs
    - device: {{ device_name }}
    - fs_type: {{ vol['filesystem_type'] }}
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
