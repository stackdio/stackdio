{%- set stack_hosts = salt['mine.get']('stack_id:' ~ grains.stack_id, 'grains.items', 'grain') -%}
# Add an IP->FQDN mapping for each machine in the stack
stack_hostnames:
  file:
    - append
    - name: /etc/hosts
    - text:
{%- for host, items in stack_hosts.iteritems() %}
      - "{{ items['ip_interfaces']['eth0'][0] }} {{ items['fqdn'] }}"
{% endfor %}
