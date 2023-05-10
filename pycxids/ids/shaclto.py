from rdflib import Graph
from rdflib import Dataset
from rdflib.namespace import RDF

g = Graph()
g.parse("./pycxids/ids/ContractOfferMessageShape.ttl")
print(g)


for s, p, o in g:
    print(s)
    print(p)
    print(o)
    print('---------')
#g.serialize(destination="output.jsonld", format="json-ld")
