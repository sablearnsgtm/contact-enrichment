# ProspectKit provider registry
from .apollo import ApolloProvider
from .hunter import HunterProvider
from .prospeo import ProspeoProvider

PROVIDERS = {
    "apollo": ApolloProvider,
    "hunter": HunterProvider,
    "prospeo": ProspeoProvider,
}
