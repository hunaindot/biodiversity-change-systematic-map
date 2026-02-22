"""Enable running wos_embeddings as a module: python -m wos_embeddings"""

from .cli import main

if __name__ == "__main__":
    exit(main())
