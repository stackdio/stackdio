# Mount the device to the given mount point, but first
# make sure the device exists. AWS requires the device
# to be defined like sdb, but in modern kernels the
# device will be remapped to xvdf.

# look up the device name using our nifty find_ebs_device method
# in our extended mount module

{% for vol in grains.get('volumes', []) %}

{% set device_name = salt['mount.find_ebs_device'](vol['device']) %}

{% if device_name %}
{{ vol['mount_point'] }}:
  mount:
    - mounted
    - device: {{ device_name }}
    - fstype: {{ vol['filesystem_type'] }}
    - mount: true
    - mkmnt: true
    - persist: false
{% endif %}

{% endfor %}
