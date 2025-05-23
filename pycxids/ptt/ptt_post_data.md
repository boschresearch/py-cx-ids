```plantuml

title POST / Push of data with Usage Policies

participant client
participant server

client -> server: Http 'HEAD' request\nHeader: <b>Policy-Post</b>: '<Client_Policy_Uri>'
server -> server: Check if policy for incoming\ndata is acceptable and\nsign it
server -> client: Response Http header only\n(HEAD never returns body / content)\nHeader:\n<b>Policy-Post: server_signed(<Client_Policy_Uri>)\nPolicy: <Server_Policy_Uri>

note over client, server
<b>Policy-Post</b> is for pushed / post / put data
<b>Policy</b> is for response content

As always, the header is not mandatory.
E.g. a response is just a 200 / 201 ok and no content or
at least no usage policy applies to the content, the
<b>Policy</b> header can be omitted.
end note

client -> client: Read <b>Policy</b> from Http header\nand sign
    
client -> server: HTTP <b>POST</b> request\nHeader:\nPolicy-Post: server_signed(<Client_Policy_Uri>)\nPolicy: client_signed(<Server_Policy_Uri>)
server -> server: <b>Verify policy signature</b>\nand check own signed Client_Policy_Uri

server -> client: Response: data
    
```