jdk6:
{% if grains['os_family'] == 'Debian' %}
  java_home: /usr/lib/jvm/java-6-oracle
{% elif grains['os_family'] == 'RedHat' %}
  java_home: /usr/java/jre1.6.0_34
{% endif %}
