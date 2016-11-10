# Make sure salt-minion starts on boot, this already happens on systemd.
{% if grains.init == 'upstart' %}
/etc/init/salt-minion.conf:
  file.managed:
    - source: salt://core/etc/init/salt-minion.conf
{% endif %}
