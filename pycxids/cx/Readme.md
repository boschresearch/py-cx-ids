Catena-X specific services go into here

# Mocks
`mocks.py` contains the CX central services that are mocked.


## IATP / STS / DIM

IATP is the "identity and trust protocol", aka as DCP "dectralize claims protocol".

DRAFT: https://eclipse-dataspace-dcp.github.io/decentralized-claims-protocol/v1.0-RC3/

The code in here, is a way to "mock" this for local development usage and learning. It is NOT meant as an official implementation of it! Do not use in production environment!

![IATP STS DIM Flow](iatp_sts_dim_flow.png)

### grantAccess request
```
{
 "grantAccess": {
  "scope": "read",
  "credentialTypes": [
   "MembershipCredential"
  ],
  "consumerDid": "did:web:dev%3A13000:BPNLconsumer",
  "providerDid": "did:web:dev%3A13000:BPNLprovider"
 }
}
```


### signToken Request
```
{
 "signToken": {
  "audience": "did:web:dev%3A13000:BPNLconsumer",
  "subject": "did:web:dev%3A13000:BPNLprovider",
  "issuer": "did:web:dev%3A13000:BPNLprovider",
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJjbGllbnRfaWQiOiJCUE5MY29uc3VtZXIiLCJleHAiOjE3NDc2NjAzMzd9.fw4DO6jMOliY1FJkYUmKdCymTHJqTsbPYWnALd_Dij8"
 }
}
```
with the `token` from our `/token` endpoint. The claims is just our dummy claims. This is not for production use!
```
{
    "alg": "HS256",
    "typ": "JWT"
}
{
    "client_id": "BPNLconsumer",
    "exp": 1747660337
}
```
Beware, that EDC does cache tokens during the `exp` lifteime of the tokens. When code is changed, restart EDC!


# Services
`services.py` contains the client side to access such services - the mocked once or the original central ones.
