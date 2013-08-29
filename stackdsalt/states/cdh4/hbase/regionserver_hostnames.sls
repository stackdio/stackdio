# Write all regionserver hosts to /etc/hosts
append_regionservers_etc_hosts:
  file:
    - append
    - name: /etc/hosts
    - text: 
{% for host, items in salt['publish.publish']('roles:cdh4.hbase.regionserver', 'grains.items', '', 'grain').items() %}
      - "{{ items['ip_interfaces']['eth0'][0] }} {{ items['fqdn'] }}"
{% endfor %}
