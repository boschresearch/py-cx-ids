```plantuml

skinparam boxpadding 20
autonumber

title tractusx-edc 0.7.1 with STS / DIM

box Consumer
participant Consumer
participant "STS" as Consumer_STS
participant "AuthServer" as Consumer_STS_AuthServer
participant "Credential Service" as CS
end box

box Provider
participant Provider
participant "STS" as Provider_STS
participant "AuthServer" as Provider_STS_AuthServer
end box



Consumer -> Consumer_STS_AuthServer: client_id/client_secret
Consumer_STS_AuthServer -> Consumer: access_token

Consumer -> Consumer_STS: <b>"grantAccess" case</b> (with access_token)
Consumer_STS -> Consumer: si-token

Consumer -> Provider: DSP call (with si-token)
Provider -> Provider_STS_AuthServer: client_id2/client_secret2
Provider_STS_AuthServer -> Provider: access_token2
Provider -> Provider_STS: <b>"signToken" case</b> to cross-sign si-token\n(access with access_token2)
Provider_STS -> Provider: enveloped/cross-signed si-token

Provider -> CS: Request actual credential\nwith <b>enveloped/cross-signed si-token</b>

CS -> CS: Check cross-signature from Provider\nCheck si-token from Consumer
CS -> Provider: Response: Verifiable Presentation (VP)\nincl. Credential (VC)

Provider -> Provider: Check VP and VCs
Provider -> Consumer: Response: Actual data

```