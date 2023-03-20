```plantuml
== regular contract negoatiation ==
consumer -> provider: negotiate contract
provider -> consumer: agreement_id
consumer -> provider: start transfer process (with agreement_id)
provider -> consumer: access token
consumer -> provider: Request data (with access token)
provider -> consumer: data

== attacker ==
attacker -> attacker: Gets to know agreement_id\n(and asset_id) from consumer or provider
note over provider, attacker
leave out negotation process and start right with:
end note
attacker -> provider: Start transfer process (with 'stolen' agreement_id)
note over provider, attacker
attacker needs to be a valid dataspace
participant, meaning, get a valid DAPS token
to be able to communicate with the provider
end note
provider -> attacker: access token
attacker -> provider: Request data (with access token)
provider -> attacker: data
note over provider, attacker
data is sent to the attacker under the
contract of consumer and provider (same
contract agreement_id)!
end note


```