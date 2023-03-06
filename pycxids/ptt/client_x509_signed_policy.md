```plantuml

participant client
participant server

== initial registration (only once) ==
client -> server: register (upload) x509 certificate
server -> server: store x509 certificate (fingerprint as name)
note over server
Of course this is unsecure!
Proper 'registration' process needs
to be in place!
end note
== fetching data ==
client -> server: HEAD
server -> client: Response HEADER only (with 'policy')

client -> client: get unique (contains hash) 'policy' url from header
    

client -> client: read private key
client -> client: create JWT with claim payload 'policy'
client -> client: JWT header 'x5tS256'\n(b64 urlsafe certificate fingerprint)
client -> client: sign JWT

    
client -> server: GET (JWT in 'policy' header)
server -> server: Get JWT from 'policy' (http) header

server -> server: Read 'x5tS256' from policy JWT header
server -> server: Read 'pinned' x509 certificate from storage\nand get public key from it
server -> server: Verify the 'policy' JWT signature

server -> server: Extract 'policy' from verified token payload

server -> server: Decide access based on policy
server -> client: Response: Actual data
    
```