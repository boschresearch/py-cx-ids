from typing import List
from uuid import uuid4
from pycxids.utils.api import GeneralApi
from pycxids.models.generated.registry import AssetAdministrationShellDescriptorCollection, AssetAdministrationShellDescriptor, SubmodelDescriptor, Endpoint, ProtocolInformation, GlobalReference
from pycxids.models.cxregistry import CxSubmodelEndpoint, CxAas

class Registry(GeneralApi):
    """
    Everything being close to the AAS Registry API goes here
    """
    def __init__(self, base_url: str, headers=None, username=None, password=None) -> None:
        super().__init__(base_url, headers, username, password)
    
    def get_shell_descriptors(self):
        data = self.get(path="/registry/shell-descriptors")
        result = AssetAdministrationShellDescriptorCollection.parse_obj(data)
        return result

    def _create_shell_descriptor(self, aas: AssetAdministrationShellDescriptor):
        """
        Private because rather not used directly
        """
        result = self.post(path="/registry/shell-descriptors", data=aas.dict())
        return result



class CxRegistry(Registry):
    """
    Every CX related simplification to use the AAS Registry goes here
    """
    def __init__(self, base_url: str, headers=None, username=None, password=None) -> None:
        super().__init__(base_url, headers, username, password)
    
    def create(self, aas: CxAas ):
        """
        Basically 'translates' from our simplified data structure into an official AAAs (Descriptor)
        before it is sent to the registry to create a AAS (or more precisely the 'Descriptor' of it)
        """
        submodel_descriptors:List[SubmodelDescriptor] = []
        for ep in aas.submodels:
            submodel_descriptors.append(
                SubmodelDescriptor(
                    identification=ep.identification,
                    idShort=ep.id_short,
                    semantic_id = GlobalReference(
                        value=[ep.semantic_id]
                    ),
                    endpoints=[
                        Endpoint(
                            interface="SUBMODEL-1.0",
                            protocol_information=ProtocolInformation(
                                endpointAddress=ep.endpoint_address,
                            )
                        )
                    ]
                )
            )
            

        aas_id = aas.identification
        original_aas: AssetAdministrationShellDescriptor = AssetAdministrationShellDescriptor(
            identification=aas_id,
            id_short = aas_id, # what is a more useful value here?
            global_asset_id=GlobalReference(value=[aas.cxid]),
            submodel_descriptors=submodel_descriptors,
        )
        print(original_aas)
        return self._create_shell_descriptor(aas=original_aas)
