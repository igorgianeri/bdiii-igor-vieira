# Importa o Flask para criar a aplicação web
from flask import Flask, request, jsonify, render_template
# Importa o cliente Redis para Python
import redis

# Cria a aplicação Flask
app = Flask(__name__)

# Conecta ao servidor Redis rodando no localhost na porta padrão 6379
r = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)

# Função para inserir dados iniciais no Redis, se ainda não existirem
def inicializar_dados():
    # Verifica se a lista "produtos" já existe no Redis
    if not r.exists("produtos"):
        # Lista de produtos exemplo (id, nome, preço, estoque, categoria)
        produtos = [
            (1, "Notebook Gamer", "4500.00", "12", "Informática"),
            (2, "Mouse sem fio", "150.00", "50", "Acessórios"),
            (3, "Teclado Mecânico", "350.00", "30", "Acessórios"),
            (4, "Monitor 24\"", "900.00", "20", "Informática")
        ]
        # Loop para adicionar cada produto no Redis
        for id, nome, preco, estoque, categoria in produtos:
            # Cria um hash com os dados do produto
            r.hset(f"produto:{id}", mapping={
                "nome": nome,
                "preco": preco,
                "estoque": estoque,
                "categoria": categoria
            })
            # Adiciona o ID na lista "produtos"
            r.rpush("produtos", id)
            # Adiciona o ID no conjunto da categoria correspondente
            r.sadd(f"categoria:{categoria}", id)

# Executa a função para garantir que o banco tenha dados
inicializar_dados()

# Rota principal (carrega a página HTML)
@app.route("/")
def index():
    # Retorna o arquivo "index.html" que está na pasta templates
    return render_template("index.html")

# Rota para buscar produtos (com ou sem filtro de categoria)
@app.route("/buscar", methods=["GET"])
def buscar():
    # Pega o parâmetro "categoria" da URL (se existir)
    categoria = request.args.get("categoria")
    resultados = []  # Lista para armazenar os resultados

    if categoria:
        # Se o usuário informou uma categoria, busca só nessa categoria
        ids = r.smembers(f"categoria:{categoria}")
        for pid in ids:
            resultados.append(r.hgetall(f"produto:{pid}"))
    else:
        # Se não informou categoria, busca todos os produtos
        for pid in r.lrange("produtos", 0, -1):
            resultados.append(r.hgetall(f"produto:{pid}"))

    # Retorna os resultados no formato JSON
    return jsonify(resultados)
    
@app.route("/adicionar", methods=["POST"])
def adicionar():
    data = request.get_json()
    novo_id = r.incr("ultimo_id")  # cria um id incremental
    r.hset(f"produto:{novo_id}", mapping={
        "nome": data["nome"],
        "preco": data["preco"],
        "estoque": data["estoque"],
        "categoria": data["categoria"]
    })
    r.rpush("produtos", novo_id)
    r.sadd(f"categoria:{data['categoria']}", novo_id)
    return jsonify({"status": "ok", "id": novo_id})

# Executa a aplicação Flask
if __name__ == "__main__":
    app.run(debug=True)
    
