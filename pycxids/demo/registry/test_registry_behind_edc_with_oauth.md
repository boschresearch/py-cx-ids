```plantuml

skinparam ParticipantPadding 20
skinparam BoxPadding 10

box "Consumer"
participant consumer_client
participant consumer_control_plane
end box

box "Provider"
participant provider_control_plane
participant provider_data_plane
participant oauth_server
participant registry
participant aasx_server
participant provider_client
end box

== Init Registry Asset ==
provider_client -> provider_control_plane: Create 'registry' EDC Asset
note over provider_control_plane
Additional dataAddress properties for oAuth
        oauth2:clientId
        oauth2:clientSecret
        oauth2:tokenUrl
        oauth2:scope
end note

== Fetch data from the registry ==

consumer_client -> consumer_control_plane: Negotiate contract
consumer_control_plane -> consumer_client: agreement_id

consumer_client -> consumer_control_plane: Start 'Transfer' with agreement_id
consumer_control_plane -> consumer_client: Provider EDR token

consumer_client -> provider_data_plane: Fetch
provider_data_plane -> oauth_server: Get token with credentials from the asset's dataAddress
oauth_server -> provider_data_plane: Registry Access token
provider_data_plane -> registry: (with Registry Access token)
registry -> provider_data_plane
provider_data_plane -> consumer_client

== Init one or multiple Submodel Endpoints ==

provider_client -> provider_control_plane: Create EDC Asset
note over provider_control_plane
can use oauth, too, but doesn't have to
Depends on the submodel endpoint / AASX Server auth
end note

== Fetch submodel data ==
consumer_client -> consumer_client: parse EDC asset_id from AAS submodel

consumer_client -> consumer_control_plane: Negotiate contract
consumer_control_plane -> consumer_client: agreement_id

consumer_client -> consumer_control_plane: Start 'Transfer' with agreement_id
consumer_control_plane -> consumer_client: Provider EDR token

consumer_client -> provider_data_plane: Fetch
provider_data_plane -> aasx_server:
note over aasx_server
aasx_server can be any kind of backend system!

Starting with product-edc 0.3.0
header contains 'edc-contract-agreement-id'
end note
opt
aasx_server -> provider_control_plane: get details for contract ('edc-contract-agreement-id')
provider_control_plane -> aasx_server
note over aasx_server
Because of a bug, the details currently (0.3.0)
do NOT contain informatin about the contract partners!
end note
end opt
aasx_server -> provider_data_plane:
provider_data_plane -> consumer_client

```