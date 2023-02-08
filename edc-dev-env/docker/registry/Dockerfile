FROM eclipse-temurin:11-jdk-alpine as build

RUN apk update && apk add git maven curl
RUN git clone --branch registry-0.3.0 https://github.com/eclipse-tractusx/sldt-digital-twin-registry.git /build

WORKDIR /build
RUN mvn install


# run container
FROM eclipse-temurin:11-jre-alpine

RUN addgroup -S spring \
    && adduser -S spring -G spring \
    && mkdir -p /service \
    && chown spring:spring /service

USER spring:spring

WORKDIR /service

COPY --from=build /build/backend/target/digital-twin-registry-backend*.jar app.jar

ENV JAVA_TOOL_OPTIONS "-Xms512m -Xmx2048m"
EXPOSE 4243

ENTRYPOINT [ "java", "-jar", "/service/app.jar" ]
