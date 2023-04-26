FROM gradle:7.4.1-jdk17 AS build

WORKDIR /build

RUN git clone --depth 1 --branch v0.0.1-milestone-8 https://github.com/eclipse-edc/Connector.git /build

RUN gradle :launchers:ids-connector:build --no-daemon


# runtime container
FROM openjdk:17-slim

WORKDIR /app
COPY --from=build /build/launchers/ids-connector/build/libs/dataspace-connector.jar /app

#ENV EDC_FS_CONFIG=config.properties
#ENV EDC_VAULT=$EDC_VAULT
#ENV EDC_KEYSTORE=$EDC_KEYSTORE
#ENV EDC_KEYSTORE_PASSWORD=$EDC_KEYSTORE_PASSWORD

EXPOSE 8181
EXPOSE 8282

#  keytool -importcert -v -file /app/certificate.cer -keystore /app/keystore.jks \
#    -alias certificate -storepass $EDC_KEYSTORE_PASSWORD -noprompt -trustcacerts && \
ENTRYPOINT java \
    -Djava.security.edg=file:/dev/.urandom \
    -Dedc.ids.id="urn:connector:edc-connector-24" \
    -Dedc.ids.title="Eclipse Dataspace Connector" \
    -Dedc.ids.description="Eclipse Dataspace Connector with IDS extensions" \
    -Dedc.ids.maintainer="https://example.maintainer.com" \
    -Dedc.ids.curator="https://example.maintainer.com" \
    -jar dataspace-connector.jar
