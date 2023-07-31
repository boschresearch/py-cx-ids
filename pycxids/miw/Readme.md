# MIW - managed identity wallet
The server is a rather mocked server. It doesn't do any real checks and is only there, to get local development running.

The predefined credentials need some configs to work out of the box.

## Example EDC seetings:
```
tx.ssi.miw.url=http://miw-server:8080/miw
tx.ssi.oauth.token.url=http://miw-server:8080/miw/token
tx.ssi.oauth.client.id=provider
tx.ssi.miw.authority.id=BPNLissuer
tx.ssi.miw.authority.issuer=did:web:dev%3A9000:BPNLissuer
```

Especially the last setting is important in case your environment looks a bit different. If `tx.ssi.miw.authority.issuer` is not set, EDC derives this value from the `tx.ssi.miw.url` which might be an issue in case of e.g. docker internal and external ports and so on.
