from typing import List
from uuid import uuid4
from pycxids.utils.api import GeneralApi
from pycxids.models.generated.registry import AssetAdministrationShellDescriptorCollection, AssetAdministrationShellDescriptor, SubmodelDescriptor, Endpoint, ProtocolInformation, GlobalReference
from pycxids.models.cxregistry import CxSubmodelEndpoint, CxAas

from oauthlib.oauth2 import BackendApplicationClient
from requests_oauthlib import OAuth2Session


class Registry(GeneralApi):
    """
    Everything being close to the AAS Registry API goes here
    """
    def __init__(self, base_url: str, headers = None, client_id: str = None, client_secret: str = None, token_url: str = None, scope:str = None) -> None:
        """
        If client_id is given, try to fetch a token with the required other fields.
        If not, you can pass in 'headers' (with an Authorization) that will be used.
        """
        if client_id:
            client = BackendApplicationClient(client_id=client_id)
            oauth_session = OAuth2Session(client=client, scope=scope)
            token = oauth_session.fetch_token(token_url=token_url, client_id=client_id, client_secret=client_secret)
            access_token = token.get('access_token', None)
            if not access_token:
                print("Could not fetch access_token for the portal access.")
            # TODO: This could be improved. e.g. check token has expired, or use the session to fetch data...
            super().__init__(base_url=base_url, headers={'Authorization': f"Bearer {access_token}" })
        else:
            super().__init__(base_url=base_url, headers=headers)
    
    def get_shell_descriptors(self) -> AssetAdministrationShellDescriptorCollection:
        """
        Returns all AAS
        """
        data = self.get(path="/registry/shell-descriptors")
        # dirty workaround for pagination vs non-pagination issue
        data_pages = None
        if isinstance(data, List):
            data_pages = {
                'items': data,
                'total_items': len(data),
                'current_page': 1, # I think CX registry pages started with 1
                'total_pages': 1,
                'item_count': len(data),
            }
        else:
            data_pages = data

        if not data_pages:
            return None
        result = AssetAdministrationShellDescriptorCollection.parse_obj(data_pages)
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
