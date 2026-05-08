import streamlit as st
import json
import os
import hashlib
import base64
import html
from datetime import date, datetime

st.set_page_config(page_title="TaskFlow", layout="wide")

ARQUIVO_TAREFAS = "tarefas.json"
ARQUIVO_USUARIOS = "usuarios.json"

TOKEN_CADASTRO = "123456"

STATUS = ["A Fazer", "Em Andamento", "Em Revisão", "Concluído"]
STATUS_ATIVOS = ["A Fazer", "Em Andamento", "Em Revisão"]
PRIORIDADES = ["Urgente", "Alta", "Média", "Baixa"]

ICONES = {
    "Baixa": "🔵",
    "Média": "🟡",
    "Alta": "🟠",
    "Urgente": "🔴"
}

PESO_PRIORIDADE = {
    "Urgente": 1,
    "Alta": 2,
    "Média": 3,
    "Baixa": 4
}


def gerar_hash(senha):
    return hashlib.sha256(senha.encode()).hexdigest()


def carregar_json(arquivo):
    if os.path.exists(arquivo):
        try:
            with open(arquivo, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            return []
    return []


def salvar_json(arquivo, dados):
    with open(arquivo, "w", encoding="utf-8") as f:
        json.dump(dados, f, ensure_ascii=False, indent=4)


def carregar_usuarios():
    return carregar_json(ARQUIVO_USUARIOS)


def salvar_usuarios(usuarios):
    salvar_json(ARQUIVO_USUARIOS, usuarios)


def carregar_tarefas():
    return carregar_json(ARQUIVO_TAREFAS)


def salvar_tarefas():
    salvar_json(ARQUIVO_TAREFAS, st.session_state.tarefas)


def corrigir_usuario(usuario):
    return {
        "usuario": usuario.get("usuario", ""),
        "senha": usuario.get("senha", ""),
        "foto": usuario.get("foto", ""),
        "foto_tipo": usuario.get("foto_tipo", "image/png")
    }


def corrigir_tarefa(tarefa):
    prioridade = tarefa.get("prioridade", "Baixa")
    status = tarefa.get("status", "A Fazer")

    if prioridade not in PRIORIDADES:
        prioridade = "Baixa"

    if status not in STATUS:
        status = "A Fazer"

    return {
        "nome": tarefa.get("nome", "Sem nome"),
        "responsavel": tarefa.get("responsavel", ""),
        "descricao": tarefa.get("descricao", ""),
        "prioridade": prioridade,
        "prazo": tarefa.get("prazo", ""),
        "hora": tarefa.get("hora", ""),
        "status": status,
        "criado_por": tarefa.get("criado_por", "")
    }


def usuarios_nomes():
    usuarios = carregar_usuarios()
    return [u.get("usuario", "") for u in usuarios if u.get("usuario")]


def buscar_usuario(nome):
    usuarios = carregar_usuarios()
    for u in usuarios:
        if u.get("usuario") == nome:
            return corrigir_usuario(u)
    return None


def salvar_foto_usuario(nome, foto_base64, foto_tipo):
    usuarios = carregar_usuarios()

    for u in usuarios:
        if u.get("usuario") == nome:
            u["foto"] = foto_base64
            u["foto_tipo"] = foto_tipo

    salvar_usuarios(usuarios)


def data_valida(texto):
    try:
        return datetime.strptime(texto, "%Y-%m-%d").date()
    except:
        return None


def ir_para(pagina):
    st.query_params["pagina"] = pagina
    st.rerun()


def mostrar_avatar_clicavel(usuario_nome):
    usuario = buscar_usuario(usuario_nome)
    nome_seguro = html.escape(usuario_nome)

    if usuario and usuario.get("foto"):
        src = f"data:{usuario.get('foto_tipo', 'image/png')};base64,{usuario['foto']}"

        st.markdown(
            f"""
            <a href="?pagina=Perfil" style="text-decoration:none;color:white;">
                <div style="text-align:center; width:90px; margin-left:auto;">
                    <img src="{src}"
                    style="
                        width:58px;
                        height:58px;
                        border-radius:50%;
                        object-fit:cover;
                        border:2px solid white;
                        display:block;
                        margin:auto;
                    ">
                    <div style="text-align:center;font-size:13px;margin-top:6px;">
                        {nome_seguro}
                    </div>
                </div>
            </a>
            """,
            unsafe_allow_html=True
        )
    else:
        letra = nome_seguro[:1].upper()

        st.markdown(
            f"""
            <a href="?pagina=Perfil" style="text-decoration:none;color:white;">
                <div style="text-align:center; width:90px; margin-left:auto;">
                    <div style="
                        width:58px;
                        height:58px;
                        border-radius:50%;
                        background:#334155;
                        display:flex;
                        align-items:center;
                        justify-content:center;
                        margin:auto;
                        border:2px solid white;
                        font-size:24px;
                        font-weight:bold;
                    ">
                        {letra}
                    </div>
                    <div style="text-align:center;font-size:13px;margin-top:6px;">
                        {nome_seguro}
                    </div>
                </div>
            </a>
            """,
            unsafe_allow_html=True
        )


if "logado" not in st.session_state:
    st.session_state.logado = False

if "usuario" not in st.session_state:
    st.session_state.usuario = ""


def tela_login():
    st.title("TaskFlow")
    st.caption("Sistema de Gestão Visual de Tarefas")

    aba_login, aba_cadastro, aba_reset = st.tabs(
        ["Entrar", "Criar conta", "Redefinir senha"]
    )

    with aba_login:
        usuario = st.text_input("Usuário", key="login_usuario")
        senha = st.text_input("Senha", type="password", key="login_senha")

        if st.button("Entrar", key="btn_login"):
            usuarios = carregar_usuarios()
            senha_hash = gerar_hash(senha)

            for u in usuarios:
                if u["usuario"] == usuario and u["senha"] == senha_hash:
                    st.session_state.logado = True
                    st.session_state.usuario = usuario
                    st.rerun()

            st.error("Usuário ou senha inválidos.")

    with aba_cadastro:
        novo_usuario = st.text_input("Novo usuário", key="cad_usuario")
        nova_senha = st.text_input("Nova senha", type="password", key="cad_senha")
        confirmar = st.text_input("Confirmar senha", type="password", key="cad_confirmar")
        token = st.text_input("Token de cadastro", type="password", key="cad_token")

        if st.button("Criar conta", key="btn_cadastro"):
            usuarios = carregar_usuarios()

            if token != TOKEN_CADASTRO:
                st.error("Token de cadastro inválido.")
            elif novo_usuario.strip() == "":
                st.error("Digite um usuário.")
            elif nova_senha.strip() == "":
                st.error("Digite uma senha.")
            elif nova_senha != confirmar:
                st.error("As senhas não coincidem.")
            elif any(u["usuario"] == novo_usuario for u in usuarios):
                st.error("Usuário já existe.")
            else:
                usuarios.append({
                    "usuario": novo_usuario,
                    "senha": gerar_hash(nova_senha),
                    "foto": "",
                    "foto_tipo": "image/png"
                })
                salvar_usuarios(usuarios)
                st.success("Conta criada com sucesso.")

    with aba_reset:
        usuario_reset = st.text_input("Usuário", key="reset_usuario")
        nova_senha_reset = st.text_input("Nova senha", type="password", key="reset_senha")
        confirmar_reset = st.text_input("Confirmar nova senha", type="password", key="reset_confirmar")

        if st.button("Redefinir senha", key="btn_reset"):
            usuarios = carregar_usuarios()

            if nova_senha_reset != confirmar_reset:
                st.error("As senhas não coincidem.")
            else:
                encontrado = False

                for u in usuarios:
                    if u["usuario"] == usuario_reset:
                        u["senha"] = gerar_hash(nova_senha_reset)
                        encontrado = True

                if encontrado:
                    salvar_usuarios(usuarios)
                    st.success("Senha redefinida.")
                else:
                    st.error("Usuário não encontrado.")


if not st.session_state.logado:
    tela_login()
    st.stop()


usuarios_corrigidos = [corrigir_usuario(u) for u in carregar_usuarios()]
salvar_usuarios(usuarios_corrigidos)

if "tarefas" not in st.session_state:
    tarefas = carregar_tarefas()
    st.session_state.tarefas = [corrigir_tarefa(t) for t in tarefas]
    salvar_tarefas()


pagina_url = st.query_params.get("pagina", "Quadro")

if pagina_url not in ["Quadro", "Concluídas", "Perfil"]:
    pagina_url = "Quadro"


topo_esq, topo_meio, topo_dir = st.columns([5, 2, 1])

with topo_esq:
    st.title("TaskFlow")

with topo_meio:
    if st.button("Sair"):
        st.session_state.logado = False
        st.session_state.usuario = ""
        st.query_params.clear()
        st.rerun()

with topo_dir:
    mostrar_avatar_clicavel(st.session_state.usuario)


with st.sidebar:
    st.markdown("## Menu")

    if st.button("📋 Quadro", use_container_width=True):
        ir_para("Quadro")

    if st.button("✅ Concluídas", use_container_width=True):
        ir_para("Concluídas")

    st.caption("Clique na foto para abrir o perfil.")

    st.divider()

    if pagina_url == "Quadro":
        st.header("Nova tarefa")

        nomes_usuarios = usuarios_nomes()

        with st.form("form_tarefa"):
            nome = st.text_input("Nome da tarefa")

            if nomes_usuarios:
                responsavel = st.selectbox("Responsável", nomes_usuarios)
            else:
                responsavel = ""

            descricao = st.text_area("Descrição")
            prioridade = st.selectbox("Prioridade", PRIORIDADES)
            prazo = st.date_input("Prazo", date.today())
            hora = st.time_input("Hora")

            criar = st.form_submit_button("Criar tarefa")

            if criar:
                if nome.strip() == "":
                    st.error("Digite o nome da tarefa.")
                elif responsavel.strip() == "":
                    st.error("Cadastre um usuário para ser responsável.")
                else:
                    st.session_state.tarefas.append({
                        "nome": nome,
                        "responsavel": responsavel,
                        "descricao": descricao,
                        "prioridade": prioridade,
                        "prazo": str(prazo),
                        "hora": str(hora),
                        "status": "A Fazer",
                        "criado_por": st.session_state.usuario
                    })
                    salvar_tarefas()
                    st.rerun()

        st.divider()
        st.header("Filtros")
        pesquisa = st.text_input("Pesquisar")
        filtro_status = st.selectbox("Status", ["Todos"] + STATUS_ATIVOS)
        filtro_prioridade = st.selectbox("Prioridade", ["Todas"] + PRIORIDADES)

    elif pagina_url == "Concluídas":
        st.header("Filtros avançados")

        pesquisa_concluidas = st.text_input("Pesquisar")
        responsavel_concluidas = st.selectbox(
            "Responsável",
            ["Todos"] + usuarios_nomes()
        )
        criador_concluidas = st.selectbox(
            "Criado por",
            ["Todos"] + usuarios_nomes()
        )
        prioridade_concluidas = st.multiselect(
            "Prioridades",
            PRIORIDADES,
            default=PRIORIDADES
        )

        ordenar_concluidas = st.selectbox(
            "Ordenar por",
            [
                "Prioridade",
                "Prazo mais próximo",
                "Prazo mais distante",
                "Nome A-Z",
                "Responsável A-Z"
            ]
        )

        st.write("Período do prazo")
        data_inicio_concluidas = st.date_input(
            "De",
            value=date(2020, 1, 1),
            key="data_inicio_concluidas"
        )
        data_fim_concluidas = st.date_input(
            "Até",
            value=date.today(),
            key="data_fim_concluidas"
        )

    else:
        st.info("Perfil aberto pela foto.")


if pagina_url == "Quadro":
    tarefas_ativas = [
        t for t in st.session_state.tarefas
        if t["status"] != "Concluído"
    ]

    st.subheader("Resumo")

    m1, m2, m3, m4 = st.columns(4)

    m1.metric("Ativas", len(tarefas_ativas))
    m2.metric("A Fazer", len([t for t in tarefas_ativas if t["status"] == "A Fazer"]))
    m3.metric("Em Andamento", len([t for t in tarefas_ativas if t["status"] == "Em Andamento"]))
    m4.metric("Em Revisão", len([t for t in tarefas_ativas if t["status"] == "Em Revisão"]))

    st.info("As tarefas são ordenadas automaticamente pela prioridade: Urgente → Alta → Média → Baixa.")

    st.divider()
    st.subheader("Quadro de tarefas")

    col1, col2, col3 = st.columns(3)

    colunas = {
        "A Fazer": col1,
        "Em Andamento": col2,
        "Em Revisão": col3
    }

    for nome_status, coluna in colunas.items():
        with coluna:
            st.markdown(f"### {nome_status}")

            tarefas_da_coluna = [
                (i, t)
                for i, t in enumerate(st.session_state.tarefas)
                if t["status"] == nome_status
            ]

            tarefas_da_coluna = sorted(
                tarefas_da_coluna,
                key=lambda item: PESO_PRIORIDADE.get(item[1]["prioridade"], 99)
            )

            mostradas = 0

            for i, tarefa in tarefas_da_coluna:
                texto = (
                    tarefa["nome"] +
                    tarefa["responsavel"] +
                    tarefa["descricao"]
                ).lower()

                if pesquisa.lower() not in texto:
                    continue

                if filtro_status != "Todos" and tarefa["status"] != filtro_status:
                    continue

                if filtro_prioridade != "Todas" and tarefa["prioridade"] != filtro_prioridade:
                    continue

                mostradas += 1
                icone = ICONES.get(tarefa["prioridade"], "⚪")

                with st.container(border=True):
                    st.markdown(f"#### {icone} {tarefa['nome']}")

                    with st.expander("Abrir tarefa"):
                        st.write(f"**Responsável:** {tarefa['responsavel']}")
                        st.write(f"**Prioridade:** {tarefa['prioridade']}")
                        st.write(f"**Prazo:** {tarefa['prazo']}")
                        st.write(f"**Hora:** {tarefa['hora']}")
                        st.write(f"**Criado por:** {tarefa.get('criado_por', '')}")

                        if tarefa["descricao"]:
                            st.write("**Descrição:**")
                            st.write(tarefa["descricao"])

                    indice_atual = STATUS.index(tarefa["status"])
                    proximo_status = STATUS[indice_atual + 1]

                    if st.button(
                        f"Avançar para {proximo_status}",
                        key=f"avancar_{i}"
                    ):
                        st.session_state.tarefas[i]["status"] = proximo_status
                        salvar_tarefas()
                        st.rerun()

                    with st.expander("Editar"):
                        novo_nome = st.text_input("Nome", value=tarefa["nome"], key=f"nome_{i}")

                        nomes_usuarios_edit = usuarios_nomes()

                        if tarefa["responsavel"] in nomes_usuarios_edit:
                            indice_resp = nomes_usuarios_edit.index(tarefa["responsavel"])
                        else:
                            indice_resp = 0

                        novo_responsavel = st.selectbox(
                            "Responsável",
                            nomes_usuarios_edit,
                            index=indice_resp,
                            key=f"resp_{i}"
                        )

                        nova_descricao = st.text_area("Descrição", value=tarefa["descricao"], key=f"desc_{i}")

                        nova_prioridade = st.selectbox(
                            "Prioridade",
                            PRIORIDADES,
                            index=PRIORIDADES.index(tarefa["prioridade"]),
                            key=f"prio_{i}"
                        )

                        novo_prazo = st.text_input("Prazo", value=tarefa["prazo"], key=f"prazo_{i}")
                        nova_hora = st.text_input("Hora", value=tarefa["hora"], key=f"hora_{i}")

                        if st.button("Salvar edição", key=f"salvar_{i}"):
                            st.session_state.tarefas[i]["nome"] = novo_nome
                            st.session_state.tarefas[i]["responsavel"] = novo_responsavel
                            st.session_state.tarefas[i]["descricao"] = nova_descricao
                            st.session_state.tarefas[i]["prioridade"] = nova_prioridade
                            st.session_state.tarefas[i]["prazo"] = novo_prazo
                            st.session_state.tarefas[i]["hora"] = nova_hora
                            salvar_tarefas()
                            st.rerun()

                    if st.button("Excluir", key=f"excluir_{i}"):
                        st.session_state.tarefas.pop(i)
                        salvar_tarefas()
                        st.rerun()

            if mostradas == 0:
                st.info("Nenhuma tarefa")


elif pagina_url == "Concluídas":
    st.subheader("Tarefas concluídas")

    concluidas = [
        (i, t)
        for i, t in enumerate(st.session_state.tarefas)
        if t["status"] == "Concluído"
    ]

    filtradas = []

    for i, tarefa in concluidas:
        texto = (
            tarefa["nome"] +
            tarefa["responsavel"] +
            tarefa["descricao"] +
            tarefa.get("criado_por", "")
        ).lower()

        if pesquisa_concluidas.lower() not in texto:
            continue

        if responsavel_concluidas != "Todos" and tarefa["responsavel"] != responsavel_concluidas:
            continue

        if criador_concluidas != "Todos" and tarefa.get("criado_por", "") != criador_concluidas:
            continue

        if tarefa["prioridade"] not in prioridade_concluidas:
            continue

        prazo_data = data_valida(tarefa.get("prazo", ""))

        if prazo_data:
            if prazo_data < data_inicio_concluidas or prazo_data > data_fim_concluidas:
                continue

        filtradas.append((i, tarefa))

    if ordenar_concluidas == "Prioridade":
        filtradas = sorted(
            filtradas,
            key=lambda item: PESO_PRIORIDADE.get(item[1]["prioridade"], 99)
        )
    elif ordenar_concluidas == "Prazo mais próximo":
        filtradas = sorted(
            filtradas,
            key=lambda item: data_valida(item[1].get("prazo", "")) or date.max
        )
    elif ordenar_concluidas == "Prazo mais distante":
        filtradas = sorted(
            filtradas,
            key=lambda item: data_valida(item[1].get("prazo", "")) or date.min,
            reverse=True
        )
    elif ordenar_concluidas == "Nome A-Z":
        filtradas = sorted(
            filtradas,
            key=lambda item: item[1]["nome"].lower()
        )
    elif ordenar_concluidas == "Responsável A-Z":
        filtradas = sorted(
            filtradas,
            key=lambda item: item[1]["responsavel"].lower()
        )

    st.metric("Resultado encontrado", len(filtradas))

    for i, tarefa in filtradas:
        icone = ICONES.get(tarefa["prioridade"], "⚪")

        with st.container(border=True):
            st.markdown(f"#### {icone} {tarefa['nome']}")

            with st.expander("Abrir tarefa concluída"):
                st.write(f"**Responsável:** {tarefa['responsavel']}")
                st.write(f"**Prioridade:** {tarefa['prioridade']}")
                st.write(f"**Prazo:** {tarefa['prazo']}")
                st.write(f"**Hora:** {tarefa['hora']}")
                st.write(f"**Criado por:** {tarefa.get('criado_por', '')}")

                if tarefa["descricao"]:
                    st.write("**Descrição:**")
                    st.write(tarefa["descricao"])

            st.success("Concluída")

    if len(filtradas) == 0:
        st.info("Nenhuma tarefa concluída encontrada.")


elif pagina_url == "Perfil":
    st.subheader("Perfil")

    usuario_atual = buscar_usuario(st.session_state.usuario)

    perfil_col1, perfil_col2 = st.columns([1, 3])

    with perfil_col1:
        if usuario_atual and usuario_atual.get("foto"):
            bytes_foto = base64.b64decode(usuario_atual["foto"])
            st.image(bytes_foto, width=128)
        else:
            st.info("Sem foto")

    with perfil_col2:
        st.write(f"**Usuário:** {st.session_state.usuario}")
        st.info("A imagem ou GIF precisa ter exatamente 128x128 pixels.")

        arquivo_foto = st.file_uploader(
            "Enviar foto/GIF 128x128 pixels",
            type=["png", "jpg", "jpeg", "gif"]
        )

        if arquivo_foto is not None:
            dados = arquivo_foto.read()
            foto_base64 = base64.b64encode(dados).decode("utf-8")
            foto_tipo = arquivo_foto.type

            st.image(dados, width=128)
            st.caption("Prévia 128x128 pixels.")

            if st.button("Salvar imagem do perfil"):
                salvar_foto_usuario(
                    st.session_state.usuario,
                    foto_base64,
                    foto_tipo
                )
                st.success("Imagem salva.")
                st.rerun()