from flask import Flask, render_template, request, jsonify
import redis

app = Flask(__name__)

# Conexão com Redis local
r = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)

# Inicializa dados de exemplo no Redis
def inicializar_dados():
    produtos = [
        {"nome": "Mouse Gamer", "preco": "150.00", "estoque": "30", "categoria": "Acessórios"},
        {"nome": "Teclado Mecânico", "preco": "350.00", "estoque": "20", "categoria": "Acessórios"},
        {"nome": "Notebook", "preco": "4500.00", "estoque": "10", "categoria": "Informática"},
    ]

    # Só insere se ainda não houver produtos
    if not r.exists("produtos"):
        for id, produto in enumerate(produtos, start=1):
            # Insere campo a campo (compatível com Redis 3.2)
            for campo, valor in produto.items():
                r.hset(f"produto:{id}", campo, valor)

            r.rpush("produtos", id)
            r.sadd(f"categoria:{produto['categoria']}", id)

        r.set("ultimo_id", len(produtos))

# Rota principal
@app.route("/")
def index():
    return render_template("index.html")

# Rota para buscar produtos
@app.route("/buscar", methods=["GET"])
def buscar():
    categoria = request.args.get("categoria")
    produtos = []

    if categoria:
        ids = r.smembers(f"categoria:{categoria}")
    else:
        ids = r.lrange("produtos", 0, -1)

    for id in ids:
        produto = r.hgetall(f"produto:{id}")
        if produto:
            produto["id"] = id
            produtos.append(produto)

    return jsonify(produtos)

# Rota para adicionar produtos
@app.route("/adicionar", methods=["POST"])
def adicionar():
    data = request.get_json()
    novo_id = r.incr("ultimo_id")

    # Insere campo a campo para compatibilidade
    for campo, valor in data.items():
        r.hset(f"produto:{novo_id}", campo, valor)

    r.rpush("produtos", novo_id)
    r.sadd(f"categoria:{data['categoria']}", novo_id)

    return jsonify({"status": "ok", "id": novo_id})

if __name__ == "__main__":
    inicializar_dados()
    app.run(debug=True)
