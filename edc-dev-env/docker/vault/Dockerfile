FROM vault:1.12.2

# we need proper bash for job managing in our vault-init script
RUN apk update && apk upgrade && apk add bash

EXPOSE 8200
ADD vault-init.sh /

RUN chmod 755 vault-init.sh

ENTRYPOINT exec "./vault-init.sh"
