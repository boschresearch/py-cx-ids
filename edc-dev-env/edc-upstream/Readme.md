https://github.com/eclipse-edc/Connector/tree/main/launchers/ids-connector

openssl pkcs12 -export -in keys/<client-name>.cert -inkey keys/<client-name>.key -out <client-name>.p12


Prepare string for vault.properties:
cat consumer.crt | sed -z 's/\n/\\r\\n/g'
(-z required!)


Contract offer received. Will be rejected: Offer validity 31535999s does not match contract definition validity 31536000s
