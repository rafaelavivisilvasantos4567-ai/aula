from flask import Flask, render_template, request, jsonify
import psycopg2
import os

app = Flask(__name__)

# 🔧 SUA CONNECTION STRING DO NEON (sem o 'psql' no início)
# Remova o 'psql ' do início e as aspas simples
DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://neondb_owner:npg_0wyUqmO6TBxd@ep-falling-poetry-a4osknmd-pooler.us-east-1.aws.neon.tech/neondb?sslmode=require')

def get_db_connection():
    """Conecta ao banco de dados"""
    try:
        # Para desenvolvimento local (sem DATABASE_URL)
        if not DATABASE_URL or 'localhost' in DATABASE_URL:
            conn = psycopg2.connect(
                host="localhost",
                database="postgres",
                user="postgres",
                password="1234",
                port="5433"
            )
            print("✅ Conectado ao PostgreSQL local (porta 5433)")
            return conn
       
        # Para produção (Neon)
        else:
            # Conecta diretamente com a URL do Neon
            conn = psycopg2.connect(DATABASE_URL)
            print("✅ Conectado ao Neon PostgreSQL na nuvem")
            return conn
           
    except Exception as e:
        print(f"❌ Erro na conexão: {e}")
        return None

def criar_tabela():
    """Cria a tabela se não existir"""
    conn = get_db_connection()
    if not conn:
        print("⚠️  Não foi possível conectar ao banco")
        return False
   
    try:
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS clientes (
                id SERIAL PRIMARY KEY,
                nome VARCHAR(100),
                email VARCHAR(100),
                telefone VARCHAR(20)
            )
        """)
        conn.commit()
        print("✅ Tabela 'clientes' criada/verificada")
        return True
    except Exception as e:
        print(f"❌ Erro ao criar tabela: {e}")
        return False
    finally:
        if conn:
            conn.close()

# Rota principal
@app.route('/')
def home():
    return render_template('index.html')

# GET - Listar todos os clientes
@app.route('/clientes')
def get_clientes():
    conn = get_db_connection()
    if not conn:
        return jsonify({'erro': 'Falha na conexão com o banco'}), 500
   
    try:
        cur = conn.cursor()
        cur.execute("SELECT * FROM clientes ORDER BY id")
        rows = cur.fetchall()
       
        # Converter para dicionários
        clientes = []
        for row in rows:
            clientes.append({
                'id': row[0],
                'nome': row[1],
                'email': row[2],
                'telefone': row[3]
            })
       
        return jsonify(clientes)
    except Exception as e:
        return jsonify({'erro': str(e)}), 500
    finally:
        if conn:
            conn.close()

# POST - Adicionar cliente
@app.route('/clientes', methods=['POST'])
def add_cliente():
    data = request.json
    conn = get_db_connection()
    if not conn:
        return jsonify({'erro': 'Falha na conexão com o banco'}), 500
   
    try:
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO clientes (nome, email, telefone) VALUES (%s, %s, %s) RETURNING id",
            (data['nome'], data['email'], data.get('telefone', ''))
        )
        id_novo = cur.fetchone()[0]
        conn.commit()
       
        mensagem = 'Cliente adicionado ao Neon!' if 'neon.tech' in DATABASE_URL else 'Cliente adicionado localmente!'
       
        return jsonify({'id': id_novo, 'msg': mensagem})
    except Exception as e:
        return jsonify({'erro': str(e)}), 500
    finally:
        if conn:
            conn.close()

# PUT - Atualizar cliente
@app.route('/clientes/<int:id>', methods=['PUT'])
def update_cliente(id):
    data = request.json
    conn = get_db_connection()
    if not conn:
        return jsonify({'erro': 'Falha na conexão com o banco'}), 500
   
    try:
        cur = conn.cursor()
        cur.execute(
            "UPDATE clientes SET nome=%s, email=%s, telefone=%s WHERE id=%s",
            (data['nome'], data['email'], data.get('telefone', ''), id)
        )
        conn.commit()
        return jsonify({'msg': 'Cliente atualizado'})
    except Exception as e:
        return jsonify({'erro': str(e)}), 500
    finally:
        if conn:
            conn.close()

# DELETE - Remover cliente
@app.route('/clientes/<int:id>', methods=['DELETE'])
def delete_cliente(id):
    conn = get_db_connection()
    if not conn:
        return jsonify({'erro': 'Falha na conexão com o banco'}), 500
   
    try:
        cur = conn.cursor()
        cur.execute("DELETE FROM clientes WHERE id=%s", (id,))
        conn.commit()
        return jsonify({'msg': 'Cliente removido'})
    except Exception as e:
        return jsonify({'erro': str(e)}), 500
    finally:
        if conn:
            conn.close()

# Rota para verificar status
@app.route('/status')
def status():
    conn = get_db_connection()
   
    if conn:
        try:
            cur = conn.cursor()
            cur.execute("SELECT version()")
            versao = cur.fetchone()[0]
           
            cur.execute("SELECT COUNT(*) FROM clientes")
            total = cur.fetchone()[0]
           
            conn.close()
           
            return jsonify({
                'status': 'online',
                'banco': 'Neon PostgreSQL' if 'neon.tech' in DATABASE_URL else 'PostgreSQL Local',
                'versao': versao,
                'total_clientes': total
            })
        except Exception as e:
            return jsonify({'status': 'error', 'erro': str(e)})
    else:
        return jsonify({'status': 'offline', 'erro': 'Não conectado ao banco'})

# Iniciar app
if __name__ == '__main__':
    criar_tabela()
   
    # Porta para Render (usar variável de ambiente) ou 5000 local
    port = int(os.getenv('PORT', 5000))
   
    print("=" * 50)
    print("🚀 SISTEMA DE CADASTRO DE CLIENTES")
    print("=" * 50)
   
    if 'neon.tech' in DATABASE_URL:
        print("🌐 Ambiente: PRODUÇÃO (Neon PostgreSQL)")
        print(f"📡 Host: ep-falling-poetry-a4osknmd-pooler.us-east-1.aws.neon.tech")
    else:
        print("💻 Ambiente: DESENVOLVIMENTO (PostgreSQL Local)")
        print("🔌 Banco: PostgreSQL (porta 5433)")
   
    print(f"🔧 Porta: {port}")
    print("=" * 50)
    print("🌐 Servidor rodando...")
   
    app.run(host='0.0.0.0', port=port, debug=True)
