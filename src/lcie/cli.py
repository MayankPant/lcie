import typer
from indexer.pipeline import index_repo


app = typer.Typer()

@app.command()
def index(path: str):
    index_repo(path)
    
@app.command()
def ask(query: str):
    print("Query: ", query)
    
    
if __name__ == "__main__":
    app()