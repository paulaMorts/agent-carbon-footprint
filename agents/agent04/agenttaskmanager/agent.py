from google.adk.agents.llm_agent import Agent
from trello import TrelloClient
from dotenv import load_dotenv
from datetime import datetime
import os

load_dotenv()

# Suas credenciais
API_KEY = os.getenv('TRELLO_API_KEY')
API_SECRET = os.getenv('TRELLO_API_SECRET')
TOKEN = os.getenv('TRELLO_TOKEN')

def get_temporal_context():
    now = datetime.now()
    return now.strftime('%Y/%m/%d %H:%M:%S')


def adicionar_tarefa(nome_da_task: str, descricao_da_task: str, due_date: str):
    
    client = TrelloClient(
        api_key=API_KEY,
        api_secret=API_SECRET,
        token=TOKEN
    )
    
    client.list_boards()
    # Obter o board (você precisa do ID ou nome do board)
    boards = client.list_boards()
    meu_board = [b for b in boards if b.name == 'ai-project'][0]

    # Obter a lista onde quer adicionar o card
    listas = meu_board.list_lists()

    minha_lista = [l for l in listas if l.name.upper() == 'TO DO' or l.name.upper()== 'A FAZER'][0]
    
    # Criar o card (task)
    minha_lista.add_card(
        name=nome_da_task,
        desc=descricao_da_task,
        due=due_date
    )

def listar_tarefas(status: str = "todas"):
    client = TrelloClient(
        api_key=API_KEY,
        api_secret=API_SECRET,
        token=TOKEN
    )

    boards = client.list_boards()
    meu_board = [b for b in boards if b.name == 'DIO'][0]
    listas = meu_board.list_lists()        

    if status.lower() == "todas":
        listas_filtradas = listas
    elif status.lower() == "a fazer":
        listas_filtradas = [l for l in listas if l.name.upper() in ['A FAZER', 'TO DO', 'TODO']]
    elif status.lower() == "em andamento":
        listas_filtradas = [l for l in listas if l.name.upper() in ['EM ANDAMENTO', 'DOING']]
    elif status.lower() == "concluido":
        listas_filtradas = [l for l in listas if l.name.upper() in ['CONCLUÍDO', 'CONCLUIDO', 'DONE']]
    else:
        listas_filtradas = listas

    tarefas = []

    for lista in listas_filtradas:
        cards = lista.list_cards()
        for card in cards:
            tarefas.append({
                "nome": card.name,
                "descricao": card.desc,
                "vencimento": card.due,
                "status": lista.name,
                "id": card.id
            })
    
    return tarefas

def mudar_status_tarefa(nome_da_task: str, novo_status: str) -> str:
    try:
        client = TrelloClient(
            api_key=API_KEY,
            api_secret=API_SECRET,
            token=TOKEN
        )

        boards = client.list_boards()
        meu_board = [b for b in boards if b.name == 'DIO'][0]
        listas = meu_board.list_lists()
                       
        # Mapear status para listas
        status_map = {
            "a fazer": "A FAZER",
            "em andamento": "EM ANDAMENTO",
            "concluido": "CONCLUÍDO"
        }
        
        nome_lista_destino = status_map.get(novo_status.lower())

        if not nome_lista_destino:
            return f"❌ Status inválido. Use: 'a fazer', 'em andamento' ou 'concluido'"
        
        # Encontrar lista de destino
        lista_destino = next(
            (l for l in listas if l.name.upper() == nome_lista_destino.upper()), 
            None
        )

        if not lista_destino:
            return f"❌ Lista '{nome_lista_destino}' não encontrada no board"
        
         # Buscar card em todas as listas
        card_encontrado = None
        lista_origem = None

        for lista in listas:
            cards = lista.list_cards()
            card_encontrado = next(
                (c for c in cards if c.name.lower() == nome_da_task.lower()), 
                None
            )
            if card_encontrado:
                lista_origem = lista
                break
        
        if not card_encontrado:
            return f"❌ Card '{nome_da_task}' não encontrado"
        
        # Mover
        card_encontrado.change_list(lista_destino.id)
        return f"✅ '{nome_da_task}': {lista_origem.name} → {lista_destino.name}"
        except Exception as e:
        return f"❌ Erro: {str(e)}"

root_agent = Agent(
    model='gemini-2.5-flash',
    name='root_agent',
    description='A helpful assistant for create tasks.',
    instruction="""
        You are an Agent responsible to create tasks.
        Your role is to receive a task and create a card in Trello with the task's name and description.
        You should ask what activities I have planned for the day and create a card for each one.
        You initiate the conversation as soon as it's activated, asking what the day's tasks are.
        Always start the conversation by asking what the day's tasks are, providing the date using the get_temporal_context tool.
        Note that Trello considers the first day of the month as 0, so enter the correct date. 
        Its functions:
            1. Add new tasks
            2. List all tasks or filter by status
            3. Mark tasks as completed
            4. Remove tasks from the list
            5. Change the task status (e.g., from "A fazer" to "Em Andamento" and from "Em Andamento" to "Concluído")
            6. Generate a temporal context (current date and time) to organize the day's tasks.
    """,
)
