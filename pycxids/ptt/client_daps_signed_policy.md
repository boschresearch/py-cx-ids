```plantuml

participant client
participant server
participant "Auth Server (e.g. DAPS)" as daps

client -> server: HEAD
server -> client: Response HEADER only (with 'policy')

client -> client: get unique (contains hash) 'policy' url from header
    
client -> daps: Request token (provide unique policy url)
daps -> daps: Check client credentials
daps -> daps: Add policy url to the token 'aud' field
daps -> client: Response: token

client -> server: GET
server -> server: Check 'policy' header
server -> daps: Request DAPS public key (JWKS)
daps -> server:

server -> server: Verify the 'policy' token signature

server -> server: Extract 'policy' from verified token

server -> server: Decide access based on policy
server -> client: Response: Actual data
    
```