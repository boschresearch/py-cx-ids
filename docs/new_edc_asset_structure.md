```plantuml

skinparam boxpadding 20

box "Consumer"
participant "App" as app
participant "Control Plane" as consumerCP
participant "Data Plane" as consumerDP
end box

database registry
participant keycloak
participant DAPS

box "Provider"
participant "Control Plane" as providerCP
participant "Data Plane" as providerDP
participant "Data Source" as backend
end box


== Lookup ==


== Negotiation ==
app -> consumerCP: start contract negotiation
consumerCP <-> providerCP: Negotiate Contract ('/contractnegotiations')
consumerCP -> app: contractNegotiationId

app -> consumerCP: start transfer
consumerCP -> providerCP: Transfer Data ('/transferprocess')
consumerCP -> app: transferprocessId
providerCP -> consumerCP: Response: *Provider* EDR Token
consumerCP -> consumerCP: Envelope into *Consumer* EDR Token
consumerCP --> app: async webhook call: *Consumer* EDR Token

app -> consumerCP: get agreementId for transfer
consumerCP -> app: agreementId

== Fetching Data ==

note over app
as long as agreementId is not part
of the EDR token, transfer via query param
end note
app -> consumerDP: Request: e.g. '/submodel?<b>agreementId=123</b>' \n (Authorization Header: *Consumer* EDR Token)
consumerDP -> consumerDP: 'Extract' *Provider* EDR from *Consumer* EDR 'envelope'
consumerDP -> providerDP: Request: e.g. '/submodel?agreementId=123' \n (Authorization Header: *Provider* EDR Token)

providerDP -> providerCP: Validate / decrypt \n *Provider* EDR \nin 'Authorization' Http Header field
providerCP -> providerDP: clear text 'dataAddress'\n(from Asset creation process)
providerDP -> backend: 'Forward' request \ne.g. Request: e.g. '/submodel?agreementId=123'\n(in the future: jwt / EDR token)

opt If required information is NOT part of the transferred token
backend -> providerCP: data for agreementId=123
providerCP -> backend: details, e.g. consumer ID
end opt
note over providerDP, backend
Right now, NO contract partners are part of the
agreement, nor the contract negotiation!
<b>This is release critical</b>
end note

backend -> backend: Decide access\nbased on agreement details
    
backend -> providerDP: Actual data, e.g. AssemblyPartRelationship
providerDP -> consumerDP
consumerDP -> app

    
```