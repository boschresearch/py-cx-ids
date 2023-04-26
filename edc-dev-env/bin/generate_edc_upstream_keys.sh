#!/bin/sh
# this generates the relevant key settings (keystore) in case the pure EDC upstream instances are used

openssl pkcs12 -passout pass:dontuseinpublic -export -in ./vault_secrets/provider.crt -inkey ./vault_secrets/provider.key -out ./edc-upstream/configs/provider.p12
openssl pkcs12 -passout pass:dontuseinpublic -export -in ./vault_secrets/consumer.crt -inkey ./vault_secrets/consumer.key -out ./edc-upstream/configs/consumer.p12
openssl pkcs12 -passout pass:dontuseinpublic -export -in ./vault_secrets/third.crt -inkey ./vault_secrets/third.key -out ./edc-upstream/configs/third.p12

openssl x509 -inform PEM -in  ./vault_secrets/provider.crt -outform DER -out ./edc-upstream/configs/provider.cer

keytool -importcert -file ./edc-upstream/configs/provider.cer -keystore ./edc-upstream/configs/provider.jks -alias "certificate"

echo -n "" > ./edc-upstream/configs/provider.vault.properties
echo -n "certificate=" >> ./edc-upstream/configs/provider.vault.properties
cat ./vault_secrets/provider.crt | sed -z 's/\n/\\r\\n/g' >> ./edc-upstream/configs/provider.vault.properties
echo "" >> ./edc-upstream/configs/provider.vault.properties
echo -n "private-key=" >> ./edc-upstream/configs/provider.vault.properties
cat ./vault_secrets/provider.key | sed -z 's/\n/\\r\\n/g' >> ./edc-upstream/configs/provider.vault.properties

echo -n "" > ./edc-upstream/configs/consumer.vault.properties
echo -n "certificate=" >> ./edc-upstream/configs/consumer.vault.properties
cat ./vault_secrets/consumer.crt | sed -z 's/\n/\\r\\n/g' >> ./edc-upstream/configs/consumer.vault.properties
echo "" >> ./edc-upstream/configs/consumer.vault.properties
echo -n "private-key=" >> ./edc-upstream/configs/consumer.vault.properties
cat ./vault_secrets/consumer.key | sed -z 's/\n/\\r\\n/g' >> ./edc-upstream/configs/consumer.vault.properties
