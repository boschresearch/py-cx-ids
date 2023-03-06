```plantuml

participant client
participant server

client -> server: Http 'HEAD' request
server -> client: Response Http header only\n(HEAD never returns body / content)

client -> client: Read policy from Http header\nand <b>sign policy</b>
    
client -> server: HTTP GET request (with 'signed policy')
server -> server: <b>Verify policy signature</b>

server -> client: Response: Actual data
    
```